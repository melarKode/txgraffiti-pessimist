"""Conjecture 1 (TxGraffiti, open since 2016).

For every nontrivial connected graph G:

        alpha(G) >= (a(G) + R(G)) / Delta(G)

where alpha(G) is the independence number, a(G) is the annihilation number, R(G) is the
residue, and Delta(G) is the maximum degree.
(Davila, Brimkov, Pepper 2025, arXiv 2507.17780, Conjecture 1.)

A counterexample is a connected graph with alpha(G) < (a(G) + R(G)) / Delta(G). The
Pessimist maximises the gap, so the reward is

        reward(G) = (a(G) + R(G)) / Delta(G) - alpha(G).

reward(G) > 0  => counterexample.
reward(G) == 0 => equality case (extremal family member).
reward(G) < 0  => the conjecture holds for G with slack.

Note: src/search.py only ever calls reward() on graphs that pass inv.is_connected(G),
and every connected graph on n >= 2 vertices has Delta(G) >= 1, so the division below
never sees Delta(G) == 0.
"""

from __future__ import annotations

import networkx as nx

import invariants as inv


def reward(G: nx.Graph) -> float:
    """(a(G) + R(G)) / Delta(G) - alpha(G). Positive means a counterexample to Conjecture 1."""
    alpha, _ = inv.alpha_and_i(G)
    return (inv.annihilation_number(G) + inv.residue(G)) / inv.max_degree(G) - alpha


def components(G: nx.Graph):
    """Return (alpha, (a+R)/Delta) -- the LHS and RHS of the conjectured inequality."""
    alpha, _ = inv.alpha_and_i(G)
    rhs = (inv.annihilation_number(G) + inv.residue(G)) / inv.max_degree(G)
    return alpha, rhs
