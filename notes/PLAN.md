# PLAN.md: living plan, status, and audit sheet

Updated at every phase. Audience: the team and the auditor session. Read this first.

## 1. Goal in one paragraph
Track A of the Pasqal challenge: assign N customers to K trucks (capacity Q) so customers sharing a truck are close, run as a QUBO on a neutral-atom emulator. Score = fewest atoms, feasible shots, small gap to the proven optimum, and an honest account of every loss.

## 2. Core claims (what we want to be judged on)

Two models, one story: the textbook-style QUBO (model A) is derived, its weights made exact, and then **measured to be impossible to lay out** on a 2D Rydberg array; model B changes what the model asks for so that the atom map *is* the customer map.

1. **Model B, seed selection: N atoms (4 / 10 / 15), no slack, no penalty weight, η small by construction.** Bit x_i = 1 means "customer i anchors a truck". Atoms sit on the scaled customer map; customers closer than a threshold r_c cannot both be seeds (Rydberg blockade), and among K-seed sets the most spread-out has the lowest energy. The capacity rule never enters the energy: a shot decodes by attaching every other customer to the nearest seed with room (light decode, O(N·K)); shots that do not decode are infeasible and discarded. The scale α = R_b / r_c and the final detuning δ_f (midpoint of the window where exactly K seeds is the ground state) are computed from the instance geometry only, no solver involved. Measured (QuTiP / emu-sv, 1000 shots): best feasible shot reaches the proven optimum on every instance tried so far; feasibility 31–79 % vs 3–40 % for a uniform random sampler; P(reach) up to 51 % (S) / 30 % (M) / 21 % (L).
2. **Model A, the direct QUBO, derived and then falsified on the device.** One bit per customer (K = 2) or one-hot (K ≥ 3), pairwise-distance objective, slack-free load-balance capacity penalty with the smallest exact λ*, A* (4 / 30 / 60 atoms vs 14 / 45 / 80 with slack). Its coupling graph is anti-geometric (far customers must become close atoms): the best layout gives η ≈ 1 and ranks the optimum ≈ 10⁴ of 59049 valid assignments on every M instance. Kept as the honest baseline (S runs end to end) and as the measured reason for model B.
3. **Every loss is split and attributed.** Decomposition loss (cluster-first vs CVRP optimum), penalty loss (model A: exact minimiser vs constrained optimum), seed-model loss (model B: hardware ground state vs optimum, per decoder), embedding error (η and ground-state rank), sampling loss (emulator vs ground state), all against proven optima from one exact DP, and all compared with a random sampler so the quantum part's contribution is a number.
4. **Pasqal's stack as the baseline.** qubo-solver's embedders and drive shapers run on the same instances; pulser validates every register and sequence; the friction log (§6b) records where the stack got in the way.

## 3. Status

| Phase | Deliverable | Status | Where |
|---|---|---|---|
| A2 instances + references | 9 instances, certificates, proven optima | **done** | `notes/instances.md`, `instances/*.json`, `cvrp/instances.py`, `cvrp/reference.py` |
| A1 model A (direct QUBO) | formulas per tier, tuned λ and A, variable-count table | **done** (all tiers tuned) | `notes/qubo.md`, `cvrp/qubo.py`, `cvrp/tune.py`, `instances/weights.json` |
| A1 model B (seeds) | N-atom seed model, two decoders, exact references over seed sets | **done, documenting** | `cvrp/seeds.py` |
| A3 layout | model A: embedder + baselines + η + ground-state rank; model B: map scale α, floor, radius compression | **done for A (negative result), done for B** | `cvrp/embedding/`, `cvrp/seeds.py` |
| A4 pulse | sequence builder (global / DMM), emulator runner, grid | **sequence + runner done; grid + results next** | `cvrp/pulse/` |
| Results | `results.csv`, README one-command | in progress | `results/`, `README.md` |
| Report (≤ 4 pages) | model, variable accounting, embedding, pulse, results, what did not work, AI use | not started | `report/` |

## 4. Brief criteria → where covered

