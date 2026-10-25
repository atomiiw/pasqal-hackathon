"""A2: seeded instance generator, feasibility certificate, validator.

Tier table from the brief (N customers, K trucks, capacity Q, demand range).
Depot is fixed at (50, 50). Customers are uniform integer points in [0, 100]^2.
An instance is accepted only if
  (a) a capacity-feasible assignment exists (exact check), and
  (b) rho = D / (K*Q) lies in [RHO_MIN, RHO_MAX], so capacity actually binds.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

import numpy as np

TIERS = {
    "S": dict(N=4, K=2, Q=7, dmin=1, dmax=4),
    "M": dict(N=10, K=3, Q=20, dmin=1, dmax=8),
    "L": dict(N=15, K=4, Q=30, dmin=1, dmax=10),
}
DEPOT = (50.0, 50.0)
RHO_MIN, RHO_MAX = 0.70, 0.95
ROOT = Path(__file__).resolve().parent.parent
INSTANCE_DIR = ROOT / "instances"


@dataclass
class Instance:
    tier: str
    seed: int
    N: int
    K: int
    Q: int
    coords: list  # [[x, y], ...] customers
    demands: list  # [d_i]
    depot: list = field(default_factory=lambda: list(DEPOT))
    certificate: list | None = None  # truck index per customer
    draws: int = 0  # how many random draws were rejected before this one
    references: dict = field(default_factory=dict)

    # --- derived -------------------------------------------------------
    @property
    def D(self) -> int:
        return int(sum(self.demands))

    @property
    def rho(self) -> float:
        return self.D / (self.K * self.Q)

    @property
    def dmax_ratio(self) -> float:
        return max(self.demands) / self.Q

    def dist_matrix(self) -> np.ndarray:
        """Customer-customer Euclidean distances, shape (N, N)."""
        P = np.asarray(self.coords, float)
        return np.linalg.norm(P[:, None] - P[None], axis=2)

    def depot_dist(self) -> np.ndarray:
        P = np.asarray(self.coords, float)
        return np.linalg.norm(P - np.asarray(self.depot), axis=1)

    @property
    def name(self) -> str:
        return f"{self.tier}_seed{self.seed}"

    # --- io ------------------------------------------------------------
    def save(self, path: Path | None = None) -> Path:
        path = path or INSTANCE_DIR / f"{self.name}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=1), encoding="utf-8")
        return path

    @staticmethod
    def load(path: Path) -> "Instance":
        return Instance(**json.loads(Path(path).read_text(encoding="utf-8")))


# ---------------------------------------------------------------------------
# Feasibility: exact bin packing by DP over subsets (N <= 15 -> 2^15 masks).
# ---------------------------------------------------------------------------
def subset_loads(demands) -> np.ndarray:
    """load[mask] = total demand of the customers in `mask`."""
    d = np.asarray(demands, int)
    n = len(d)
    load = np.zeros(1 << n, dtype=np.int64)
    for i in range(n):
        bit = 1 << i
        load[bit:(bit << 1)] = load[:bit] + d[i]
    return load


def first_fit_decreasing(demands, K: int, Q: int) -> list | None:
    """Fast heuristic packing. Returns an assignment or None (None is not a proof)."""
    order = sorted(range(len(demands)), key=lambda i: -demands[i])
    loads = [0] * K
    assign = [None] * len(demands)
    for i in order:
        for t in range(K):
            if loads[t] + demands[i] <= Q:
                loads[t] += demands[i]
                assign[i] = t
                break
        else:
            return None
    return assign


def feasible_assignment(demands, K: int, Q: int) -> list | None:
    """Return a truck index per customer with every load <= Q, or None if impossible.

    Tries first-fit-decreasing first. If that fails, runs an exact DP:
    reach[k][mask] = the customers in `mask` fit in k trucks. Enumerates
    submasks (3^N work), fine for N <= 15 since it rarely runs.
    """
    n = len(demands)
    if n == 0:
        return []
    if max(demands) > Q:
        return None
    ffd = first_fit_decreasing(demands, K, Q)
    if ffd is not None:
        return ffd
    full = (1 << n) - 1
    fits = subset_loads(demands) <= Q  # subsets that fit in one truck
    reach = [np.zeros(1 << n, bool) for _ in range(K + 1)]
    reach[0][0] = True
    choice = {}  # (k, mask) -> submask used as truck k
    used = None
    for k in range(1, K + 1):
        prev, cur = reach[k - 1], reach[k]
        for mask in range(1 << n):
            if prev[mask]:
                cur[mask] = True
                continue
            low = mask & -mask  # the lowest customer goes in the new truck
            rest = mask ^ low
            sub = rest
            while True:
                s = sub | low
                if fits[s] and prev[mask ^ s]:
                    cur[mask] = True
                    choice[(k, mask)] = s
                    break
                if sub == 0:
                    break
                sub = (sub - 1) & rest
        if cur[full]:
            used = k
            break
    if used is None:
        return None
    assign = [None] * n
    mask, k = full, used
    while mask:
        while reach[k - 1][mask]:
            k -= 1
        s = choice[(k, mask)]
        for i in range(n):
            if s >> i & 1:
                assign[i] = k - 1
        mask ^= s
        k -= 1
    return assign


def validate(inst: Instance, assignment) -> tuple[bool, str]:
    """Check a customer->truck assignment against the instance's rules."""
    if assignment is None or len(assignment) != inst.N:
        return False, "assignment length != N"
    a = list(assignment)
    if any((t is None) or t < 0 or t >= inst.K for t in a):
        return False, "truck index out of range"
    loads = [0] * inst.K
    for i, t in enumerate(a):
        loads[t] += inst.demands[i]
    if max(loads) > inst.Q:
        return False, f"overloaded: loads={loads} > Q={inst.Q}"
    if max(inst.demands) > inst.Q:
        return False, "a demand exceeds Q"
    return True, f"ok: loads={loads}"


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------
def capacity_binds(inst: Instance) -> bool:
    """True if the optimum of the clustering objective WITHOUT capacity is overloaded.

    Only such instances test the capacity encoding; on the others lambda = 0 would do.
    """
    from .reference import pairwise_subset_cost, partition_optimum

    w = pairwise_subset_cost(inst.dist_matrix())
    all_fit = np.ones(1 << inst.N, bool)
    _, groups, _ = partition_optimum(w, all_fit, inst.K, inst.N)
    return any(sum(inst.demands[i] for i in g) > inst.Q for g in groups)


