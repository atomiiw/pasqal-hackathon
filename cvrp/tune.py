"""Penalty-weight tuning: the smallest weights whose exact minimiser is feasible.

lam : smallest value such that the minimiser of  C + lam*P_cap  over VALID
      assignments has every load <= Q. (Valid-assignment search is a DP over
      set partitions; the penalty is additive over groups.)
A   : smallest value such that the exact minimiser of the full QUBO over ALL
      bitstrings is a valid assignment (brute force on S, CPLEX MILP on M/L).
Both are searched geometrically then refined by bisection, and multiplied by
a small safety margin.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .classical import exact_min
from .instances import Instance, subset_loads, INSTANCE_DIR
from .qubo import build_qubo
from .reference import pairwise_subset_cost, partition_optimum

MARGIN = 1.1
WEIGHTS_FILE = INSTANCE_DIR / "weights.json"


def penalised_valid_optimum(inst: Instance, lam: float):
    """Minimise C + lam * sum_k (L_k - D/K)^2 over valid assignments (loads unconstrained)."""
    dist = inst.dist_matrix()
    n, K = inst.N, inst.K
    D = sum(inst.demands)
    load = subset_loads(inst.demands)
    w = pairwise_subset_cost(dist) + lam * (load - D / K) ** 2
    all_fit = np.ones(1 << n, bool)  # no capacity filter here, that is the point
    # groups fewer than K: each unused truck costs lam*(D/K)^2; add it via K separate runs
    best, best_groups = np.inf, None
    for j in range(1, K + 1):
        val, groups, _ = partition_optimum(w, all_fit, j, n)
        val += (K - j) * lam * (D / K) ** 2
        if val < best - 1e-9 and len(groups) == j:
            best, best_groups = val, groups
    return best, best_groups


def loads_ok(inst: Instance, groups) -> bool:
    return all(sum(inst.demands[i] for i in g) <= inst.Q for g in groups)


def _search(pred, lo_guess: float, factor: float = 1.5, bisect_steps: int = 12):
    """Smallest x (approximately) with pred(x) True; pred assumed monotone."""
    x = lo_guess
    if pred(x):
        while x > 1e-6 and pred(x / factor):
            x /= factor
        lo, hi = x / factor, x
    else:
        while not pred(x):
            x *= factor
            if x > 1e9:
                raise RuntimeError("no feasible weight found")
        lo, hi = x / factor, x
    for _ in range(bisect_steps):
        mid = (lo + hi) / 2
        if pred(mid):
            hi = mid
        else:
            lo = mid
    return hi


def tune_lambda(inst: Instance) -> float:
    dist = inst.dist_matrix()
    lo_guess = dist.max() / (max(inst.demands) ** 2)
    return _search(lambda l: loads_ok(inst, penalised_valid_optimum(inst, l)[1]), lo_guess)


def tune_A(inst: Instance, lam: float) -> float:
    if inst.K == 2:
        return 0.0
    dist = inst.dist_matrix()

    def ok(A):
        q = build_qubo(inst, lam, A)
        _, x, _ = exact_min(q, time_limit=60)
        return q.decode(x) is not None

    return _search(ok, dist.sum(axis=1).max(), factor=1.5, bisect_steps=8)


def tune(inst: Instance, verbose=True) -> dict:
    lam = MARGIN * tune_lambda(inst)
    A = MARGIN * tune_A(inst, lam) if inst.K > 2 else 0.0
    q = build_qubo(inst, lam, A)
    q.self_test()
    e, x, info = exact_min(q, time_limit=120)
    assign = q.decode(x)
    groups_ref = inst.references["model_groups"]
    from .reference import assignment_to_groups, cluster_cost
    groups = assignment_to_groups(assign, inst.K) if assign else None
    model_cost = cluster_cost(assign, inst.dist_matrix()) if assign else None
    out = dict(qubo_min=e, feasible=q.is_feasible(x), groups=groups,
               model_cost=model_cost, model_optimum=inst.references["model_optimum"],
               matches_model_optimum=(groups == groups_ref), solver=info.get("status"))
    out.update(q.summary())
    if verbose:
        print(f"{inst.name}: lam={lam:.4f} A={A:.2f} | QUBO min feasible={out['feasible']} "
              f"groups={groups} cost={model_cost} vs model*={inst.references['model_optimum']:.2f} "
              f"match={out['matches_model_optimum']} | a in [{out['a_min']:.1f},{out['a_max']:.1f}] b_max={out['b_max']:.1f}")
    return out


def load_weights() -> dict:
    return json.loads(WEIGHTS_FILE.read_text()) if WEIGHTS_FILE.exists() else {}


if __name__ == "__main__":
    import sys
    tiers = sys.argv[1:] or ["S", "M", "L"]
    weights = load_weights()
    for p in sorted(INSTANCE_DIR.glob("*.json")):
        if p.name == "weights.json":
            continue
        inst = Instance.load(p)
        if inst.tier in tiers:
            weights[inst.name] = tune(inst)
    WEIGHTS_FILE.write_text(json.dumps(weights, indent=1))
