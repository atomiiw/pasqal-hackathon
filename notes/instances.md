# Instances (A2)

Depot (50, 50). Coordinates: uniform integers in [0,100]². Demands: uniform in the tier range. Accepted only if (a) an exact packing exists, (b) ρ = D/(K·Q) ∈ [0.7, 0.95], (c) capacity binds: the optimum of the clustering objective without the capacity rule is overloaded, so every instance actually tests the capacity encoding. RNG: `numpy.random.default_rng([ord(tier), seed])`.

Reference method: set-partition DP (proven optimum). TSP per group: Held-Karp (exact). Cross-checks: brute force over all assignments (S, M) and CPLEX MILP (all tiers). Vehicle relabelings count as one solution.

Customers are labelled A, B, …; the depot is 0 in tours.

![maps](figures/instances_map.png)

## Tier S: N=4, K=2, Q=7, demands 1..4

| seed | coords (A, B, …) | demands | ρ | d_max/Q | certificate (truck per customer) | optimal clustering (model) | model cost | CVRP optimum (tours) | CVRP length | #opt (model / CVRP) | CPLEX agrees | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | (82,70) (32,40) (14,53) (72,42) | [4, 3, 2, 4] | 0.929 | 0.57 | [0, 0, 1, 1] | {A,C} / {B,D} | 110.14 | 0→A→C→0 / 0→B→D→0 | 228.00 | 1 / 1 | True | proven optimum |
| 1 | (77,0) (91,54) (40,95) (50,50) | [2, 1, 4, 4] | 0.786 | 0.57 | [0, 0, 0, 1] | {A,D} / {B,C} | 122.26 | 0→A→B→C→0 / 0→D→0 | 224.14 | 1 / 1 | True | proven optimum |
| 2 | (96,55) (39,5) (11,92) (46,15) | [1, 4, 3, 4] | 0.857 | 0.57 | [1, 0, 0, 1] | {A,D} / {B,C} | 155.43 | 0→A→D→0 / 0→B→C→0 | 340.56 | 1 / 1 | True | proven optimum |

## Tier M: N=10, K=3, Q=20, demands 1..8

| seed | coords (A, B, …) | demands | ρ | d_max/Q | certificate (truck per customer) | optimal clustering (model) | model cost | CVRP optimum (tours) | CVRP length | #opt (model / CVRP) | CPLEX agrees | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | (6,79) (64,55) (80,24) (87,33) (97,32) (36,39) (32,80) (18,9) (92,37) (21,79) | [6, 7, 6, 5, 8, 2, 7, 3, 6, 7] | 0.950 | 0.40 | [1, 0, 2, 0, 0, 2, 1, 2, 2, 1] | {A,G,J} / {B,C,F,H} / {D,E,I} | 353.04 | 0→A→J→G→0 / 0→B→C→H→F→0 / 0→D→E→I→0 | 381.86 | 1 / 1 | True | proven optimum |
| 1 | (16,13) (50,16) (22,56) (23,26) (87,28) (6,95) (58,91) (83,88) (77,90) (100,30) | [4, 7, 8, 6, 4, 5, 7, 7, 3, 1] | 0.867 | 0.40 | [2, 0, 0, 1, 2, 0, 1, 1, 2, 2] | {A,B,D} / {C,F,G} / {E,H,I,J} | 489.32 | 0→B→A→D→0 / 0→C→F→G→0 / 0→E→J→H→I→0 | 454.96 | 1 / 1 | True | proven optimum |
| 2 | (89,51) (79,89) (62,10) (47,91) (93,13) (87,47) (36,90) (49,1) (51,76) (35,94) | [4, 6, 1, 8, 4, 7, 6, 3, 3, 5] | 0.783 | 0.40 | [1, 1, 2, 0, 1, 0, 1, 2, 2, 0] | {A,B,F,I} / {C,E,H} / {D,G,J} | 329.21 | 0→A→F→E→C→H→0 / 0→B→I→0 / 0→D→J→G→0 | 379.45 | 1 / 1 | True | proven optimum |

## Tier L: N=15, K=4, Q=30, demands 1..10

| seed | coords (A, B, …) | demands | ρ | d_max/Q | certificate (truck per customer) | optimal clustering (model) | model cost | CVRP optimum (tours) | CVRP length | #opt (model / CVRP) | CPLEX agrees | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | (31,60) (90,97) (93,15) (38,26) (84,28) (18,23) (37,59) (76,35) (48,7) (67,92) (45,13) (63,93) (60,54) (57,30) (22,28) | [9, 4, 10, 2, 5, 6, 1, 9, 7, 2, 5, 10, 1, 9, 10] | 0.750 | 0.33 | [1, 2, 0, 1, 2, 2, 1, 1, 2, 2, 2, 0, 2, 1, 0] | {A,G,M,N} / {B,J,L} / {C,E,H} / {D,F,I,K,O} | 475.36 | 0→G→A→L→J→B→M→0 / 0→C→E→H→0 / 0→D→K→I→F→O→0 / 0→N→0 | 437.32 | 1 / 1 | True | proven optimum |
| 1 | (21,4) (6,70) (6,86) (87,48) (65,51) (62,88) (33,14) (34,73) (11,70) (64,16) (46,30) (67,57) (59,2) (64,6) (79,10) | [8, 7, 9, 2, 9, 10, 3, 8, 8, 1, 9, 2, 7, 4, 6] | 0.775 | 0.33 | [1, 2, 0, 0, 0, 0, 3, 1, 2, 1, 1, 2, 2, 1, 2] | {A,G,H,K} / {B,C,I} / {D,E,F,L} / {J,M,N,O} | 534.58 | 0→A→G→K→0 / 0→C→B→I→0 / 0→E→D→O→N→M→J→0 / 0→H→F→L→0 | 491.89 | 1 / 1 | True | proven optimum |
| 2 | (11,12) (24,6) (56,5) (94,31) (42,4) (82,75) (23,21) (76,21) (48,15) (25,53) (49,73) (53,48) (53,65) (88,36) (21,28) | [9, 6, 3, 8, 9, 2, 7, 4, 9, 3, 9, 3, 4, 5, 9] | 0.750 | 0.30 | [0, 2, 0, 1, 0, 2, 2, 1, 0, 2, 1, 2, 2, 2, 1] | {A,G,J,O} / {B,C,E,I} / {D,H,N} / {F,K,L,M} | 459.22 | 0→G→A→O→J→0 / 0→B→E→C→I→0 / 0→F→N→D→H→L→0 / 0→K→M→0 | 449.91 | 1 / 1 | True | proven optimum |

## Decomposition gap (model optimum routed exactly vs CVRP optimum)

| instance | model optimum routed exactly | CVRP optimum | gap |
|---|---|---|---|
| L_seed0 | 466.99 | 437.32 | 6.78% |
| L_seed1 | 529.82 | 491.89 | 7.71% |
| L_seed2 | 463.48 | 449.91 | 3.02% |
| M_seed0 | 381.86 | 381.86 | 0.00% |
| M_seed1 | 454.96 | 454.96 | 0.00% |
| M_seed2 | 390.45 | 379.45 | 2.90% |
| S_seed0 | 228.00 | 228.00 | 0.00% |
| S_seed1 | 266.38 | 224.14 | 18.84% |
| S_seed2 | 340.56 | 340.56 | 0.00% |

Instance files: `instances/<tier>_seed<n>.json` (coords, demands, certificate, references). Regenerate with `python -m cvrp.instances && python -m cvrp.reference`.
