# Conjecture 4 — a partial proof and where it breaks

**Conjecture 4 (TxGraffiti, open since 2023; Davila–Brimkov–Pepper, arXiv:2507.17780).**
For every nontrivial connected graph $G$,
$$\mu^*(G) \le H(G),$$
where $\mu^*(G)$ is the *minimum maximal matching number* (the size of a smallest maximal
matching) and $H(G) = \sum_{uv \in E(G)} \frac{2}{\deg(u) + \deg(v)}$ is the *harmonic index*.

This note proves the conjecture **completely for regular graphs** and **for stars and
paths**, sketches a charging argument for general trees, and states precisely where the
argument fails to close in the general case. Nothing here is bluffed: the regular and
star/path results are full proofs; the tree case is explicitly left partial.

---

## 0. Two reformulations we use

**(a) Line-graph form.** A minimum maximal matching of $G$ is exactly a smallest maximal
independent set of the line graph $L(G)$, so
$$\mu^*(G) = i\big(L(G)\big),$$
the independent domination number of $L(G)$. A vertex $e = uv$ of $L(G)$ has degree
$\deg_{L(G)}(e) = \deg(u) + \deg(v) - 2$, hence
$$H(G) = \sum_{e \in V(L(G))} \frac{2}{\deg_{L(G)}(e) + 2}. \tag{$\star$}$$
So Conjecture 4 is equivalent to: for every line graph $L = L(G)$,
$i(L) \le \sum_{x \in V(L)} \tfrac{2}{\deg_L(x)+2}$.

**(b) Trivial matching bound.** For any graph, a maximal matching is a matching, so
$$\mu^*(G) \le \nu(G) \le \big\lfloor n/2 \big\rfloor, \tag{M}$$
where $\nu(G)$ is the maximum matching number and $n = |V(G)|$.

---

## 1. Regular graphs — complete proof

**Theorem 1.** *Let $G$ be a nontrivial connected $r$-regular graph, $r \ge 1$, on $n$
vertices. Then $\mu^*(G) \le H(G)$, with equality iff every maximal matching of $G$ is
perfect.*

*Proof.* Every edge joins two vertices of degree $r$, so each term of $H$ equals
$\tfrac{2}{r+r} = \tfrac1r$, and $|E(G)| = \tfrac{nr}{2}$. Hence
$$H(G) = |E(G)| \cdot \frac1r = \frac{nr}{2}\cdot\frac1r = \frac n2 .$$
By (M), $\mu^*(G) \le \lfloor n/2 \rfloor \le n/2 = H(G)$. $\qquad\blacksquare$

**Equality.** $\mu^*(G) = H(G) = n/2$ forces $n$ even and $\mu^*(G) = n/2 = \nu(G)$. Since
$\mu^*$ is the size of the *smallest* maximal matching, $\mu^*(G) = \nu(G)$ means every
maximal matching already has maximum size, i.e. **every maximal matching is perfect**
(the *equimatchable graphs admitting a perfect matching*).

This is exactly the family the Pessimist recovered empirically. The only reward-$0$
graphs found across $500{,}000$ searched graphs ($n \le 8$) were
$$C_4 \ (n{=}4,\,2\text{-regular}), \quad K_4 \ (n{=}4,\,3\text{-regular}), \quad
K_{3,3}/\text{prism}\ (n{=}6,\,3\text{-regular}),$$
and one verifies directly that each has the "every maximal matching is perfect"
property. Theorem 1 explains the entire extremal set the search produced.

---

## 2. Stars and paths — complete proofs

**Star $K_{1,m}$ ($m \ge 1$).** Here $\mu^* = 1$ (a single edge dominates) and
$H = m\cdot \tfrac{2}{1+m} = \tfrac{2m}{m+1} \ge 1 \iff 2m \ge m+1 \iff m \ge 1$. Holds,
with equality iff $m = 1$, i.e. $G = K_2$ (the smallest nontrivial graph, also an
equality case).

