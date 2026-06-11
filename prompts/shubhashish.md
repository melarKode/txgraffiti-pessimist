# Base prompt for Shubhashish — Conjecture 3 (Pessimist search)

> Hand this to Claude Code (Claude Opus, plan mode) from inside the repo, on your own
> branch. Tweak as you go. Most of the infrastructure already exists and is reusable —
> you are NOT rebuilding invariants, only (a) wiring Conjecture 3's reward into them,
> (b) adding the one piece of search infrastructure that's missing (a regular-graph
> search loop), running it, and reporting honestly.

## Context you (Claude) are joining

This repo (`txgraffiti-pessimist`) is a "Pessimist" agent that adversarially searches for
counterexamples to four open TxGraffiti conjectures (Davila, Brimkov, Pepper 2025,
[arXiv:2507.17780](https://arxiv.org/abs/2507.17780)). Navneet built the shared
infrastructure (`src/`) and the Conjecture 4 pipeline (`conjectures/conj4_*.py`,
`experiments/run_conj4.py`, `results/conj4/`); Tridiv mirrored it for Conjecture 1
(`conjectures/conj1_*.py`, `experiments/run_conj1.py`, `results/conj1/`). You are
implementing **Conjecture 3**.

**Conjecture 3 (open since 2020).** For every `r`-regular graph `G` with `r > 0`:
$$i(G) \le \mu^*(G)$$
where `i` = independent domination number (size of a smallest *maximal* independent
set) and `μ*` = minimum maximal matching number. A **counterexample** is an
`r`-regular graph (`r > 0`) with `i(G) > μ*(G)`.

**Important difference from Conjectures 1 and 4**: those are hypothesised over *all
nontrivial connected graphs*, so the existing CEM (which samples a Bernoulli
probability per possible edge over a general graph) is a fine search space — almost
any sampled graph is a valid candidate. Conjecture 3's hypothesis is **only
`r`-regular graphs**, which is a much smaller, structurally rigid subset; a Bernoulli
edge-probability search would essentially never land on a regular graph by chance, so
**you cannot reuse `run_cem`/`run_search` unmodified**. This is the one place where
you'll need to add new shared search infrastructure — see "Your tasks", step 0.

## What already exists and that you MUST reuse (do not reimplement)

- `src/invariants.py`:
  - `alpha_and_i(G)` -> `(alpha, i)` — `i` (the second element) is exactly the
    independent domination number `i(G)` you need. Exact, via maximal independent
    sets of the complement.
  - `mustar(G)` — minimum maximal matching number `μ*(G)`. Exact: brute-force subset
    enumeration for `|E(G)| <= 12`, otherwise a 0/1 ILP solved via CBC (`pulp`), with
    an `i(L(G))` line-graph cross-check for `n <= 10`.
  - `is_regular(G)`, `min_degree(G)`, `max_degree(G)`, `is_connected(G)`. All memoised.
  - **Known environment issue**: on this machine (Apple Silicon), `pulp`'s bundled CBC
    binary is x86 and fails with `OSError: Bad CPU type in executable` — this is why
    `tests/test_invariants.py::test_mustar_le_max_matching` and
    `test_spot_values[Petersen-...]` already fail on `main` (pre-existing, unrelated
    to your work). For `r`-regular graphs, `|E| = n*r/2`, so **as long as you keep
    `n*r/2 <= 12` your searches stay on the brute-force path and never touch CBC** —
    this is a strong reason to favour small `r` (e.g. `r=3`, cubic graphs) and modest
    `n`. If you need larger `n*r/2`, you'll either need a working CBC (try
    `conda install -c conda-forge coincbc` / `brew install cbc` for an arm64 binary)
    or to extend `_mustar_bruteforce`'s applicability — flag this rather than silently
    getting `OSError`s.
- `src/graphclasses.py`:
  - `regular_sampler(n, r, rng)` — draws a random `r`-regular graph on `n` vertices
    (`nx.random_regular_graph`; raises if `n*r` is odd or `r >= n`).
  - `regular_mutator(G, rng)` — a degree-preserving double-edge-swap mutation; an
    `r`-regular graph stays `r`-regular under this move. **These two functions exist
    specifically for Conjecture 3** (see the module docstring) and are your building
    blocks for the new search loop.
- `src/search.py`:
  - `evaluate(G, reward_fn, require_connected=True)`, `run_cem`, `run_search` — the
    existing Bernoulli-edge CEM for Conjectures 1/4. Read it for the *shape* of a
    result (`CEMResult`: best graph/reward, WL-deduped equality cases at
    `|reward| < EQUALITY_TOL = 1e-9`, per-iteration log) and the multi-restart wrapper
    pattern (`run_search`) — your new regular-graph search should return something
    structurally compatible so `experiments/run_conj3.py` can stay parallel to
    `run_conj1.py`/`run_conj4.py`.
- `experiments/run_conj1.py` / `run_conj4.py` — the template for `run_conj3.py`'s
  outer structure: `EQ_TOL = 1e-9`, `reverify`/`handle_counterexample`/`VERIFIED.md`,
  `make_scatter`, per-`(n, seed)` (here also per-`r`) logging, `summary.json`,
  `equality_cases.json`, `RUN_NOTES.md`, the 10-minute (`budget_seconds=600`)
  per-search-unit wall-clock cap that aborts and documents honestly, and the CLI flag
  style (`--seeds/--iters/--batch/--seed/--budget/--smoke`).
- `lean/Conjectures.lean` — already contains, against Mathlib (builds clean on
  Lean v4.30.0 / Mathlib v4.30.0):
  ```
  theorem conjecture_three (G : SimpleGraph V) [DecidableRel G.Adj] (r : ℕ) (hr : 0 < r)
      (hreg : G.IsRegularOfDegree r) :
      independent_domination_number G ≤ min_maximal_matching_number G := by
    sorry
  ```
- Tests live in `tests/`; run `pytest -q` — the 2 pre-existing CBC failures noted above
  are acceptable baseline (don't try to fix them as part of this task unless they
  start blocking your own searches), but don't introduce *new* failures.

## Your tasks

0. **Design and add a regular-graph search loop** (the one shared-infra change this
   task needs — be careful not to break Conjectures 1/4):
   - A simple, honest approach: a `(mu + lambda)`-style evolutionary search over
     `r`-regular graphs. Maintain a population of `r`-regular graphs on `n` vertices
     (seed with `regular_sampler`); each iteration, generate children via
     `regular_mutator` (one or a few double-edge-swaps per child), score everyone with
     `evaluate`-style reward, keep the best `mu` as the next generation's parents.
     Track best-ever graph/reward and WL-deduped equality cases exactly like
     `CEMResult` does.
   - Where this lives: either a new function (e.g. `run_regular_search` /
     `RegularSearchResult`) added to `src/search.py` alongside the existing CEM code
     (keep `run_cem`/`run_search` untouched — additive only), or self-contained inside
     `experiments/run_conj3.py` if you'd rather not touch the shared file at all.
     Either is fine; just don't change the behaviour or signatures of the existing
     Conjecture 1/4 code paths. Run `pytest -q` after this step to confirm.
   - `require_connected` doesn't apply the same way here — Conjecture 3's hypothesis
     is just "`r`-regular, `r > 0`" (no connectivity requirement). `regular_sampler`
     can produce disconnected regular graphs (e.g. disjoint unions); decide whether to
     allow that or restrict to connected regular graphs for tractability, and document
     your choice in `RUN_NOTES.md` either way — don't silently narrow the hypothesis.

1. **`conjectures/conj3_independence_domination_minmaxmatching.py`** (mirror the
   docstring style of `conj1_independence_annihilation_residue.py` /
   `conj4_minmaxmatching_harmonic.py`):
   - `reward(G) -> float`: `inv.alpha_and_i(G)[1] - inv.mustar(G)`, i.e. `i(G) - μ*(G)`.
     Positive ⇒ counterexample, `0` (within `EQ_TOL`) ⇒ equality/extremal, negative ⇒
     conjecture holds with slack.
   - `components(G)`: return `(i, μ*)` — `(LHS, RHS)` of `i ≤ μ*`, parallel to conj1's
     `(alpha, (a+R)/Δ)` and conj4's `(mu*, H)`.

2. **`experiments/run_conj3.py`**: structure parallel to `run_conj1.py`/`run_conj4.py`,
   but the outer loop is over **`(n, r)` pairs with `r > 0`, `r < n`, `n*r` even**
   (not just `n`), since the hypothesis is regularity-indexed. Sensible starting point:
   fix `r=3` (cubic graphs — smallest non-trivial, well-studied case) and sweep `n`
   even, `n >= 4`; optionally also try `r=4` or `r=5` if time/budget allow, documenting
   each `r` swept separately in `RUN_NOTES.md`. `OUTDIR = os.path.join(ROOT, "results",
   "conj3")`. Update all docstrings/labels/`summary["conjecture"]`/`summary["reward"]`/
   `VERIFIED.md` wording to Conjecture 3's statement and reward formula.
   - **Scatter convention**: `i ≤ μ*` is the same direction as conj4's `μ* ≤ H`
     (LHS ≤ RHS), so follow conj4's convention — `μ*` on the x-axis, `i` on the
     y-axis, feasible region *below* the `y=x` diagonal, boundary labelled `i = μ*`.
   - Create `results/conj3/.gitkeep`.

3. **Run it**:
   - `python experiments/run_conj3.py --smoke` first — must finish well under 2
     minutes and write `summary.json`, `equality_cases.json`, scatter PNG, and
     per-`(n, r, seed)` logs into `results/conj3/`.
   - Then a full run. Respect the per-search-unit 10-minute budget; if `n*r/2 > 12`
     pushes you onto the CBC path and CBC is broken in your environment, either cap
     the sweep below that threshold or fix CBC first (see the environment note above)
     — don't let `mustar` silently raise/crash mid-run.
   - Document the actual measured cap(s) (per `r`, the largest `n` reached) in
     `results/conj3/RUN_NOTES.md` with a timing table — don't guess.

4. **Honest framing**: realistic expectation is **zero counterexamples** (open since
   2020, empirically validated for a decade). Deliverables:
   - the search + adversarial validation results, per `r` swept,
   - any recovered **extremal (equality, `i = μ*`) family** — characterise it (degree
     sequence / structure) in `RUN_NOTES.md`,
   - optionally, a proof attempt for a structured subfamily in
     `results/conj3/proof_attempt.md` (mirror `results/conj1/proof_attempt.md`'s
     rigor — exact hand computation for small cases, e.g. `r=3` on `n=4` (`K4`)).
   - In the unexpected event `reward > EQ_TOL`, follow the `reverify` /
     `handle_counterexample` / `VERIFIED.md` pattern — recompute `i` and `μ*` by
     independent methods (brute-force maximal independent sets / brute-force maximal
     matchings) before calling it real.

5. **(Optional, strong)** Attempt to discharge `conjecture_three`'s `sorry` in
   `lean/Conjectures.lean` for a structured subfamily (e.g. `r`-regular bipartite
   graphs, or whatever extremal family you find empirically), or state+prove the
   equality characterisation as a separate lemma. Confirm `lake build` still succeeds
   from `lean/` after your edit, even if `conjecture_three` itself keeps a `sorry` for
   the general case. **Do not change the statement/hypotheses of the other three
   theorems** (`conjecture_one`, `conjecture_two`, `conjecture_four`) — those are
   teammates' shared formal statements; if you think one needs adjusting, document it
   as an open question (as Tridiv did for `conjecture_one` in
   `results/conj1/proof_attempt.md`) rather than editing it.

## Working agreement

- Plan mode first. Commit in small, labelled checkpoints (mirror
  `prompts/navneet.md`'s "eight commits, not one dump" discipline): regular-graph
  search infra → reward+components → driver script → smoke run → full run →
  RUN_NOTES/equality analysis → (optional) Lean → README update. Run `pytest -q`
  before each commit.
- Commit and push at every numbered step/checkpoint, not just at the end:
  `git add -A && git commit -m "..." && git push -u origin <your-branch>`.
- If a step fails (script error, smoke run doesn't finish, pytest fails, Lean doesn't
  build, CBC errors, etc.), diagnose and retry within that step until it works — do
  not skip ahead to the next step with a broken or unverified prior step.
- Update the project README's Conjecture 3 section with your actual results once the
  run completes (it currently says Conjecture 3 "is searched on Shubhashish's branch
  with the same engine and reporting format" — fill in the real numbers and link your
  results, on your branch; a maintainer can later merge it into `main`).
