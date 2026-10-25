2026-10-25 — Rebuilt 7 slides around the user's A2 → A1 → A3 → A4 storyline; A1/A3 receive 260 of 420 seconds.
Centered cluster/capacity passing-line logic, expanded per-atom/per-pair coefficients, and a green/red QUBO-versus-Pasqal E comparison.
Replaced dark figures with light matplotlib plots: independent functions in charts.py, 300 dpi PNG plus SVG; added a Pulser-valid model B trial layout.
Kept direct QUBO as the documented baseline, model B as under test, logged ranks approximate, proposed pulse grids unexecuted, and performance explicitly MOCK.
Rebuilt PPTX/PDF, seven preview PNGs, contact sheet and Chinese speaker notes; verified seven online slides; ready for auditor polish with no further restyling planned.

## Auditor handoff
Current Google Slides version: https://docs.google.com/presentation/d/1sjMFEckTIL_jstEWymnfuXBOF4c4sS3_8ex2ppPEN18/edit?usp=drivesdk
- Sync only: imported the auditor-polished existing PPTX without rebuilding or restyling. Connector does not support PPTX conversion into an existing native Slides ID.
- CLEANUP PENDING: connector has permanent delete only, no trash operation; neither old deck was deleted. Move both previous deck IDs to trash manually: 1zRsaBK5Vxb3iq2unFv2klAFlNzvb6CVsd2vepoi8cOk and 18T1sd4o_xxR-VfbCionZzlS4qCzPr7jyMBvRrva5L-s.
- Old deck identity verified before cleanup: 18T1sd4o... = Pasqal Track A — 7-Minute Talk [MOCK Performance], 7 slides; 1zRsaBK5... = Pasqal Track A — A2 → A1 → A3 → A4 [MOCK · Auditor Handoff], 7 slides.
- Final new native import verified: Pasqal Track A — Polished Presentation [MOCK Performance], 7 slides; Chinese speaker notes preserved on every slide.
- Local deliverables: `TrackA_7min_MOCK.pptx`, `TrackA_7min_MOCK.pdf`, `preview/Slide1.PNG` through `Slide7.PNG`, `contact_sheet.png`.
- Narrative/layout builder: `build_deck.py`. Figure-only styling: `charts.py` (each figure has its own function; functions accept input data).
- Rebuild: `.venv\Scripts\python.exe -X utf8 presentation/build_deck.py` from repository root. PowerPoint COM was used to export PDF and previews.
- `build_deck_v1.py` preserves the previous builder. Old unused chart assets remain but the new deck embeds only outputs from `charts.py`.
- New figure assets: `01_atom_counts`, `02_certified_instances`, `03_loss_and_expansion`, `04_qubo_vs_pasqal`, `05_requested_atom_distances`, `05_expected_loss`, `06_proposed_pulse`, `07_MOCK_metrics` (each PNG + SVG).

## Evidence and unresolved model status

- Read `notes/PLAN.md` §§2/5/6 and `notes/track-A-understanding.md`. PLAN still documents sparsification; `cvrp/seeds.py` now implements seed-selection model B. Slide 5 explicitly describes B as the next direction under test, not a completed validated pipeline.
- `notes/track-A-understanding.md` contains an older count-based capacity example. Slides use the demand-weighted formulas actually implemented in `cvrp/qubo.py`; the old count penalty is not presented as valid for heterogeneous demands.
- A1 desired behavior is capacity pass/fail, but implemented load balance keeps penalizing uneven feasible loads. Slide 3 says this explicitly; slide 7 retains the saved M_seed2 13.8% pre-quantum objective loss.
- PLAN §6's ≈10^4 rank and η≈1 are approximate log summaries, not newly reproduced experiment rows. 59,049 is all assignment-valid 3^10 states, including capacity-infeasible assignments.
- Actual model B layout example in `seed_layout_example.json`: M_seed0, one optimization restart, Pulser register validation passed, not emulated. It is illustrative geometry, not evidence of optimization quality.
- Fixed 10 rad/µs, 4,000 ns and the detuning grids on slide 6 are proposed starting settings, not measured winners. The plotted direct-baseline candidate was constructed with `cvrp.pulse.sequence.build_sequence` and validated by Pulser.
- Candidate seed detuning window from adjacent excitation sectors needs a full-bitstring cardinality check; speaker notes flag this. Capacity is enforced by the classical decoder, not by seed Hamiltonian penalties.
- `mock_metrics.csv` is unchanged from the prior fixture, explicitly synthetic. It is not seed-model B data and cannot justify performance claims. Plot means/min–max are visual placeholders.
- Conditional expected feasible clustering loss is a definition on slide 5, not a computed curve; feasibility probability P(F) must be reported separately. It is undefined when P(F)=0.

## Verification

- 7 PPTX slides, 7 PDF pages, 7 populated Chinese notes; time allocations sum to 420 seconds.
- No shapes extend beyond the slide bounds. Local slide renders inspected; final slide 5 checked after the consolidated repair.
- Online native Google Slides readback confirms 7 slides and Chinese notes on all 7 slides. Online rendering may differ slightly from PowerPoint; final Google Slides visual polish belongs to the auditor.
