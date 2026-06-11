# Conjecture 4 full run — notes

- Requested n range: 4..14
- Per-n wall-clock budget: 600.0s (10 min)
- **Actual cap reached: n = 8**
- n = 9 exceeded the budget and was aborted (not recorded). The minimum maximal matching ILP solves a CBC subprocess per graph (~30-80 ms each on this machine), so the ~100,000 evaluations per n become the bottleneck at large n.

## Per-n wall time (recorded n only)

| n | seconds | max reward |
|---|---------|------------|
| 4 | 7 | +0.000000 |
| 5 | 7 | -0.257143 |
| 6 | 9 | +0.000000 |
| 7 | 359 | -0.095238 |
| 8 | 564 | -0.083333 |

Counterexample found: **False**. Global best reward: +2.220446e-16.
