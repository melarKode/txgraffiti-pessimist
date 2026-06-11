"""Tests for src/graphclasses.py: codec round-trip and regular generators."""

import networkx as nx
import numpy as np
import pytest

import graphclasses as gc


def test_bitstring_roundtrip():
    # Encode -> decode -> encode reproduces the same bitstring for several graphs.
    n = 6
    rng = np.random.default_rng(0)
    for _ in range(20):
        d = n * (n - 1) // 2
        bits = rng.integers(0, 2, size=d)
        G = gc.general_from_bitstring(bits, n)
        bits2 = gc.bitstring_from_graph(G, n)
        assert np.array_equal(bits, bits2)


def test_all_ones_is_complete_and_keeps_isolated_allowed():
    n = 5
    d = n * (n - 1) // 2
    G = gc.general_from_bitstring(np.ones(d, dtype=int), n)
    assert G.number_of_edges() == d
    assert nx.is_isomorphic(G, nx.complete_graph(n))
    # All zeros: edgeless graph with n isolated nodes, returned (not rejected).
    H = gc.general_from_bitstring(np.zeros(d, dtype=int), n)
    assert H.number_of_nodes() == n and H.number_of_edges() == 0
    assert not nx.is_connected(H)


def test_regular_sampler_degrees_and_parity():
    rng = np.random.default_rng(42)
    G = gc.regular_sampler(8, 3, rng)
    assert all(deg == 3 for _, deg in G.degree())
    assert G.number_of_nodes() == 8
    # Odd n*r is rejected.
    with pytest.raises(ValueError):
        gc.regular_sampler(7, 3, rng)  # 7*3 = 21 is odd


def test_regular_mutator_preserves_degree_sequence():
    rng = np.random.default_rng(7)
    G = gc.regular_sampler(10, 3, rng)
    before = sorted(d for _, d in G.degree())
    H = gc.regular_mutator(G, rng)
    after = sorted(d for _, d in H.degree())
    assert before == after  # degree-preserving
    assert G.number_of_edges() == H.number_of_edges()
