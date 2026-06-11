# Base prompt for Tridiv — Conjecture 1 (Pessimist search)

> Hand this to Claude Code (Claude Opus, plan mode) from inside the repo. Tweak as you go.
> The infrastructure already exists and is reusable — you are NOT rebuilding invariants or
> the search engine, only wiring Conjecture 1 into them and running it.

## Context you (Claude) are joining

This repo (`txgraffiti-pessimist`) is a "Pessimist" agent that adversarially searches for
counterexamples to four open TxGraffiti conjectures (Davila, Brimkov, Pepper 2025,
[arXiv:2507.17780](https://arxiv.org/abs/2507.17780)). Navneet already built the shared
infrastructure and the Conjecture 4 pipeline. You are implementing **Conjecture 1**.

**Conjecture 1 (open since 2016).** For every nontrivial connected graph `G`:
$$\alpha(G) \ge \frac{a(G) + R(G)}{\Delta(G)}$$
where `α` = independence number, `a` = annihilation number, `R` = residue, `Δ` = max degree.
A **counterexample** is a connected `G` with `α(G) < (a(G)+R(G))/Δ(G)`.

## What already exists and that you MUST reuse (do not reimplement)

- `src/invariants.py` — exact, cached invariants. You need: `alpha_and_i(G)` (returns
  `(alpha, i)`), `annihilation_number(G)`, `residue(G)`, `max_degree(G)`, `is_connected(G)`.
- `src/search.py` — the reward-agnostic cross-entropy method. Use `run_search(n, reward_fn,
  iters, batch, seeds, seed, progress)` which returns `(best_result, per_seed_results)`, or
  `run_cem(...)` for a single restart. Disconnected graphs are auto-penalised; do not
  special-case them.
- `src/graphclasses.py` — bitstring↔graph codec used by the search.
- `experiments/run_conj4.py` — the **template** for your driver: per-(n,seed) JSON logs,
  `summary.json`, WL-deduped equality cases, scatter plot, a per-n 10-minute wall-clock
  budget that aborts and documents the cap in `RUN_NOTES.md`, and a counterexample
  verification path. Copy its structure.
- `lean/Conjectures.lean` — already contains `conjecture_one` stated against Mathlib with
  `sorry`. The Lean project builds (Lean v4.30.0 / Mathlib v4.30.0).
- Tests live in `tests/`; run `pytest -q` (should be green before and after your changes).

## Your tasks

1. `conjectures/conj1_independence_annihilation_residue.py`:
   - `reward(G) = (a(G) + R(G)) / Δ(G) - α(G)`  (a float; **positive ⇒ counterexample**,
     `0` ⇒ equality/extremal, negative ⇒ conjecture holds with slack).
   - a `components(G)` helper returning the LHS `α(G)` and RHS `(a+R)/Δ` for logging/scatter.
   - Guard `Δ(G) = 0` (only the edgeless graph; not connected for n≥2, so the search's
     connectivity penalty already excludes it — but assert/handle defensively).
2. `experiments/run_conj1.py`: copy `run_conj4.py`, import the Conjecture 1 `reward`/
   `components`, set `OUTDIR = results/conj1/`, and adjust the scatter axes to `α` vs
   `(a+R)/Δ` with the boundary line `α = (a+R)/Δ`. Keep the 10-min/n budget and cap logic.
   Create `results/conj1/.gitkeep`.
3. Run `python experiments/run_conj1.py --smoke` (must finish < 2 min and write files),
   then the full run `python experiments/run_conj1.py`. Document the actual cap honestly in
   `results/conj1/RUN_NOTES.md` (the α/a/R/Δ invariants are far cheaper than Conjecture 4's
   ILP, so you should reach a much higher `n` than Navneet's n=8 cap).
4. Honest framing: the realistic expectation is **zero counterexamples**. Do not add
   heuristics chasing positive reward. The deliverables are the search, the adversarial
   validation, any recovered **extremal (equality) family**, and (optionally) a proof
   attempt for a structured subfamily in `results/conj1/proof_attempt.md`.
5. (Optional, strong) Attempt to discharge `conjecture_one`'s `sorry` for a subfamily in
   Lean, or at least add the equality-case characterisation you find empirically.

## Working agreement

- Use plan mode first; commit in small, labelled checkpoints; run `pytest -q` before each
  commit. Mirror the discipline in `prompts/navneet.md`.
- Note: `src/invariants.mustar` uses a CBC subprocess per call and is slow at large n.
  Conjecture 1 does **not** need `mustar`, so your runs will be much faster — exploit that
  to push `n` higher and search more graphs.
