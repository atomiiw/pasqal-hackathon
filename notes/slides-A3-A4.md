# Slide content for A3 and A4 (format: one title, one equation, one table or figure)

Figures (real data, regenerate with `python -m cvrp.report_mechanism M_seed0`):
- `notes/figures/mechanism_B_M_seed0.png` — 6 panels: map → atoms → pulse → 1000 shots → decoded shot → optimum
- `notes/figures/mechanism_B_L_seed0.png` — same for L_seed0 (the shot shown appeared 100 times and is the optimum)
- `notes/figures/layouts_B.png` — all 9 layouts

## Slide: A3 Atom layout — the map is the layout

$$r_{ij} = \alpha\, d_{ij}, \qquad \alpha = \frac{R_b}{r_c}, \qquad R_b = \Big(\frac{C_6}{\Omega}\Big)^{1/6}$$

| | S | M | L |
|---|---|---|---|
| atoms | 4 | 10 | 15 |
| $R_b$ (µm) | 7 | 9 | 9 |
| $\alpha$ (µm per map unit) | 0.08–0.14 | 0.12–0.17 | 0.18–0.20 |
| radius after layout (µm) | 6–8 | 10–11 | 14 |
| pulser `validate_register` | pass | pass | pass |

(customers closer than $r_c$ on the map land inside one blockade radius: they cannot both be seeds)

## Slide: A3 Why the direct QUBO cannot be laid out

$$\text{wanted } b_{ij} \uparrow \text{ with } d_{ij} \quad\text{but}\quad U_{ij} = \frac{C_6}{r_{ij}^6} \downarrow \text{ with } r_{ij}$$

| tier | atoms | η | rank of the optimum under realised energies |
|---|---|---|---|
| S | 4 | 0.54–0.62 | 2–8 of 16 |
| M | 30 | 1.0–1.25 | 8 784 / 19 930 / 11 182 of 59 049 |
| L | 60 | 1.0–1.3 | not computable |

## Slide: A4 Pulse — three knobs, grid search

$$\Omega(t): 0 \to \Omega_{\max} \to 0 \quad (10\,\% \text{ rise/fall}), \qquad \delta(t): \delta_0 \to \delta_f = c \cdot \tfrac{1}{2}\big[(U_K - U_{K-1}) + (U_{K+1} - U_K)\big]$$

| knob | grid | scope | selected (S / M / L) |
|---|---|---|---|
| $R_b$ → $\Omega_{\max} = C_6/R_b^6$ | 7, 9, 12 µm | per tier | 7 / 9 / 9 µm (7.36 / 1.63 / 1.63 rad/µs) |
| $T$ | 2000, 4000, 6000 ns | per tier | 4000 / 2000 / 6000 ns |
| $c$ (final detuning) | 0.7, 1.0, 1.3, 1.6, 1.9 | per instance | 1.3–1.9 |
| score | P(reach optimum), then valid-shot rate | | 1000 shots |

## Slide: Results

| | valid shots, device / random bits | P(optimum \| valid), device / random K seeds |
|---|---|---|
| S | 90–99 % / 40 % | 51–98 % / 67 % |
| M | 31–52 % / 11 % | 25–65 % / 13–31 % (1.9–2.8×) |
| L | 47–54 % / 3 % | 4–59 % / 3–4 % (1.4–15×) |

(light-multi decode; exact decode: M 64–70 % → 2.1–2.3×, L 33–82 % → 2.4–6.2×)
