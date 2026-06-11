"""Exact graph invariants for the Pessimist search.

Every invariant here is computed *exactly* (no heuristics, no approximations) so that
a positive reward genuinely means a counterexample, never a numerical artefact. The
intended operating regime is small graphs (n up to ~22), where exact enumeration and
small ILPs are tractable.

Invariants provided:
  max_degree, min_degree, is_regular, is_connected   -- networkx wrappers
  annihilation_number(G)  a(G)   -- Pepper 2004
  residue(G)              R(G)   -- Havel-Hakimi terminal zero count
  harmonic_index(G)       H(G)
  alpha_and_i(G)        (alpha, i)  -- independence and independent-domination numbers
  mustar(G)              mu*(G)  -- minimum maximal matching (= i of the line graph)

A small in-memory cache keyed by the sorted edge tuple avoids recomputation when the
same graph is revisited (the CEM resamples identical graphs constantly).
"""

from __future__ import annotations

import itertools
import warnings

import networkx as nx
import pulp


# --------------------------------------------------------------------------- #
# Caching
# --------------------------------------------------------------------------- #
def _key(G: nx.Graph):
    """Hashable canonical-ish key: number of nodes plus the sorted edge list.

    Not isomorphism-canonical (that would be expensive); two graphs with the same
    labelled edge set collide, which is exactly what we want for a memo cache.
    """
    return (G.number_of_nodes(), tuple(sorted(tuple(sorted(e)) for e in G.edges())))


_CACHE: dict = {}


def _memo(name, func, G):
    k = (name, _key(G))
    if k not in _CACHE:
        _CACHE[k] = func(G)
    return _CACHE[k]


def clear_cache():
    """Drop the invariant cache (used by tests to measure cold cost)."""
    _CACHE.clear()


# --------------------------------------------------------------------------- #
# Degree-based wrappers
# --------------------------------------------------------------------------- #
def _degrees(G: nx.Graph):
    return [d for _, d in G.degree()]


def max_degree(G: nx.Graph) -> int:
    return max(_degrees(G), default=0)


def min_degree(G: nx.Graph) -> int:
    return min(_degrees(G), default=0)


def is_regular(G: nx.Graph) -> bool:
    degs = _degrees(G)
    return len(set(degs)) <= 1


def is_connected(G: nx.Graph) -> bool:
    if G.number_of_nodes() == 0:
        return False
    return nx.is_connected(G)


# --------------------------------------------------------------------------- #
# Annihilation number  a(G)  (Pepper 2004)
# --------------------------------------------------------------------------- #
def _annihilation_number(G: nx.Graph) -> int:
    """Largest k such that the sum of the k smallest degrees is at most |E(G)|."""
    degs = sorted(_degrees(G))
    m = G.number_of_edges()
    running = 0
    k = 0
    for i, d in enumerate(degs, start=1):
        running += d
        if running <= m:
            k = i
        else:
            break
    return k


def annihilation_number(G: nx.Graph) -> int:
    return _memo("a", _annihilation_number, G)


# --------------------------------------------------------------------------- #
# Residue  R(G)  (Havel-Hakimi)
# --------------------------------------------------------------------------- #
def _residue(G: nx.Graph) -> int:
    """Standard Havel-Hakimi residue: repeatedly delete the largest degree d and
    subtract 1 from the next d degrees; the residue is the number of zeros left
    when the sequence is exhausted (i.e. all remaining entries are zero)."""
    seq = sorted(_degrees(G), reverse=True)
    # Drop trailing/initial zeros are handled naturally by the loop.
    while seq and seq[0] > 0:
        d = seq.pop(0)
        if d > len(seq):
            # Not graphical in the Havel-Hakimi sense; shouldn't happen for a real
            # graph's degree sequence, but guard anyway.
            d = len(seq)
        for i in range(d):
            seq[i] -= 1
        seq.sort(reverse=True)
    # Everything remaining is a zero; the residue counts them.
    return len(seq)


def residue(G: nx.Graph) -> int:
    return _memo("R", _residue, G)


# --------------------------------------------------------------------------- #
# Harmonic index  H(G)
# --------------------------------------------------------------------------- #
def _harmonic_index(G: nx.Graph) -> float:
    deg = dict(G.degree())
    total = 0.0
    for u, v in G.edges():
        total += 2.0 / (deg[u] + deg[v])
    return total


def harmonic_index(G: nx.Graph) -> float:
    return _memo("H", _harmonic_index, G)


