"""Conjecture 4 (TxGraffiti, open since 2023).

For every nontrivial connected graph G:

        mu*(G) <= H(G)

where mu*(G) is the minimum maximal matching number (the size of a smallest maximal
matching) and H(G) = sum_{uv in E} 2 / (deg u + deg v) is the harmonic index.
(Davila, Brimkov, Pepper 2025, arXiv 2507.17780, Conjecture 4.)

A counterexample is a connected graph with mu*(G) > H(G). The Pessimist maximises the
gap, so the reward is

        reward(G) = mu*(G) - H(G).

reward(G) > 0  => counterexample.
reward(G) == 0 => equality case (extremal family member).
reward(G) < 0  => the conjecture holds for G with slack.
"""

from __future__ import annotations

import networkx as nx

import invariants as inv


def reward(G: nx.Graph) -> float:
    """mu*(G) - H(G). Positive means a counterexample to Conjecture 4."""
    return inv.mustar(G) - inv.harmonic_index(G)


def components(G: nx.Graph):
    """Return (mu*, H) so callers can log both sides of the inequality."""
    return inv.mustar(G), inv.harmonic_index(G)