| Brief item | Covered by | Status |
|---|---|---|
| Derive 2.1 formal CVRP (sets, params, variables, eq vs ineq) | `notes/qubo.md` §0 | done |
| Derive 3.1 what the register minimises | `notes/qubo.md` §5 | done |
| Derive 4.1 variable-count table | `notes/qubo.md` §7, `cvrp/qubo.py:variable_count_table` | done (14/45/80 slack vs 4/30/60 model A vs 4/10/15 model B) |
| A1 model: variables, objective, both constraints, penalty weights and how set | `notes/qubo.md` §1–6 (A), §9 (B); `cvrp/tune.py` | done |
| A2 generator: seeded, assumptions, certificate + validator, ρ and d_max/Q | `cvrp/instances.py`, `notes/instances.md` | done |
| A3 embed within 5 µm / 38 µm, report realised vs wanted couplings | `notes/embedding-plan.md`, `cvrp/embedding/`, `results/layouts/` | done (A: negative result measured; B: map layout) |
| A4 pulses, multiple instances, results | `notes/pulse-plan.md`, `cvrp/pulse/`, `results/runs_log.csv` | done (grid), S run; M/L running |
| Reference C*: brute force → CPLEX → SA; S must agree | DP (proven) + brute force + CPLEX, all agree on all 9 | done |
| Gaps: model gap, CVRP gap (Track A) | `cvrp/evaluate.py` | done |
| Metrics: best gap, feasibility rate, P(reach ref) with ε, atom count, embedding fidelity (formula stated), reference status | `results/results.csv` columns | done |
| Relabelings = same solution | `reference.assignment_to_groups` canonical form | done |
| Never report an infeasible bitstring's cost | `evaluate.py`: only decodable, capacity-feasible shots are scored | done |
| DMM results labelled and compared separately | `variant` column: global / dmm / random | done |
| emu-mps bond dimension reported | `bond_dim` column (model B never needs emu-mps; model A M/L not run) | done |
| SA / CPLEX settings reported | CPLEX time limits in code; SA helper returns its parameters (SA not needed: all references proven) | done |
| Random-sampler comparison ("how much work does the quantum part do") | rows `B-random-*`, `A-random`, columns `*_random_K`, `p_reach_ratio_vs_random_K` | done |
| Repo: README one-command repro, pinned env | `README.md`, `requirements.txt` | done |
| Report: what did not work, where AI was used | §6, §6b here; `report/` | report todo (deliverable session) |

## 5. Decisions and why

| Decision | Why |
|---|---|
| 3 instances per tier, seeds 0,1,2 | enough for "multiple instances"; L-tier emulation is slow |
| Accept only instances where ρ ∈ [0.70, 0.95] **and capacity binds** (unconstrained optimum overloaded) | first draft without the binding rule gave λ* = 0 on 5 of 6 S/M instances: the capacity encoding was never tested |
| One capacity penalty for all tiers, Σ_k (L_k − D/K)² | one derivation, one story; for K = 2 it is number partitioning (Lucas 2014), for K ≥ 3 it is the balance form of unbalanced penalisation (Montañez-Barrera 2024) |
| 1 bit per customer for K = 2, one-hot for K ≥ 3 | only encodings with all-positive couplings (domain-wall and binary need negative or 3-body terms) |
| λ*, A* = smallest exact-feasible weights × 1.1 | smallest weights keep the useful energy range large; exactness checked by DP / CPLEX, not assumed |
| Both global-only and DMM variants | global-only is QPU-legal; DMM fixes the per-atom linear term in emulation; brief asks to compare separately |
| References by exact DP, not CPLEX | proven optimum on every tier in seconds; CPLEX kept only as the cross-check the brief requires |

### Auditor findings and answers (pass 1, 2026-10-25)

| # | Finding (auditor) | Answer |
|---|---|---|
| 1 | DMM: AnalogDevice has no DMM; label DMM results, keep a global-only headline | Agreed. Brief §3.1 allows DMM in emulation only. Implementation: `qoolqit.AnalogDeviceWithDMM` (= `AnalogDevice.to_virtual()` + one DMM). Every results row carries `variant = global / dmm`; the QPU-relevant headline is global-only. Wording "exact per-atom linear terms (DMM)" now reads "exact per-atom linear terms (DMM, emulation only)". |
| 2 | MIS pivot: conflict graph of candidate clusters is not unit-disk | Confirmed by measurement (§6): 7–12 % of conflict pairs misclassified by any centroid-distance threshold; centroid layout needs a 400–1000 µm radius; conflict degree 30–50 vs the ≤ 9 blockade neighbours a 5 µm-spaced 2D array allows. **MIS pivot dropped.** |
| 3 | MIS = set packing, coverage not guaranteed | Moot after #2; noted as the reason an MIS encoding would need a coverage check on every shot. |
| 4 | Candidate pool is classical work | Moot after #2. The same concern applies to our sparsification (below): the kept-pair rule is stated as part of the model and its loss is measured classically before any quantum step. |
| 5 | 1/r⁶ tails bias toward sparse sets; keep S as the honest baseline | Agreed: S runs end to end with the dense model; the tail/zero-pair error is reported as η and as the ground-state rank. |

