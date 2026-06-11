# txgraffiti-pessimist

**DSA5210 Assignment 3 — pattern-discovery option.**

A *Pessimist* agent (in the sense of Davila's Optimist/Pessimist framework,
[arXiv:2411.09158](https://arxiv.org/abs/2411.09158)) that hunts for **counterexamples**
to four open graph-theory conjectures produced by the automated conjecturing system
TxGraffiti (Davila, Brimkov, Pepper 2025, [arXiv:2507.17780](https://arxiv.org/abs/2507.17780)).
Where the *Optimist* proposes conjectures, the *Pessimist* attacks them: it runs an
ML-guided adversarial search (a per-edge cross-entropy method) that mutates graphs to
maximise the *violation margin* of each conjectured inequality.

All four targets have been open for years, empirically validated on the ~335 small graphs
in the TxGraffiti corpus, and unrefuted for up to a decade.

> **Honest framing.** The realistic expectation is **zero counterexamples**, and indeed we
> found none. This project is *not* a heuristic chase for positive reward. Its deliverables
> are (1) the **Pessimist engine** itself, (2) **adversarial validation orders of magnitude
> beyond the published dataset**, (3) the **extremal (equality) families** the search
> recovers, and (4) **Lean 4 statements** of all four conjectures that type-check against
> Mathlib. A negative result here is the intended, informative outcome.

---

## The four target conjectures

All from Davila, Brimkov, Pepper, *Automated Conjecturing in Graph Theory with TxGraffiti*,
[arXiv:2507.17780](https://arxiv.org/abs/2507.17780). Invariants: independence number
$\alpha$, annihilation number $a$, residue $R$, maximum degree $\Delta$, zero forcing
number $Z$, independent domination number $i$, minimum maximal matching number $\mu^*$,
harmonic index $H(G) = \sum_{uv\in E}\frac{2}{\deg u + \deg v}$.

| # | Open since | Statement | Hypothesis |
|---|-----------|-----------|------------|
| **1** | 2016 | $\alpha(G) \ge \dfrac{a(G) + R(G)}{\Delta(G)}$ | nontrivial connected $G$ |
| **2** | 2017 | $Z(G) \le \alpha(G) + 1$ | connected, $\Delta(G)\le 3$, $G\not\cong K_4$ |
| **3** | 2020 | $i(G) \le \mu^*(G)$ | $r$-regular, $r>0$ |
| **4** | 2023 | $\mu^*(G) \le H(G)$ | nontrivial connected $G$ |

The team runs the Pessimist against **three of these conjectures**, one per member, each
plugging a conjecture-specific reward into the shared search engine:

- **Conjecture 1** ($\alpha \ge (a+R)/\Delta$) — Tridiv
- **Conjecture 3** ($i \le \mu^*$) — Shubhashish
- **Conjecture 4** ($\mu^* \le H$) — Navneet

All four conjectures (including Conjecture 2) are also stated formally in Lean.
Conjectures 1 and 4 are fully written up below (Conjecture 3 is searched on
Shubhashish's branch with the same engine and reporting format).

---

## What the Pessimist found (Conjecture 4)

A per-edge Bernoulli **cross-entropy method** (CEM; Wagner 2021 style) maximises the reward
$\text{reward}(G) = \mu^*(G) - H(G)$ — a positive reward would be a counterexample.

| Metric | Value |
|---|---|
| Vertex range searched | $n = 4 \dots 8$ (see cap note below) |
| Restarts × iterations × batch | $10 \times 50 \times 200$ per $n$ |
| **Total graphs searched** | **500,000** |
| Counterexamples found | **0** |
| Global best reward | $+2.2\times10^{-16}$ (i.e. equality, no violation) |
| Distinct equality cases (post WL-dedup) | **3** |

**Max reward per $n$** (all $\le 0$ ⇒ conjecture holds on every searched graph):

| $n$ | 4 | 5 | 6 | 7 | 8 |
|-----|---|---|---|---|---|
| max reward | $0$ | $-0.257$ | $0$ | $-0.095$ | $-0.083$ |

**Recovered extremal family.** The only reward-$0$ (equality, $\mu^* = H$) graphs found were
$C_4$, $K_4$, and the cubic graph on 6 vertices ($K_{3,3}$/prism) — **all regular graphs**.
This is not a coincidence: for any $r$-regular graph $H(G) = n/2 \ge \lfloor n/2\rfloor \ge
\mu^*(G)$, with equality exactly when every maximal matching is perfect. See
[`results/conj4/proof_attempt.md`](results/conj4/proof_attempt.md) for the proof and the
characterisation. Scatter of $\mu^*$ vs $H$ (equality cases marked):
[`results/conj4/scatter_mustar_vs_H.png`](results/conj4/scatter_mustar_vs_H.png).

**Cap note.** The minimum maximal matching is computed *exactly* via an ILP that spawns a
CBC subprocess per graph (~30–80 ms each), so the 100,000 evaluations per $n$ become the
bottleneck at large $n$. The driver enforces a hard 10-minute-per-$n$ budget: $n=8$
completed in 564 s, $n=9$ exceeded the budget and was **aborted and excluded** (not
silently truncated). The documented cap is therefore $n=8$; details in
[`results/conj4/RUN_NOTES.md`](results/conj4/RUN_NOTES.md).

---

## What the Pessimist found (Conjecture 1)

The same per-edge Bernoulli CEM maximises
$\text{reward}(G) = \dfrac{a(G)+R(G)}{\Delta(G)} - \alpha(G)$ — a positive reward would be
a counterexample to $\alpha(G) \ge (a(G)+R(G))/\Delta(G)$.

| Metric | Value |
|---|---|
| Vertex range searched | $n = 4 \dots 22$ (see cap note below) |
| Restarts × iterations × batch | $10 \times 50 \times 200$ per $n$ |
| **Total graphs searched** | **1,900,000** |
| Counterexamples found | **0** |
| Global best reward | $0.000000$ (equality, no violation) |
| Distinct equality cases (post WL-dedup) | **6** |

**Max reward per $n$** (all $\le 0$ ⇒ conjecture holds on every searched graph; selected
$n$, full table in [`results/conj1/RUN_NOTES.md`](results/conj1/RUN_NOTES.md)):

| $n$ | 4 | 5 | 6 | 7 | 8 | 10 | 14 | 18 | 22 |
|-----|---|---|---|---|---|----|----|----|----|
| max reward | $0$ | $0$ | $0$ | $0$ | $-0.33$ | $-0.67$ | $-1.00$ | $-2.00$ | $-2.64$ |

**Recovered extremal family.** The 6 equality ($\alpha = (a+R)/\Delta$) graphs found are
$C_4$, $P_4$, $K_4$, $C_5$, $P_6$, $C_7$ — all small, low-degree ($\Delta \in \{2,3\}$)
graphs, with no equality cases at $n \ge 8$. Equality appears to be a sporadic
finite-graph phenomenon rather than an infinite family; see
[`results/conj1/proof_attempt.md`](results/conj1/proof_attempt.md) for exact hand
verification of the $n=3$ cases ($P_3$, $K_3$, both equality) and a noteworthy boundary
case at $n=2$: $K_2$ gives reward $=+1$ (the literal counterexample condition), which is
why `lean/Conjectures.lean`'s `conjecture_one` requires $n \ge 3$ rather than $n \ge 2$.
Scatter of $\alpha$ vs $(a+R)/\Delta$ (equality cases marked):
[`results/conj1/scatter_alpha_vs_a_plus_R_over_delta.png`](results/conj1/scatter_alpha_vs_a_plus_R_over_delta.png).

**Cap note.** Conjecture 1 needs only $\alpha, a, R, \Delta$ — no CBC/ILP subprocess —
so it is far cheaper per graph than Conjecture 4's $\mu^*$. The same hard 10-minute-per-$n$
budget applies: $n=22$ completed in 458 s, $n=23$ exceeded the budget and was **aborted
and excluded**. The documented cap is therefore $n=22$, nearly triple Conjecture 4's
$n=8$; details in [`results/conj1/RUN_NOTES.md`](results/conj1/RUN_NOTES.md). At this
range, $\alpha(G)$'s exact computation via maximal cliques of the complement graph is the
bottleneck, not connectivity or search overhead.

---

## Repository layout

```
src/
  invariants.py        exact graph invariants (alpha, i, mu*, residue, annihilation, H)
  graphclasses.py      bitstring<->graph codec; regular sampler & degree-preserving mutator
  search.py            per-edge Bernoulli cross-entropy method (the Pessimist optimiser)
conjectures/
  conj4_minmaxmatching_harmonic.py    reward(G) = mu*(G) - H(G)
  conj1_independence_annihilation_residue.py    reward(G) = (a(G)+R(G))/Delta(G) - alpha(G)
experiments/
  run_conj4.py         multi-seed driver: logs, summary, equality cases, scatter, cap guard
  run_conj1.py         same driver pattern, wired to the Conjecture 1 reward
results/conj4/         per-(n,seed) logs, summary.json, equality_cases.json, scatter,
                       RUN_NOTES.md, proof_attempt.md
results/conj1/         same outputs for Conjecture 1 (cap n=22)
tests/                 pytest: invariant spot-values + theorem fuzz, codec, WL-hash dedup
lean/                  Lean 4 project; Conjectures.lean states all four with `sorry`
prompts/navneet.md     the verbatim build prompt
```

---

## Install & run

```bash
# Python 3.11+
pip install -r requirements.txt          # networkx, numpy, matplotlib, pulp, pytest, tqdm

# Tests (invariants cross-checked against literature + theorems)
pytest -q

# Smoke run of the Pessimist on Conjecture 4 (< 2 min)
python experiments/run_conj4.py --smoke

# Full run (per-n 10-min budget; auto-caps and documents in RUN_NOTES.md)
python experiments/run_conj4.py

# Smoke / full run on Conjecture 1 (cap reaches n=22; <10 min total)
python experiments/run_conj1.py --smoke
python experiments/run_conj1.py

# Standalone CEM engine (default objective = Conjecture 4 reward)
python src/search.py --n 7 --iters 50 --batch 200 --seeds 10 --seed 0
```

### Lean build

```bash
cd lean
lake update            # resolves Mathlib @ v4.30.0 (pinned to match the toolchain)
lake exe cache get     # downloads Mathlib's precompiled olean cache (mandatory)
lake build             # type-checks Conjectures.lean against Mathlib
```

`lean/Conjectures.lean` **builds successfully against Mathlib** (Lean v4.30.0 / Mathlib
v4.30.0). It declares the eight graph invariants as `opaque` constants over
`SimpleGraph V` and states all four conjectures as theorems, each closed with `sorry`
(the statements type-check; the proofs are open — these are open conjectures).

**Open question for the team:** `conjecture_one`'s current hypothesis
`2 ≤ Fintype.card V` is arguably too weak for the statement to be true as written —
for `K₂` (the connected graph on 2 vertices), $\alpha=1$ but $(a+R)/\Delta = 2$, so the
inequality fails for `K₂`. See
[`results/conj1/proof_attempt.md`](results/conj1/proof_attempt.md) for the exact
computation and a proposed fix (`3 ≤ Fintype.card V`, matching "nontrivial connected
graph" and the search range $n \ge 4$). This file builds successfully either way
(`conjecture_one` is still closed with `sorry`); the hypothesis itself was left
unchanged pending the team's decision.

---

## How it works

- **Invariants** (`src/invariants.py`) are all *exact*: $\alpha$ and $i$ via maximal
  independent sets of the complement; $\mu^*$ via a 0/1 ILP (minimise $\sum x_e$ subject to
  per-vertex matching constraints and per-edge maximality constraints), with a brute-force
  fallback for $\lvert E\rvert\le 12$ and an $i(L(G))$ line-graph cross-check on $n\le 10$.
  An exactness guarantee matters: a positive reward must mean a real counterexample, never
  a numerical artefact.
- **Search** (`src/search.py`) maintains a Bernoulli probability $p_e$ per possible edge,
  samples a batch of graphs each iteration, decodes via the bitstring codec, scores them,
  and refits $p$ toward the top-10% elite frequencies (lr 0.7, additive noise 0.05, clipped
  to $[0.02,0.98]$). Disconnected graphs receive reward $-10^6$, steering the optimiser into
  the feasible region without any conjecture-specific hack.
- **Counterexample protocol.** Any reward exceeding the equality tolerance triggers a full
  provenance dump (`COUNTEREXAMPLE_<ts>.json`), independent re-verification of every
  invariant (brute force where feasible, plus the line-graph cross-method and a fresh ILP),
  and a `VERIFIED.md`. None triggered.

---

## AI agent

Built with **Claude Code (Claude Opus)**. **Plan mode** was used to scope and approve the
implementation before any code was written; the full build prompt is preserved verbatim in
[`prompts/navneet.md`](prompts/navneet.md).

## Team

| Member | Contribution |
|--------|--------------|
| Navneet | Infrastructure (invariants, CEM engine, experiment harness, Lean project) + Conjecture 4 search |
| Tridiv | Conjecture 1 ($\alpha \ge (a+R)/\Delta$), search to $n=22$, equality family + $K_2$ boundary case |
| Shubhashish | Conjecture 3 ($i \le \mu^*$) |

## References

- R. Davila, B. Brimkov, R. Pepper. *Automated Conjecturing in Graph Theory with
  TxGraffiti.* [arXiv:2507.17780](https://arxiv.org/abs/2507.17780) (2025).
- R. Davila. *The Optimist: Towards Fully Automated Graph Theory.*
  [arXiv:2411.09158](https://arxiv.org/abs/2411.09158) (2024).
- A. Z. Wagner. *Constructions in combinatorics via neural networks* (deep cross-entropy
  method). [arXiv:2104.14516](https://arxiv.org/abs/2104.14516) (2021).
- R. Pepper. *Binding independence and the annihilation number* (2004).
- O. Favaron, M. Mahéo, J.-F. Saclé. *On the residue of a graph* (1991).
