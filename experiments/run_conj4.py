"""Pessimist run against Conjecture 4:  mu*(G) <= H(G)  for nontrivial connected G.

For each vertex count n we launch a multi-restart CEM search that maximises the gap
reward(G) = mu*(G) - H(G). We log every run, summarise the best reward per n, collect
all equality cases (reward == 0, i.e. extremal graphs with mu* = H) deduplicated by
Weisfeiler-Lehman hash, and draw a mu* vs H scatter. A positive reward anywhere would be
a counterexample; if that ever happens we dump full provenance, re-verify every invariant
by an independent method, and write VERIFIED.md.

Usage:
  python experiments/run_conj4.py            # full run: n in 4..14, 10 seeds, 50 iters, batch 200
  python experiments/run_conj4.py --smoke    # n in 4..6, 2 seeds, 10 iters, batch 50
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

import matplotlib

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
import conj4_minmaxmatching_harmonic as conj4  # noqa: E402
from search import run_search  # noqa: E402

OUTDIR = os.path.join(ROOT, "results", "conj4")

# A reward within EQ_TOL of zero is an equality case (mu* = H), not a counterexample.
# Only reward strictly above this tolerance refutes the conjecture. This matters because
# float rounding makes exact-equality graphs like K4 (mu*=2, H=2) land at +2e-16.
EQ_TOL = 1e-9


# --------------------------------------------------------------------------- #
# Counterexample handling (defensive; expected never to trigger)
# --------------------------------------------------------------------------- #
def reverify(G: nx.Graph) -> dict:
    """Recompute mu* and H by independent methods and report all of them.

    mu* is recomputed three ways where feasible: the production path, an explicit
    brute-force subset search, and i(L(G)) (smallest maximal independent set of the
    line graph). H is recomputed from the degree sequence directly.
    """
    m = G.number_of_edges()
    deg = dict(G.degree())
    H_manual = sum(2.0 / (deg[u] + deg[v]) for u, v in G.edges())

    methods = {"mustar_production": inv.mustar(G)}
    if m <= 18:
        methods["mustar_bruteforce"] = inv._mustar_bruteforce(G)
    methods["mustar_via_line_graph_i"] = inv.alpha_and_i(nx.line_graph(G))[1] if m else 0
    methods["mustar_fresh_ilp"] = inv._mustar_ilp(G) if m else 0

    return {
        "edges": sorted(tuple(sorted(e)) for e in G.edges()),
        "n": G.number_of_nodes(),
        "m": m,
        "degree_sequence": sorted(deg.values(), reverse=True),
        "H_manual": H_manual,
        "H_production": inv.harmonic_index(G),
        "mustar_methods": methods,
        "all_mustar_agree": len(set(methods.values())) == 1,
        "reward": methods["mustar_production"] - H_manual,
    }


def handle_counterexample(G: nx.Graph, n: int, seed_idx: int):
    ts = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    verification = reverify(G)
    provenance = {
        "conjecture": "Conjecture 4 (arXiv 2507.17780): mu*(G) <= H(G) for nontrivial connected G",
        "found_at": ts,
        "n": n,
        "seed_index": seed_idx,
        "connected": inv.is_connected(G),
        "verification": verification,
    }
    path = os.path.join(OUTDIR, f"COUNTEREXAMPLE_{ts}.json")
    with open(path, "w") as f:
        json.dump(provenance, f, indent=2)

    with open(os.path.join(OUTDIR, "VERIFIED.md"), "w") as f:
        f.write("# Conjecture 4 counterexample — verification\n\n")
        f.write(f"Found {ts}, n={n}, seed index {seed_idx}.\n\n")
        f.write(f"- Edges: `{verification['edges']}`\n")
        f.write(f"- Degree sequence: {verification['degree_sequence']}\n")
        f.write(f"- H(G) (manual) = {verification['H_manual']}\n")
        f.write(f"- mu* by all methods: {verification['mustar_methods']}\n")
        f.write(f"- All mu* methods agree: {verification['all_mustar_agree']}\n")
        f.write(f"- reward = mu* - H = {verification['reward']}\n\n")
        f.write("If `all_mustar_agree` is true and reward > 0, this is a genuine "
                "counterexample to Conjecture 4.\n")
    print(f"\n!!! POSITIVE REWARD at n={n}. Wrote {path} and VERIFIED.md !!!")


# --------------------------------------------------------------------------- #
# Plot
# --------------------------------------------------------------------------- #
def make_scatter(points, path):
    """points: list of (H, mustar, is_equality)."""
    if not points:
        return
    Hs = [p[0] for p in points]
    mus = [p[1] for p in points]
    eq = [p[2] for p in points]

    fig, ax = plt.subplots(figsize=(7, 6))
    non_eq = [(h, m) for h, m, e in points if not e]
    eq_pts = [(h, m) for h, m, e in points if e]
    if non_eq:
        ax.scatter([h for h, _ in non_eq], [m for _, m in non_eq], s=18, alpha=0.5,
                   label="best per run (mu* < H)", color="#3366cc")
    if eq_pts:
        ax.scatter([h for h, _ in eq_pts], [m for _, m in eq_pts], s=60, marker="D",
                   label="equality cases (mu* = H)", color="#cc3311", zorder=5)

    lo = 0
    hi = max(max(Hs), max(mus)) + 1
    ax.plot([lo, hi], [lo, hi], "k--", lw=1, label="mu* = H (conjecture boundary)")
    ax.set_xlabel("H(G)  (harmonic index)")
    ax.set_ylabel("mu*(G)  (min maximal matching)")
    ax.set_title("Conjecture 4: mu*(G) <= H(G)\nall searched graphs lie on/under the boundary")
    ax.legend(loc="upper left")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def run(ns, seeds, iters, batch, seed, progress=True):
    os.makedirs(OUTDIR, exist_ok=True)

    summary = {
        "conjecture": "Conjecture 4 (arXiv 2507.17780): mu*(G) <= H(G), nontrivial connected G",
        "reward": "mu*(G) - H(G); positive == counterexample",
        "params": {"ns": list(ns), "seeds": seeds, "iters": iters, "batch": batch, "seed": seed},
        "per_n": {},
        "total_graphs_searched": 0,
        "global_best_reward": None,
        "counterexample_found": False,
    }

    equality = {}          # wl_hash -> edge list
    scatter_points = []    # (H, mustar, is_equality)
    global_best_reward = -float("inf")

    for n in ns:
        best, per_seed = run_search(
            n, conj4.reward, iters=iters, batch=batch, seeds=seeds,
            seed=seed + n, progress=progress,
        )

        for k, res in enumerate(per_seed):
            with open(os.path.join(OUTDIR, f"log_n{n:02d}_seed{k}.json"), "w") as f:
                json.dump(res.to_json(), f, indent=2)

            if res.best_graph is not None and res.best_graph.number_of_edges() > 0:
                mu, H = conj4.components(res.best_graph)
                scatter_points.append((H, mu, abs(res.best_reward) < 1e-9))

            for G in res.equality_graphs:
                h = nx.weisfeiler_lehman_graph_hash(G)
                if h not in equality:
                    equality[h] = sorted(tuple(sorted(e)) for e in G.edges())
                    mu, H = conj4.components(G)
                    scatter_points.append((H, mu, True))

        max_reward_n = max(r.best_reward for r in per_seed)
        summary["per_n"][str(n)] = {
            "max_reward": max_reward_n,
            "best_edges": best.best_edges,
            "graphs_searched": iters * batch * seeds,
        }
        summary["total_graphs_searched"] += iters * batch * seeds

        if max_reward_n > global_best_reward:
            global_best_reward = max_reward_n

        if max_reward_n > EQ_TOL:
            status = "COUNTEREXAMPLE!"
        elif max_reward_n > -EQ_TOL:
            status = "holds (equality reached)"
        else:
            status = "holds"
        print(f"n={n:2d}: max reward = {max_reward_n:+.6f}  [{status}]")

        if max_reward_n > EQ_TOL:
            summary["counterexample_found"] = True
            handle_counterexample(best.best_graph, n, 0)

    summary["global_best_reward"] = global_best_reward
    summary["distinct_equality_cases"] = len(equality)

    with open(os.path.join(OUTDIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    with open(os.path.join(OUTDIR, "equality_cases.json"), "w") as f:
        json.dump(
            {"count": len(equality), "edge_lists": list(equality.values())}, f, indent=2
        )
    make_scatter(scatter_points, os.path.join(OUTDIR, "scatter_mustar_vs_H.png"))

    print(f"\nDone. global best reward = {global_best_reward:+.6f}; "
          f"{len(equality)} distinct equality case(s); "
          f"{summary['total_graphs_searched']} graphs searched.")
    print(f"Outputs in {OUTDIR}")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description="Pessimist run against Conjecture 4 (mu* <= H).")
    parser.add_argument("--n-min", type=int, default=4)
    parser.add_argument("--n-max", type=int, default=14)
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--iters", type=int, default=50)
    parser.add_argument("--batch", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--smoke", action="store_true",
                        help="tiny run: n in 4..6, 2 seeds, 10 iters, batch 50")
    args = parser.parse_args(argv)

    if args.smoke:
        args.n_min, args.n_max = 4, 6
        args.seeds, args.iters, args.batch = 2, 10, 50

    ns = range(args.n_min, args.n_max + 1)
    run(ns, seeds=args.seeds, iters=args.iters, batch=args.batch, seed=args.seed)


if __name__ == "__main__":
    main()
