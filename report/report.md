# Capacitated clustering on a neutral-atom emulator — Track A

Team Byteskip (Atom Wang, Lucas Ma). Repo: github.com/atomiiw/pasqal-hackathon. Reproduce: `python -m cvrp.run_all --tier S` (2 min) or `--all`.

## 1. Problem and references (A2)

CVRP, cluster-first: assign N customers (demands $d_i$) to K trucks of capacity Q so that customers sharing a truck are close; objective = sum of pairwise distances inside each truck. Equality: each customer on exactly one truck. Inequality: load $L_k \le Q$.

Nine seeded instances (3 per tier; depot (50,50); coordinates uniform in $[0,100]^2$). Accepted only if a packing exists, $\rho = D/(KQ) \in [0.70, 0.95]$, and **capacity binds** (the unconstrained optimum is overloaded; otherwise the capacity encoding is never tested). Each ships a certificate checked by the validator. References are **proven optima** from one exact dynamic program over set partitions (clustering optimum and, with Held-Karp tours, the CVRP optimum); brute force (S, M) and CPLEX agree on all nine. Decomposition gap (cluster-first vs CVRP optimum): 0–19 %. Details: `notes/instances.md`.

## 2. Model A: the direct QUBO, and why it cannot be laid out (A1, A3)

Bits: one per customer for K = 2 ($x_i = 1$: truck 1), one-hot $x_{ik}$ for K ≥ 3. Total = $C + A\,P_{\text{assign}} + \lambda\,P_{\text{cap}}$ with $C = \sum_k\sum_{i<j} d_{ij}x_{ik}x_{jk}$, $P_{\text{assign}} = \sum_i(1-\sum_k x_{ik})^2$ and the slack-free **load-balance** penalty $P_{\text{cap}} = \sum_k (L_k - D/K)^2$ (K = 2: number partitioning, Lucas 2014; K ≥ 3: the balance form of unbalanced penalisation, Montañez-Barrera et al. 2024). Expanded coefficients, per atom $a_{ik} = -A + \lambda d_i(d_i - 2D/K)$, per same-truck pair $d_{ij} + 2\lambda d_i d_j$, per same-customer pair $2A$, all couplings $\ge 0$ (`notes/qubo.md`). Weights: $\lambda^*$, $A^*$ = smallest values whose exact minimiser is feasible (set-partition DP / CPLEX), × 1.1.

| encoding | S | M | L |
|---|---|---|---|
| one-hot + binary slack | 14 | 45 | 80 |
| model A (no slack) | 4 | 30 | 60 |
| **model B (seeds)** | **4** | **10** | **15** |

