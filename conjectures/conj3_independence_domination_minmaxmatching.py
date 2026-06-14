"""Conjecture 3 (TxGraffiti, open since 2020).

For every r-regular graph G with r > 0:

        i(G) <= mu*(G)

where i(G) is the independent domination number (the size of a smallest *maximal*
independent set) and mu*(G) is the minimum maximal matching number (the size of a
smallest maximal matching).
(Davila, Brimkov, Pepper 2025, arXiv 2507.17780, Conjecture 3.)

A counterexample is an r-regular graph (r > 0) with i(G) > mu*(G). The Pessimist
maximises the gap, so the reward is

        reward(G) = i(G) - mu*(G).

reward(G) > 0  => counterexample.
reward(G) == 0 => equality case (extremal family member).
reward(G) < 0  => the conjecture holds for G with slack.

Unlike Conjectures 1 and 4 (hypothesised over all nontrivial connected graphs), this
conjecture is hypothesised only over r-regular graphs, so it is searched with the
regular-graph evolutionary loop (src/search.run_regular_search) rather than the
Bernoulli-edge CEM. This module only supplies the reward; it does not check regularity
itself -- the search space guarantees it.
"""

from __future__ import annotations

import networkx as nx

import invariants as inv


def reward(G: nx.Graph) -> float:
    """i(G) - mu*(G). Positive means a counterexample to Conjecture 3."""
    _, i = inv.alpha_and_i(G)
    return i - inv.mustar(G)


def components(G: nx.Graph):
    """Return (i, mu*) -- the LHS and RHS of the conjectured inequality i <= mu*."""
    _, i = inv.alpha_and_i(G)
    return i, inv.mustar(G)
