# Pulse (A4)

Shape (fixed): amplitude $0 \to \Omega_{\max}$ (first 10 % of $T$) → hold → $0$ (last 10 %); detuning $\delta_0 < 0$ → linear sweep to $\delta_f$ during the hold. Global channel only for the headline; DMM (emulation) only in model A's labelled variant.

## Is grid search enough? Yes: 2 knobs per tier, 1 per instance.

| knob | set by | grid | scope |
|---|---|---|---|
| $R_b$ → $\Omega_{\max} = C_6 / R_b^6$ (model B) | how far apart two customers must be to both be seeds | 7, 9, 12 µm → 7.36, 1.63, 0.29 rad/µs | per tier (seed 0) |
| $\Omega_{\max}$ as a fraction of the median wanted coupling (model A) | couplings must beat the drive at the end | 0.25, 0.5, 1.0 | per tier (seed 0) |
| $T$ | slower = more adiabatic; device cap 6000 ns | 2000, 4000, 6000 ns | per tier (seed 0) |
| $\delta_f = c \times$ nominal | nominal from the model (B: midpoint of the exactly-$K$ window; A: $-s\,\bar a$) | $c$ = 0.7, 1.0, 1.3 | per instance |
| $\delta_0$ | start far below resonance | $-\max(2\Omega_{\max}, 5)$ (B), $-(2\Omega_{\max} + |\delta_f|)$ (A), capped at 125.66 | fixed |

Score (brief §8.2): P(reach the proven optimum), then best gap, then feasibility rate. Never the mean energy. Shots: 1000.

Emulator by atom count: ≤ 12 pulser-simulation (QuTiP), ≤ 20 emu-sv, > 20 emu-mps (bond dimension recorded). Model B never needs emu-mps.

Tier S, model B (seed 0): $R_b = 7$ µm, $T = 4000$ ns wins (feasibility 99 %, P(reach) 46 %); $R_b = 12$ µm gives $\Omega = 0.29$ rad/µs, too weak to move anything in 6 µs (feasibility ≈ 0). Full grid: `results/runs_log.csv`.

Baselines in the same table: uniform random bitstrings, uniform over exactly-$K$ seed sets (analytic), and qubo-solver's default pipeline on model A.

Code: `cvrp/pulse/sequence.py` (pulser sequence, validated by the device), `cvrp/pulse/run.py` (emulators), `cvrp/pulse/search.py` (grid and score), `cvrp/run_all.py` (selection and `results.csv`).