Two measured costs of model A. **Penalty loss:** on valid assignments the balance penalty reduces to $\sum_k L_k^2$, so it prefers balanced loads over the true optimum: 0 / 0.7 / 13.8 % on M before any quantum step. **No 2D layout:** the penalty makes far-apart customers need strongly coupled, i.e. close, atoms, the opposite of the map; every atom wants ~N−1+K−1 near-equal couplings and the $1/r^6$ law puts all wanted distances in 5–7 µm. Best layouts (MDS start, SLSQP on a log-distance loss under the 5 µm / 38 µm limits; Pasqal's BLaDE and greedy embedders give the same) reach $\eta = \|U - sb\|/\|sb\| \approx 1.0$–1.25 on M and rank the optimum 8 784 / 19 930 / 11 182 of 59 049 valid assignments. Fitting energies instead of couplings and sparsifying the objective do not change this. On S (4 atoms, η 0.54–0.62) the pipeline runs: usable shots 5 / 90 / 96 %, best shot = optimum on all three, P(reach) 3 / 4 / 95 % (global detuning; DMM variant labelled separately in `results.csv`).

## 3. Model B: seed selection (A1, A3)

Brief §4.1: "avoid the inequality altogether by changing what the model asks for". Bit $x_i = 1$ means customer $i$ is a **seed** (anchor of one truck). One atom per customer, on the **scaled customer map**: $r_{ij} = \alpha d_{ij}$, $\alpha = R_b / r_c$, where $R_b = (C_6/\Omega)^{1/6}$ is the blockade radius and $r_c$ lies between the K- and (K+1)-dispersion radii of the map (largest $r$ such that $j$ customers are pairwise $\ge r$ apart). Customers closer than $r_c$ cannot both be seeds; among K-seed sets the most spread-out has the lowest energy. Pairs under 5 µm are floored at 5.5 µm (blockaded either way); the map is compressed by the same optimiser only when it exceeds the 38 µm radius. The hardware energy $-\delta\sum_i x_i + \sum_{i<j} C_6/r_{ij}^6\,x_ix_j$ **is** the QUBO: no coefficient is requested that the device does not give. $\delta_f$ = midpoint of the window in which exactly K seeds is the ground state (from pair-energy sums over j-subsets); checked by brute force over all $2^N$ strings.

Capacity never enters the energy. A shot is decoded by attaching each non-seed, largest demand first, to the group with room whose members are closest (light, $O(N^2K)$; **light-multi** = the same under 3 fixed item orders, best kept); shots with ≠ K seeds or no fitting assignment are infeasible and discarded. An **exact** decode (cheapest feasible assignment to the given seeds, a small GAP) is reported as labelled classical post-processing. All layouts pass `AnalogDevice.validate_register`.

## 4. Pulse (A4)

Ω: 0 → Ω_max → 0 (10 % rise/fall); δ: $\delta_0 = -\max(2\Omega_{\max}, 5)$ → $\delta_f = c \times$ nominal. Grid: $R_b \in \{7, 9, 12\}$ µm and $T \in \{2, 4, 6\}$ µs per tier (seed 0), $c \in \{0.7, \dots, 1.9\}$ per instance; 1000 shots; scored by P(reach optimum), then valid-shot rate (never mean energy). Selected: S $R_b$ 7 µm, 4 µs; M 9 µm, 2 µs; L 9 µm, 6 µs. Emulators: pulser-simulation (≤ 12 atoms), emu-sv (15 atoms); emu-mps never needed. Baselines: uniform random bitstrings and a sampler uniform over exactly-K seed sets (analytic), both with the same decode; qubo-solver's default pipeline on model A (S).

## 5. Results (`results/results.csv`, 78 rows)

| tier | valid shots: device / random bits | P(optimum): device (light-multi) / random bits / random K seeds | given a valid shot, device ÷ random K seeds |
|---|---|---|---|
| S | 90–99 % / 40 % | 51–91 % / 25–27 % / 67 % | 0.8–1.5× |
| M | 31–52 % / 11 % | 13–20 % / 1.6–2.9 % / 13–30 % | 1.9–2.8× |
| L | 47–54 % / 2.6 % | 2–32 % / 0–0.2 % / 2.8–4.0 % | 1.4–15× |

Exact decode: P(optimum) M 20–37 %, L 16–44 %; conditional 2.1–6.2×. Best feasible shot equals the proven optimum on every instance (not evidence at these sizes: 120 and 1365 seed sets vs 1000 shots). Honest reading: S is too small to separate device from chance; on M/L the device beats random bitstrings by 3–160×, matches or beats the stricter K-seed sampler on 7 of 12 (instance, decoder) cases unconditionally, and on all of them given a valid shot. The price is the valid-shot rate (31–54 %). Metrics per brief §9.4 (best gap at model and CVRP level, feasibility rate, P(reach) with ε = 10⁻⁶, atoms, η with its formula, reference status) are columns of `results.csv`; relabelled vehicles count as one solution; infeasible shots are never scored.

## 6. What did not work

1. Model A's exact weights are fine on paper and useless on the device: no 2D layout (section 2). Sparsifying the objective (keep each customer's m farthest partners) and an energy-space fit (torch) did not help; the graph is anti-geometric, not merely dense.
2. A candidate-cluster MIS encoding (one atom per compact feasible cluster, blockade = overlap) is also not geometric: 7–12 % of conflicts misclassified by any centroid distance, conflict degree 30–50 vs ≤ 9 blockade neighbours possible. Dropped after measurement.
3. Two scale rules for model B failed before the one above: scaling from the closest pair spreads seeds so far that the exactly-K margin was 0.001 rad/µs; scaling from the K-dispersion radius alone breaks the 5 µm spacing.
4. First δ_f rule (geometric mean of the window) gave ~0 valid shots; the midpoint works.
5. The plain light decode is greedy-order-sensitive (S_seed2: 0.6 % vs 82 % with light-multi); kept in the table.
6. The instance generator's first version let λ* = 0 on 5 of 6 S/M instances: capacity was never binding. Fixed by the binding rule.
7. Tooling: the brief's qubo-solver parameter names do not exist in 0.9.1; pulser's AnalogDevice has no DMM (we copy qoolqit's AnalogDeviceWithDMM for emulation); the 38 µm radius is measured from the coordinate origin, so a layout re-centred after optimisation can be rejected.

## 7. Where AI was used

Everywhere, with checks. Three Claude sessions (builder, auditor, slides) wrote essentially all code, derivation drafts, literature search, figures and slides. The humans decided the task split (A2 → A1 → A3 → A4), wrote the eight-equation understanding document, chose instances per tier, the penalty scheme, the global/DMM variants and the Track A scope, rejected drafts they could not explain, and asked for the seed → join → laser visual. Errors the AI made and what caught them: a factor-2 mismatch in the K = 2 penalty (caught by the expansion self-test on all 16 bitstrings); the λ* = 0 instances (caught by the tuning log); the MIS pivot (killed by measurement and the auditor); a layout re-centred past 38 µm (caught by pulser's validator); the stale qubo-solver API in the brief (caught by reading the installed source); the δ_f rule (caught by the shot histogram). Nothing hardware-related was trusted on plausibility: every register went through `validate_register`, every sequence was built on `AnalogDevice`, every reference was computed twice.
