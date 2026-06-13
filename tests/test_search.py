"""Tests for the regular-graph evolutionary search (Conjecture 3 infrastructure).

These exercise `run_regular_search` only; the CEM paths (`run_cem`/`run_search`) keep
their existing coverage. Everything here stays on small graphs so the reward never
touches the ILP path of mustar.
"""

import json

import numpy as np

import invariants as inv
from search import RegularSearchResult, run_regular_search


def _conj3_reward(G):
    """i(G) - mu*(G); the Conjecture 3 objective, inlined to avoid a module dependency."""
    return inv.alpha_and_i(G)[1] - inv.mustar(G)


def test_run_regular_search_returns_regular_best_graph():
    rng = np.random.default_rng(np.random.SeedSequence([0, 6, 3]))
    res = run_regular_search(6, 3, _conj3_reward, iters=8, batch=30, rng=rng, progress=False)

    assert isinstance(res, RegularSearchResult)
    assert res.n == 6 and res.r == 3
    # The best graph must stay inside the search space: 3-regular on 6 vertices.
    assert inv.is_regular(res.best_graph)
    assert inv.min_degree(res.best_graph) == 3
    assert inv.max_degree(res.best_graph) == 3
    # mu + iters*lam evaluations (mu = max(4, batch//5) = 6, lam = batch = 30).
    assert res.evaluations == 6 + 8 * 30


def test_run_regular_search_result_is_json_serialisable():
    rng = np.random.default_rng(np.random.SeedSequence([0, 8, 3]))
    res = run_regular_search(8, 3, _conj3_reward, iters=5, batch=20, rng=rng, progress=False)

    payload = res.to_json()
    assert set(payload) == {
        "n", "r", "best_reward", "best_edges", "equality_edges", "evaluations", "log"
    }
    # Serialises cleanly through JSON (tuples become lists; that's fine -- this is
    # exactly what the driver does when it json.dumps each per-run log).
    reloaded = json.loads(json.dumps(payload))
    assert reloaded["n"] == 8 and reloaded["r"] == 3
    assert reloaded["best_edges"] == [list(e) for e in payload["best_edges"]]
    assert len(res.log) == 5
    assert all({"iter", "max", "mean", "median"} <= set(entry) for entry in res.log)


def test_run_regular_search_is_deterministic_for_a_fixed_rng():
    def run():
        rng = np.random.default_rng(np.random.SeedSequence([7, 6, 3]))
        return run_regular_search(6, 3, _conj3_reward, iters=6, batch=20, rng=rng, progress=False)

    a, b = run(), run()
    assert a.best_reward == b.best_reward
    assert a.best_edges == b.best_edges
    assert a.evaluations == b.evaluations
