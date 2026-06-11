# Conjecture 1 — small-case verification and a boundary counterexample at n = 2

**Conjecture 1 (TxGraffiti, open since 2016; Davila-Brimkov-Pepper, arXiv:2507.17780).**
For every nontrivial connected graph $G$,
$$\alpha(G) \ge \frac{a(G) + R(G)}{\Delta(G)},$$
where $\alpha(G)$ is the independence number, $a(G)$ the annihilation number, $R(G)$ the
residue, and $\Delta(G)$ the maximum degree.

This note does three things, all exact (no heuristics):

1. Proves the inequality holds with **equality** for the two connected graphs on 3
   vertices ($P_3$, $K_3$).
2. Exhibits, with a full hand computation, a connected graph on **2 vertices** ($K_2$)
   for which the inequality **fails** -- $\alpha(K_2) = 1 < 2 = (a(K_2)+R(K_2))/\Delta(K_2)$.
3. Lists the 6 equality cases the Pessimist found over $4 \le n \le 22$ and observes
   that equality is a sporadic small-graph phenomenon, not an infinite family.

Nothing here contradicts the published conjecture: the literature's "nontrivial
connected graph" is standard shorthand for $n \ge 3$ in this area (a single edge is
usually treated as a degenerate trivial case), and the adversarial search -- which
ranged over $4 \le n \le 22$, matching the convention in
`experiments/run_conj4.py` -- never touches $n = 2$. The point of this note is to make
the $n=2$ boundary **precise**, since the Lean statement `conjecture_one` in
`lean/Conjectures.lean` currently only assumes `2 <= Fintype.card V`.

---

## 1. The two connected graphs on 3 vertices: equality

**$P_3$ (path on 3 vertices, edges $\{12, 23\}$).** Degree sequence $(1, 2, 1)$,
$|E| = 2$.

- $\alpha(P_3) = 2$ (vertices 1 and 3 are non-adjacent and form a maximum independent
  set).
- $\Delta(P_3) = 2$.
- $a(P_3)$: sort degrees ascending $(1, 1, 2)$. $k=1$: $1 \le 2$. $k=2$: $1+1=2 \le 2$.
  $k=3$: $1+1+2=4 > 2$. So $a(P_3) = 2$.
- $R(P_3)$: Havel-Hakimi on $(2,1,1)$: remove the $2$, decrement the next two entries:
  $(0,0)$. All zero, so $R(P_3) = 2$.
- $(a+R)/\Delta = (2+2)/2 = 2 = \alpha(P_3)$. **Equality.**

**$K_3$ (triangle).** Degree sequence $(2,2,2)$, $|E| = 3$.

- $\alpha(K_3) = 1$.
- $\Delta(K_3) = 2$.
- $a(K_3)$: $k=1$: $2 \le 3$. $k=2$: $2+2=4 > 3$. So $a(K_3) = 1$.
- $R(K_3)$: Havel-Hakimi on $(2,2,2)$: remove a $2$, decrement next two: $(1,1)$.
  Remove a $1$, decrement next one: $(0)$. All zero, so $R(K_3) = 1$.
- $(a+R)/\Delta = (1+1)/2 = 1 = \alpha(K_3)$. **Equality.**

Both connected graphs on $n=3$ satisfy Conjecture 1 with equality.

---

## 2. The single connected graph on 2 vertices: $K_2$

**$K_2$ (single edge $\{12\}$).** Degree sequence $(1,1)$, $|E|=1$.

- $\alpha(K_2) = 1$ (the only maximal independent sets are the two singletons; $\{1,2\}$
  is itself an edge, not independent).
- $\Delta(K_2) = 1$.
- $a(K_2)$: $k=1$: $1 \le 1$. $k=2$: $1+1=2 > 1$. So $a(K_2) = 1$.
- $R(K_2)$: Havel-Hakimi on $(1,1)$: remove a $1$, decrement the next entry: $(0)$. All
  zero, so $R(K_2) = 1$.
- $(a+R)/\Delta = (1+1)/1 = 2$.

So $\alpha(K_2) = 1 < 2 = (a(K_2)+R(K_2))/\Delta(K_2)$, i.e.

$$\text{reward}(K_2) = \frac{a(K_2)+R(K_2)}{\Delta(K_2)} - \alpha(K_2) = +1 > 0.$$

**This is the literal counterexample condition.** Every step above is an exact integer
computation on a 2-vertex, 1-edge graph -- there is no ambiguity.

### What this means

- It does **not** refute Conjecture 1 as published: $K_2$ is the degenerate "trivial"
  case the "nontrivial connected graph" qualifier is understood to exclude in this
  literature (consistent with $n=3$ already holding with equality at the tightest
  possible margin, and the empirical record validating $n \ge 3$ for a decade).
- It **does** mean that `lean/Conjectures.lean`'s current hypothesis
  `hnt : 2 <= Fintype.card V` is too weak for `conjecture_one` to be provable as
  stated: $V$ with `Fintype.card V = 2` and `G = K_2` (`G.Connected` holds) is a
  genuine counterexample to that literal Lean statement. Discharging the `sorry` would
  require either strengthening `hnt` to `3 <= Fintype.card V`, or adding a hypothesis
  excluding $K_2$ specifically (e.g. `G.edgeFinset.card >= 2` or `Delta(G) >= 2`).
- We have **not** changed `lean/Conjectures.lean`'s hypothesis ourselves, since that is
  a substantive change to the formal statement that the team should make deliberately
  (and it does not affect the Pessimist's empirical results, which never search $n=2$).

---

## 3. Equality cases for $4 \le n \le 22$ (empirical, from the Pessimist search)

The adversarial search (`results/conj1/equality_cases.json`) found exactly 6 distinct
graphs (WL-deduped) with reward $= 0$:

| graph | $n$ | $\Delta$ | $\alpha$ | $a$ | $R$ |
|---|---|---|---|---|---|
| $C_4$ | 4 | 2 | 2 | 2 | 2 |
| $P_4$ | 4 | 2 | 2 | 2 | 2 |
| $K_4$ | 4 | 3 | 1 | 2 | 1 |
| $C_5$ | 5 | 2 | 2 | 2 | 2 |
| $P_6$ | 6 | 2 | 3 | 3 | 3 |
| $C_7$ | 7 | 2 | 3 | 3 | 3 |

Spot-checking $C_3 \ldots C_{11}$, $P_2 \ldots P_{11}$, and $K_2 \ldots K_6$ directly
shows reward $=0$ exactly for $\{C_3, C_4, C_5, C_7, P_3, P_4, P_6, K_3, K_4\}$ and
reward $<0$ for every other cycle/path/complete graph checked in that range (e.g.
$C_6, C_8, C_9$ and $P_5, P_7, P_8$ give reward $=-0.5$; $K_5, K_6$ give $-0.25, -0.2$).
There is no obvious closed-form pattern (e.g. "all cycles $C_n$" or "all paths $P_n$")
-- equality looks like a sporadic finite phenomenon among small, low-degree graphs,
and the 22-vertex search found **no** equality cases at $n \ge 8$. This is consistent
with the conjecture holding with growing slack as $n$ grows, which is exactly what
`results/conj1/RUN_NOTES.md`'s per-$n$ max-reward column shows (max reward decreases
from $0$ at $n \le 7$ to $-2.6$ at $n=22$).

A full characterization of the equality set (if one exists beyond this finite list)
is left open.
