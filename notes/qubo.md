# The model (A1)

Notation: customers $i, j$ (A, B, …), demands $d_i$, $D = \sum_i d_i$, distances $d_{ij}$, $S_i = \sum_{j \ne i} d_{ij}$, trucks $k = 1..K$, capacity $Q$, load $L_k$ = total demand on truck $k$.

## 0. The CVRP, formally (Derive 2.1)

| | |
|---|---|
| sets | customers $\{1..N\}$, trucks $\{1..K\}$, depot 0 |
| parameters | $d_i$, $Q$, distances between all locations |
| decision | which truck serves each customer; the visiting order per truck |
| objective | total distance of all tours |
| **equality** | every customer on exactly one truck |
| **inequality** | $L_k \le Q$ for every truck |

Track A keeps the assignment and replaces "tour length" by "distance inside each truck".

## 1. Total loss

$$\text{Total} = C + A\,P_{\text{assign}} + \lambda\,P_{\text{cap}}$$

| part | job | lowest value |
|---|---|---|
| $C$ | customers sharing a truck are close | optimise |
| $P_{\text{assign}}$ | each customer on exactly one truck | must be 0 |
| $P_{\text{cap}}$ | loads balanced, so none exceeds $Q$ | small enough (see §4) |

## 2. Cluster function

$$C = \sum_k \sum_{i<j} d_{ij}\,[\,i \text{ and } j \text{ on truck } k\,]$$

## 3. Capacity function (same for every tier)

$$P_{\text{cap}} = \sum_{k=1}^{K} \Big(L_k - \frac{D}{K}\Big)^2$$

No slack bits. It pushes every load toward the average $D/K$. On valid assignments $\sum_k L_k = D$ is fixed, so this equals $\sum_k L_k^2 + \text{const}$: the penalty is "balance the loads", whatever target is written. Overloading one truck unbalances the loads, so it is penalised; but so is any uneven feasible split (the **penalty loss**, measured in §6).

| loads (K = 2, D = 13, Q = 7) | $P_{\text{cap}}$ | feasible? |
|---|---|---|
| 7 / 6 | 0.5 | ✅ |
| 8 / 5 | 4.5 | ❌ |
| 9 / 4 | 12.5 | ❌ |
| 13 / 0 | 84.5 | ❌ |

## 4. Expanded form: one number per atom, one per atom pair

$$\text{Total} = \text{const} + \sum_a a_a\,x_a + \sum_{a<b} b_{ab}\,x_a x_b$$

**Tier S (K = 2): one bit per customer, $x_i = 1$ → truck 1, $x_i = 0$ → truck 2. $N$ atoms.**

| | formula |
|---|---|
| $C$ | $\sum_{i<j} d_{ij}\,(1 - x_i - x_j + 2x_ix_j)$ |
| $P_{\text{cap}}$ | $2\,(\sum_i d_i x_i - D/2)^2$ |
| per atom $a_i$ | $-S_i + 2\lambda\,d_i\,(d_i - D)$ |
| per pair $b_{ij}$ | $2d_{ij} + 4\lambda\,d_i d_j$ |
| const | $\sum_{i<j} d_{ij} + \lambda D^2/2$ |

**Tiers M, L (K ≥ 3): one-hot $x_{ik} = 1$ → customer $i$ on truck $k$. $N \cdot K$ atoms.**

| | formula |
|---|---|
| $C$ | $\sum_k \sum_{i<j} d_{ij}\,x_{ik}x_{jk}$ |
| $P_{\text{assign}}$ | $\sum_i (1 - \sum_k x_{ik})^2$ |
| $P_{\text{cap}}$ | $\sum_k (\sum_i d_i x_{ik} - D/K)^2$ |
| per atom $a_{ik}$ | $-A + \lambda\,d_i\,(d_i - 2D/K)$ |
| per pair, same truck $(ik),(jk)$ | $d_{ij} + 2\lambda\,d_i d_j$ |
| per pair, same customer $(ik),(il)$ | $2A$ |
| per pair, otherwise | $0$ |
| const | $NA + \lambda D^2/K$ |

Check (truth table, one-hot, one customer, K = 3): $P_{\text{assign}}$ term $= 1 - \sum_k x_{ik} + 2\sum_{k<l} x_{ik}x_{il}$

| $x_{i1}x_{i2}x_{i3}$ | trucks chosen | $(1-\sum)^2$ | expanded |
|---|---|---|---|
| 000 | 0 | 1 | 1 − 0 + 0 = 1 |
| 100 | 1 | 0 | 1 − 1 + 0 = 0 |
| 110 | 2 | 1 | 1 − 2 + 2 = 1 |
| 111 | 3 | 4 | 1 − 3 + 6 = 4 |

Code check: `QUBO.self_test()` compares the expanded energy with the original definition on all 16 bitstrings (S) or 20 000 random bitstrings (M, L). Max difference < 1e-6 on every instance.

