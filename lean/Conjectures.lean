/-
  Formal statements of the four open TxGraffiti conjectures from

      R. Davila, B. Brimkov, R. Pepper,
      "Automated Conjecturing in Graph Theory with TxGraffiti",
      arXiv:2507.17780 (2025).

  The graph invariants are introduced as `opaque` constants over `SimpleGraph V`
  (for a finite vertex type `V`). We do not formalise their definitions here -- the
  point of this file is to pin down the *statements* of the conjectures so they
  type-check against Mathlib; each theorem is therefore closed with `sorry`.

  Connectivity uses Mathlib's `SimpleGraph.Connected`. Regularity uses
  `SimpleGraph.IsRegularOfDegree`. The exclusion of K₄ in Conjecture 2 is encoded as
  the non-existence of a graph isomorphism `G ≃g ⊤` to the complete graph on `Fin 4`.

  All inequalities that mix a natural-valued invariant with the rational-valued
  harmonic index, or that involve division, are stated over `ℚ` with explicit casts so
  they mean exactly what the paper's real-number inequalities mean.
-/
import Mathlib

open scoped SimpleGraph

namespace TxGraffiti

universe u
variable {V : Type u} [Fintype V] [DecidableEq V]

/-- Independence number `α(G)`: the size of a largest independent set. -/
opaque independence_number (G : SimpleGraph V) : ℕ

/-- Annihilation number `a(G)` (Pepper 2004): the largest `k` such that the `k`
    smallest vertex degrees sum to at most `|E(G)|`. -/
opaque annihilation_number (G : SimpleGraph V) : ℕ

/-- Residue `R(G)`: the number of zeros produced by the Havel–Hakimi process on the
    degree sequence of `G`. -/
opaque residue (G : SimpleGraph V) : ℕ

/-- Maximum degree `Δ(G)`. -/
opaque max_degree (G : SimpleGraph V) : ℕ

/-- Zero forcing number `Z(G)`. -/
opaque zero_forcing_number (G : SimpleGraph V) : ℕ

/-- Independent domination number `i(G)`: the size of a smallest maximal independent
    set. -/
opaque independent_domination_number (G : SimpleGraph V) : ℕ

/-- Minimum maximal matching number `μ*(G)`: the size of a smallest maximal matching
    (equivalently `i` of the line graph of `G`). -/
opaque min_maximal_matching_number (G : SimpleGraph V) : ℕ

/-- Harmonic index `H(G) = ∑_{uv ∈ E(G)} 2 / (deg u + deg v)`. Rational-valued for a
    finite graph. -/
opaque harmonic_index (G : SimpleGraph V) : ℚ

/-- **Conjecture 1** (TxGraffiti, open since 2016, arXiv:2507.17780).
    For every nontrivial connected graph `G`,
    `α(G) ≥ (a(G) + R(G)) / Δ(G)`. -/
theorem conjecture_one (G : SimpleGraph V) (hconn : G.Connected)
    (hnt : 2 ≤ Fintype.card V) :
    ((annihilation_number G : ℚ) + (residue G : ℚ)) / (max_degree G : ℚ)
      ≤ (independence_number G : ℚ) := by
  sorry

/-- **Conjecture 2** (TxGraffiti, open since 2017, arXiv:2507.17780).
    If `G ≇ K₄` is connected with `Δ(G) ≤ 3`, then `Z(G) ≤ α(G) + 1`. -/
theorem conjecture_two (G : SimpleGraph V) (hconn : G.Connected)
    (hmaxdeg : max_degree G ≤ 3)
    (hK4 : IsEmpty (G ≃g (⊤ : SimpleGraph (Fin 4)))) :
    zero_forcing_number G ≤ independence_number G + 1 := by
  sorry

/-- **Conjecture 3** (TxGraffiti, open since 2020, arXiv:2507.17780).
    For every `r`-regular graph with `r > 0`, `i(G) ≤ μ*(G)`. -/
theorem conjecture_three (G : SimpleGraph V) [DecidableRel G.Adj] (r : ℕ) (hr : 0 < r)
    (hreg : G.IsRegularOfDegree r) :
    independent_domination_number G ≤ min_maximal_matching_number G := by
  sorry

/-- **Conjecture 4** (TxGraffiti, open since 2023, arXiv:2507.17780).
    For every nontrivial connected graph `G`, `μ*(G) ≤ H(G)`.
    This is the conjecture searched adversarially by the Pessimist engine. -/
theorem conjecture_four (G : SimpleGraph V) (hconn : G.Connected)
    (hnt : 2 ≤ Fintype.card V) :
    (min_maximal_matching_number G : ℚ) ≤ harmonic_index G := by
  sorry

end TxGraffiti
