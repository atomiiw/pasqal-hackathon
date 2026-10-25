"""Reference values (brief 9.3): exact optima by dynamic programming.

Two problems share one engine, a DP over set partitions of the customers
into <= K capacity-feasible groups:
  * model optimum : group weight = sum of pairwise distances inside the group
  * CVRP optimum  : group weight = exact TSP tour length depot -> group -> depot
Both are proven optima for N <= 15. CPLEX is used as the cross-check the
brief asks for (tier S must agree).
"""
from __future__ import annotations

import time
from itertools import product

import numpy as np

from .instances import Instance, subset_loads


# ---------------------------------------------------------------------------
# Per-subset weights
# ---------------------------------------------------------------------------
def _bits_matrix(n: int) -> np.ndarray:
    """bits[mask, i] = 1 if customer i is in mask."""
    masks = np.arange(1 << n)
    return ((masks[:, None] >> np.arange(n)) & 1).astype(np.int64)


def pairwise_subset_cost(dist: np.ndarray) -> np.ndarray:
    """w[mask] = sum of d_ij over pairs i<j inside mask (our clustering objective)."""
    n = len(dist)
    bits = _bits_matrix(n)
    w = np.zeros(1 << n)
    for i in range(n):
        bit = 1 << i
        w[bit:(bit << 1)] = w[:bit] + bits[:bit] @ dist[i]
    return w


def tsp_subset_cost(dist: np.ndarray, depot_dist: np.ndarray) -> np.ndarray:
    """tsp[mask] = exact shortest tour depot -> all customers in mask -> depot.

    Held-Karp: dp[mask, j] = shortest path from depot through mask ending at j.
    """
    n = len(dist)
    INF = np.inf
    dp = np.full((1 << n, n), INF)
    for j in range(n):
        dp[1 << j, j] = depot_dist[j]
    for mask in range(1, 1 << n):
        row = dp[mask]
        if not np.isfinite(row).any():
            continue
        best_to = (row[:, None] + dist).min(axis=0)  # best way to extend to each j
        for j in range(n):
            if not mask >> j & 1:
                m2 = mask | (1 << j)
                if best_to[j] < dp[m2, j]:
                    dp[m2, j] = best_to[j]
    tsp = (dp + depot_dist[None, :]).min(axis=1)
    tsp[0] = 0.0
    return tsp


# ---------------------------------------------------------------------------
# Set-partition DP
# ---------------------------------------------------------------------------
def partition_optimum(weight: np.ndarray, fits: np.ndarray, K: int, n: int,
                      tol: float = 1e-9):
    """Minimise sum of weight[group] over partitions into <= K groups with fits[group].

    g[j][mask] = best value using exactly j groups. The lowest customer in
    `mask` is always put in the newest group, so every unordered partition
    is enumerated exactly once (vehicle relabelings are not double counted).
    Returns (best_value, groups, number_of_optimal_partitions).
    """
    full = (1 << n) - 1
    INF = np.inf
    g = [np.full(1 << n, INF) for _ in range(K + 1)]
    cnt = [np.zeros(1 << n, dtype=np.int64) for _ in range(K + 1)]
    choice = [dict() for _ in range(K + 1)]
    g[0][0], cnt[0][0] = 0.0, 1
    fits_l = fits.tolist()
    weight_l = weight.tolist()
    for j in range(1, K + 1):
        prev, prev_cnt = g[j - 1], cnt[j - 1]
        cur, cur_cnt, ch = g[j], cnt[j], choice[j]
        prev_l = prev.tolist()
        for mask in range(1, 1 << n):
            low = mask & -mask
            rest = mask ^ low
            best, best_cnt, best_s = INF, 0, None
            sub = rest
            while True:
                s = sub | low
                if fits_l[s]:
                    r = mask ^ s
                    pv = prev_l[r]
                    if pv < INF:
                        v = weight_l[s] + pv
                        if v < best - tol:
                            best, best_cnt, best_s = v, int(prev_cnt[r]), s
                        elif abs(v - best) <= tol:
                            best_cnt += int(prev_cnt[r])
                if sub == 0:
                    break
                sub = (sub - 1) & rest
            cur[mask], cur_cnt[mask] = best, best_cnt
            if best_s is not None:
                ch[mask] = best_s
    vals = [g[j][full] for j in range(1, K + 1)]
    best = min(vals)
    n_opt = sum(int(cnt[j][full]) for j in range(1, K + 1) if abs(g[j][full] - best) <= tol)
    j = 1 + int(np.argmin(vals))
    groups, mask = [], full
    while mask:
        s = choice[j][mask]
        groups.append([i for i in range(n) if s >> i & 1])
        mask ^= s
        j -= 1
    return float(best), groups, n_opt