## 5. What the register minimises (Derive 3.1), and the mapping

Laser off ($\Omega = 0$), bitstring $x$:

$$E_{\text{Pasqal}}(x) = \sum_a (-\delta_a)\,x_a + \sum_{a<b} \frac{C_6}{r_{ab}^6}\,x_a x_b$$

| term | we control through | limit |
|---|---|---|
| $-\delta_a$ | laser detuning; **one value for all atoms** (DMM in emulation: $\delta_a = \delta_g + \varepsilon_a \delta_{\text{DMM}}$, $\delta_{\text{DMM}} \le 0$) | $|\delta| \le 125.66$ rad/µs |
| $C_6 / r_{ab}^6$ | atom positions; always $> 0$ | $r \ge 5$ µm → $\le 55.4$ rad/µs; radius $\le 38$ µm |
| $C_6$, the $1/r^6$ law, the sign | nothing | fixed |

Mapping: choose a scale $s$ and ask for $C_6/r_{ab}^6 = s\,b_{ab}$ and $-\delta_a = s\,a_a$.

| wanted | hardware | match? |
|---|---|---|
| $s\,b_{ab} > 0$ | $C_6/r_{ab}^6 > 0$ | approximate (A3 measures it) |
| $b_{ab} = 0$ (one-hot, different customer and truck) | $> 0$ | **the real error** |
| $s\,a_a$, different per customer | one $\delta$ | **irrelevant on valid assignments** for one-hot: each customer has exactly one bit on, so $\sum_a a_a x_a = \sum_i a_i$ is the same constant for every valid assignment. Only invalid strings feel the mismatch. DMM fixes it exactly in emulation. |

$s$ is the largest value allowed by the limits: $s \le 55.4 / \max b$, $|{-s\,\bar a}| \le 125.66$ (global), $s(\max a - \min a) \le 125.66$ (DMM).

## 6. Weights

* $\lambda^*$ = smallest $\lambda$ such that the exact minimiser of $C + \lambda P_{\text{cap}}$ over valid assignments has every $L_k \le Q$ (set-partition DP, exact).
* $A^*$ = smallest $A$ such that the exact minimiser of the full QUBO over all bitstrings is a valid assignment (brute force on S, CPLEX on M, L).
* Used: $1.1\,\lambda^*$, $1.1\,A^*$.
* **Penalty loss** = cost of the QUBO's exact minimiser − constrained optimum. It is zero only when the balanced split is also the best split.

| instance | atoms | λ | A | QUBO minimiser feasible | cost of QUBO minimiser | constrained optimum | penalty loss | $a$ range | $\max b$ |
|---|---|---|---|---|---|---|---|---|---|
| S_seed0 | 4 | 16.007 | 0.0 | True | 110.14 | 110.14 | 0.0% | [-1311, -856] | 1084 |
| S_seed1 | 4 | 1.868 | 0.0 | True | 122.26 | 122.26 | 0.0% | [-318, -200] | 264 |
| S_seed2 | 4 | 9.261 | 0.0 | True | 155.43 | 155.43 | 0.0% | [-772, -436] | 627 |
| M_seed0 | 30 | 1.274 | 159.4 | True | 353.04 | 353.04 | 0.0% | [-465, -251] | 319 |
| M_seed1 | 30 | 1.084 | 241.4 | True | 492.61 | 489.32 | 0.7% | [-473, -278] | 483 |
| M_seed2 | 30 | 1.447 | 129.3 | True | 374.60 | 329.21 | 13.8% | [-399, -173] | 259 |
| L_seed0 | 60 | 0.063 | 113.2 | True | 475.36 | 475.36 | 0.0% | [-135, -116] | 226 |
| L_seed1 | 60 | 1.394 | 192.4 | True | 577.22 | 534.58 | 8.0% | [-701, -256] | 385 |
| L_seed2 | 60 | 0.014 | 151.8 | True | 459.22 | 459.22 | 0.0% | [-156, -153] | 304 |

## 7. Variable count (Derive 4.1)

| encoding | S | M | L | fits in 80 atoms? |
|---|---|---|---|---|
| assignment variables only (one-hot N·K), no constraints | 8 | 30 | 60 | yes |
| + binary-encoded slack, K·⌈log₂(Q+1)⌉ bits | 14 | 45 | 80 | L uses all 80 |
| **ours** (1 bit/customer for K = 2, one-hot otherwise, no slack) | **4** | **30** | **60** | yes |

## 8. Scale and detunings per instance (rad/µs)