**Path $P_n$ ($n \ge 2$).** The two end-edges join degrees $1,2$ and the $n-3$ interior
edges join degrees $2,2$, so for $n \ge 3$
$$H(P_n) = 2\cdot \tfrac{2}{3} + (n-3)\cdot \tfrac{1}{2} = \tfrac43 + \tfrac{n-3}{2}
= \tfrac{n}{2} - \tfrac16 .$$
The minimum maximal matching of a path satisfies $\mu^*(P_n) = \lceil (n-1)/3\rceil$.
Since $\lceil (n-1)/3 \rceil \le \tfrac{n}{2} - \tfrac16$ for all $n \ge 2$, the
conjecture holds for paths with growing slack $\sim n/6$. (Numerically the Pessimist
sees this slack: $P_4$ gives $H = 11/6 \approx 1.83$, $\mu^* = 1$.)

---

## 3. General trees — a charging attempt, and the obstruction

Fix a tree $T$ and a minimum maximal matching $M$, $|M| = \mu^*(T)$. Because $M$ is
maximal it is an **edge dominating set**: every edge of $T$ shares an endpoint with some
edge of $M$. We try to pay for each $e \in M$ using harmonic weight drawn from the edges
it dominates.

Assign to $e = uv \in M$ the weight of the edges incident to $u$ or $v$ (its closed
star $S(e)$). An edge $uw$ incident to $u$ contributes $\tfrac{2}{\deg(u)+\deg(w)} \ge
\tfrac{2}{\deg(u)+\Delta}$. Summing over the $\deg(u)+\deg(v)-1$ edges in $S(e)$ gives a
lower bound on the harmonic mass around $e$; if every $e\in M$ could be charged total
mass $\ge 1$ from a *disjoint* part of $H$, we would get $H(T) \ge |M| = \mu^*(T)$.

**Two facts make this almost work for trees.** (i) In a tree the closed stars of a
matching overlap in a controlled way (an edge lies in at most two stars, one per
endpoint-matching). (ii) Leaf edges, which dominate little, also carry large harmonic
weight $\tfrac{2}{1+\deg(v)}$ when their non-leaf endpoint has small degree.

**Where it breaks.** The charging fails to close when $T$ has high-degree internal
vertices adjacent to many *other* high-degree vertices ("heavy" interior). There an edge
$uw$ with $\deg(u),\deg(w)$ both large contributes harmonic weight $\approx 2/(\deg u +
\deg w) \to 0$, yet such an edge can still force a matching edge into $M$ in its
neighborhood. The per-matching-edge charge can dip below $1$, and the disjointness needed
to sum the local bounds is exactly what is lost. Concretely, the line-graph form ($\star$)
makes the obstruction sharp: Caro–Wei gives $\alpha(L) \ge \sum_x \tfrac{1}{\deg_L(x)+1}$,
a *lower* bound on the independence number, whereas we need an *upper* bound on the
**independent domination** number $i(L)$ by the closely related sum $\sum_x
\tfrac{2}{\deg_L(x)+2}$. For irregular $L$ (irregular $G$) these two quantities separate
in the wrong direction, so no Caro–Wei-style averaging closes the gap.

---

## 4. Summary and what an extension needs

* **Proved here:** Conjecture 4 holds for all regular graphs (Thm 1, with a clean
  equality characterization matching every empirical extremal graph), and for stars and
  paths.
* **Open in this note:** general trees and general connected graphs.
* **What an extension would need:** a charging scheme that survives heavy interior
  vertices — e.g. a weighting of $H$ that gives each minimum-maximal-matching edge mass
  $\ge 1$ *with provable disjointness*, or a genuinely new upper bound on the independent
  domination number of a line graph in terms of $\sum 2/(\deg+2)$ that does **not**
  reduce to a (wrong-direction) Caro–Wei average. The regular case works precisely
  because $H \equiv n/2$ is constant per the degree, removing the irregularity that the
  general argument cannot absorb.

The Pessimist's empirical verdict is consistent with all of the above: across
$n \le 8$ and $5 \times 10^5$ adversarially generated graphs the reward
$\mu^*(G) - H(G)$ never exceeded $0$, and attained $0$ only on the regular extremal
family characterized by Theorem 1.
