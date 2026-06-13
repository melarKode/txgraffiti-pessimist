"""Pessimist run against Conjecture 3:  i(G) <= mu*(G)  for r-regular G, r > 0.

Conjecture 3's hypothesis is r-regularity, a structurally rigid subset of all graphs, so
the Bernoulli-edge CEM used for Conjectures 1/4 would essentially never sample a valid
candidate. Instead we search each (n, r) cell with a (mu + lambda) evolutionary loop over
r-regular graphs (search.run_regular_search), maximising reward(G) = i(G) - mu*(G). We log
every run, summarise the best reward per (n, r), collect all equality cases (reward == 0,
i.e. extremal graphs with i = mu*) deduplicated by Weisfeiler-Lehman hash, and draw an
i vs mu* scatter. A positive reward anywhere would be a counterexample; if that ever
happens we dump full provenance, re-verify i and mu* by independent methods, and write
VERIFIED.md.

The outer loop is over (n, r) pairs with r > 0, r < n, and n*r even (the parity condition
for an r-regular graph). Because mu* is exact by brute force only while |E| = n*r/2 <= 12,
pairs above that threshold are skipped unless --allow-ilp is passed (they would fall back
on the CBC ILP path).

Usage:
  python experiments/run_conj3.py            # full run: r=3, n in 4..8, 10 seeds, 50 iters, batch 200
  python experiments/run_conj3.py --r-values 3,4 --n-max 8
  python experiments/run_conj3.py --smoke    # r=3, n in 4..6, 2 seeds, 10 iters, batch 40
"""

from __future__ import annotations

import argparse
import datetime as dt
import itertools
import json
import os
import random
import sys
import time

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

