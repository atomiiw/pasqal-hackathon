# Pasqal Challenge — DuQuantum Hackathon

Challenge brief and pre-reading are in `pdfs/`.

**Task:** Capacitated Vehicle Routing (CVRP), cluster-first / route-second, on Pasqal neutral-atom emulators.
Track A = capacity-feasible clustering. Track B = clustering + per-cluster TSP routing.
Goal: fewest binary variables (1 variable = 1 atom, max 80).

**Device limits (Pulser AnalogDevice):** 80 atoms, min spacing 5 µm, max radius 38 µm,
Ω ≤ 12.57 rad/µs, global detuning ±125.66 rad/µs, sequence ≤ 6000 ns, couplings C6/r⁶ always positive.

**How to help:**
- Explain reasoning so we can defend every line to the judges.
- Check layouts and pulses against the device limits; say when unsure; never invent citations.
- Keep things simple. Only create notes or docs when we ask.
- Never commit credentials.

Environment: Python 3.12 in `.venv` (`.venv\Scripts\activate`).
