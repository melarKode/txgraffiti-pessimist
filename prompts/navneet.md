You are building a research codebase that hunts for counterexamples to open graph-theory
conjectures using ML-guided adversarial search (a "Pessimist" agent in the sense of
Davila's Optimist/Pessimist framework, arXiv 2411.09158). The four target conjectures are
from Davila, Brimkov, Pepper 2025 (arXiv 2507.17780): all open for years, empirically
validated on ~335 small graphs, none refuted in a decade. Realistic expectation: zero
counterexamples. The deliverable is the Pessimist engine itself, adversarial validation
orders of magnitude beyond the published dataset, the recovered extremal families, and
Lean 4 statements. Frame the README this way. Do not add desperate heuristics chasing
positive reward.

Stack: Python 3.11+, networkx, numpy, matplotlib, pulp, pytest, tqdm. Lean 4 + Mathlib.
Work in the current git repo, which is already initialised on `main` and pushed to GitHub.

Commit and push at every numbered step. Use `git add -A && git commit -m "..." && git
push origin main` at each checkpoint. Eight commits, not one dump. If a step fails,
diagnose and retry within the step. Do not skip ahead.

==== Step 1: skeleton ====
Create:
- README.md stub: "DSA5210 Assignment 3, pattern-discovery option. Pessimist agent
  against four open TxGraffiti conjectures (Davila, Brimkov, Pepper, arXiv 2507.17780).
  Team: Navneet (infra + Conjecture 4), <teammate2> (Conjecture 1), <teammate3>
  (Conjecture 3). Agent: Claude Code (Claude Opus). Full README populated in step 8."
- requirements.txt pinned: networkx>=3.2, numpy>=1.26, matplotlib>=3.8, pulp>=2.8,
  pytest>=8.0, tqdm>=4.66
- .gitignore additions: results/*.png, __pycache__/, .venv/, .DS_Store, lean/.lake/,
  lean/build/, *.olean
- Directory layout: src/, conjectures/, experiments/, results/conj4/, lean/, tests/,
  prompts/ each containing a .gitkeep
Commit: "step 1: repo skeleton". Push.

==== Step 2: invariants ====
src/invariants.py, in-memory cache keyed by tuple(sorted(G.edges())):
- max_degree, min_degree, is_regular, is_connected (networkx wrappers)
- annihilation_number(G): sort degrees ascending, a = max k with sum of k smallest <= |E(G)|
- residue(G): standard Havel-Hakimi residue (terminal count of zeros)
- harmonic_index(G): sum over edges uv of 2 / (deg(u) + deg(v))
- alpha_and_i(G) -> (alpha, i): enumerate maximal independent sets via
  networkx.find_cliques(nx.complement(G)); return (max length, min length). Exact, fast
  for n up to 22.
- mustar(G): minimum maximal matching via direct ILP with pulp using PULP_CBC_CMD(msg=0).
  Variables x_e in {0,1}. Matching: per vertex v, sum of incident x_e <= 1. Maximality:
  for every edge e, x_e + sum over edges f sharing an endpoint with e of x_f >= 1.
  Minimise sum x_e. Brute force fallback when |E| <= 12.
- On n <= 10, cross-check mustar(G) == i(L(G)) via nx.line_graph and alpha_and_i; warn
  on mismatch.
Commit: "step 2: exact invariants". Push.

==== Step 3: invariant tests ====
tests/test_invariants.py with pytest:
- Spot values on P4, C5, K4, Petersen for alpha, mu, i, mustar. Look up published values,
  do not invent.
- Theorem-based fuzz: with fixed seed, 300 random connected graphs over n in 5..15 and
  p in {0.2, 0.4, 0.6}, retried until connected. For every graph assert alpha(G) >= R(G)
  (Favaron-Maheo-Sacle 1991) and alpha(G) <= a(G) (Pepper 2004). Any failure is an
  invariant bug; fix the invariant, never the test.
Run pytest. All tests pass before continuing.
Commit: "step 3: invariant tests passing". Push.

==== Step 4: graph classes ====
src/graphclasses.py:
- general_from_bitstring(bits, n) -> nx.Graph: decode length n(n-1)/2 array to a graph
  on vertices 0..n-1. Do NOT reject disconnected; caller penalises via reward.
- bitstring_from_graph(G, n) for round-trip tests.
- regular_sampler(n, r, rng) using nx.random_regular_graph with even-parity check.
- regular_mutator(G, rng) using nx.double_edge_swap (degree-preserving).
Add 4 short tests under tests/test_graphclasses.py. Run pytest, all green.
Commit: "step 4: graph samplers". Push.

==== Step 5: CEM search ====
src/search.py: classic per-edge Bernoulli cross-entropy method.
- Parameters: p in [0.02, 0.98]^d for d = n(n-1)/2, initialised at 0.5.
- Each iteration: sample `batch` bitstrings, decode, compute reward. Disconnected graphs
  get reward = -1e6. Sort. Refit p toward elite (top 10 percent) empirical frequency
  with lr=0.7, additive noise=0.05, clipped to [0.02, 0.98].
- Returns: best graph, best reward, all graphs with abs(reward) < 1e-9 (equality cases),
  per-iteration JSON log of max, mean, median reward.
- argparse CLI: --n, --iters (default 50), --batch (default 200), --seeds (default 10),
  --seed (int, controls numpy and random seeding for determinism), --out, --smoke
  (sets iters=10, batch=50, seeds=2).
- tqdm progress bar over iterations.
Commit: "step 5: CEM engine". Push.

==== Step 6: Conjecture 4 plumbing + smoke ====
Conjecture 4 (TxGraffiti, open since 2023): for every nontrivial connected G,
mustar(G) <= H(G). Counterexample: connected G with mustar(G) > H(G).
- conjectures/conj4_minmaxmatching_harmonic.py: reward(G) = mustar(G) - H(G).
- experiments/run_conj4.py: argparse. Real defaults n in 4..14, 10 seeds per n,
  50 iters, batch 200. Smoke: n in 4..6, 2 seeds, 10 iters, batch 50.
- Output to results/conj4/: per-(n, seed) JSON log, summary.json (max reward per n),
  all equality-case graphs as edge lists deduplicated by
  nx.weisfeiler_lehman_graph_hash, scatter mustar vs H with equality cases marked.
- If reward > 0 ever: save graph to COUNTEREXAMPLE_<timestamp>.json with full
  provenance, recompute every invariant via a second method (brute force where
  feasible), write VERIFIED.md.

Run: `python experiments/run_conj4.py --smoke`. Must complete in under 2 minutes and
produce files. If it doesn't, debug before proceeding.
Commit: "step 6: Conjecture 4 plumbing + smoke run". Push.

==== Step 7: full run ====
Run `python experiments/run_conj4.py` (no --smoke). Expected under an hour. If any
single n takes longer than 10 minutes, lower the cap to (n-1) and document the actual
cap in results/conj4/RUN_NOTES.md. Do not silently truncate.
Commit: "step 7: Conjecture 4 full run, n up to <actual cap>". Push.

==== Step 8: Lean + proof attempt + README ====

Lean setup. The user has Lean 4 already installed via elan on this Mac (from a prior
Lean autoformalization project for the same course, likely under ~ or ~/Projects).
Before doing anything else in this step, run:

  which lake && lake --version
  which lean && lean --version
  elan show 2>/dev/null || true

If any of those fail, stop and print: "Lean toolchain not on PATH. The user installed
it for Assignment 2; ask them where lake/lean live and how to source the env." Do not
attempt to install Lean yourself.

If they succeed, set up the Lean project inside lean/:
- Scaffold with `lake +stable new pessimist math` in a temp directory, then move its
  generated lakefile.lean, lean-toolchain, and lakefile-style structure into lean/.
  Rationale: this gets the current Mathlib-compatible toolchain pin and dependency
  block without you guessing versions.
- Or, equivalently, write lean/lakefile.lean declaring `package pessimist` with a
  `require mathlib from git "https://github.com/leanprover-community/mathlib4" @ "stable"`
  and copy lean-toolchain from Mathlib's current stable tag. If unsure, use the scaffold.
- lean/Conjectures.lean: import Mathlib. Open a namespace. Declare `opaque`
  definitions over `SimpleGraph V` (with `[Fintype V] [DecidableEq V]` as needed) for:
  independence_number, annihilation_number, residue, max_degree, zero_forcing_number,
  independent_domination_number, min_maximal_matching_number, harmonic_index. Use
  Mathlib's `SimpleGraph.Connected` for connectivity. State all four theorems from
  the appendix of arXiv 2507.17780, each ending in `sorry`.

Build sequence inside lean/:
  lake update
  lake exe cache get      # downloads Mathlib's precompiled olean cache, ~5 min
  lake build              # should be near-instant after cache get

The `lake exe cache get` step is mandatory; without it `lake build` compiles all of
Mathlib from scratch and takes 30+ minutes. The `lake update` step pulls dependency
sources and may take 10 minutes on first run; do not abort it, do not retry on
timeout, let it finish. If your shell tool has a timeout, run these with an extended
timeout (at least 30 minutes for `lake update`, 15 for `lake exe cache get`).

`lake build` must succeed. Theorems carry `sorry` but the file must type-check
against Mathlib. If the build fails, fix lean/Conjectures.lean until it succeeds.

results/conj4/proof_attempt.md: a serious 1-2 page proof sketch for Conjecture 4
restricted to a structured subfamily (trees, or cubic graphs). State what you can
show, where the argument breaks for the general case, and what an extension would
need. Do not bluff; honest "stuck here because X" is fine.

Populate README.md fully:
- Project description: DSA5210 Assignment 3, pattern-discovery option.
- All four target conjectures stated formally with citation to arXiv 2507.17780.
- Honest framing: zero counterexamples expected; contribution is the Pessimist,
  adversarial validation, extremal families, Lean.
- Repo layout.
- Install + run instructions (Python deps, smoke test, full run, Lean build).
- Results summary for Conjecture 4: max reward per n, total graphs searched, number
  of distinct equality cases found (post WL-dedup), link to scatter plot.
- Lean: states that lean/ builds against Mathlib and the four conjectures are
  formally stated with `sorry`.
- AI agent: Claude Code (Claude Opus). Plan mode used.
- Team contributions table.
- References: Davila Brimkov Pepper 2025 (arXiv 2507.17780), Davila Optimist 2024
  (arXiv 2411.09158), Wagner 2021 (deep CEM, arXiv 2104.14516), Pepper 2004
  (annihilation), Favaron-Maheo-Sacle 1991 (residue).

Save this prompt verbatim to prompts/navneet.md.
Commit: "step 8: Lean buildable against Mathlib, proof attempt, full README". Push.
