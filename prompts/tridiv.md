# Base prompt for Tridiv — Conjecture 1 (Pessimist search)

> Hand this to Claude Code (Claude Opus, plan mode) from inside the repo. Tweak as you go.
> The infrastructure already exists and is reusable — you are NOT rebuilding invariants or
> the search engine, only wiring Conjecture 1 into them, running it, and reporting honestly.

## Context you (Claude) are joining

This repo (`txgraffiti-pessimist`) is a "Pessimist" agent that adversarially searches for
counterexamples to four open TxGraffiti conjectures (Davila, Brimkov, Pepper 2025,
[arXiv:2507.17780](https://arxiv.org/abs/2507.17780)). Navneet already built the shared
infrastructure (`src/`) and the Conjecture 4 pipeline (`conjectures/conj4_*.py`,
`experiments/run_conj4.py`, `results/conj4/`). You are implementing **Conjecture 1**, end
to end, by mirroring that pipeline.

**Conjecture 1 (open since 2016).** For every nontrivial connected graph `G`:
$$\alpha(G) \ge \frac{a(G) + R(G)}{\Delta(G)}$$
where `α` = independence number, `a` = annihilation number, `R` = residue, `Δ` = max
degree. A **counterexample** is a connected `G` with `α(G) < (a(G)+R(G))/Δ(G)`.

## What already exists and that you MUST reuse (do not reimplement)

- `src/invariants.py`:
  - `alpha_and_i(G)` -> `(alpha, i)`, exact via maximal cliques of the complement,
    "fast for n up to ~22" per its docstring — this is the operation most likely to
    dominate runtime for Conjecture 1, so it's what determines your n-cap.
  - `annihilation_number(G)` (O(n log n) on the degree sequence) and `residue(G)`
    (Havel–Hakimi residue) — both cheap.
  - `max_degree(G)`, `is_connected(G)`. All four are memoised by `_memo`/`_key`.
- `src/search.py`:
  - `evaluate(G, reward_fn, require_connected=True)` — **already applies the
    connectivity guard before calling `reward_fn`**. `reward_fn` is only ever invoked
    on graphs that pass `inv.is_connected(G)`. For a connected graph on `n >= 2`
    vertices every degree is `>= 1`, so `Δ(G) >= 0` is impossible and the `Δ(G)=0`
    case **cannot occur** in practice. Don't build special-case logic around it — an
    `assert Δ > 0` (or just letting a ZeroDivisionError surface, which would indicate
    a real bug elsewhere) is enough.
  - `run_cem(n, reward_fn, iters, batch, rng, progress, desc)` — one CEM restart,
    returns a `CEMResult` (best graph/reward, WL-deduped equality cases where
    `|reward| < EQUALITY_TOL = 1e-9`, per-iteration log). `run_search(...)` wraps
    multiple restarts. Use these as-is; do not touch `src/search.py`.
- `src/graphclasses.py` — bitstring↔graph codec used by the search. Not your concern
  beyond importing it if `run_conj4.py` does.
- `experiments/run_conj4.py` — **the template for `run_conj1.py`**. Copy its structure
  wholesale and adapt only the conjecture-specific pieces:
  - `EQ_TOL = 1e-9` equality tolerance — reuse the same constant and same "positive
    reward ⇒ counterexample, |reward|<EQ_TOL ⇒ equality, else ⇒ holds" classification.
  - `reverify(G)` / `handle_counterexample(G, n, seed_idx)` — keep this pattern, but
    recompute `α`, `a`, `R`, `Δ` by independent methods (e.g. `alpha_and_i` is itself
    already brute-force-exact via complement cliques; for `a`/`R` recompute directly
    from the sorted degree sequence inline rather than via `inv` as a second method).
  - `make_scatter(points, path)` — adapt axes (see "Scatter convention" below).
  - `_run_one_n` / `run` / `write_run_notes` — same per-n multi-seed loop, same
    10-minute (`budget_seconds=600`) per-n wall-clock cap that aborts and documents
    the cap honestly, same `summary.json` / `equality_cases.json` / `RUN_NOTES.md`
    output triple.
  - The CLI flags (`--n-min`, `--n-max`, `--seeds`, `--iters`, `--batch`, `--seed`,
    `--budget`, `--smoke`) and smoke defaults (`n` 4..6, 2 seeds, 10 iters, batch 50)
    — keep identical for consistency across both pipelines.
- `lean/Conjectures.lean` — already contains, against Mathlib (builds clean on
  Lean v4.30.0 / Mathlib v4.30.0):
  ```
  theorem conjecture_one (G : SimpleGraph V) (hconn : G.Connected)
      (hnt : 2 ≤ Fintype.card V) :
      ((annihilation_number G : ℚ) + (residue G : ℚ)) / (max_degree G : ℚ)
        ≤ (independence_number G : ℚ) := by
    sorry
  ```
- Tests live in `tests/`; run `pytest -q` — must be green before and after every
  change you make.

## Your tasks

1. **`conjectures/conj1_independence_annihilation_residue.py`** (mirror the docstring
   style of `conj4_minmaxmatching_harmonic.py`):
   - `reward(G) -> float`: `(a(G) + R(G)) / Δ(G) - α(G)`. Positive ⇒ counterexample,
     `0` (within `EQ_TOL`) ⇒ equality/extremal, negative ⇒ conjecture holds with slack.
   - `components(G)`: return `(alpha, (a+R)/Δ)` — i.e. `(LHS, RHS)` of the conjectured
     inequality `α ≥ (a+R)/Δ`, in that order, so `run_conj1.py` and the scatter can
     stay structurally parallel to `conj4`'s `(mu*, H)` = `(LHS, RHS)` of `mu* ≤ H`.

2. **`experiments/run_conj1.py`**: copy `run_conj4.py`, swap the `conj4` import for
   `conj1_independence_annihilation_residue as conj1`, set
   `OUTDIR = os.path.join(ROOT, "results", "conj1")`. Update all conjecture text/labels
   (docstring, `summary["conjecture"]`, `summary["reward"]`, print statements,
   `VERIFIED.md` wording) to Conjecture 1's statement and reward formula.
   - **Scatter convention**: for Conjecture 4, `mu* ≤ H` puts the feasible region
     *below* the `y=x` diagonal (y=mu* on the vertical axis, x=H on the horizontal).
     For Conjecture 1, `α ≥ (a+R)/Δ` is the mirror inequality, so put
     `(a+R)/Δ` on the x-axis and `α` on the y-axis; the feasible region is *above*
     the `y=x` diagonal, with the boundary line labelled `α = (a+R)/Δ`. Equality
     cases (diamonds) sit on the diagonal. Keep axis labels honest:
     `"(a(G)+R(G))/Δ(G)"` and `"α(G)"`.
   - Create `results/conj1/.gitkeep` (or just let the directory get created by the
     first run + `os.makedirs`, then `git add` the outputs).

3. **Run it**:
   - `python experiments/run_conj1.py --smoke` must finish in well under 2 minutes and
     write `summary.json`, `equality_cases.json`, the scatter PNG, and per-(n,seed)
     logs into `results/conj1/`.
   - Then the full run `python experiments/run_conj1.py`. Because Conjecture 1 needs
     only `α`, `a`, `R`, `Δ` — no CBC/ILP subprocess — each graph evaluation is far
     cheaper than Conjecture 4's `mu*`. **You should comfortably exceed Navneet's
     n=8 cap**; the likely bottleneck becomes `alpha_and_i`'s clique enumeration on
     the complement graph as `n` grows (his docstring says "fast for n up to ~22",
     but worst case is exponential, so the 10-minute budget will still bite
     somewhere — find out empirically where).
   - If a given `n` blows the 10-minute budget, let `run_conj1.py` abort it exactly
     as `run_conj4.py` does (don't record it, cap at `n-1`, stop). Document the
     **actual measured cap** in `results/conj1/RUN_NOTES.md`, including the per-n
     timing table — do not guess or round up.
   - If you have time/budget after reaching a wall-clock cap, consider whether
     `--iters`/`--batch`/`--seeds` could be tuned (more seeds at smaller n vs. fewer
     at larger n) to search more graphs per second — but keep any deviation from
     `run_conj4.py`'s defaults explicit and justified in `RUN_NOTES.md`, since the
     two pipelines should otherwise stay comparable.

4. **Honest framing**: realistic expectation is **zero counterexamples** (this
   conjecture has been open and empirically validated since 2016). Do not add
   heuristics chasing positive reward, and do not pad the search beyond what the
   budget naturally allows. Deliverables:
   - the search + adversarial validation results,
   - any recovered **extremal (equality) family** — characterise it in
     `RUN_NOTES.md` (e.g. degree sequence / structure of the WL-deduped equality
     graphs in `equality_cases.json`),
   - optionally, a proof attempt for a structured subfamily in
     `results/conj1/proof_attempt.md` (mirror `results/conj4/proof_attempt.md`'s
     format if it's useful as a template).
   - In the unexpected event `reward > EQ_TOL`, follow the `reverify` /
     `handle_counterexample` / `VERIFIED.md` pattern from `run_conj4.py` exactly —
     recompute every one of `α`, `a`, `R`, `Δ` by an independent method before
     calling it real.

5. **(Optional, strong)** Attempt to discharge `conjecture_one`'s `sorry` in
   `lean/Conjectures.lean` for a structured subfamily (e.g. the extremal family you
   find empirically), or at minimum state and prove the equality-case
   characterisation as a separate lemma. Confirm `lake build` (or however the Lean
   project is built — check `lean/` for a `lakefile`) still succeeds after your edit,
   even if `conjecture_one` itself keeps a `sorry` for the general case.

## Working agreement

- Plan mode first. Commit in small, labelled checkpoints (mirror the 8-step
  discipline in `prompts/navneet.md`: skeleton/file additions → reward+components →
  driver script → smoke run → full run → RUN_NOTES/equality analysis →
  (optional) Lean → README update). Run `pytest -q` before each commit.
- Commit and push at every numbered step/checkpoint, not just at the end. Use
  `git add -A && git commit -m "..." && git push origin main` at each checkpoint —
  same discipline as `prompts/navneet.md` ("Eight commits, not one dump"). Push to
  this same repo (`origin`/`main`); don't create a separate fork or branch unless
  asked.
- If a step fails (script error, smoke run doesn't finish, pytest fails, Lean
  doesn't build, etc.), diagnose and retry within that step until it works — do not
  skip ahead to the next step with a broken or unverified prior step.
- Update the project README's Conjecture 1 section (it currently frames this as a
  three-conjecture team effort — Conj 1, 3, 4) with your actual results once the run
  completes.
