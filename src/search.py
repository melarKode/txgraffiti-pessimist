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