def generate(tier: str, seed: int, max_draws: int = 10_000, require_binding: bool = True) -> Instance:
    t = TIERS[tier]
    rng = np.random.default_rng([tier.encode()[0], seed])
    for draw in range(max_draws):
        coords = rng.integers(0, 101, size=(t["N"], 2)).tolist()
        demands = rng.integers(t["dmin"], t["dmax"] + 1, size=t["N"]).tolist()
        D = sum(demands)
        rho = D / (t["K"] * t["Q"])
        if not (RHO_MIN <= rho <= RHO_MAX):
            continue
        cert = feasible_assignment(demands, t["K"], t["Q"])
        if cert is None:
            continue
        inst = Instance(tier, seed, t["N"], t["K"], t["Q"], coords, demands,
                        certificate=cert, draws=draw)
        ok, msg = validate(inst, cert)
        assert ok, msg
        if require_binding and not capacity_binds(inst):
            continue
        return inst
    raise RuntimeError(f"no feasible instance for {tier} seed {seed} in {max_draws} draws")


def generate_all(seeds=(0, 1, 2)) -> list[Instance]:
    return [generate(tier, s) for tier in TIERS for s in seeds]


if __name__ == "__main__":
    for inst in generate_all():
        p = inst.save()
        print(f"{inst.name}: N={inst.N} K={inst.K} Q={inst.Q} demands={inst.demands} "
              f"rho={inst.rho:.3f} dmax/Q={inst.dmax_ratio:.2f} cert={inst.certificate} "
              f"draws={inst.draws} -> {p.name}")
