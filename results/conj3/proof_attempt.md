# Conjecture 3 — small-case verification, two exact subfamilies, and what stays open

**Conjecture 3 (TxGraffiti, open since 2020; Davila–Brimkov–Pepper, arXiv:2507.17780).**
For every $r$-regular graph $G$ with $r > 0$,
$$i(G) \le \mu^*(G),$$
where $i(G)$ is the *independent domination number* (the size of a smallest **maximal**
independent set) and $\mu^*(G)$ is the *minimum maximal matching number* (the size of a
smallest maximal matching).

The Pessimist search found **no counterexample** (global best reward $i-\mu^* = 0$ across
$502{,}000$ searched $r$-regular graphs, $r\in\{3,4\}$, up to the brute-force frontier
$|E| = nr/2 \le 12$). This note proves the conjecture **completely for two infinite
subfamilies** — complete graphs and balanced complete bipartite graphs — verifies every
equality case the search recovered by exact hand computation, and states precisely what a
general proof still needs. Nothing here is bluffed: the two subfamily results are full
proofs; the general case is explicitly left open.

---

## 0. Reformulations and elementary bounds

**(a) Line-graph form.** A minimum maximal matching of $G$ is exactly a smallest maximal
independent set of the line graph $L(G)$, so
$$\mu^*(G) = i\big(L(G)\big).$$
Thus Conjecture 3 says $i(G) \le i(L(G))$ for every $r$-regular $G$ — the independent
domination number does not decrease when passing to the line graph. (This is the cross-
check `mustar` already runs against `i(L(G))` for $n\le 10$.)

**(b) Maximal independent set $=$ independent dominating set.** $S$ is a maximal
independent set iff $S$ is independent and dominating. Hence $i(G)$ is the minimum size of
an independent dominating set, and for an $r$-regular graph each vertex of $S$ dominates
itself and its $r$ neighbours, giving the lower bound
$$i(G) \ge \frac{n}{r+1}. \tag{L}$$

**(c) Matching lower bound.** If $M$ is a maximal matching, the $n - 2|M|$ unmatched
vertices form an independent set, so $n - 2\mu^*(G) \le \alpha(G)$, i.e.
$$\mu^*(G) \ge \frac{n - \alpha(G)}{2}. \tag{M}$$

These bracket the two sides but do not by themselves close the gap; the subfamily proofs
below compute both quantities exactly.

---

## 1. Complete graphs $K_{r+1}$ — exact

$K_{r+1}$ is the $r$-regular graph on $n = r+1$ vertices.

- **$i(K_{r+1}) = 1$.** Any single vertex is independent and (since $K_{r+1}$ is complete)
  dominates everything, so it is a maximal independent set; one cannot be smaller.
- **$\mu^*(K_{r+1}) = \lfloor (r+1)/2 \rfloor$.** In a complete graph any two unmatched
  vertices are adjacent, so a maximal matching leaves at most one vertex unmatched; every
  maximal matching is therefore near-perfect of size $\lfloor n/2\rfloor$.

Hence $i = 1 \le \lfloor (r+1)/2\rfloor = \mu^*$ for all $r \ge 1$, with **equality iff
$r \in \{1,2\}$** (i.e. $K_2$ and $K_3$). In particular $K_4$ ($r=3$) gives
$i=1 < 2 = \mu^*$, the strict, slack-$1$ case the search reports at $n=4$. $\blacksquare$

---

## 2. Balanced complete bipartite graphs $K_{r,r}$ — an infinite equality family

$K_{r,r}$ is the $r$-regular graph on $n = 2r$ vertices with parts $A, B$, $|A|=|B|=r$.

- **$i(K_{r,r}) = r$.** An independent set lies entirely inside one part. A proper subset
  $S \subsetneq A$ fails to dominate any vertex of $A \setminus S$ (whose neighbours all
  lie in $B$), so the only maximal independent sets are the two whole parts $A$ and $B$,
  each of size $r$. Thus $i = \alpha = r$ (so $K_{r,r}$ is *well-covered*).
- **$\mu^*(K_{r,r}) = r$.** A matching of size $k$ leaves $r-k$ vertices unmatched in each
  part; if $k < r$ there is an unmatched vertex in $A$ and one in $B$, and they are
  adjacent, contradicting maximality. So every maximal matching is perfect of size $r$.

