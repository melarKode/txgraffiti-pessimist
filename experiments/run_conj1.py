"""Pessimist run against Conjecture 1:  alpha(G) >= (a(G) + R(G)) / Delta(G)  for
nontrivial connected G.

For each vertex count n we launch a multi-restart CEM search that maximises the gap
reward(G) = (a(G) + R(G)) / Delta(G) - alpha(G). We log every run, summarise the best
reward per n, collect all equality cases (reward == 0, i.e. extremal graphs with
alpha = (a+R)/Delta) deduplicated by Weisfeiler-Lehman hash, and draw an alpha vs
(a+R)/Delta scatter. A positive reward anywhere would be a counterexample; if that ever
happens we dump full provenance, re-verify every invariant by an independent method, and
write VERIFIED.md.

Usage:
  python experiments/run_conj1.py            # full run: n in 4..14, 10 seeds, 50 iters, batch 200
  python experiments/run_conj1.py --smoke    # n in 4..6, 2 seeds, 10 iters, batch 50
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
import conj1_independence_annihilation_residue as conj1  # noqa: E402
from search import run_cem  # noqa: E402

OUTDIR = os.path.join(ROOT, "results", "conj1")

# A reward within EQ_TOL of zero is an equality case (alpha = (a+R)/Delta), not a
# counterexample. Only reward strictly above this tolerance refutes the conjecture.
EQ_TOL = 1e-9


# --------------------------------------------------------------------------- #
# Counterexample handling (defensive; expected never to trigger)
# --------------------------------------------------------------------------- #
def _annihilation_manual(degrees: list[int], m: int) -> int:
    """Largest k such that the sum of the k smallest degrees is <= m, computed
    directly from a degree sequence (independent of inv.annihilation_number)."""
    degs = sorted(degrees)
    running = 0
    k = 0
    for i, d in enumerate(degs, start=1):
        running += d
        if running <= m:
            k = i
        else:
            break
    return k


def _residue_manual(degrees: list[int]) -> int:
    """Havel-Hakimi residue computed directly from a degree sequence (independent
    of inv.residue)."""
    seq = sorted(degrees, reverse=True)
    while seq and seq[0] > 0:
        d = seq.pop(0)
        if d > len(seq):
            d = len(seq)
        for i in range(d):
            seq[i] -= 1
        seq.sort(reverse=True)
    return len(seq)


def _alpha_bruteforce(G: nx.Graph) -> int:
    """Independence number by direct subset enumeration (independent of
    inv.alpha_and_i's complement-clique method). Only feasible for small n."""
    nodes = list(G.nodes())
    n = len(nodes)
    edges = set(frozenset(e) for e in G.edges())
    best = 0
    for k in range(n, 0, -1):
        if k <= best:
            break
        for combo in itertools.combinations(nodes, k):
            if all(frozenset((u, v)) not in edges
                   for u, v in itertools.combinations(combo, 2)):
                best = k
                break
    return best


def reverify(G: nx.Graph) -> dict:
    """Recompute alpha, a, R, Delta by independent methods and report all of them."""
    n = G.number_of_nodes()
    m = G.number_of_edges()
    deg = dict(G.degree())
    degrees = list(deg.values())

    alpha_methods = {"alpha_production": inv.alpha_and_i(G)[0]}
    if n <= 20:
        alpha_methods["alpha_bruteforce"] = _alpha_bruteforce(G)

    a_methods = {
        "a_production": inv.annihilation_number(G),
        "a_manual": _annihilation_manual(degrees, m),
    }
    R_methods = {
        "R_production": inv.residue(G),
        "R_manual": _residue_manual(degrees),
    }
    delta_methods = {
        "delta_production": inv.max_degree(G),
        "delta_manual": max(degrees) if degrees else 0,
    }

    rhs = (a_methods["a_production"] + R_methods["R_production"]) / delta_methods["delta_production"]

    return {
        "edges": sorted(tuple(sorted(e)) for e in G.edges()),
        "n": n,
        "m": m,
        "degree_sequence": sorted(degrees, reverse=True),
        "alpha_methods": alpha_methods,
        "a_methods": a_methods,
        "R_methods": R_methods,
        "delta_methods": delta_methods,
        "all_alpha_agree": len(set(alpha_methods.values())) == 1,
        "all_a_agree": len(set(a_methods.values())) == 1,
        "all_R_agree": len(set(R_methods.values())) == 1,
        "all_delta_agree": len(set(delta_methods.values())) == 1,
        "rhs": rhs,
        "reward": rhs - alpha_methods["alpha_production"],
    }


def handle_counterexample(G: nx.Graph, n: int, seed_idx: int):
    ts = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    verification = reverify(G)
    provenance = {
        "conjecture": "Conjecture 1 (arXiv 2507.17780): alpha(G) >= (a(G)+R(G))/Delta(G) "
                       "for nontrivial connected G",
        "found_at": ts,
        "n": n,
        "seed_index": seed_idx,
        "connected": inv.is_connected(G),
        "verification": verification,
    }
    path = os.path.join(OUTDIR, f"COUNTEREXAMPLE_{ts}.json")
    with open(path, "w") as f:
        json.dump(provenance, f, indent=2)

    all_agree = (verification["all_alpha_agree"] and verification["all_a_agree"]
                  and verification["all_R_agree"] and verification["all_delta_agree"])
    with open(os.path.join(OUTDIR, "VERIFIED.md"), "w") as f:
        f.write("# Conjecture 1 counterexample — verification\n\n")
        f.write(f"Found {ts}, n={n}, seed index {seed_idx}.\n\n")
        f.write(f"- Edges: `{verification['edges']}`\n")
        f.write(f"- Degree sequence: {verification['degree_sequence']}\n")
        f.write(f"- alpha by all methods: {verification['alpha_methods']}\n")
        f.write(f"- a by all methods: {verification['a_methods']}\n")
        f.write(f"- R by all methods: {verification['R_methods']}\n")
        f.write(f"- Delta by all methods: {verification['delta_methods']}\n")
        f.write(f"- (a+R)/Delta = {verification['rhs']}\n")
        f.write(f"- All independent methods agree: {all_agree}\n")
        f.write(f"- reward = (a+R)/Delta - alpha = {verification['reward']}\n\n")
        f.write("If all independent methods agree and reward > 0, this is a genuine "
                "counterexample to Conjecture 1.\n")
    print(f"\n!!! POSITIVE REWARD at n={n}. Wrote {path} and VERIFIED.md !!!")


# --------------------------------------------------------------------------- #
# Plot
# --------------------------------------------------------------------------- #
def make_scatter(points, path):
    """points: list of (rhs, alpha, is_equality) where rhs = (a+R)/Delta."""
    if not points:
        return
    rhss = [p[0] for p in points]
    alphas = [p[1] for p in points]

    fig, ax = plt.subplots(figsize=(7, 6))
    non_eq = [(r, a) for r, a, e in points if not e]
    eq_pts = [(r, a) for r, a, e in points if e]
    if non_eq:
        ax.scatter([r for r, _ in non_eq], [a for _, a in non_eq], s=18, alpha=0.5,
                   label="best per run (alpha > (a+R)/Delta)", color="#3366cc")
    if eq_pts:
        ax.scatter([r for r, _ in eq_pts], [a for _, a in eq_pts], s=60, marker="D",
                   label="equality cases (alpha = (a+R)/Delta)", color="#cc3311", zorder=5)

    lo = 0
    hi = max(max(rhss), max(alphas)) + 1
    ax.plot([lo, hi], [lo, hi], "k--", lw=1, label="alpha = (a+R)/Delta (conjecture boundary)")
    ax.set_xlabel("(a(G)+R(G))/Delta(G)")
    ax.set_ylabel("alpha(G)")
    ax.set_title("Conjecture 1: alpha(G) >= (a(G)+R(G))/Delta(G)\n"
                  "all searched graphs lie on/above the boundary")
    ax.legend(loc="upper left")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def _run_one_n(n, seeds, iters, batch, seed, budget_seconds, progress):
    """Run `seeds` CEM restarts for a single n, aborting as soon as the *cumulative*
    wall time for this n crosses budget_seconds. Returns (per_seed_results, elapsed,
    over_budget). On abort, per_seed_results holds only the restarts that finished."""
    random.seed(seed + n)
    np.random.seed(seed + n)
    child_seeds = np.random.SeedSequence(seed + n).spawn(seeds)

    per_seed = []
    t0 = time.time()
    over_budget = False
    for k, ss in enumerate(child_seeds):
        rng = np.random.default_rng(ss)
        res = run_cem(n, conj1.reward, iters=iters, batch=batch, rng=rng,
                      progress=progress, desc=f"n={n} seed={k}")
        per_seed.append(res)
        if time.time() - t0 > budget_seconds:
            over_budget = True
            break
    return per_seed, time.time() - t0, over_budget


def run(ns, seeds, iters, batch, seed, progress=True, budget_seconds=600):
    """Run the Pessimist over the given n's. Any n whose full multi-restart search
    exceeds budget_seconds (default 10 min) is treated as over the cap: it is NOT
    recorded, the search stops, and the documented cap becomes the previous n. This
    is the explicit, non-silent truncation the experiment protocol calls for."""
    os.makedirs(OUTDIR, exist_ok=True)
    ns = list(ns)

    summary = {
        "conjecture": "Conjecture 1 (arXiv 2507.17780): alpha(G) >= (a(G)+R(G))/Delta(G), "
                       "nontrivial connected G",
        "reward": "(a(G)+R(G))/Delta(G) - alpha(G); positive == counterexample",
        "params": {"requested_ns": ns, "seeds": seeds, "iters": iters, "batch": batch,
                   "seed": seed, "budget_seconds_per_n": budget_seconds},
        "per_n": {},
        "total_graphs_searched": 0,
        "global_best_reward": None,
        "counterexample_found": False,
    }

    equality = {}          # wl_hash -> edge list
    scatter_points = []    # (rhs, alpha, is_equality)
    global_best_reward = -float("inf")
    per_n_times = {}       # n -> seconds (recorded n only)
    actual_cap = None
    aborted_n = None

    for n in ns:
        per_seed, elapsed, over_budget = _run_one_n(
            n, seeds, iters, batch, seed, budget_seconds, progress
        )

        if over_budget:
            # This n blew the 10-minute budget: do not record it; cap at n-1 and stop.
            aborted_n = n
            print(f"n={n:2d}: ABORTED after {elapsed:.0f}s (> {budget_seconds}s budget); "
                  f"capping at n={n - 1}.")
            break

        for k, res in enumerate(per_seed):
            with open(os.path.join(OUTDIR, f"log_n{n:02d}_seed{k}.json"), "w") as f:
                json.dump(res.to_json(), f, indent=2)

            if res.best_graph is not None and res.best_graph.number_of_edges() > 0:
                alpha, rhs = conj1.components(res.best_graph)
                scatter_points.append((rhs, alpha, abs(res.best_reward) < 1e-9))

            for G in res.equality_graphs:
                h = nx.weisfeiler_lehman_graph_hash(G)
                if h not in equality:
                    equality[h] = sorted(tuple(sorted(e)) for e in G.edges())
                    alpha, rhs = conj1.components(G)
                    scatter_points.append((rhs, alpha, True))

        max_reward_n = max(r.best_reward for r in per_seed)
        best = max(per_seed, key=lambda r: r.best_reward)
        summary["per_n"][str(n)] = {
            "max_reward": max_reward_n,
            "best_edges": best.best_edges,
            "graphs_searched": iters * batch * len(per_seed),
            "seconds": round(elapsed, 1),
        }
        summary["total_graphs_searched"] += iters * batch * len(per_seed)
        per_n_times[n] = elapsed
        actual_cap = n

        if max_reward_n > global_best_reward:
            global_best_reward = max_reward_n

        if max_reward_n > EQ_TOL:
            status = "COUNTEREXAMPLE!"
        elif max_reward_n > -EQ_TOL:
            status = "holds (equality reached)"
        else:
            status = "holds"
        print(f"n={n:2d}: max reward = {max_reward_n:+.6f}  [{status}]  ({elapsed:.0f}s)")

        if max_reward_n > EQ_TOL:
            summary["counterexample_found"] = True
            handle_counterexample(best.best_graph, n, 0)

    summary["global_best_reward"] = global_best_reward
    summary["distinct_equality_cases"] = len(equality)
    summary["actual_cap"] = actual_cap

    with open(os.path.join(OUTDIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    with open(os.path.join(OUTDIR, "equality_cases.json"), "w") as f:
        json.dump(
            {"count": len(equality), "edge_lists": list(equality.values())}, f, indent=2
        )
    make_scatter(scatter_points, os.path.join(OUTDIR, "scatter_alpha_vs_a_plus_R_over_delta.png"))
    write_run_notes(ns, per_n_times, actual_cap, aborted_n, budget_seconds, summary)

    print(f"\nDone. cap=n{actual_cap}; global best reward = {global_best_reward:+.6f}; "
          f"{len(equality)} distinct equality case(s); "
          f"{summary['total_graphs_searched']} graphs searched.")
    print(f"Outputs in {OUTDIR}")
    return summary


def write_run_notes(requested_ns, per_n_times, actual_cap, aborted_n, budget, summary):
    lines = ["# Conjecture 1 full run — notes\n"]
    lines.append(f"- Requested n range: {requested_ns[0]}..{requested_ns[-1]}")
    lines.append(f"- Per-n wall-clock budget: {budget}s (10 min)")
    lines.append(f"- **Actual cap reached: n = {actual_cap}**")
    if aborted_n is not None:
        lines.append(f"- n = {aborted_n} exceeded the budget and was aborted "
                     f"(not recorded). Conjecture 1 needs only alpha, a, R, Delta -- "
                     f"no CBC/ILP subprocess -- but alpha(G) (via maximal cliques of "
                     f"the complement) becomes the bottleneck as n grows, so the "
                     f"~{summary['params']['iters'] * summary['params']['batch'] * summary['params']['seeds']:,} "
                     f"evaluations per n eventually exceed the budget.")
    else:
        lines.append("- No n was aborted; the full requested range completed within budget.")
    lines.append("")
    lines.append("## Per-n wall time (recorded n only)\n")
    lines.append("| n | seconds | max reward |")
    lines.append("|---|---------|------------|")
    for n in sorted(per_n_times):
        mr = summary["per_n"][str(n)]["max_reward"]
        lines.append(f"| {n} | {per_n_times[n]:.0f} | {mr:+.6f} |")
    lines.append("")
    lines.append(f"Counterexample found: **{summary['counterexample_found']}**. "
                 f"Global best reward: {summary['global_best_reward']:+.6e}.")
    with open(os.path.join(OUTDIR, "RUN_NOTES.md"), "w") as f:
        f.write("\n".join(lines) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Pessimist run against Conjecture 1 (alpha >= (a+R)/Delta).")
    parser.add_argument("--n-min", type=int, default=4)
    parser.add_argument("--n-max", type=int, default=14)
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--iters", type=int, default=50)
    parser.add_argument("--batch", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--budget", type=float, default=600.0,
                        help="per-n wall-clock budget in seconds; an n exceeding it is "
                             "aborted and the cap drops to n-1 (default 600 = 10 min)")
    parser.add_argument("--smoke", action="store_true",
                        help="tiny run: n in 4..6, 2 seeds, 10 iters, batch 50")
    args = parser.parse_args(argv)

    if args.smoke:
        args.n_min, args.n_max = 4, 6
        args.seeds, args.iters, args.batch = 2, 10, 50

    ns = range(args.n_min, args.n_max + 1)
    run(ns, seeds=args.seeds, iters=args.iters, batch=args.batch, seed=args.seed,
        budget_seconds=args.budget)


if __name__ == "__main__":
    main()
