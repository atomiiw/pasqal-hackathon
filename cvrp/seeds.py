"""Model B: seed selection. One atom per customer, placed on the (scaled) customer map.

  x_i = 1  <=>  customer i is a seed (the anchor of one truck).  N atoms, no slack.

Hardware energy (laser off):  E(x) = -delta * sum_i x_i + sum_{i<j} C6 / r_ij^6  x_i x_j
with r_ij ~ alpha * d_ij. Two close customers cannot both be seeds (blockade), and
among K-seed sets the most spread-out one has the lowest energy.

Decoding a shot: exactly K seeds, then every other customer joins the nearest seed
that still has room (capacity-aware nearest-seed, O(N K log N)). Capacity is never
penalised in the energy: shots whose decode fails are infeasible and discarded.

What is classical here: the scale alpha (so that K seeds fit under the blockade),
the decode, and the scoring. The combinatorial choice of the seed set is the
quantum part; its value is measured against uniform random seed sets.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

import numpy as np

from .hardware import C6, R_MIN, R_MAX, couplings
from .instances import Instance
from .reference import assignment_to_groups, cluster_cost


def assign_light(inst: Instance, seeds, dist: np.ndarray):
    """Light decode, O(N K): non-seeds in decreasing demand (big items first, as in bin
    packing), each to the nearest seed that still has room. None if someone does not fit."""
    seeds = list(seeds)
    loads = [inst.demands[s] for s in seeds]
    a = [None] * inst.N
    for t, s in enumerate(seeds):
        a[s] = t
    rest = sorted((i for i in range(inst.N) if a[i] is None), key=lambda i: -inst.demands[i])
    for i in rest:
        for t in np.argsort([dist[i, s] for s in seeds]):
            if loads[t] + inst.demands[i] <= inst.Q:
                loads[t] += inst.demands[i]
                a[i] = int(t)
                break
        else:
            return None
    return a


def assign_exact(inst: Instance, seeds, dist: np.ndarray):
    """Exact decode: the cheapest capacity-feasible assignment of the non-seeds to the
    seeds (clustering cost). Brute force over K^(N-K) when small, CPLEX MILP otherwise."""
    from itertools import product

    seeds = list(seeds)
    K = len(seeds)
    rest = [i for i in range(inst.N) if i not in seeds]
    d = np.asarray(inst.demands)
    if K ** len(rest) <= 300_000:
        best, best_a = np.inf, None
        base = np.zeros(inst.N, int)
        for s_idx, s in enumerate(seeds):
            base[s] = s_idx
        choices = np.array(list(product(range(K), repeat=len(rest))), dtype=np.int8)  # (M, N-K)
        A = np.tile(base, (len(choices), 1))
        A[:, rest] = choices
        loads = np.zeros((len(choices), K))
        for t in range(K):
            loads[:, t] = ((A == t) * d).sum(axis=1)
        ok = (loads <= inst.Q).all(axis=1)
        if not ok.any():
            return None
        same = A[ok][:, :, None] == A[ok][:, None, :]
        cost = (same * np.triu(dist, 1)[None]).sum(axis=(1, 2))
        return A[ok][int(np.argmin(cost))].tolist()
    from docplex.mp.model import Model

    m = Model("gap")
    x = {(i, t): m.binary_var(name=f"x{i}_{t}") for i in rest for t in range(K)}
    pairs = [(i, j) for i in range(inst.N) for j in range(i + 1, inst.N)]
    y = {}
    for (i, j) in pairs:
        for t in range(K):
            xi = 1 if i == seeds[t] else (x[i, t] if i in rest else 0)
            xj = 1 if j == seeds[t] else (x[j, t] if j in rest else 0)
            if isinstance(xi, int) and isinstance(xj, int):
                continue
            v = m.continuous_var(lb=0, name=f"y{i}_{j}_{t}")
            m.add_constraint(v >= xi + xj - 1)
            y[(i, j, t)] = v
    for i in rest:
        m.add_constraint(m.sum(x[i, t] for t in range(K)) == 1)
    for t in range(K):
        m.add_constraint(inst.demands[seeds[t]] + m.sum(inst.demands[i] * x[i, t] for i in rest) <= inst.Q)
    m.minimize(m.sum(dist[i, j] * v for (i, j, t), v in y.items()))
    m.parameters.timelimit = 60
    sol = m.solve()
    if sol is None:
        return None
    a = [None] * inst.N
    for t, s in enumerate(seeds):
        a[s] = t
    for i in rest:
        a[i] = next(t for t in range(K) if sol.get_value(x[i, t]) > 0.5)
    return a


DECODERS = {"light": assign_light, "exact": assign_exact}


def dispersion_radius(dist: np.ndarray, K: int) -> float:
    """Largest r such that K customers exist with all pairwise distances >= r."""
    n = len(dist)
    return max(min(dist[i, j] for i, j in combinations(S, 2)) for S in combinations(range(n), K))


def dispersion_radius_plus(dist: np.ndarray, K: int) -> float:
    """Same for K+1 customers (0 if K+1 > N)."""
    n = len(dist)
    if K + 1 > n:
        return 0.0
    return dispersion_radius(dist, K + 1)


@dataclass
class SeedModel:
    inst: Instance
    blockade_radius: float  # um; the Rb the pulse will use (set by Omega)
    decoder: str = "light"  # "light" (O(NK) nearest-fit) or "exact" (best feasible assignment)
    encoding: str = "seeds"
    lam: float = 0.0
    A: float = 0.0
    alpha: float = field(init=False)  # um per map unit
    coords0: np.ndarray = field(init=False)  # atoms exactly on the scaled map (may break device limits)

    def __post_init__(self):
        inst = self.inst
        dist = inst.dist_matrix()
        rK = dispersion_radius(dist, inst.K)
        rK1 = dispersion_radius_plus(dist, inst.K)
        # Blockade threshold on the map: customers closer than r_c cannot both be seeds.
        # K seeds pairwise >= r_c exist iff r_c <= rK; K+1 do not iff r_c > rK1.
        self.r_c = float(0.5 * (rK + rK1)) if rK1 > 0 else float(rK)
        self.alpha = float(self.blockade_radius / self.r_c)  # um per map unit: r_c maps to Rb
        P = np.asarray(inst.coords, float) * self.alpha
        self.coords0 = P - P.mean(axis=0)
        # target distances: scaled map, floored at 5.5 um (pairs under the floor are blockaded anyway)
        rstar = np.maximum(np.linalg.norm(P[:, None] - P[None], axis=2), R_MIN + 0.5)
        np.fill_diagonal(rstar, np.inf)
        self.target_U = C6 / rstar ** 6
        self._cache: dict = {}

    def layout(self, restarts: int = 6, seed: int = 0):
        """Device-legal atom positions reproducing target_U as closely as possible, starting from the map."""
        from .embedding.ours import embed, is_legal

        if is_legal(self.coords0) and np.allclose(couplings(self.coords0), self.target_U):
            return self.coords0.copy(), {"loss": 0.0, "distorted": False}
        X, info = embed(self.target_U, restarts=restarts, seed=seed, x0=self.coords0)
        info["distorted"] = True
        return X, info

    # --- interface shared with QUBO (used by evaluate.py) ---------------------
    @property
    def n_vars(self) -> int:
        return self.inst.N

    @property
    def labels(self):
        return [f"s{i}" for i in range(self.inst.N)]

    def decode(self, x):
        x = np.asarray(x, int)
        seeds = np.flatnonzero(x)
        if len(seeds) != self.inst.K:
            return None
        key = tuple(seeds)
        if key not in self._cache:
            self._cache[key] = DECODERS[self.decoder](self.inst, seeds, self.inst.dist_matrix())
        return self._cache[key]

    def is_feasible(self, x) -> bool:
        return self.decode(x) is not None

    def encode(self, seeds) -> np.ndarray:
        x = np.zeros(self.inst.N, int)
        x[list(seeds)] = 1
        return x

    # --- energies -------------------------------------------------------------
    def hardware_energies(self, X, coords: np.ndarray, delta: float) -> np.ndarray:
        X = np.asarray(X, float)
        U = couplings(coords)
        return -delta * X.sum(axis=1) + 0.5 * np.einsum("ma,ab,mb->m", X, U, X)

    # --- exact classical references for this model -----------------------------
    def brute_force(self, coords: np.ndarray | None = None, delta: float | None = None) -> dict:
        """Over all K-subsets: clustering cost after decoding (model optimum, proven),
        and how the hardware energy on `coords` ranks them."""
        inst = self.inst
        dist = inst.dist_matrix()
        subsets = list(combinations(range(inst.N), inst.K))
        X = np.array([self.encode(s) for s in subsets])
        costs = np.full(len(subsets), np.inf)
        for m, s in enumerate(subsets):
            a = self.decode(self.encode(s))
            if a is not None:
                costs[m] = cluster_cost(a, dist)
        feas = np.isfinite(costs)
        best = int(np.argmin(costs))
        n_opt_sets = int((np.abs(costs - costs[best]) < 1e-9).sum())
        out = dict(n_seed_sets=len(subsets), n_feasible=int(feas.sum()), n_optimal_seed_sets=n_opt_sets,
                   model_optimum=float(costs[best]),
                   model_groups=assignment_to_groups(self.decode(self.encode(subsets[best])), inst.K),
                   model_seeds=list(subsets[best]), decoder=self.decoder)
        if coords is not None:
            E = self.hardware_energies(X, coords, delta or 0.0)
            order = np.argsort(E)
            out["rank_of_model_optimum"] = int(np.where(order == best)[0][0]) + 1
            gs = int(order[0])
            out["hardware_ground_state_seeds"] = list(subsets[gs])
            out["hardware_ground_state_feasible"] = bool(feas[gs])
            out["hardware_ground_state_cost"] = float(costs[gs]) if feas[gs] else None
            # does the K-seed ground state beat all other excitation numbers? (full 2^N check)
            allX = ((np.arange(1 << inst.N)[:, None] >> np.arange(inst.N)) & 1)
            Eall = self.hardware_energies(allX, coords, delta or 0.0)
            out["ground_state_has_K_seeds"] = bool(allX[int(np.argmin(Eall))].sum() == inst.K)
        return out

    def delta_window(self, coords: np.ndarray) -> tuple[float, float]:
        """Range of final detuning for which the lowest-energy state has exactly K seeds.
        U_j = smallest pair-sum among j-subsets; need U_K - U_{K-1} < delta < U_{K+1} - U_K."""
        inst = self.inst
        U = couplings(coords)

        def umin(j):
            if j == 0:
                return 0.0
            return min(sum(U[a, b] for a, b in combinations(S, 2)) for S in combinations(range(inst.N), j))

        uk = umin(inst.K)
        lo = uk - umin(inst.K - 1)
        hi = (umin(inst.K + 1) - uk) if inst.K + 1 <= inst.N else np.inf
        return float(lo), float(hi)

    def delta_nominal(self, coords: np.ndarray) -> float:
        """Midpoint of the window: the K-seed states sit farthest below both K-1 and K+1."""
        lo, hi = self.delta_window(coords)
        if not np.isfinite(hi):
            return max(2 * lo, 1.0)
        return 0.5 * (max(lo, 0.0) + hi)