def groups_to_assignment(groups, n: int) -> list:
    a = [None] * n
    for t, grp in enumerate(groups):
        for i in grp:
            a[i] = t
    return a


def assignment_to_groups(assignment, K: int) -> list:
    """Canonical form: list of sorted groups, sorted by first customer; empties dropped."""
    groups = [sorted(i for i, t in enumerate(assignment) if t == k) for k in range(K)]
    return sorted([g for g in groups if g], key=lambda g: g[0])


# ---------------------------------------------------------------------------
# Costs of a given assignment (used for gaps later)
# ---------------------------------------------------------------------------
def cluster_cost(assignment, dist: np.ndarray) -> float:
    a = np.asarray(assignment)
    same = (a[:, None] == a[None, :])
    return float(np.triu(dist * same, 1).sum())


def routed_cost(assignment, tsp: np.ndarray, K: int) -> float:
    """Total length when each group is routed exactly (needs tsp from tsp_subset_cost)."""
    total = 0.0
    for grp in assignment_to_groups(assignment, K):
        mask = sum(1 << i for i in grp)
        total += tsp[mask]
    return float(total)


# ---------------------------------------------------------------------------
# Brute force over all assignments (tiers S, M) as an independent check
# ---------------------------------------------------------------------------
def brute_force_model(inst: Instance, dist: np.ndarray):
    """Enumerate all K^N assignments (M: 59049). Returns (best, groups, n_distinct_optima)."""
    n, K, Q = inst.N, inst.K, inst.Q
    d = np.asarray(inst.demands)
    A = np.array(list(product(range(K), repeat=n)), dtype=np.int8)  # (K^N, n)
    onehot = (A[:, :, None] == np.arange(K)[None, None, :])  # (M, n, K)
    loads = np.einsum("mnk,n->mk", onehot, d)
    feas = (loads <= Q).all(axis=1)
    same = A[:, :, None] == A[:, None, :]
    cost = (same * np.triu(dist, 1)[None]).sum(axis=(1, 2))
    cost[~feas] = np.inf
    best = cost.min()
    opt = {tuple(map(tuple, assignment_to_groups(a, K))) for a in A[np.abs(cost - best) <= 1e-9]}
    groups = [list(g) for g in next(iter(sorted(opt)))]
    return float(best), groups, len(opt)


# ---------------------------------------------------------------------------
# CPLEX cross-check (MILP with linearised products; community edition is enough)
# ---------------------------------------------------------------------------
def cplex_model(inst: Instance, dist: np.ndarray, time_limit: float = 60.0):
    from docplex.mp.model import Model

    n, K, Q = inst.N, inst.K, inst.Q
    m = Model("clustering")
    x = {(i, k): m.binary_var(name=f"x_{i}_{k}") for i in range(n) for k in range(K)}
    y = {(i, j, k): m.continuous_var(lb=0, name=f"y_{i}_{j}_{k}")
         for i in range(n) for j in range(i + 1, n) for k in range(K)}
    for i in range(n):
        m.add_constraint(m.sum(x[i, k] for k in range(K)) == 1)
    for k in range(K):
        m.add_constraint(m.sum(inst.demands[i] * x[i, k] for i in range(n)) <= Q)
    for (i, j, k), v in y.items():
        m.add_constraint(v >= x[i, k] + x[j, k] - 1)
    m.add_constraint(x[0, 0] == 1)  # symmetry breaking
    m.minimize(m.sum(dist[i, j] * y[i, j, k] for (i, j, k) in y))
    m.parameters.timelimit = time_limit
    t0 = time.time()
    sol = m.solve()
    if sol is None:
        raise RuntimeError("CPLEX found no solution")
    assign = [next(k for k in range(K) if sol.get_value(x[i, k]) > 0.5) for i in range(n)]
    status = m.solve_details.status
    return float(sol.objective_value), assignment_to_groups(assign, K), status, time.time() - t0


