"""Cross-entropy method (CEM) over per-edge Bernoulli parameters.

This is the Pessimist's optimiser: a classic, reward-agnostic CEM that searches the
space of labelled graphs on n vertices by maintaining an independent Bernoulli
probability p_e for each of the d = n(n-1)/2 possible edges. Each iteration samples a
batch of bitstrings, decodes them to graphs, scores them with a caller-supplied reward
function, and refits p toward the empirical edge frequencies of the elite (top 10%).

The engine is deliberately generic: the conjecture-specific logic lives entirely in the
`reward_fn` passed in. A graph that is disconnected receives reward -1e6, since every
target conjecture is hypothesised only for connected (or regular) graphs; this teaches
the optimiser to stay inside the feasible region without any conjecture-specific tweak.

Returned from a run:
  best_graph, best_reward, the equality-case graphs (|reward| < 1e-9, WL-deduped), and
  a per-iteration JSON-serialisable log of (max, mean, median) reward.

This module also has a small argparse CLI whose default objective is the Conjecture 4
reward mu*(G) - H(G); the real experiment driver is experiments/run_conj4.py.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass, field

import networkx as nx
import numpy as np
from tqdm import tqdm

import graphclasses as gc
import invariants as inv

DISCONNECTED_PENALTY = -1e6
EQUALITY_TOL = 1e-9


# --------------------------------------------------------------------------- #
# Result containers
# --------------------------------------------------------------------------- #
@dataclass
class CEMResult:
    n: int
    best_reward: float
    best_edges: list                       # sorted edge list of the best graph
    equality_edges: list = field(default_factory=list)   # list of sorted edge lists
    log: list = field(default_factory=list)              # per-iteration stats
    best_graph: nx.Graph = None            # not serialised
    equality_graphs: list = field(default_factory=list)  # not serialised

    def to_json(self) -> dict:
        return {
            "n": self.n,
            "best_reward": self.best_reward,
            "best_edges": self.best_edges,
            "equality_edges": self.equality_edges,
            "log": self.log,
        }


@dataclass
class RegularSearchResult:
    """Result of one regular-graph evolutionary-search restart.

    Deliberately a superset of CEMResult (same field names + `r` and `evaluations`)
    so experiments/run_conj3.py can consume it exactly like run_conj4.py consumes a
    CEMResult: `.to_json()`, `.best_graph`, `.equality_graphs`, `.best_reward`,
    `.best_edges`.
    """

    n: int
    r: int
    best_reward: float
    best_edges: list                       # sorted edge list of the best graph
    equality_edges: list = field(default_factory=list)   # list of sorted edge lists
    log: list = field(default_factory=list)              # per-generation stats
    evaluations: int = 0                   # number of reward evaluations performed
    best_graph: nx.Graph = None            # not serialised
    equality_graphs: list = field(default_factory=list)  # not serialised

    def to_json(self) -> dict:
        return {
            "n": self.n,
            "r": self.r,
            "best_reward": self.best_reward,
            "best_edges": self.best_edges,
            "equality_edges": self.equality_edges,
            "evaluations": self.evaluations,
            "log": self.log,
        }


# --------------------------------------------------------------------------- #
# Core CEM
# --------------------------------------------------------------------------- #
def evaluate(G: nx.Graph, reward_fn, require_connected: bool = True) -> float:
    """Reward with the connectivity guard applied."""
    if require_connected and not inv.is_connected(G):
        return DISCONNECTED_PENALTY
    return float(reward_fn(G))


def run_cem(
    n: int,
    reward_fn,
    iters: int,
    batch: int,
    rng: np.random.Generator,
    elite_frac: float = 0.10,
    lr: float = 0.70,
    noise: float = 0.05,
    p_min: float = 0.02,
    p_max: float = 0.98,
    require_connected: bool = True,
    progress: bool = True,
    desc: str = "cem",
) -> CEMResult:
    """One CEM restart. Returns the best graph found and all equality cases seen."""
    d = n * (n - 1) // 2
    p = np.full(d, 0.5)

    best_reward = -np.inf
    best_graph = None
    log = []

    equality_graphs = []
    equality_hashes = set()

    n_elite = max(1, int(round(elite_frac * batch)))

    iterator = range(iters)
    if progress:
        iterator = tqdm(iterator, desc=desc, leave=False)

    for it in iterator:
        samples = (rng.random((batch, d)) < p)  # bool array (batch, d)
        rewards = np.empty(batch, dtype=float)

        for b in range(batch):
            G = gc.general_from_bitstring(samples[b], n)
            r = evaluate(G, reward_fn, require_connected)
            rewards[b] = r

            if r > best_reward:
                best_reward = r
                best_graph = G

            if abs(r) < EQUALITY_TOL:
                h = nx.weisfeiler_lehman_graph_hash(G)
                if h not in equality_hashes:
                    equality_hashes.add(h)
                    equality_graphs.append(G)

        log.append(
            {
                "iter": it,
                "max": float(np.max(rewards)),
                "mean": float(np.mean(rewards)),
                "median": float(np.median(rewards)),
            }
        )

        # Refit p toward elite empirical edge frequencies.
        elite_idx = np.argsort(rewards)[::-1][:n_elite]
        elite_freq = samples[elite_idx].mean(axis=0)
        p = (1.0 - lr) * p + lr * elite_freq
        p = p + rng.normal(0.0, noise, size=d)        # additive exploration noise
        p = np.clip(p, p_min, p_max)

        if progress:
            iterator.set_postfix(best=f"{best_reward:.4f}")

    return CEMResult(
        n=n,
        best_reward=float(best_reward),
        best_edges=sorted(tuple(sorted(e)) for e in best_graph.edges()) if best_graph else [],
        equality_edges=[
            sorted(tuple(sorted(e)) for e in G.edges()) for G in equality_graphs
        ],
        log=log,
        best_graph=best_graph,
        equality_graphs=equality_graphs,
    )


def run_search(
    n: int,
    reward_fn,
    iters: int,
    batch: int,
    seeds: int,
    seed: int,
    require_connected: bool = True,
    progress: bool = True,
    **cem_kwargs,
):
    """Run `seeds` independent CEM restarts with deterministic, independent RNGs.

    Returns (best_result, per_seed_results). The per-seed RNGs are spawned from a
    single SeedSequence(seed) so the whole multi-restart search is reproducible.
    """
    random.seed(seed)
    np.random.seed(seed)
    child_seeds = np.random.SeedSequence(seed).spawn(seeds)

    per_seed = []
    for k, ss in enumerate(child_seeds):
        rng = np.random.default_rng(ss)
        res = run_cem(
            n,
            reward_fn,
            iters=iters,
            batch=batch,
            rng=rng,
            require_connected=require_connected,
            progress=progress,
            desc=f"n={n} seed={k}",
            **cem_kwargs,
        )
        per_seed.append(res)

    best_result = max(per_seed, key=lambda r: r.best_reward)
    return best_result, per_seed


# --------------------------------------------------------------------------- #
# Regular-graph search (Conjecture 3)
# --------------------------------------------------------------------------- #
# The Bernoulli-edge CEM above samples arbitrary graphs and would essentially never
# land on an r-regular one by chance, so it cannot search Conjecture 3's hypothesis
# space. Instead we stay inside the r-regular subspace using degree-preserving moves:
# gc.regular_sampler seeds r-regular graphs and gc.regular_mutator (a double edge swap)
# keeps every vertex at degree r. This is additive infrastructure -- run_cem/run_search
# above are unchanged.
def run_regular_search(
    n: int,
    r: int,
    reward_fn,
    iters: int,
    batch: int,
    rng: np.random.Generator,
    require_connected: bool = True,
    progress: bool = True,
    desc: str = "reg",
    mu: int = None,
    lam: int = None,
    n_swaps: int = 1,
    connect_tries: int = 20,
) -> RegularSearchResult:
    """One (mu + lambda) evolutionary-search restart over r-regular graphs on n vertices.

    Maintains a population of `mu` r-regular graphs; each generation breeds `lam`
    children via `regular_mutator` (degree-preserving double edge swaps), scores
    everyone with `evaluate`, and keeps the best `mu` (parents and children together)
    as the next generation. Tracks the best-ever graph/reward and all equality cases
    (|reward| < EQUALITY_TOL, WL-deduped) exactly like run_cem.

    `mu`/`lam` default to values derived from `batch` so the experiment CLI can stay
    parallel to the CEM drivers (lam = batch, mu = max(4, batch // 5)). When
    `require_connected`, the initial population is resampled (up to `connect_tries`
    per seed) to favour connected graphs; mutation+selection handle the rest.
    """
    if lam is None:
        lam = batch
    if mu is None:
        mu = max(4, batch // 5)

    evaluations = 0
    best_reward = -np.inf
    best_graph = None
    equality_graphs = []
    equality_hashes = set()
    log = []

    def score(G):
        nonlocal evaluations
        evaluations += 1
        return evaluate(G, reward_fn, require_connected)

    def consider(reward, G):
        nonlocal best_reward, best_graph
        if reward > best_reward:
            best_reward = reward
            best_graph = G
        if abs(reward) < EQUALITY_TOL:
            h = nx.weisfeiler_lehman_graph_hash(G)
            if h not in equality_hashes:
                equality_hashes.add(h)
                equality_graphs.append(G)

    def make_seed():
        G = gc.regular_sampler(n, r, rng)
        if require_connected:
            for _ in range(connect_tries):
                if inv.is_connected(G):
                    break
                G = gc.regular_sampler(n, r, rng)
        return G

    # Initial population.
    population = []  # list of (reward, graph); sorted by reward via an explicit key
    for _ in range(mu):
        G = make_seed()
        rew = score(G)
        consider(rew, G)
        population.append((rew, G))

    iterator = range(iters)
    if progress:
        iterator = tqdm(iterator, desc=desc, leave=False)

    for it in iterator:
        children = []
        for _ in range(lam):
            parent = population[int(rng.integers(0, len(population)))][1]
            child = parent
            for _ in range(n_swaps):
                child = gc.regular_mutator(child, rng)
            rew = score(child)
            consider(rew, child)
            children.append((rew, child))

        # (mu + lambda) selection: keep the best mu of parents + children. Sort by an
        # explicit key so equal rewards never trigger an (unorderable) Graph comparison.
        combined = population + children
        combined.sort(key=lambda t: t[0], reverse=True)
        population = combined[:mu]

        gen_rewards = [rew for rew, _ in (children if children else population)]
        log.append(
            {
                "iter": it,
                "max": float(np.max(gen_rewards)),
                "mean": float(np.mean(gen_rewards)),
                "median": float(np.median(gen_rewards)),
            }
        )
        if progress:
            iterator.set_postfix(best=f"{best_reward:.4f}")

    return RegularSearchResult(
        n=n,
        r=r,
        best_reward=float(best_reward),
        best_edges=sorted(tuple(sorted(e)) for e in best_graph.edges()) if best_graph else [],
        equality_edges=[
            sorted(tuple(sorted(e)) for e in G.edges()) for G in equality_graphs
        ],
        log=log,
        evaluations=evaluations,
        best_graph=best_graph,
        equality_graphs=equality_graphs,
    )


# --------------------------------------------------------------------------- #
# Default objective for the standalone CLI: Conjecture 4 reward mu*(G) - H(G)
# --------------------------------------------------------------------------- #
def _conj4_reward(G: nx.Graph) -> float:
    return inv.mustar(G) - inv.harmonic_index(G)


def _dedup_equality(results) -> list:
    """Union of equality graphs across restarts, deduplicated by WL hash."""
    seen = set()
    unique = []
    for res in results:
        for G in res.equality_graphs:
            h = nx.weisfeiler_lehman_graph_hash(G)
            if h not in seen:
                seen.add(h)
                unique.append(sorted(tuple(sorted(e)) for e in G.edges()))
    return unique


def main(argv=None):
    parser = argparse.ArgumentParser(description="CEM search over graphs (default objective: Conjecture 4 mu* - H).")
    parser.add_argument("--n", type=int, required=True, help="number of vertices")
    parser.add_argument("--iters", type=int, default=50)
    parser.add_argument("--batch", type=int, default=200)
    parser.add_argument("--seeds", type=int, default=10, help="number of independent restarts")
    parser.add_argument("--seed", type=int, default=0, help="master seed (numpy + random)")
    parser.add_argument("--out", type=str, default=None, help="path to write a JSON summary")
    parser.add_argument("--smoke", action="store_true", help="tiny run: iters=10, batch=50, seeds=2")
    args = parser.parse_args(argv)

    if args.smoke:
        args.iters, args.batch, args.seeds = 10, 50, 2

    best, per_seed = run_search(
        args.n,
        _conj4_reward,
        iters=args.iters,
        batch=args.batch,
        seeds=args.seeds,
        seed=args.seed,
    )

    summary = {
        "n": args.n,
        "iters": args.iters,
        "batch": args.batch,
        "seeds": args.seeds,
        "seed": args.seed,
        "objective": "conjecture4: mu*(G) - H(G)",
        "best_reward": best.best_reward,
        "best_edges": best.best_edges,
        "equality_cases": _dedup_equality(per_seed),
        "per_seed_logs": [r.log for r in per_seed],
    }

    print(f"n={args.n}: best reward = {best.best_reward:.6f} "
          f"({'COUNTEREXAMPLE!' if best.best_reward > 0 else 'no counterexample'}); "
          f"{len(summary['equality_cases'])} distinct equality case(s).")

    if args.out:
        with open(args.out, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"wrote {args.out}")

    return summary


if __name__ == "__main__":
    main()
