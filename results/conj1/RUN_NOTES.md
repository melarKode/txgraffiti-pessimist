# Conjecture 1 full run — notes

- Requested n range: 4..30
- Per-n wall-clock budget: 600.0s (10 min)
- **Actual cap reached: n = 22**
- n = 23 exceeded the budget and was aborted (not recorded). Conjecture 1 needs only alpha, a, R, Delta -- no CBC/ILP subprocess -- but alpha(G) (via maximal cliques of the complement) becomes the bottleneck as n grows, so the ~100,000 evaluations per n eventually exceed the budget.

## Per-n wall time (recorded n only)

| n | seconds | max reward |
|---|---------|------------|
| 4 | 2 | +0.000000 |
| 5 | 2 | +0.000000 |
| 6 | 2 | +0.000000 |
| 7 | 3 | +0.000000 |
| 8 | 3 | -0.333333 |
| 9 | 5 | -0.333333 |
| 10 | 7 | -0.666667 |
| 11 | 9 | -0.750000 |
| 12 | 11 | -0.750000 |
| 13 | 14 | -1.000000 |
| 14 | 16 | -1.000000 |
| 15 | 18 | -1.000000 |
| 16 | 22 | -1.777778 |
| 17 | 69 | -1.777778 |
| 18 | 150 | -2.000000 |
| 19 | 237 | -2.076923 |
| 20 | 274 | -2.000000 |
| 21 | 346 | -2.727273 |
| 22 | 458 | -2.636364 |

Counterexample found: **False**. Global best reward: +0.000000e+00.

## Equality cases (n = 4..22 search range)

The search found 6 distinct (WL-deduped) equality graphs, all with reward exactly 0
(`alpha(G) == (a(G)+R(G))/Delta(G)`):

| graph | n | m | degree sequence | alpha | a | R | Delta | (a+R)/Delta |
|---|---|---|---|---|---|---|---|---|
| C4 (4-cycle) | 4 | 4 | [2,2,2,2] | 2 | 2 | 2 | 2 | 2.0 |
| P4 (path) | 4 | 3 | [2,2,1,1] | 2 | 2 | 2 | 2 | 2.0 |
| K4 (complete) | 4 | 6 | [3,3,3,3] | 1 | 2 | 1 | 3 | 1.0 |
| C5 (5-cycle) | 5 | 5 | [2,2,2,2,2] | 2 | 2 | 2 | 2 | 2.0 |
| P6 (path) | 6 | 5 | [2,2,2,2,1,1] | 3 | 3 | 3 | 2 | 3.0 |
| C7 (7-cycle) | 7 | 7 | [2,2,2,2,2,2,2] | 3 | 3 | 3 | 2 | 3.0 |

All six are small graphs of maximum degree 2 or 3 (cycles, paths, and K4). Spot-checking
further small cycles/paths (`C3..C11`, `P3..P11`, `K2..K6`) shows reward = 0 only for
`C3, C4, C5, C7, P3, P4, P6, K3, K4` -- equality is **not** an infinite family with a
simple closed form over cycles/paths; it occurs for a sporadic finite set of small
graphs with `Delta in {2, 3}`. No equality cases were found at any `n >= 8` in the
22-vertex search, consistent with this being a small-graph phenomenon.

## A boundary case at n = 2: K2

The search range starts at `n = 4` (matching `run_conj4.py`'s convention), but checking
`n = 2` and `n = 3` by hand against `conj1.reward` is instructive:

| graph | n | alpha | a | R | Delta | (a+R)/Delta | reward |
|---|---|---|---|---|---|---|---|
| K2 = P2 (single edge) | 2 | 1 | 1 | 1 | 1 | 2.0 | **+1.0** |
| P3 | 3 | 2 | 2 | 2 | 2 | 2.0 | 0.0 |
| K3 | 3 | 1 | 1 | 1 | 2 | 1.0 | 0.0 |

`K2`, the smallest connected graph with `n >= 2`, has `alpha(K2) = 1` but
`(a(K2)+R(K2))/Delta(K2) = (1+1)/1 = 2`, so `alpha(K2) < (a(K2)+R(K2))/Delta(K2)` --
i.e. **`reward(K2) = +1 > 0`, the literal counterexample condition**, under the
hypothesis `n >= 2` (as stated in `lean/Conjectures.lean`'s `conjecture_one`, which
requires only `2 <= Fintype.card V`). At `n = 3` both connected graphs (`P3`, `K3`)
satisfy the conjecture with equality.

This is **not** a refutation of the published Conjecture 1 -- the literature's
"nontrivial connected graph" almost certainly intends `n >= 3` (excluding the single
edge as a degenerate case), and the search range `n >= 4` never encounters it. But it
is worth flagging precisely: if `conjecture_one` is ever proved in Lean under the literal
hypothesis `2 <= Fintype.card V`, `K2` is a genuine counterexample to *that* statement,
and the hypothesis should be strengthened to `3 <= Fintype.card V` (or "nontrivial"
should be defined to exclude `K2`). See `proof_attempt.md` for the exact computation.
