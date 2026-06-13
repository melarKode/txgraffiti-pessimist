"""Tests for Conjecture 3: i(G) <= mu*(G) for r-regular graphs, r > 0.

reward(G) = i(G) - mu*(G); positive would be a counterexample. All graphs here are
small (<= 12 edges) so mustar stays on its exact brute-force path.
"""

import networkx as nx
import numpy as np
import pytest

import invariants as inv
import conj3_independence_domination_minmaxmatching as conj3
from search import run_regular_search

EQ_TOL = 1e-9


@pytest.mark.parametrize(
    "name, G, i_expected, mustar_expected",
    [
        ("K4", nx.complete_graph(4), 1, 2),          # 3-regular: i=1 < mu*=2 (slack)
        ("C4", nx.cycle_graph(4), 2, 2),             # 2-regular: i=2 = mu*=2 (equality)
        ("C5", nx.cycle_graph(5), 2, 2),             # 2-regular: equality
        ("K_3_3", nx.complete_bipartite_graph(3, 3), 3, 3),  # 3-regular: equality
        ("Prism", nx.circular_ladder_graph(3), 2, 2),        # 3-regular: equality
    ],
)
def test_conj3_components_spot_values(name, G, i_expected, mustar_expected):
    i, mustar = conj3.components(G)
    assert (i, mustar) == (i_expected, mustar_expected), name
    assert conj3.reward(G) == pytest.approx(i_expected - mustar_expected)


def test_conj3_reward_sign_convention():
    # K4: i < mu* so the conjecture holds with slack -> negative reward.
    assert conj3.reward(nx.complete_graph(4)) < -EQ_TOL
    # C4: i == mu* so it is an equality/extremal case -> reward ~ 0.
    assert abs(conj3.reward(nx.cycle_graph(4))) < EQ_TOL


@pytest.mark.parametrize("r, n", [(3, 4), (3, 6), (3, 8), (4, 6)])
def test_conj3_holds_on_random_regular_sample(r, n):
    # n*r/2 <= 12 keeps every graph on the brute-force mustar path. The conjecture is
    # believed true (open since 2020); on small r-regular graphs reward must be <= 0.
    rng = np.random.default_rng(np.random.SeedSequence([12345, n, r]))
    for _ in range(15):
        G = nx.random_regular_graph(r, n, seed=int(rng.integers(0, 2**31 - 1)))
        assert conj3.reward(G) <= EQ_TOL


def test_conj3_search_finds_no_counterexample_small():
    # Drive the actual search with the real conj3 reward on cubic graphs; the best
    # reward it can find must not exceed the equality tolerance.
    rng = np.random.default_rng(np.random.SeedSequence([0, 8, 3]))
    res = run_regular_search(8, 3, conj3.reward, iters=10, batch=40, rng=rng, progress=False)
    assert res.best_reward <= EQ_TOL
    assert inv.is_regular(res.best_graph) and inv.min_degree(res.best_graph) == 3
