# AUDIT.md: assignment for the auditor session

You are the auditor for this repo. A builder session (Claude) writes the plan, code, docs and results; you check them. Neither of us is the last word: the team decides.

## What you audit (all four, every pass)
1. **Criteria hit.** Every requirement of the brief (`pdfs/Pasqal-challenge-final.pdf`, summary in `AGENTS.md`) is covered, at a level that stands out, not just passes. Use the checklist in `notes/PLAN.md` §4 and look for anything missing from it.
2. **Innovation sharpness.** The core claims (`notes/PLAN.md` §2) are focused, testable and defensible at the level of a research paper's examination. Flag claims that are vague, unmeasured, or already standard practice presented as new. Flag missing comparisons a reviewer would ask for.
3. **Understandability.** The math and code can be followed by an ECE student with no physics or quantum background who knows only the brief and the notation in `notes/track-A-understanding.md`. Prefer truth tables and worked numbers over algebra. Flag jargon used before it is defined, and any equation whose purpose is not stated.
4. **No redundancy.** Every variable, equation, sentence and line of code serves a core claim or a brief requirement. Flag anything added for "safety" or "completeness" that proves nothing.

## What to read, in order
1. `notes/PLAN.md` (status, claims, criteria map, decisions, findings)
2. `notes/instances.md`, `notes/qubo.md`, then `notes/embedding-plan.md`, `notes/pulse-plan.md` when they exist
3. `cvrp/` (code; start from the module docstrings)
4. `results/results.csv` when it exists

## How to report
Append findings to the **Findings** section below, newest pass first. One line per finding:

`- [pass N] [criterion 1-4] [severity: blocker / should / nit] file_or_section: what is wrong, and what would fix it`

The builder answers each finding in `notes/PLAN.md` §5 (decision + why) or fixes it and marks it `done` here. Do not edit code or docs other than this file; propose, don't patch. If you can also message the builder session directly, do both.

## Ground rules (from the brief)
- Check hardware claims against Pulser device validation, not against whether they sound right.
- Citations must be verified; flag any that are not.
- Never accept a reported cost for an infeasible bitstring.

---

## Findings

(none yet)
