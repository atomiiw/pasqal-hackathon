# PLAN.md: living plan, status, and audit sheet

Updated at every phase. Audience: the team and the auditor session. Read this first.

## 1. Goal in one paragraph
Track A of the Pasqal challenge: assign N customers to K trucks (capacity Q) so customers sharing a truck are close, run as a QUBO on a neutral-atom emulator. Score = fewest atoms, feasible shots, small gap to the proven optimum, and an honest account of every loss.

## 2. Core claims (what we want to be judged on)
1. **Slack-free capacity with a proven-exact weight.** Capacity is a load-balance penalty λ·Σ_k (L_k − D/K)². No slack bits: 4 / 30 / 60 atoms vs 14 / 45 / 80 for the textbook encoding. The smallest exact λ* is computed, not guessed: it is the smallest λ whose exact minimiser (set-partition DP) is feasible.
2. **Model gap split into penalty loss and sampling loss.** Penalty loss = cost of the QUBO's exact minimiser minus the constrained optimum (a property of the encoding, zero quantum involved). Sampling loss = what the emulator adds on top. Reported separately per instance. Below λ* the penalty loss shrinks but the feasibility rate drops; λ is a measured trade-off knob, legal because we post-select feasible shots (brief Pitfall 9.1).
3. **Hardware mismatch, classified and measured.** For one-hot encodings the per-atom linear term is provably irrelevant on valid assignments (each customer has exactly one bit on), so the global-detuning limit only affects invalid strings. The only real error is the "want 0, get > 0" pairs. We report η = ‖U − s·b‖/‖s·b‖ and a ground-state-preserved check on the realised energies.
4. **Layout and pulse with Pasqal's own tools as baselines.** Our embedder (log-distance loss + device constraints, MDS start) and our pulse grid are compared against qubo-solver's BLaDE / greedy embedders and its drive shapers on the same QUBO.

## 3. Status

| Phase | Deliverable | Status | Where |
|---|---|---|---|
| A2 instances + references | 9 instances, certificates, proven optima | **done** | `notes/instances.md`, `instances/*.json`, `cvrp/instances.py`, `cvrp/reference.py` |
| A1 QUBO | formulas per tier, tuned λ and A, variable-count table | **in progress** (S, M tuned; L running) | `notes/qubo.md`, `cvrp/qubo.py`, `cvrp/tune.py`, `instances/weights.json` |
| A3 layout | plan + pipeline + η per instance | not started | `notes/embedding-plan.md`, `cvrp/embedding/` |
| A4 pulse | plan + grid search + shots | not started | `notes/pulse-plan.md`, `cvrp/pulse/` |
| Results | `results.csv`, README one-command | not started | `results/`, `README.md` |
| Report (≤ 4 pages) | model, variable accounting, embedding, pulse, results, what did not work, AI use | not started | `report/` |

## 4. Brief criteria → where covered

| Brief item | Covered by | Status |
|---|---|---|
| Derive 2.1 formal CVRP (sets, params, variables, eq vs ineq) | `notes/qubo.md` §0 | todo |
| Derive 3.1 what the register minimises | `notes/qubo.md` §5 (E_Pasqal) | todo |
| Derive 4.1 variable-count table | `notes/qubo.md`, `cvrp/qubo.py:variable_count_table` | done in code |
| A1 model: variables, objective, both constraints, penalty weights and how set | `notes/qubo.md`, `cvrp/tune.py` | in progress |
| A2 generator: seeded, assumptions, certificate + validator, ρ and d_max/Q | `cvrp/instances.py`, `notes/instances.md` | done |
| A3 embed within 5 µm / 38 µm, report realised vs wanted couplings | `cvrp/embedding/` | todo |
| A4 pulses, multiple instances, results | `cvrp/pulse/` | todo |
| Reference C*: brute force → CPLEX → SA; S must agree | DP (proven) + brute force + CPLEX, all agree on all 9 | done |
| Gaps: model gap, CVRP gap (Track A) | `cvrp/evaluate.py` | todo |
| Metrics: best gap, feasibility rate, P(reach ref) with ε, atom count, embedding fidelity (formula stated), reference status | `results/results.csv` | todo |
| Relabelings = same solution | `reference.assignment_to_groups` canonical form | done |
| Never report an infeasible bitstring's cost | `evaluate.py` post-selection | todo |
| DMM results labelled and compared separately | results `variant` column | todo |
| emu-mps bond dimension reported | results `bond_dim` column | todo |
| SA / CPLEX settings reported | `classical.simulated_annealing` returns params; CPLEX time limit logged | partly |
| Random-sampler comparison ("how much work does the quantum part do") | `pulse/search.py` baseline | todo |
| Repo: README one-command repro, pinned env | `README.md`, `requirements.txt` | todo |
| Report: what did not work, where AI was used | `report/` | todo (log kept in §6 below) |

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

## 6. Findings so far (feeds "what did not work")
- **Penalty loss is real.** With λ*, the QUBO's exact minimiser is feasible on all 6 S/M instances but is the constrained optimum on only 4: M_seed1 loses 0.7 %, M_seed2 loses 13.8 % before any quantum step. Any slack-free quadratic penalty has this: on valid assignments it reduces to "minimise Σ_k L_k²", i.e. balance, whatever target you write. A smaller λ trades this against feasibility rate (claim 2).
- **Decomposition gap** (cluster-first heuristic vs true CVRP) is 0–19 % on our instances; reported per instance in `notes/instances.md`.
- Bug caught by the self-test: the K = 2 QUBO used half the penalty the tuner assumed. Fixed by using the same Σ_k form for every tier.

## 7. Open questions for the auditor
1. Is claim 2 (penalty-loss / sampling-loss split, λ as a measured trade-off) sharp enough as the headline, or should the headline be the atom count?
2. Should the symmetry fix (pin customer A to truck 1, saves K − 1 atoms) be on by default? It changes the linear terms and is not required.

## 8. Next steps
1. Finish L tuning; write `notes/qubo.md` (formulas, truth-table checks, tuned weights, hardware mapping).
2. A3: embedder + baselines + η; one figure per instance.
3. A4: pulse grid on tier S end-to-end, then M, L.
4. `evaluate.py`, `results.csv`, README.
