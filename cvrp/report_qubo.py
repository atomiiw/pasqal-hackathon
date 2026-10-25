"""Render notes/qubo.md: the A1 model, with numbers taken from the code."""
from __future__ import annotations

import json

import numpy as np

from .hardware import make_map, scale_bounds, U_MAX, DELTA_MAX, C6
from .instances import Instance, INSTANCE_DIR, ROOT
from .qubo import build_qubo, variable_count_table
from .tune import WEIGHTS_FILE

HEAD = r"""# The model (A1)

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
"""


MODEL_B = r"""
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

Three decoders, all reported on the same shots: **light** = above, $O(N^2 K)$; **light-multi** = light under 3 fixed item orders (demand descending, ascending, distance to nearest seed), best kept, $O(3N^2K)$, the headline; **exact** = cheapest capacity-feasible assignment of the non-seeds to the given seeds (a small generalised assignment problem, classical post-processing, labelled as such).

**Fair baseline.** A sampler uniform over exactly-$K$ seed sets reaches the optimum with probability (#seed sets whose decode is optimal) / $\binom{N}{K}$, computed exactly; results report the device's P(reach) next to it and their ratio. A best gap of 0 % alone is not evidence at these sizes ($\binom{10}{3} = 120$, $\binom{15}{4} = 1365$ seed sets vs 1000 shots).
"""


def weights_table(insts, weights):
    rows = ["| instance | atoms | λ | A | QUBO minimiser feasible | cost of QUBO minimiser | constrained optimum | penalty loss | $a$ range | $\\max b$ |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for inst in insts:
        w = weights.get(inst.name)
        if not w:
            rows.append(f"| {inst.name} | | (not tuned yet) | | | | | | | |")
            continue
        loss = 100 * (w["model_cost"] - w["model_optimum"]) / w["model_optimum"] if w["model_cost"] else float("nan")
        rows.append(f"| {inst.name} | {w['n_vars']} | {w['lam']:.3f} | {w['A']:.1f} | {w['feasible']} | {w['model_cost']:.2f} "
                    f"| {w['model_optimum']:.2f} | {loss:.1f}% | [{w['a_min']:.0f}, {w['a_max']:.0f}] | {w['b_max']:.0f} |")
    return "\n".join(rows)


def hardware_table(insts, weights):
    rows = ["| instance | $s$ (global) | $\\delta$ global | $s$ (DMM) | $\\delta_g$ | $\\delta_{\\text{DMM}}$ | binding limit |",
            "|---|---|---|---|---|---|---|"]
    for inst in insts:
        w = weights.get(inst.name)
        if not w:
            continue
        q = build_qubo(inst, w["lam"], w["A"])
        g = make_map(q.a, q.B, dmm=False)
        m = make_map(q.a, q.B, dmm=True)
        bounds = scale_bounds(q.a, q.B, dmm=True)
        rows.append(f"| {inst.name} | {g.s:.4f} | {g.delta_global:.1f} | {m.s:.4f} | {m.delta_global:.1f} | {m.delta_dmm:.1f} "
                    f"| {min(bounds, key=bounds.get)} |")
    return "\n".join(rows)


def vc_table():
    rows = ["| encoding | S | M | L | fits in 80 atoms? |", "|---|---|---|---|---|"]
    t = {r["tier"]: r for r in variable_count_table()}
    rows.append(f"| assignment variables only (one-hot N·K), no constraints | {t['S']['onehot']} | {t['M']['onehot']} | {t['L']['onehot']} | yes |")
    rows.append(f"| + binary-encoded slack, K·⌈log₂(Q+1)⌉ bits | {t['S']['onehot_plus_slack']} | {t['M']['onehot_plus_slack']} | {t['L']['onehot_plus_slack']} | L uses all 80 |")
    rows.append(f"| **ours** (1 bit/customer for K = 2, one-hot otherwise, no slack) | **{t['S']['ours']}** | **{t['M']['ours']}** | **{t['L']['ours']}** | yes |")
    return "\n".join(rows)


def main():
    insts = [Instance.load(p) for p in sorted(INSTANCE_DIR.glob("*_seed*.json"))]
    order = {"S": 0, "M": 1, "L": 2}
    insts.sort(key=lambda i: (order[i.tier], i.seed))
    weights = json.loads(WEIGHTS_FILE.read_text()) if WEIGHTS_FILE.exists() else {}
    doc = HEAD
    doc += "\n" + weights_table(insts, weights) + "\n"
    doc += "\n## 7. Variable count (Derive 4.1)\n\n" + vc_table() + "\n"
    doc += "\n## 8. Scale and detunings per instance (rad/µs)\n\n" + hardware_table(insts, weights) + "\n"
    doc += MODEL_B
    doc += "\nRegenerate: `python -m cvrp.tune && python -m cvrp.report_qubo`.\n"
    out = ROOT / "notes" / "qubo.md"
    out.write_text(doc, encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
