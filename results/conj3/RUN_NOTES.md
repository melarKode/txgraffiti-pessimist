# Conjecture 3 full run — notes

Conjecture 3 (open since 2020): for every r-regular graph G with r > 0, i(G) <= mu*(G), where i is the independent domination number and mu* the minimum maximal matching number. Reward = i(G) - mu*(G); a positive reward on an r-regular graph would be a counterexample.

## Search space & methodology
- The hypothesis is r-regularity, so the search is a (mu + lambda) evolutionary loop over r-regular graphs (regular_sampler seeds the population; the degree-preserving regular_mutator breeds children), not the Bernoulli-edge CEM used for Conjectures 1/4 -- that never lands on a regular graph.
- **Connectivity choice:** the search is restricted to *connected* r-regular graphs. This does NOT narrow the conjecture. i(G) and mu*(G) are both additive over connected components, so a disconnected r-regular counterexample would require some connected r-regular component that is itself a counterexample. Restricting to connected graphs therefore loses no counterexamples while concentrating the search.
- Per-(n, r) wall-clock budget: 600.0s. A cell exceeding it is not recorded and that r's sweep stops at the previous n.
- mu* is exact by brute force while |E| = n*r/2 <= 12; cells above that are skipped unless --allow-ilp is set (CBC ILP path).

## Per-r coverage
- r = 3: largest n reached = 8
- r = 4: largest n reached = 6

## Per-(n, r) wall time (recorded cells only)

| n | r | seconds | graphs searched | max reward |
|---|---|---------|-----------------|------------|
| 4 | 3 | 30 | 100400 | -1.000000 |
| 5 | 4 | 34 | 100400 | -1.000000 |
| 6 | 3 | 14 | 100400 | +0.000000 |
| 6 | 4 | 21 | 100400 | +0.000000 |
| 8 | 3 | 18 | 100400 | +0.000000 |

## Equality cases (i = mu*) recovered
These are the extremal r-regular graphs the search found on the boundary i = mu*. Every one is connected and **well-covered** (alpha = i, i.e. all maximal independent sets have the same size); the recovered family is small dense regular graphs such as the triangular prism (n=6, r=3) and the octahedron K_{2,2,2} (n=6, r=4).

| n | r | i | mu* | alpha | triangles | bipartite | well-covered |
|---|---|---|-----|-------|-----------|-----------|--------------|
| 6 | 3 | 2 | 2 | 2 | 2 | False | True |
| 8 | 3 | 3 | 3 | 3 | 1 | False | True |
| 6 | 4 | 2 | 2 | 2 | 8 | False | True |

Counterexample found: **False**. Global best reward: +0.000000e+00. Distinct equality (i = mu*) cases: 3. Total graphs searched: 502000.
