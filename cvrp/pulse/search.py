"""A4: the parameter grid, and how a pulse is scored.

Knobs (model B):  R_b (blockade radius -> Omega = C6/R_b^6) and T, per tier (tuned on seed 0);
                  delta_f multiplier c, per instance.  delta_0 = -max(2 Omega, 5) fixed.
Knobs (model A):  Omega_max as a fraction of the median wanted coupling, and T, per tier;
                  delta_f multiplier c, per instance.
Score (brief 8.2 / 9.4): P(reach reference) first, then best gap, then feasibility rate.
Never the mean energy.
"""
from __future__ import annotations

from dataclasses import asdict

import numpy as np

from ..evaluate import evaluate_shots, random_sampler
from ..hardware import C6, DELTA_MAX, OMEGA_MAX
from .run import run_sequence
from .sequence import PulseParams, build_sequence

TIER_GRID_B = dict(Rb=(7.0, 9.0, 12.0), T=(2000, 4000, 6000))
TIER_GRID_A = dict(omega_frac=(0.25, 0.5, 1.0), T=(2000, 4000, 6000))
INSTANCE_GRID = dict(c=(0.7, 1.0, 1.3, 1.6, 1.9))  # model B: delta_f is a few rad/us, far from the limit
INSTANCE_GRID_A = dict(c=(0.7, 1.0, 1.3))  # model A: delta_f ~ 60 rad/us, 1.9x would exceed 125.66


def score_key(ev: dict):
    """P(reach) first, then feasibility, then best gap (gap is almost always 0 at these sizes)."""
    gap = ev["model_best_gap"]
    return (-round(ev["p_reach_ref"], 2), -ev["feasibility_rate"], np.inf if gap is None else gap)


def run_point(inst, model, coords, params: PulseParams, shots: int, bond_dim: int = 64) -> dict:
    seq = build_sequence(coords, model.labels, params)
    counts, rinfo = run_sequence(seq, shots=shots, bond_dim=bond_dim)
    ev = evaluate_shots(inst, model, counts)
    row = {**asdict(params), **rinfo, **ev}
    row.pop("dmm_weights", None)
    row["variant"] = params.variant
    row["counts"] = counts
    return row


def random_row(inst, model, shots: int, seed: int = 0) -> dict:
    ev = evaluate_shots(inst, model, random_sampler(model, shots, seed))
    return {**ev, "variant": "random", "emulator": "uniform random bitstrings"}


def seed_params(sm, coords, Rb: float, T: int, c: float = 1.0) -> PulseParams:
    omega = min(C6 / Rb ** 6, OMEGA_MAX)
    delta_f = c * sm.delta_nominal(coords)
    return PulseParams(omega_max=omega, duration=T, delta_0=-max(2 * omega, 5.0), delta_f=delta_f)


def qubo_params(q, hmap, omega_frac: float, T: int, c: float = 1.0) -> PulseParams:
    iu = np.triu_indices(q.n_vars, 1)
    wanted = hmap.target_U[iu]
    med = float(np.median(wanted[wanted > 0]))
    omega = min(omega_frac * med, OMEGA_MAX)
    delta_f = float(np.clip(c * hmap.delta_global, -DELTA_MAX, DELTA_MAX))
    return PulseParams(omega_max=omega, duration=T, delta_0=-min(DELTA_MAX, 2 * omega + abs(delta_f)),
                       delta_f=delta_f, delta_dmm=hmap.delta_dmm, dmm_weights=hmap.dmm_weights)
