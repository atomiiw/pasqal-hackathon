# Atom layout (A3)

Goal: positions $r_a$ such that $C_6 / \lVert r_a - r_b\rVert^6 \approx$ the wanted coupling, with $\lVert r_a - r_b\rVert \ge 5$ µm and $\lVert r_a\rVert \le 38$ µm (pulser `AnalogDevice.validate_register` is the judge).

## Model A: fit the couplings

1. Wanted distance per pair: $r^*_{ab} = (C_6 / (s\,b_{ab}))^{1/6}$; $s$ = largest scale allowed by the 5 µm and detuning limits.
2. Start: classical MDS on $r^*$ (pairs with $b = 0$ get a large distance), plus random restarts.
3. Refine: SLSQP on $\sum_{b>0} (\log U_{ab} - \log s\,b_{ab})^2 + \mu \sum_{b=0} (U_{ab}/U_{\min})^2$ under the two device constraints. Log loss = every pair matched in percent terms (our choice; Pasqal's `InteractionEmbedder` uses absolute error, BLaDE a force layout).
4. Report $\eta = \lVert U - s\,b\rVert_F / \lVert s\,b\rVert_F$, the worst pair error, and the **ground-state check**: is the constrained optimum still the lowest realised energy among valid assignments?

Result (the negative result of this project):

| instance | atoms | η | rank of optimum under realised energies |
|---|---|---|---|
| S_seed0 / 1 / 2 | 4 | 0.54 / 0.62 / 0.56 | 8 / 4 / 2 of 16 (global δ) |
| M_seed0 / 1 / 2 | 30 | ≈ 1.0 | ≈ 31 000 / 14 000 / 17 000 of 59 049 valid assignments |

Why: every atom wants $N-1$ same-truck plus $K-1$ same-customer couplings within a factor ≈ 5 of each other; with $U \propto 1/r^6$ all wanted distances fall in 5–7 µm, and a plane offers at most 6 such neighbours. Worse, the graph is anti-geometric (far customers ↔ close atoms). Fitting energies instead of couplings (torch, valid-assignment subspace) and sparsifying the objective (keep each customer's $m$ farthest partners) were both tried and do not change the rank. Pasqal's BLaDE / greedy embedders give the same η on the same matrices.

## Model B: the map is the layout

1. $\alpha = R_b / r_c$ (see `notes/qubo.md` §9); atoms at $\alpha \times$ customer coordinates, centred.
2. Pairs closer than 5.5 µm are floored to 5.5 µm (both customers are blockaded either way).
3. If the map exceeds the 38 µm radius it is compressed by the same optimiser as model A, started from the map, target = floored map couplings.
4. η is reported against the floored map; what matters is checked exactly: does the hardware ground state have $K$ seeds, and what does it decode to.

| instance | atoms | radius before / after | η vs floored map | ground state = optimum? |
|---|---|---|---|---|
| S_seed0 | 4 | 8.4 / 8.4 | 0.23 | no (rank 3 of 6 seed sets), but P(reach) 46 % |
| M_seed0 | 10 | 10.3 / 10.3 | 0.72 | yes (exact decode) |
| L_seed0 | 15 | 13.8 / 13.8 | 0.90 | yes (light decode, rank 1 of 1365) |

η here is large because the floor moves many close pairs, yet the ground state is right: for model B the blockade structure matters, not the exact coupling values.

Code: `cvrp/embedding/ours.py` (optimiser), `cvrp/embedding/fidelity.py` (η, ground-state check), `cvrp/embedding/baselines.py` (qoolqit / qubo-solver embedders), `cvrp/seeds.py` (`SeedModel.layout`). Layouts per instance: `results/layouts/*.json`.