# --------------------------------------------------------------------------- #
# Independence number alpha and independent domination number i
# --------------------------------------------------------------------------- #
def _alpha_and_i(G: nx.Graph):
    """Enumerate all *maximal* independent sets of G as the maximal cliques of the
    complement, then return (max size, min size) = (alpha(G), i(G)).

    A maximal independent set of G is exactly a maximal clique of complement(G);
    the largest is the independence number alpha, the smallest is the independent
    domination number i (smallest maximal independent set). Exact and fast for
    n up to ~22.
    """
    n = G.number_of_nodes()
    if n == 0:
        return (0, 0)
    if G.number_of_edges() == 0:
        # Complement is complete: the only maximal independent set is all of V.
        return (n, n)
    comp = nx.complement(G)
    sizes = [len(c) for c in nx.find_cliques(comp)]
    return (max(sizes), min(sizes))


def alpha_and_i(G: nx.Graph):
    return _memo("alpha_i", _alpha_and_i, G)


# --------------------------------------------------------------------------- #
# Minimum maximal matching number  mu*(G)
# --------------------------------------------------------------------------- #
def _mustar_bruteforce(G: nx.Graph) -> int:
    """Exact minimum maximal matching by subset enumeration. Used when |E| is small
    (<= 12) both as the primary method there and as an independent cross-check."""
    edges = [tuple(sorted(e)) for e in G.edges()]
    m = len(edges)
    if m == 0:
        return 0

    def is_matching(subset):
        seen = set()
        for u, v in subset:
            if u in seen or v in seen:
                return False
            seen.add(u)
            seen.add(v)
        return True

    def is_maximal(subset):
        matched = set()
        for u, v in subset:
            matched.add(u)
            matched.add(v)
        # Maximal iff no edge has both endpoints unmatched.
        for u, v in edges:
            if u not in matched and v not in matched:
                return False
        return True

    best = m
    for size in range(1, m + 1):
        if size >= best:
            break
        for subset in itertools.combinations(edges, size):
            if is_matching(subset) and is_maximal(subset):
                best = size
                break
        else:
            continue
        break
    return best


def _mustar_ilp(G: nx.Graph) -> int:
    """Minimum maximal matching via a direct 0/1 ILP solved with CBC.

    Variables x_e in {0,1}. Constraints:
      matching   : for every vertex v, sum of incident x_e <= 1
      maximality : for every edge e, x_e + sum_{f shares an endpoint with e} x_f >= 1
    Objective: minimise sum x_e.
    """
    edges = [tuple(sorted(e)) for e in G.edges()]
    if not edges:
        return 0

    prob = pulp.LpProblem("min_maximal_matching", pulp.LpMinimize)
    x = {e: pulp.LpVariable(f"x_{i}", cat="Binary") for i, e in enumerate(edges)}

    prob += pulp.lpSum(x.values())

    incident = {v: [] for v in G.nodes()}
    for e in edges:
        u, v = e
        incident[u].append(e)
        incident[v].append(e)
    for v in G.nodes():
        if incident[v]:
            prob += pulp.lpSum(x[e] for e in incident[v]) <= 1

    for e in edges:
        u, v = e
        neighbours = set(incident[u]) | set(incident[v])  # includes e itself
        prob += pulp.lpSum(x[f] for f in neighbours) >= 1

    status = prob.solve(pulp.PULP_CBC_CMD(msg=0))
    if pulp.LpStatus[status] != "Optimal":
        raise RuntimeError(f"ILP for mu* did not solve to optimality: {pulp.LpStatus[status]}")
    return int(round(pulp.value(prob.objective)))


def _mustar(G: nx.Graph) -> int:
    if G.number_of_edges() <= 12:
        return _mustar_bruteforce(G)
    return _mustar_ilp(G)


def mustar(G: nx.Graph) -> int:
    """Minimum maximal matching number mu*(G).

    On graphs with n <= 10 we cross-check against i(L(G)) -- the independent
    domination number of the line graph -- since a minimum maximal matching of G is
    exactly a smallest maximal independent set of L(G). A mismatch indicates an
    invariant bug and emits a warning.
    """
    val = _memo("mustar", _mustar, G)
    if G.number_of_nodes() <= 10 and G.number_of_edges() > 0:
        L = nx.line_graph(G)
        _, i_line = alpha_and_i(L)
        if i_line != val:
            warnings.warn(
                f"mustar cross-check mismatch: mustar={val} but i(L(G))={i_line} "
                f"for graph with edges {sorted(G.edges())}",
                RuntimeWarning,
            )
    return val
