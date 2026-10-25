# Results (Track A)

Source: `results/results.csv`. Gaps are on feasible shots only; P(reach) counts shots whose decoded clustering equals the proven optimum (ε = 1e-6, relabelings equal). `feas_random_K` / `p_reach_random_K`: a sampler uniform over exactly-K seed sets with the same decode (analytic). 
![summary](figures/results_summary.png)

![layouts](figures/layouts_B.png)

| instance | method | atoms | feasibility_rate | feas_random_K | p_reach_ref | p_reach_random_K | p_reach_ratio_vs_random_K | p_reach_given_feasible | conditional_ratio_vs_random_K | model_best_gap | cvrp_best_gap | eta | gs_rank | emulator | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S_seed0 | B-seeds-light | 4 | 99.0% | 100.0% | 50.7% | 50.0% | 1.0x | 51.2% | 1.0x | 0.0% | 0.0% | 0.23 | 3 | pulser-simulation | headline: light decode, O(N^2 K); same shots for all decoders; seed-model optimum 110.14;  |
| S_seed0 | B-seeds-light-multi | 4 | 99.0% | 100.0% | 50.7% | 66.7% | 0.8x | 51.2% | 0.8x | 0.0% | 0.0% | 0.23 | 3 | pulser-simulation | light decode under 3 fixed item orders, best kept (classical-light, O(3 N^2 K)); same shot |
| S_seed0 | B-seeds-exact | 4 | 99.0% | 100.0% | 50.7% | 66.7% | 0.8x | 51.2% | 0.8x | 0.0% | 0.0% | 0.23 | 3 | pulser-simulation | exact decode = best feasible assignment to the seeds (classical post-processing, GAP); sam |
| S_seed0 | B-random-light | 4 | 39.9% |  | 19.0% |  |  |  |  | 0.0% | 0.0% |  |  | uniform random bitstrings | uniform random bitstrings, same decode |
| S_seed1 | B-seeds-light | 4 | 92.0% | 100.0% | 90.5% | 66.7% | 1.4x | 98.4% | 1.5x | 0.0% | 18.8% | 0.09 | 4 | pulser-simulation | headline: light decode, O(N^2 K); same shots for all decoders; seed-model optimum 122.26;  |
| S_seed1 | B-seeds-light-multi | 4 | 92.0% | 100.0% | 90.5% | 66.7% | 1.4x | 98.4% | 1.5x | 0.0% | 18.8% | 0.09 | 4 | pulser-simulation | light decode under 3 fixed item orders, best kept (classical-light, O(3 N^2 K)); same shot |
| S_seed1 | B-seeds-exact | 4 | 92.0% | 100.0% | 90.5% | 66.7% | 1.4x | 98.4% | 1.5x | 0.0% | 18.8% | 0.09 | 4 | pulser-simulation | exact decode = best feasible assignment to the seeds (classical post-processing, GAP); sam |
| S_seed1 | B-random-light | 4 | 39.9% |  | 25.1% |  |  |  |  | 0.0% | 18.8% |  |  | uniform random bitstrings | uniform random bitstrings, same decode |
| S_seed2 | B-seeds-light | 4 | 89.9% | 100.0% | 0.6% | 33.3% | 0.0x | 0.7% | 0.0x | 0.0% | 0.0% | 0.62 | 5 | pulser-simulation | headline: light decode, O(N^2 K); same shots for all decoders; seed-model optimum 155.43;  |
| S_seed2 | B-seeds-light-multi | 4 | 89.9% | 100.0% | 82.1% | 66.7% | 1.2x | 91.3% | 1.4x | 0.0% | 0.0% | 0.62 | 5 | pulser-simulation | light decode under 3 fixed item orders, best kept (classical-light, O(3 N^2 K)); same shot |
| S_seed2 | B-seeds-exact | 4 | 89.9% | 100.0% | 82.1% | 66.7% | 1.2x | 91.3% | 1.4x | 0.0% | 0.0% | 0.62 | 5 | pulser-simulation | exact decode = best feasible assignment to the seeds (classical post-processing, GAP); sam |
| S_seed2 | B-random-light | 4 | 39.9% |  | 12.3% |  |  |  |  | 0.0% | 0.0% |  |  | uniform random bitstrings | uniform random bitstrings, same decode |
| M_seed0 | B-seeds-light | 10 | 30.5% | 95.8% | 2.9% | 10.0% | 0.3x | 9.5% | 0.9x | 0.0% | 0.0% | 0.72 | 78 | pulser-simulation | headline: light decode, O(N^2 K); same shots for all decoders; seed-model optimum 353.04;  |
| M_seed0 | B-seeds-light-multi | 10 | 30.5% | 98.3% | 19.9% | 30.0% | 0.7x | 65.2% | 2.1x | 0.0% | 0.0% | 0.72 | 37 | pulser-simulation | light decode under 3 fixed item orders, best kept (classical-light, O(3 N^2 K)); same shot |
| M_seed0 | B-seeds-exact | 10 | 30.5% | 100.0% | 19.9% | 30.0% | 0.7x | 65.2% | 2.2x | 0.0% | 0.0% | 0.72 | 37 | pulser-simulation | exact decode = best feasible assignment to the seeds (classical post-processing, GAP); sam |
| M_seed0 | B-random-light | 10 | 10.7% |  | 0.8% |  |  |  |  | 0.0% | 0.0% |  |  | uniform random bitstrings | uniform random bitstrings, same decode |
| M_seed1 | B-seeds-light | 10 | 51.9% | 100.0% | 3.0% | 5.0% | 0.6x | 5.8% | 1.2x | 0.0% | 0.0% | 0.88 | 27 | pulser-simulation | headline: light decode, O(N^2 K); same shots for all decoders; seed-model optimum 489.32;  |
| M_seed1 | B-seeds-light-multi | 10 | 51.9% | 100.0% | 12.9% | 13.3% | 1.0x | 24.9% | 1.9x | 0.0% | 0.0% | 0.88 | 27 | pulser-simulation | light decode under 3 fixed item orders, best kept (classical-light, O(3 N^2 K)); same shot |
| M_seed1 | B-seeds-exact | 10 | 51.9% | 100.0% | 36.5% | 30.0% | 1.2x | 70.3% | 2.3x | 0.0% | 0.0% | 0.88 | 27 | pulser-simulation | exact decode = best feasible assignment to the seeds (classical post-processing, GAP); sam |
| M_seed1 | B-random-light | 10 | 11.2% |  | 0.3% |  |  |  |  | 0.0% | 0.0% |  |  | uniform random bitstrings | uniform random bitstrings, same decode |
| M_seed2 | B-seeds-light | 10 | 40.7% | 100.0% | 10.0% | 8.3% | 1.2x | 24.6% | 2.9x | 0.0% | 2.9% | 0.73 | 69 | pulser-simulation | headline: light decode, O(N^2 K); same shots for all decoders; seed-model optimum 329.21;  |
| M_seed2 | B-seeds-light-multi | 10 | 40.7% | 100.0% | 18.7% | 16.7% | 1.1x | 45.9% | 2.8x | 0.0% | 2.9% | 0.73 | 14 | pulser-simulation | light decode under 3 fixed item orders, best kept (classical-light, O(3 N^2 K)); same shot |
| M_seed2 | B-seeds-exact | 10 | 40.7% | 100.0% | 26.2% | 30.0% | 0.9x | 64.4% | 2.1x | 0.0% | 2.9% | 0.73 | 17 | pulser-simulation | exact decode = best feasible assignment to the seeds (classical post-processing, GAP); sam |
| M_seed2 | B-random-light | 10 | 11.2% |  | 1.1% |  |  |  |  | 0.0% | 2.9% |  |  | uniform random bitstrings | uniform random bitstrings, same decode |
| L_seed0 | B-seeds-light | 15 | 53.7% | 100.0% | 0.5% | 0.1% | 3.4x | 0.9% | 6.4x | 0.0% | 6.8% | 0.90 | 31 | emu-sv | headline: light decode, O(N^2 K); same shots for all decoders; seed-model optimum 475.36;  |
| L_seed0 | B-seeds-light-multi | 15 | 53.7% | 100.0% | 31.6% | 3.9% | 8.1x | 58.8% | 15.2x | 0.0% | 6.8% | 0.90 | 4 | emu-sv | light decode under 3 fixed item orders, best kept (classical-light, O(3 N^2 K)); same shot |
| L_seed0 | B-seeds-exact | 15 | 53.7% | 100.0% | 44.1% | 13.2% | 3.3x | 82.1% | 6.2x | 0.0% | 6.8% | 0.90 | 260 | emu-sv | exact decode = best feasible assignment to the seeds (classical post-processing, GAP); sam |
| L_seed0 | B-random-light | 15 | 2.6% |  | 0.1% |  |  |  |  | 0.0% | 6.8% |  |  | uniform random bitstrings | uniform random bitstrings, same decode |
| L_seed1 | B-seeds-light | 15 | 50.9% | 100.0% | 0.0% | 0.7% | 0.0x | 0.0% | 0.0x | 10.2% | 11.3% | 0.90 | 253 | emu-sv | headline: light decode, O(N^2 K); same shots for all decoders; seed-model optimum 555.51;  |
| L_seed1 | B-seeds-light-multi | 15 | 50.9% | 100.0% | 2.0% | 2.8% | 0.7x | 3.9% | 1.4x | 0.0% | 7.7% | 0.90 | 43 | emu-sv | light decode under 3 fixed item orders, best kept (classical-light, O(3 N^2 K)); same shot |
| L_seed1 | B-seeds-exact | 15 | 50.9% | 100.0% | 33.7% | 14.1% | 2.4x | 66.2% | 4.7x | 0.0% | 7.7% | 0.90 | 24 | emu-sv | exact decode = best feasible assignment to the seeds (classical post-processing, GAP); sam |
| L_seed1 | B-random-light | 15 | 2.6% |  | 0.0% |  |  |  |  | 17.6% | 13.7% |  |  | uniform random bitstrings | uniform random bitstrings, same decode |
| L_seed2 | B-seeds-light | 15 | 46.5% | 100.0% | 3.2% | 2.2% | 1.5x | 6.9% | 3.1x | 0.0% | 3.0% | 0.90 | 279 | emu-sv | headline: light decode, O(N^2 K); same shots for all decoders; seed-model optimum 459.22;  |
| L_seed2 | B-seeds-light-multi | 15 | 46.5% | 100.0% | 6.2% | 4.0% | 1.6x | 13.3% | 3.4x | 0.0% | 3.0% | 0.90 | 259 | emu-sv | light decode under 3 fixed item orders, best kept (classical-light, O(3 N^2 K)); same shot |
| L_seed2 | B-seeds-exact | 15 | 46.5% | 100.0% | 15.5% | 14.1% | 1.1x | 33.3% | 2.4x | 0.0% | 3.0% | 0.90 | 259 | emu-sv | exact decode = best feasible assignment to the seeds (classical post-processing, GAP); sam |
| L_seed2 | B-random-light | 15 | 2.6% |  | 0.0% |  |  |  |  | 5.5% | 5.4% |  |  | uniform random bitstrings | uniform random bitstrings, same decode |
| S_seed0 | A-direct-global | 4 | 5.4% |  | 2.9% |  |  |  |  | 0.0% | 0.0% | 0.54 | 8 | pulser-simulation | penalty loss 0.0% |
| S_seed0 | A-direct-dmm | 4 | 11.5% |  | 3.3% |  |  |  |  | 0.0% | 0.0% | 0.54 | 5 | pulser-simulation | penalty loss 0.0% |
| S_seed1 | A-direct-global | 4 | 90.1% |  | 4.4% |  |  |  |  | 0.0% | 18.8% | 0.62 | 4 | pulser-simulation | penalty loss 0.0% |
| S_seed1 | A-direct-dmm | 4 | 81.5% |  | 13.2% |  |  |  |  | 0.0% | 18.8% | 0.62 | 7 | pulser-simulation | penalty loss 0.0% |
| S_seed2 | A-direct-global | 4 | 95.8% |  | 95.3% |  |  |  |  | 0.0% | 0.0% | 0.56 | 2 | pulser-simulation | penalty loss 0.0% |
| S_seed2 | A-direct-dmm | 4 | 91.4% |  | 90.3% |  |  |  |  | 0.0% | 0.0% | 0.56 | 1 | pulser-simulation | penalty loss 0.0% |
| S_seed0 | A-random | 4 | 25.1% |  | 12.8% |  |  |  |  | 0.0% | 0.0% |  |  | uniform random bitstrings | uniform random bitstrings |
| S_seed0 | A-qubosolver-default | 4 | 0.1% |  | 0.1% |  |  |  |  | 0.0% | 0.0% |  |  | qubo-solver[blade+local_energy_scale] | Pasqal qubo-solver default quantum pipeline (its embedder, its drive, DMM device) |
| S_seed1 | A-random | 4 | 51.1% |  | 14.8% |  |  |  |  | 0.0% | 18.8% |  |  | uniform random bitstrings | uniform random bitstrings |
| S_seed1 | A-qubosolver-default | 4 | 71.0% |  | 0.7% |  |  |  |  | 0.0% | 18.8% |  |  | qubo-solver[blade+local_energy_scale] | Pasqal qubo-solver default quantum pipeline (its embedder, its drive, DMM device) |
| S_seed2 | A-random | 4 | 27.1% |  | 14.8% |  |  |  |  | 0.0% | 0.0% |  |  | uniform random bitstrings | uniform random bitstrings |
| S_seed2 | A-qubosolver-default | 4 | 80.4% |  | 80.3% |  |  |  |  | 0.0% | 0.0% |  |  | qubo-solver[blade+local_energy_scale] | Pasqal qubo-solver default quantum pipeline (its embedder, its drive, DMM device) |
