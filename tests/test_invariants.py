"""Tests for src/invariants.py.

Two layers:
  1. Spot values on P4, C5, K4, Petersen. The expected numbers are standard
     textbook / literature values for the independence number (alpha), independent
     domination number (i), and minimum maximal matching number (mu*), NOT values
     read back out of our own code:
       - P4:  alpha=2, i=2, mu*=1     (path on 4 vertices)
       - C5:  alpha=2, i=2, mu*=2     (5-cycle)
       - K4:  alpha=1, i=1, mu*=2     (complete graph; mu* = perfect matching size)
       - Petersen: alpha=4, i=3, mu*=3  (Petersen graph; standard values)
  2. Theorem-based fuzz over 300 random connected graphs:
       alpha(G) >= R(G)   (Favaron, Maheo, Sacle 1991)
       alpha(G) <= a(G)   (Pepper 2004)
     A failure here is a bug in the invariant code -- fix the invariant, never the test.
"""

import networkx as nx
import pytest

import invariants as inv


# --------------------------------------------------------------------------- #
# 1. Spot values (literature)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "name, G, alpha_exp, i_exp, mustar_exp",
    [
        ("P4", nx.path_graph(4), 2, 2, 1),
        ("C5", nx.cycle_graph(5), 2, 2, 2),
        ("K4", nx.complete_graph(4), 1, 1, 2),
        ("Petersen", nx.petersen_graph(), 4, 3, 3),
    ],
)
def test_spot_values(name, G, alpha_exp, i_exp, mustar_exp):
    alpha, i = inv.alpha_and_i(G)
    assert alpha == alpha_exp, f"{name}: alpha {alpha} != {alpha_exp}"
    assert i == i_exp, f"{name}: i {i} != {i_exp}"
    assert inv.mustar(G) == mustar_exp, f"{name}: mu* {inv.mustar(G)} != {mustar_exp}"


def test_harmonic_index_regular():
    # For an r-regular graph H(G) = |E| / r exactly. Petersen: 15 edges, r=3 -> 5.
    G = nx.petersen_graph()
    assert inv.harmonic_index(G) == pytest.approx(15 / 3)
    # C5: 5 edges, r=2 -> 2.5
    assert inv.harmonic_index(nx.cycle_graph(5)) == pytest.approx(2.5)


def test_mustar_le_max_matching():
    # mu*(G) <= mu(G) always (a minimum maximal matching is a matching).
    for G in (nx.path_graph(4), nx.cycle_graph(5), nx.complete_graph(4), nx.petersen_graph()):
        mu = len(nx.max_weight_matching(G, maxcardinality=True))
        assert inv.mustar(G) <= mu


# --------------------------------------------------------------------------- #
# 2. Theorem-based fuzz
# --------------------------------------------------------------------------- #
def _random_connected(n, p, rng_seed):
    """Draw a connected G(n,p), retrying with fresh seeds until connected."""
    seed = rng_seed
    while True:
        G = nx.gnp_random_graph(n, p, seed=seed)
        if G.number_of_nodes() > 0 and nx.is_connected(G):
            return G
        seed += 100003  # large prime stride to avoid cycling


def test_theorem_inequalities_fuzz():
    import random

    rng = random.Random(20260611)
    count = 0
    target = 300
    while count < target:
        n = rng.randint(5, 15)
        p = rng.choice([0.2, 0.4, 0.6])
        G = _random_connected(n, p, rng.randint(0, 2**31 - 1))

        alpha, _ = inv.alpha_and_i(G)
        R = inv.residue(G)
        a = inv.annihilation_number(G)

        assert alpha >= R, (
            f"Favaron-Maheo-Sacle violated: alpha={alpha} < R={R} "
            f"on n={n} edges={sorted(G.edges())}"
        )
        assert alpha <= a, (
            f"Pepper bound violated: alpha={alpha} > a={a} "
            f"on n={n} edges={sorted(G.edges())}"
        )
        count += 1

    assert count == target
