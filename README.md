# Capacitated clustering on a neutral-atom emulator (Pasqal challenge, Track A)

Cluster-first step of the CVRP, run as an analog Rydberg program on Pasqal emulators.
Two encodings: the direct QUBO (model A, derived and shown not to be layout-able) and
seed selection (model B, one atom per customer on the scaled customer map, 4 / 10 / 15 atoms).

## Reproduce

```bash
python -m venv .venv && .venv\Scripts\activate        # Windows; use source .venv/bin/activate elsewhere
pip install -r requirements.txt
python -m cvrp.run_all --tier S                        # headline on tier S, about 2 minutes
python -m cvrp.run_all --all                           # S, M, L (L uses emu-sv, ~25 s per run)
```

Outputs: `results/results.csv` (one row per instance × method × seed), `results/runs_log.csv`
(every grid point), `results/layouts/*.json` (atom positions and checks), `instances/*.json`
(seeded instances with certificates and proven reference values).

## Read

| file | what |
|---|---|
| `notes/PLAN.md` | plan, claims, criteria checklist, decisions, what did not work, friction log |
| `notes/instances.md` | the 9 instances, certificates, proven optima (A2) |
| `notes/qubo.md` | model A formulas and weights, hardware mapping, model B (A1) |
| `notes/embedding-plan.md` | atom layout method and results (A3) |
| `notes/pulse-plan.md` | pulse grid and scoring (A4) |
| `notes/track-A-understanding.md` | the problem in eight equations (background) |

## Code map

`cvrp/instances.py` generator + validator · `cvrp/reference.py` exact DP references · `cvrp/qubo.py`, `cvrp/tune.py` model A ·
`cvrp/seeds.py` model B · `cvrp/hardware.py` device limits and mapping · `cvrp/embedding/` layouts ·
`cvrp/pulse/` sequences, emulators, grid · `cvrp/evaluate.py` metrics · `cvrp/run_all.py` everything.

Pinned environment: `requirements.txt`. No credentials anywhere in the repo.