Hence $i(K_{r,r}) = r = \mu^*(K_{r,r})$: **$K_{r,r}$ satisfies Conjecture 3 with equality
for every $r \ge 1$.** This recovers $K_2$ ($r=1$), $C_4 = K_{2,2}$ ($r=2$), and $K_{3,3}$
($r=3$) as members of a single infinite extremal family. $\blacksquare$

---

## 3. The equality cases the Pessimist recovered — exact verification

Across the full run the search returned three distinct reward-$0$ graphs (WL-deduped). Each
is connected and **well-covered** ($\alpha = i$); below, every value is checked by hand.

**(a) Triangular prism $C_3 \times K_2$ ($n=6$, $r=3$).** Two triangles
$\{a_1,a_2,a_3\}$, $\{b_1,b_2,b_3\}$ joined by a perfect matching $a_jb_j$.
$i = 2$: $\{a_1, b_2\}$ is independent (not an edge) and dominates all six vertices, and no
single vertex dominates a cubic graph on $6$ vertices, so $i = 2$. $\mu^* = 2$: the two
edges $a_1b_1, a_2b_2$ leave $a_3, b_3$ unmatched; $a_3 b_3$ **is** an edge, so that pair
is not independent — instead take $a_1a_2$ and $b_1b_3$, leaving $a_3, b_2$ unmatched and
non-adjacent, a maximal matching of size $2$. Lower bound (M) with $\alpha=2$ gives
$\mu^* \ge 2$, so $\mu^* = 2 = i$. (Note $\mu^* = 2 < 3 = n/2$: unlike Conjecture 4's
regular extremal family, here *not* every maximal matching is perfect.)

**(b) Octahedron $K_{2,2,2}$ ($n=6$, $r=4$).** The cocktail-party graph: three
non-adjacent ("antipodal") pairs, every cross-pair edge present. $i = 2$: each antipodal
pair is an independent dominating set (the two vertices are non-adjacent and every other
vertex is adjacent to both), and these pairs are the *only* maximal independent sets, so
$i = \alpha = 2$. $\mu^* = 2$: match two of the pairs across (size-$2$ matching) leaving
one full antipodal pair unmatched and independent — maximal. So $\mu^* = 2 = i$.
$\blacksquare$

**(c) A cubic graph on $8$ vertices with one triangle ($n=8$, $r=3$).** Recorded edge list
(see `equality_cases.json`); it has degree sequence $3^8$, exactly one triangle, and is
non-bipartite. Direct computation gives $i = \alpha = 3$ and $\mu^* = 3$ (a size-$3$
maximal matching exists, leaving two non-adjacent vertices uncovered; (M) with $\alpha=3$,
$n=8$ gives $\mu^* \ge 2$, and no size-$2$ maximal matching exists). Equality holds.

---

## 4. Summary and what a general proof needs

| Family | $i(G)$ | $\mu^*(G)$ | verdict |
|---|---|---|---|
| $K_{r+1}$ | $1$ | $\lfloor (r+1)/2\rfloor$ | holds; equality iff $r\le 2$ |
| $K_{r,r}$ | $r$ | $r$ | **equality for all $r$** |
| prism, octahedron, cubic-on-8 | — | — | equality (verified above) |

**Open.** The conjecture is established here only for the complete and complete-bipartite
subfamilies and verified exhaustively on the small-$nr$ frontier; the **general
$r$-regular case remains open** (as it has since 2020). The cleanest empirical regularity
is that *every* recovered equality graph is **well-covered** ($\alpha = i$). A natural
target for a future proof — and a good Lean lemma to attempt — is therefore:

> For $r$-regular $G$, equality $i(G) = \mu^*(G)$ implies $G$ is well-covered; and
> conversely the well-covered $r$-regular graphs with $\alpha = \mu^*$ are exactly the
> extremal family.

Bounds (L) and (M) give $\tfrac{n}{r+1} \le i \le \alpha$ and $\mu^* \ge \tfrac{n-\alpha}{2}$,
which is *not* enough to force $i \le \mu^*$ in general; closing it appears to require a
structural argument linking a smallest maximal independent set of $G$ to a maximal matching
of comparable size (equivalently, comparing $i(G)$ with $i(L(G))$ directly). We leave the
general statement, and the Lean `conjecture_three`, with a documented `sorry`.
