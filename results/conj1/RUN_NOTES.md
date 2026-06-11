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