## 6. Findings so far (feeds "what did not work")
- **The dense one-hot QUBO cannot be laid out in 2D (A3, blocker-level, measured).** Each atom wants ~N−1 same-truck + K−1 same-customer couplings within a factor ≈ 5 of each other; because U ∝ 1/r⁶, every wanted distance lands in 5–7 µm, and a 5 µm-spaced plane offers at most 6 such neighbours. Measured: best per-pair fit gives η ≈ 1.0 and the model optimum ranks ≈ 10⁴ of 59049 valid assignments on all three M instances (S: rank 2–8 of 16). Fitting positions to energies on the valid subspace (torch, 3000 Adam steps) instead of to couplings does not change this (corr ≈ 0.6). Exact per-atom linear terms do not change it either, so it is the couplings, not the detuning. This is Pitfall 4.1 of the brief, met head-on.
- **Candidate-cluster MIS encoding is also dense** (see auditor #2). Dropped after measurement, not after discussion.
- **Model B works end to end (2026-10-25 02:15).** Smoke test, R_b = 9 µm (Ω = 1.63 rad/µs), T = 4000 ns, δ_f = window midpoint, 1000 shots: S_seed0 feasibility 79 % (random 40 %), P(reach) 51 %; M_seed0 31 % / 20 % (exact decode); M_seed2 41–45 % / 20–30 %; L_seed0 (emu-sv, 15 atoms, 25 s) 34–36 % (random 3 %) / 4 % light, 21 % exact. Best feasible shot = proven optimum in every case. The light decode is the headline (classical part O(N·K)); the exact decode (best feasible assignment to the given seeds) is the labelled post-processing variant.
- **Two scale rules that failed before the one that works:** α from the closest customer pair (spreads seeds so far apart that the "exactly K" margin was 0.001 rad/µs); α from the K-dispersion radius only (breaks the 5 µm spacing). The working rule ties the blockade radius to r_c, the threshold between the K- and (K+1)-dispersion radii, and floors sub-5 µm pairs (already blockaded).
- **Sparsifying model A does not rescue it** (m = 3 farthest partners: degree 7, still η ≈ 1, rank 12732/59049): the problem is that the coupling graph is anti-geometric, not merely dense.
- **Direction tested earlier: sparsify the model.** Keep, per customer, only the m farthest partners in the clustering cost (and in the capacity pair terms); everything else is 0. The sparse model's exact optimum is still computed by the same DP, so the **sparsification loss** (its optimum's true cost minus the full optimum) is known exactly before any quantum step. The curve m → (sparsification loss, η, ground-state rank) is the measurable answer to "how much of the QUBO must be dropped for a 2D Rydberg array to represent it, and what does it cost". m = 2 is too aggressive (a zero-cost valid assignment exists, so the model is empty); m = 3..9 running.
- **Weight rule refined:** A = max(1.1·A*, strongest objective coupling / 2), so the one-hot coupling 2A is never weaker than any objective coupling (a hard constraint has to be the strongest interaction; otherwise the sparse models drive A → 0 and the one-hot cliques vanish from the layout).
- **Penalty loss is real.** With λ*, the QUBO's exact minimiser is feasible on all 6 S/M instances but is the constrained optimum on only 4: M_seed1 loses 0.7 %, M_seed2 loses 13.8 % before any quantum step. Any slack-free quadratic penalty has this: on valid assignments it reduces to "minimise Σ_k L_k²", i.e. balance, whatever target you write. A smaller λ trades this against feasibility rate (claim 2).
- **Decomposition gap** (cluster-first heuristic vs true CVRP) is 0–19 % on our instances; reported per instance in `notes/instances.md`.
- Bug caught by the self-test: the K = 2 QUBO used half the penalty the tuner assumed. Fixed by using the same Σ_k form for every tier.

## 6b. Friction log (Pasqal stack, for the report)

| Tool | What happened | Workaround |
|---|---|---|
| qubo-solver 0.9.1 | The brief's parameter names (`use_quantum`, `classical_solver_type`, `sa_initial_temp`, …) do not exist; the API is `SolverConfig(solving=ClassicalSolvingConfig(algorithm=...))`, and SA temperatures are only reachable by calling `solving.classical.simulated_annealing.solve` directly | wrote `cvrp/classical.py` against the real API; CPLEX needs `pip install cplex` |
| pulser AnalogDevice | has no DMM channel, although the brief allows a DMM in emulation | copy of `qoolqit.AnalogDeviceWithDMM`: `replace(AnalogDevice.to_virtual(), dmm_objects=(DMM(...),))` |
| pulser register radius | the 38 µm radius is measured from the coordinate origin, not from the atoms' centre; a layout legal around its centroid can be rejected | never re-centre a layout after optimising it against the device limits |
| qoolqit embedders | `InteractionEmbedder` / `Blade` take dimensionless matrices (C6 = 1, distance unit = 5 µm) and return a `DataGraph`; no device-limit check inside the optimiser | baselines wrapped in `cvrp/embedding/baselines.py` with explicit unit conversion |
| scikit-learn MDS | deprecation warnings (`dissimilarity` → `metric`, `init` default change) | harmless; pinned version |

## 7. Open questions for the auditor
1. Is claim 2 (penalty-loss / sampling-loss split, λ as a measured trade-off) sharp enough as the headline, or should the headline be the atom count?
2. Should the symmetry fix (pin customer A to truck 1, saves K − 1 atoms) be on by default? It changes the linear terms and is not required.

## 8. Next steps
1. Finish L tuning; write `notes/qubo.md` (formulas, truth-table checks, tuned weights, hardware mapping).
2. A3: embedder + baselines + η; one figure per instance.
3. A4: pulse grid on tier S end-to-end, then M, L.
4. `evaluate.py`, `results.csv`, README.
