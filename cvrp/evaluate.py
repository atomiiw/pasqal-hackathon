"""Turn measured bitstrings into the brief's metrics (9.2, 9.4).

Post-selection: only shots that decode to a valid, capacity-feasible assignment
are ever scored. The feasibility rate says how many were thrown away.
"""
from __future__ import annotations

import numpy as np

from .instances import Instance
from .qubo import QUBO
from .reference import assignment_to_groups, cluster_cost, routed_cost, tsp_subset_cost


def evaluate_shots(inst: Instance, q: QUBO, counts: dict[str, int], eps: float = 1e-6) -> dict:
    """counts: bitstring -> number of shots (bit order = QUBO variable order)."""
    dist = inst.dist_matrix()
    tsp = tsp_subset_cost(dist, inst.depot_dist())
    ref = inst.references
    ref_groups = ref["model_groups"]
    model_opt, cvrp_opt = ref["model_optimum"], ref["cvrp_optimum"]
    total = sum(counts.values())
    n_feas, n_reach = 0, 0
    best_model, best_cvrp, best_groups, best_shot = np.inf, np.inf, None, None
    for bits, c in counts.items():
        x = np.array([int(b) for b in bits])
        if not q.is_feasible(x):
            continue
        a = q.decode(x)
        n_feas += c
        groups = assignment_to_groups(a, inst.K)
        cm = cluster_cost(a, dist)
        if cm <= model_opt * (1 + eps):
            n_reach += c
        if cm < best_model:
            best_model, best_groups, best_shot = cm, groups, bits
            best_cvrp = routed_cost(a, tsp, inst.K)
    out = dict(shots=total, feasibility_rate=n_feas / total if total else 0.0,
               p_reach_ref=n_reach / total if total else 0.0, eps=eps)
    if best_groups is None:
        out.update(model_best_gap=None, cvrp_best_gap=None, best_groups=None, best_shot=None)
    else:
        out.update(model_best_gap=100 * (best_model - model_opt) / model_opt,
                   cvrp_best_gap=100 * (best_cvrp - cvrp_opt) / cvrp_opt,
                   best_groups=best_groups, best_shot=best_shot, best_model_cost=best_model,
                   best_routed_cost=best_cvrp)
    return out


def random_sampler(q: QUBO, shots: int, seed: int = 0) -> dict[str, int]:
    """Uniform random bitstrings: what a sampler that does no work would give."""
    rng = np.random.default_rng(seed)
    X = rng.integers(0, 2, size=(shots, q.n_vars))
    counts: dict[str, int] = {}
    for x in X:
        s = "".join(map(str, x))
        counts[s] = counts.get(s, 0) + 1
    return counts