| instance | $s$ (global) | $\delta$ global | $s$ (DMM) | $\delta_g$ | $\delta_{\text{DMM}}$ | binding limit |
|---|---|---|---|---|---|---|
| S_seed0 | 0.0511 | 57.9 | 0.0511 | 67.0 | -23.3 | min_spacing |
| S_seed1 | 0.2101 | 55.1 | 0.2101 | 66.8 | -24.9 | min_spacing |
| S_seed2 | 0.0883 | 60.3 | 0.0883 | 68.2 | -29.7 | min_spacing |
| M_seed0 | 0.1738 | 67.8 | 0.1738 | 80.8 | -37.2 | min_spacing |
| M_seed1 | 0.1147 | 46.2 | 0.1147 | 54.2 | -22.3 | min_spacing |
| M_seed2 | 0.2142 | 65.3 | 0.2142 | 85.5 | -48.4 | min_spacing |
| L_seed0 | 0.2447 | 31.1 | 0.2447 | 33.1 | -4.7 | min_spacing |
| L_seed1 | 0.1440 | 76.1 | 0.1440 | 100.9 | -64.1 | min_spacing |
| L_seed2 | 0.1825 | 28.3 | 0.1825 | 28.5 | -0.6 | min_spacing |

## 9. Why model A cannot be laid out, and model B

Model A's couplings are **large between far-apart customers** (they must not share a truck). Large coupling = close atoms. So far customers need close atoms and near customers need far atoms: the coupling graph is the opposite of the map, and for N ≥ 6 no 2D layout reproduces it (measured: η ≈ 1, optimum ranked ≈ 10⁴ of 59049 valid assignments on every M instance; see `notes/embedding-plan.md`).

**Model B changes what the model asks for** (brief §4.1: "Some avoid the inequality altogether by changing what the model asks for").

| | model A (direct) | model B (seeds) |
|---|---|---|
| bit | $x_{ik}$: customer $i$ on truck $k$ | $x_i$: customer $i$ is a **seed** (anchors one truck) |
| atoms | $N$ (K = 2) or $N\cdot K$ | $N$: **4 / 10 / 15** |
| atom position | fitted to couplings | **the customer map**, scaled by $\alpha$ |
| energy | $\text{const} + \sum a_a x_a + \sum b_{ab} x_a x_b$ | $-\delta \sum_i x_i + \sum_{i<j} \dfrac{C_6}{(\alpha d_{ij})^6}\, x_i x_j$ |
| what the ground state is | best clustering, if the layout were exact | the $K$ seeds that are **most spread out** |
| capacity | penalty $\lambda P_{\text{cap}}$ in the energy | **in the decode**: each non-seed joins the nearest group with room; shots that do not decode are infeasible |
| equality (one truck per customer) | penalty $A P_{\text{assign}}$ | automatic |
| price | penalty loss, unembeddable couplings | feasibility rate < 100 %; the clustering cost is optimised only through which seeds are chosen |

**Two numbers set everything, from geometry only (no solver):**

| | formula | meaning |
|---|---|---|
| $r_c$ | between $r_K$ and $r_{K+1}$, where $r_j$ = largest $r$ such that $j$ customers are pairwise $\ge r$ apart | customers closer than $r_c$ cannot both be seeds |
| $\alpha$ | $R_b / r_c$, with $R_b = (C_6/\Omega)^{1/6}$ the blockade radius | map scale: $r_c$ lands on the blockade radius |
| $\delta_f$ | midpoint of $[\,U_K - U_{K-1},\ U_{K+1} - U_K\,]$, $U_j$ = smallest pair-energy sum over $j$-subsets | exactly $K$ seeds is the ground state, with the largest margin |

Pairs that would land under 5 µm are floored at 5.5 µm (they are blockaded either way). Truth table for one shot (K = 2, customers A..D, Q = 7, demands 1, 4, 3, 4):

| shot | seeds | decode (light) | loads | feasible? |
|---|---|---|---|---|
| 1001 | A, D | B→D? 4+4 = 8 > 7 → B→A; C→A? 1+4+3 = 8 → C→D | {A,B} 5, {C,D} 7 | ✅ |
| 0110 | B, C | A→C, D→? B 4+4 = 8, C 3+1+4 = 8 | – | ❌ (discarded) |
| 1000 | A | one seed only | – | ❌ (discarded) |

Two decoders, both reported on the same shots: **light** = above, $O(N^2 K)$, the headline; **exact** = cheapest capacity-feasible assignment of the non-seeds to the given seeds (a small generalised assignment problem, classical post-processing, labelled as such).

**Fair baseline.** A sampler uniform over exactly-$K$ seed sets reaches the optimum with probability (#seed sets whose decode is optimal) / $\binom{N}{K}$, computed exactly; results report the device's P(reach) next to it and their ratio. A best gap of 0 % alone is not evidence at these sizes ($\binom{10}{3} = 120$, $\binom{15}{4} = 1365$ seed sets vs 1000 shots).

Regenerate: `python -m cvrp.tune && python -m cvrp.report_qubo`.
