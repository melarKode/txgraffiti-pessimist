"""The equality-case dedup key is a Weisfeiler-Lehman graph hash. This guards that
the hash is deterministic across calls (it is in networkx >= 3, but a flaky key would
silently corrupt the dedup), and that isomorphic relabellings collide as intended."""

import networkx as nx


def test_wl_hash_deterministic_on_k4():
    G = nx.complete_graph(4)
    h1 = nx.weisfeiler_lehman_graph_hash(G)
    h2 = nx.weisfeiler_lehman_graph_hash(G)
    assert h1 == h2


def test_wl_hash_invariant_under_relabel():
    G = nx.cycle_graph(6)
    H = nx.relabel_nodes(G, {i: (i + 3) % 6 for i in range(6)})
    assert nx.weisfeiler_lehman_graph_hash(G) == nx.weisfeiler_lehman_graph_hash(H)
