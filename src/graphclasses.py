"""Graph encoders and samplers used by the Pessimist search.

Two families of generators:

  * General graphs via a length n(n-1)/2 bitstring over the upper-triangle of the
    adjacency matrix. Disconnected graphs are *not* rejected here -- the search
    penalises them through the reward function so the optimiser learns to avoid
    them on its own.

  * Regular graphs, for conjectures whose hypothesis is r-regularity (e.g.
    Conjecture 3). `regular_sampler` draws random r-regular graphs and
    `regular_mutator` does a degree-preserving double edge swap.
"""

from __future__ import annotations

import itertools

import networkx as nx
import numpy as np


def _pair_index(n):
    """The canonical ordering of vertex pairs (i, j), i < j, used by the codec."""
    return list(itertools.combinations(range(n), 2))


def general_from_bitstring(bits, n: int) -> nx.Graph:
    """Decode a length n(n-1)/2 array of 0/1 into a graph on vertices 0..n-1.

    Bit k (in the order given by itertools.combinations(range(n), 2)) is the
    presence of edge (i, j). Disconnected results are returned as-is; the caller
    is responsible for penalising them.
    """
    bits = np.asarray(bits).ravel()
    pairs = _pair_index(n)
    if len(bits) != len(pairs):
        raise ValueError(
            f"bitstring length {len(bits)} != n(n-1)/2 = {len(pairs)} for n={n}"
        )
    G = nx.Graph()
    G.add_nodes_from(range(n))
    for bit, (i, j) in zip(bits, pairs):
        if bit:
            G.add_edge(i, j)
    return G


def bitstring_from_graph(G: nx.Graph, n: int) -> np.ndarray:
    """Encode a graph on vertices 0..n-1 back into its bitstring (inverse of
    general_from_bitstring). Used for round-trip tests."""
    pairs = _pair_index(n)
    bits = np.zeros(len(pairs), dtype=np.int8)
    for k, (i, j) in enumerate(pairs):
        if G.has_edge(i, j):
            bits[k] = 1
    return bits


def regular_sampler(n: int, r: int, rng: np.random.Generator) -> nx.Graph:
    """Draw a random r-regular graph on n vertices.

    nx.random_regular_graph requires n*r to be even (the handshake/parity
    condition); we check it explicitly and raise a clear error otherwise.
    """
    if (n * r) % 2 != 0:
        raise ValueError(f"n*r must be even for an r-regular graph (n={n}, r={r})")
    if r >= n:
        raise ValueError(f"need r < n for a simple r-regular graph (n={n}, r={r})")
    seed = int(rng.integers(0, 2**31 - 1))
    return nx.random_regular_graph(r, n, seed=seed)


def regular_mutator(G: nx.Graph, rng: np.random.Generator) -> nx.Graph:
    """Return a degree-preserving mutation of G via a double edge swap.

    nx.double_edge_swap keeps every vertex's degree fixed, so an r-regular graph
    stays r-regular. Operates on a copy; the input is left unchanged.
    """
    H = G.copy()
    if H.number_of_edges() < 2:
        return H
    seed = int(rng.integers(0, 2**31 - 1))
    try:
        nx.double_edge_swap(H, nswap=1, max_tries=100, seed=seed)
    except nx.NetworkXAlgorithmError:
        # Not enough eligible edges to swap (e.g. very small/dense graph); return
        # the unchanged copy rather than failing the search.
        pass
    return H