# ---------------------------------------------------------------------------
# Compute and attach all references to an instance
# ---------------------------------------------------------------------------
def compute_references(inst: Instance, cplex_check: bool = True, verbose: bool = True) -> dict:
    dist = inst.dist_matrix()
    dd = inst.depot_dist()
    n, K, Q = inst.N, inst.K, inst.Q
    fits = subset_loads(inst.demands) <= Q

    t0 = time.time()
    w = pairwise_subset_cost(dist)
    model_best, model_groups, model_nopt = partition_optimum(w, fits, K, n)
    t_model = time.time() - t0

    t0 = time.time()
    tsp = tsp_subset_cost(dist, dd)
    cvrp_best, cvrp_groups, cvrp_nopt = partition_optimum(tsp, fits, K, n)
    t_cvrp = time.time() - t0

    ref = {
        "model_optimum": model_best, "model_groups": model_groups,
        "model_n_optimal": model_nopt, "model_method": "set-partition DP (proven)",
        "model_routed_exactly": routed_cost(groups_to_assignment(model_groups, n), tsp, K),
        "cvrp_optimum": cvrp_best, "cvrp_groups": cvrp_groups,
        "cvrp_tours": [tour_order(grp, dist, dd) for grp in cvrp_groups],
        "cvrp_n_optimal": cvrp_nopt, "cvrp_method": "Held-Karp + set-partition DP (proven)",
        "status": "proven optimum",
        "time_s": {"model_dp": round(t_model, 2), "cvrp_dp": round(t_cvrp, 2)},
    }
    ref["decomposition_gap_pct"] = 100 * (ref["model_routed_exactly"] - cvrp_best) / cvrp_best

    if inst.tier in ("S", "M"):
        bf_best, bf_groups, bf_nopt = brute_force_model(inst, dist)
        assert abs(bf_best - model_best) < 1e-6, (bf_best, model_best)
        assert bf_nopt == model_nopt, (bf_nopt, model_nopt)
        ref["model_bruteforce_agrees"] = True
    if cplex_check:
        try:
            c_best, c_groups, c_status, c_time = cplex_model(inst, dist)
            ref["cplex_model_optimum"] = c_best
            ref["cplex_status"] = str(c_status)
            ref["cplex_time_s"] = round(c_time, 2)
            ref["cplex_agrees"] = abs(c_best - model_best) < 1e-6
        except ImportError as e:
            ref["cplex_status"] = f"not run: {e}"
    inst.references = ref
    if verbose:
        print(f"{inst.name}: model*={model_best:.3f} groups={model_groups} (x{model_nopt}) "
              f"| CVRP*={cvrp_best:.3f} groups={cvrp_groups} (x{cvrp_nopt}) "
              f"| decomp gap={ref['decomposition_gap_pct']:.2f}% "
              f"| cplex={ref.get('cplex_agrees')} | t={t_model:.1f}s+{t_cvrp:.1f}s")
    return ref


def tour_order(group, dist, depot_dist):
    """Best visiting order inside one group (brute force, groups are small)."""
    from itertools import permutations
    best, best_p = np.inf, None
    for p in permutations(group):
        if len(p) > 1 and p[0] > p[-1]:
            continue  # same tour reversed
        c = depot_dist[p[0]] + depot_dist[p[-1]] + sum(dist[p[t], p[t + 1]] for t in range(len(p) - 1))
        if c < best:
            best, best_p = c, list(p)
    return best_p


if __name__ == "__main__":
    import sys
    from .instances import generate_all, INSTANCE_DIR

    tiers = sys.argv[1:] or ["S", "M", "L"]
    for inst in generate_all():
        if inst.tier not in tiers:
            continue
        compute_references(inst)
        inst.save()