# Make src/ and conjectures/ importable when run as a script.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for sub in ("src", "conjectures"):
    p = os.path.join(ROOT, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

import invariants as inv  # noqa: E402
import conj3_independence_domination_minmaxmatching as conj3  # noqa: E402
from search import run_regular_search  # noqa: E402

OUTDIR = os.path.join(ROOT, "results", "conj3")

# A reward within EQ_TOL of zero is an equality case (i = mu*), not a counterexample.
# Only reward strictly above this tolerance refutes the conjecture (i and mu* are
# integers, so genuine equality lands exactly at 0, but we keep the tolerance for parity
# with the other drivers).
EQ_TOL = 1e-9

# mu* is exact by brute force while the edge count stays at or below this; above it the
# production path falls back on the CBC ILP solver.
MAX_BRUTEFORCE_EDGES = 12


# --------------------------------------------------------------------------- #
# Counterexample handling (defensive; expected never to trigger)
# --------------------------------------------------------------------------- #
def _i_bruteforce(G: nx.Graph) -> int:
    """Independent recomputation of i(G) = smallest *maximal* independent set.

    A maximal independent set is exactly an independent dominating set, so we search
    subsets in increasing size and return the first independent dominating one. This is
    algorithmically distinct from the production path (maximal cliques of the complement),
    giving a genuine cross-check. Only invoked on a (rare) candidate counterexample.
    """
    nodes = list(G.nodes())
    n = len(nodes)
    adj = {v: set(G.neighbors(v)) for v in nodes}
    for k in range(n + 1):
        for S in itertools.combinations(nodes, k):
            Sset = set(S)
            if any(adj[u] & Sset for u in S):      # not independent
                continue
            dominated = set(Sset)
            for u in S:
                dominated |= adj[u]
            if len(dominated) == n:                # independent and dominating == maximal
                return k
    return n


def reverify(G: nx.Graph) -> dict:
    """Recompute i and mu* by independent methods and report all of them.

    i is recomputed two ways: the production path (maximal cliques of the complement) and
    an explicit smallest-independent-dominating-set search. mu* is recomputed three ways
    where feasible: the production path, an explicit brute-force subset search, and
    i(L(G)) (smallest maximal independent set of the line graph).
    """
    m = G.number_of_edges()
    n = G.number_of_nodes()
    deg = dict(G.degree())

    i_methods = {"i_production": inv.alpha_and_i(G)[1]}
    if n <= 18:
        i_methods["i_bruteforce"] = _i_bruteforce(G)

    mu_methods = {"mustar_production": inv.mustar(G)}
    if m <= 18:
        mu_methods["mustar_bruteforce"] = inv._mustar_bruteforce(G)
    mu_methods["mustar_via_line_graph_i"] = inv.alpha_and_i(nx.line_graph(G))[1] if m else 0

    return {
        "edges": sorted(tuple(sorted(e)) for e in G.edges()),
        "n": n,
        "m": m,
        "degree_sequence": sorted(deg.values(), reverse=True),
        "is_regular": inv.is_regular(G),
        "r": inv.min_degree(G) if inv.is_regular(G) else None,
        "connected": inv.is_connected(G),
        "i_methods": i_methods,
        "mustar_methods": mu_methods,
        "all_i_agree": len(set(i_methods.values())) == 1,
        "all_mustar_agree": len(set(mu_methods.values())) == 1,
        "reward": i_methods["i_production"] - mu_methods["mustar_production"],
    }


def handle_counterexample(G: nx.Graph, n: int, r: int, seed_idx: int):
    ts = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    verification = reverify(G)
    provenance = {
        "conjecture": "Conjecture 3 (arXiv 2507.17780): i(G) <= mu*(G) for r-regular G, r>0",
        "found_at": ts,
        "n": n,
        "r": r,
        "seed_index": seed_idx,
        "verification": verification,
    }
    path = os.path.join(OUTDIR, f"COUNTEREXAMPLE_{ts}.json")
    with open(path, "w") as f:
        json.dump(provenance, f, indent=2)

    with open(os.path.join(OUTDIR, "VERIFIED.md"), "w") as f:
        f.write("# Conjecture 3 counterexample — verification\n\n")
        f.write(f"Found {ts}, n={n}, r={r}, seed index {seed_idx}.\n\n")
        f.write(f"- Edges: `{verification['edges']}`\n")
        f.write(f"- Degree sequence: {verification['degree_sequence']}\n")
        f.write(f"- r-regular: {verification['is_regular']} (r={verification['r']}), "
                f"connected: {verification['connected']}\n")
        f.write(f"- i(G) by all methods: {verification['i_methods']}\n")
        f.write(f"- mu*(G) by all methods: {verification['mustar_methods']}\n")
        f.write(f"- All i methods agree: {verification['all_i_agree']}; "
                f"all mu* methods agree: {verification['all_mustar_agree']}\n")
        f.write(f"- reward = i - mu* = {verification['reward']}\n\n")
        f.write("If both invariant cross-checks agree and reward > 0 on an r-regular "
                "graph with r > 0, this is a genuine counterexample to Conjecture 3.\n")
    print(f"\n!!! POSITIVE REWARD at n={n}, r={r}. Wrote {path} and VERIFIED.md !!!")


# --------------------------------------------------------------------------- #
# Plot
# --------------------------------------------------------------------------- #
def make_scatter(points, path):
    """points: list of (mustar, i, is_equality).

    Mirrors conj4's LHS<=RHS convention: RHS (mu*) on the x-axis, LHS (i) on the y-axis,
    so the feasible region i <= mu* is on/under the y=x diagonal.
    """
    if not points:
        return
    mus = [p[0] for p in points]
    iis = [p[1] for p in points]

    fig, ax = plt.subplots(figsize=(7, 6))
    non_eq = [(mu, i) for mu, i, e in points if not e]
    eq_pts = [(mu, i) for mu, i, e in points if e]
    if non_eq:
        ax.scatter([mu for mu, _ in non_eq], [i for _, i in non_eq], s=18, alpha=0.5,
                   label="best per run (i < mu*)", color="#3366cc")
    if eq_pts:
        ax.scatter([mu for mu, _ in eq_pts], [i for _, i in eq_pts], s=60, marker="D",
                   label="equality cases (i = mu*)", color="#cc3311", zorder=5)

    lo = 0
    hi = max(max(mus), max(iis)) + 1
    ax.plot([lo, hi], [lo, hi], "k--", lw=1, label="i = mu* (conjecture boundary)")
    ax.set_xlabel("mu*(G)  (min maximal matching)")
    ax.set_ylabel("i(G)  (independent domination)")
    ax.set_title("Conjecture 3: i(G) <= mu*(G)\nall searched r-regular graphs lie on/under the boundary")
    ax.legend(loc="upper left")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def _run_one_nr(n, r, seeds, iters, batch, seed, budget_seconds, progress):
    """Run `seeds` regular-search restarts for a single (n, r), aborting as soon as the
    *cumulative* wall time for this cell crosses budget_seconds. Returns
    (per_seed_results, elapsed, over_budget). The per-seed RNGs are spawned from
    SeedSequence([seed, n, r]) so each (n, r) cell is independent and reproducible -- key
    on both n and r so different r never collide."""
    child_seeds = np.random.SeedSequence([seed, n, r]).spawn(seeds)

    per_seed = []
    t0 = time.time()
    over_budget = False
    for k, ss in enumerate(child_seeds):
        rng = np.random.default_rng(ss)
        res = run_regular_search(n, r, conj3.reward, iters=iters, batch=batch, rng=rng,
                                 progress=progress, desc=f"n={n} r={r} seed={k}")
        per_seed.append(res)
        if time.time() - t0 > budget_seconds:
            over_budget = True
            break
    return per_seed, time.time() - t0, over_budget


def run(pairs_by_r, seeds, iters, batch, seed, progress=True, budget_seconds=600):
    """Run the Pessimist over the given {r: [n, ...]} cells. Within each r, n ascends; an
    (n, r) cell whose multi-restart search exceeds budget_seconds is NOT recorded, and the
    sweep for *that r* stops there (its cap becomes the previous n) while other r values
    continue. This is the explicit, non-silent truncation the protocol calls for."""
    os.makedirs(OUTDIR, exist_ok=True)

    summary = {
        "conjecture": "Conjecture 3 (arXiv 2507.17780): i(G) <= mu*(G) for r-regular G, r>0",
        "reward": "i(G) - mu*(G); positive == counterexample",
        "params": {
            "requested": {str(r): list(ns) for r, ns in pairs_by_r.items()},
            "seeds": seeds, "iters": iters, "batch": batch, "seed": seed,
            "budget_seconds_per_cell": budget_seconds,
        },
        "per_pair": {},
        "total_graphs_searched": 0,
        "global_best_reward": None,
        "counterexample_found": False,
    }

    equality = {}          # wl_hash -> edge list
    scatter_points = []    # (mustar, i, is_equality)
    global_best_reward = -float("inf")
    per_pair_times = {}    # (n, r) -> seconds (recorded cells only)
    actual_cap = {}        # r -> largest n reached
    aborted = {}           # r -> aborted n

    for r in sorted(pairs_by_r):
        for n in sorted(pairs_by_r[r]):
            per_seed, elapsed, over_budget = _run_one_nr(
                n, r, seeds, iters, batch, seed, budget_seconds, progress
            )

            if over_budget:
                aborted[r] = n
                prev = actual_cap.get(r)
                cap_msg = f"n={prev}" if prev is not None else "no n recorded"
                print(f"n={n:2d} r={r}: ABORTED after {elapsed:.0f}s "
                      f"(> {budget_seconds}s budget); capping r={r} at {cap_msg}.")
                break  # stop increasing n for this r; continue with other r values

            for k, res in enumerate(per_seed):
                with open(os.path.join(OUTDIR, f"log_n{n:02d}_r{r}_seed{k}.json"), "w") as f:
                    json.dump(res.to_json(), f, indent=2)

                if res.best_graph is not None and res.best_graph.number_of_edges() > 0:
                    i_val, mu_val = conj3.components(res.best_graph)
                    scatter_points.append((mu_val, i_val, abs(res.best_reward) < EQ_TOL))

                for G in res.equality_graphs:
                    h = nx.weisfeiler_lehman_graph_hash(G)
                    if h not in equality:
                        equality[h] = sorted(tuple(sorted(e)) for e in G.edges())
                        i_val, mu_val = conj3.components(G)
                        scatter_points.append((mu_val, i_val, True))

            max_reward = max(r_.best_reward for r_ in per_seed)
            best = max(per_seed, key=lambda r_: r_.best_reward)
            graphs_searched = sum(r_.evaluations for r_ in per_seed)
            summary["per_pair"][f"{n},{r}"] = {
                "n": n,
                "r": r,
                "max_reward": max_reward,
                "best_edges": best.best_edges,
                "graphs_searched": graphs_searched,
                "seconds": round(elapsed, 1),
            }
            summary["total_graphs_searched"] += graphs_searched
            per_pair_times[(n, r)] = elapsed
            actual_cap[r] = n

            if max_reward > global_best_reward:
                global_best_reward = max_reward

            if max_reward > EQ_TOL:
                status = "COUNTEREXAMPLE!"
            elif max_reward > -EQ_TOL:
                status = "holds (equality reached)"
            else:
                status = "holds"
            print(f"n={n:2d} r={r}: max reward = {max_reward:+.6f}  [{status}]  ({elapsed:.0f}s)")

            if max_reward > EQ_TOL:
                summary["counterexample_found"] = True
                handle_counterexample(best.best_graph, n, r, 0)

    summary["global_best_reward"] = global_best_reward if scatter_points else None
    summary["distinct_equality_cases"] = len(equality)
    summary["actual_cap"] = {str(r): actual_cap[r] for r in actual_cap}

    with open(os.path.join(OUTDIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    with open(os.path.join(OUTDIR, "equality_cases.json"), "w") as f:
        json.dump(
            {"count": len(equality), "edge_lists": list(equality.values())}, f, indent=2
        )
    make_scatter(scatter_points, os.path.join(OUTDIR, "scatter_i_vs_mustar.png"))
    write_run_notes(pairs_by_r, per_pair_times, actual_cap, aborted, budget_seconds, summary)

    caps = ", ".join(f"r={r}:n<={actual_cap[r]}" for r in sorted(actual_cap)) or "none"
    print(f"\nDone. caps=[{caps}]; global best reward = {summary['global_best_reward']}; "
          f"{len(equality)} distinct equality case(s); "
          f"{summary['total_graphs_searched']} graphs searched.")
    print(f"Outputs in {OUTDIR}")
    return summary


def write_run_notes(pairs_by_r, per_pair_times, actual_cap, aborted, budget, summary):
    lines = ["# Conjecture 3 full run — notes\n"]
    lines.append("Conjecture 3 (open since 2020): for every r-regular graph G with r > 0, "
                 "i(G) <= mu*(G), where i is the independent domination number and mu* the "
                 "minimum maximal matching number. Reward = i(G) - mu*(G); a positive "
                 "reward on an r-regular graph would be a counterexample.\n")

    lines.append("## Search space & methodology")
    lines.append("- The hypothesis is r-regularity, so the search is a (mu + lambda) "
                 "evolutionary loop over r-regular graphs (regular_sampler seeds the "
                 "population; the degree-preserving regular_mutator breeds children), not "
                 "the Bernoulli-edge CEM used for Conjectures 1/4 -- that never lands on a "
                 "regular graph.")
    lines.append("- **Connectivity choice:** the search is restricted to *connected* "
                 "r-regular graphs. This does NOT narrow the conjecture. i(G) and mu*(G) "
                 "are both additive over connected components, so a disconnected r-regular "
                 "counterexample would require some connected r-regular component that is "
                 "itself a counterexample. Restricting to connected graphs therefore loses "
                 "no counterexamples while concentrating the search.")
    lines.append(f"- Per-(n, r) wall-clock budget: {budget}s. A cell exceeding it is not "
                 "recorded and that r's sweep stops at the previous n.")
    lines.append(f"- mu* is exact by brute force while |E| = n*r/2 <= {MAX_BRUTEFORCE_EDGES}; "
                 "cells above that are skipped unless --allow-ilp is set (CBC ILP path).\n")

    lines.append("## Per-r coverage")
    all_rs = sorted(set(pairs_by_r) | set(actual_cap) | set(aborted))
    for r in all_rs:
        cap = actual_cap.get(r)
        cap_s = f"largest n reached = {cap}" if cap is not None else "no n recorded"
        if r in aborted:
            cap_s += f" (n={aborted[r]} exceeded the {budget}s budget)"
        lines.append(f"- r = {r}: {cap_s}")
    lines.append("")

    lines.append("## Per-(n, r) wall time (recorded cells only)\n")
    lines.append("| n | r | seconds | graphs searched | max reward |")
    lines.append("|---|---|---------|-----------------|------------|")
    for (n, r) in sorted(per_pair_times):
        d = summary["per_pair"][f"{n},{r}"]
        lines.append(f"| {n} | {r} | {per_pair_times[(n, r)]:.0f} | "
                     f"{d['graphs_searched']} | {d['max_reward']:+.6f} |")
    lines.append("")

    gbr = summary["global_best_reward"]
    gbr_s = f"{gbr:+.6e}" if isinstance(gbr, (int, float)) else str(gbr)
    lines.append(f"Counterexample found: **{summary['counterexample_found']}**. "
                 f"Global best reward: {gbr_s}. "
                 f"Distinct equality (i = mu*) cases: {summary['distinct_equality_cases']}. "
                 f"Total graphs searched: {summary['total_graphs_searched']}.")
    with open(os.path.join(OUTDIR, "RUN_NOTES.md"), "w") as f:
        f.write("\n".join(lines) + "\n")


def _build_pairs(n_min, n_max, r_values, allow_ilp):
    """Return ({r: [n, ...]}, skipped) for valid (n, r): 0 < r < n and n*r even, and
    n*r/2 <= MAX_BRUTEFORCE_EDGES unless allow_ilp."""
    pairs_by_r = {}
    skipped = []
    for r in r_values:
        ns = []
        for n in range(n_min, n_max + 1):
            if not (0 < r < n):
                continue
            if (n * r) % 2 != 0:
                continue
            if (n * r) // 2 > MAX_BRUTEFORCE_EDGES and not allow_ilp:
                skipped.append((n, r))
                continue
            ns.append(n)
        if ns:
            pairs_by_r[r] = ns
    return pairs_by_r, skipped


def main(argv=None):
    parser = argparse.ArgumentParser(description="Pessimist run against Conjecture 3 (i <= mu*).")
    parser.add_argument("--n-min", type=int, default=4)
    parser.add_argument("--n-max", type=int, default=8)
    parser.add_argument("--r-values", type=str, default="3",
                        help="comma-separated regularities to sweep, e.g. '3,4' (default 3)")
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--iters", type=int, default=50)
    parser.add_argument("--batch", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--budget", type=float, default=600.0,
                        help="per-(n,r) wall-clock budget in seconds; a cell exceeding it "
                             "is aborted and that r's sweep stops (default 600 = 10 min)")
    parser.add_argument("--allow-ilp", action="store_true",
                        help=f"permit (n,r) cells with n*r/2 > {MAX_BRUTEFORCE_EDGES} "
                             "(mu* falls back to the CBC ILP path)")
    parser.add_argument("--smoke", action="store_true",
                        help="tiny run: r=3, n in 4..6, 2 seeds, 10 iters, batch 40")
    args = parser.parse_args(argv)

    if args.smoke:
        args.n_min, args.n_max = 4, 6
        args.r_values = "3"
        args.seeds, args.iters, args.batch = 2, 10, 40

    r_values = [int(x) for x in args.r_values.split(",") if x.strip()]
    pairs_by_r, skipped = _build_pairs(args.n_min, args.n_max, r_values, args.allow_ilp)

    if skipped:
        print(f"Skipping {len(skipped)} cell(s) with |E| > {MAX_BRUTEFORCE_EDGES} "
              f"(pass --allow-ilp to include them): "
              f"{', '.join(f'(n={n},r={r})' for n, r in skipped)}")
    if not pairs_by_r:
        print("No valid (n, r) cells to search. Check --n-min/--n-max/--r-values.")
        return None

    print("Sweeping cells: "
          + "; ".join(f"r={r}: n in {pairs_by_r[r]}" for r in sorted(pairs_by_r)))
    return run(pairs_by_r, seeds=args.seeds, iters=args.iters, batch=args.batch,
               seed=args.seed, budget_seconds=args.budget)


if __name__ == "__main__":
    main()
