"""A1: the clustering QUBO per tier.

Notation (same as notes/track-A-understanding.md):
  customers i, j; demands d_i; D = sum d_i; distances d_ij; S_i = sum_{j != i} d_ij
  K trucks, capacity Q.

Tier S (K = 2): one bit per customer, x_i = 1 -> truck 1, x_i = 0 -> truck 2.
  Total = C + lam * P
  C = sum_{i<j} d_ij (1 - x_i - x_j + 2 x_i x_j)        (distance inside each truck)
  P = (sum_i d_i x_i - D/2)^2                            (load balance; window D-Q <= L1 <= Q)
  a_i  = -S_i + lam * d_i (d_i - D)
  b_ij = 2 d_ij + 2 lam d_i d_j
  const = sum_{i<j} d_ij + lam D^2 / 4

Tiers M, L (K >= 3): one-hot x_ik, N*K bits.
  Total = C + A * P_assign + lam * P_cap
  C        = sum_k sum_{i<j} d_ij x_ik x_jk
  P_assign = sum_i (1 - sum_k x_ik)^2
  P_cap    = sum_k (sum_i d_i x_ik - D/K)^2
  a_ik                    = -A + lam * d_i (d_i - 2D/K)
  b_(ik),(jk)  same truck = d_ij + 2 lam d_i d_j
  b_(ik),(il)  same cust. = 2A
  b_(ik),(jl)  otherwise  = 0
  const = N A + lam D^2 / K
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .instances import Instance


@dataclass
class QUBO:
    inst: Instance
    encoding: str  # "onebit" or "onehot"
    lam: float
    A: float
    a: np.ndarray  # linear coefficients, shape (n_vars,)
    B: np.ndarray  # symmetric pair matrix, zero diagonal; pair term = sum_{a<b} B_ab x_a x_b
    const: float
    labels: list = field(default_factory=list)
    pair_kind: np.ndarray | None = None  # 0 none, 1 same truck, 2 same customer

    @property
    def n_vars(self) -> int:
        return len(self.a)

    # --- energies ---------------------------------------------------------
    def energy(self, x) -> float:
        x = np.asarray(x, float)
        return float(self.const + self.a @ x + 0.5 * x @ self.B @ x)

    def energies(self, X) -> np.ndarray:
        X = np.asarray(X, float)
        return self.const + X @ self.a + 0.5 * np.einsum("ma,ab,mb->m", X, self.B, X)

    # --- decoding ---------------------------------------------------------
    def decode(self, x) -> list | None:
        """Bitstring -> truck index per customer, or None if not a valid assignment."""
        x = np.asarray(x, int)
        if self.encoding == "onebit":
            return [0 if v == 1 else 1 for v in x]
        X = x.reshape(self.inst.N, self.inst.K)
        if not (X.sum(axis=1) == 1).all():
            return None
        return X.argmax(axis=1).tolist()

    def encode(self, assignment) -> np.ndarray:
        if self.encoding == "onebit":
            return np.array([1 if t == 0 else 0 for t in assignment], int)
        X = np.zeros((self.inst.N, self.inst.K), int)
        X[np.arange(self.inst.N), assignment] = 1
        return X.ravel()

    def is_feasible(self, x) -> bool:
        a = self.decode(x)
        if a is None:
            return False
        loads = np.bincount(a, weights=self.inst.demands, minlength=self.inst.K)
        return bool((loads <= self.inst.Q).all())

    # --- the original (un-expanded) cost, for the self-test ---------------
    def cost_original(self, x) -> float:
        inst, dist, d = self.inst, self.inst.dist_matrix(), np.asarray(self.inst.demands, float)
        x = np.asarray(x, float)
        if self.encoding == "onebit":
            same = 1 - x[:, None] - x[None, :] + 2 * np.outer(x, x)
            C = np.triu(dist * same, 1).sum()
            P = (d @ x - d.sum() / 2) ** 2
            return float(C + self.lam * P)
        X = x.reshape(inst.N, inst.K)
        C = sum(np.triu(dist * np.outer(X[:, k], X[:, k]), 1).sum() for k in range(inst.K))
        Pa = ((1 - X.sum(axis=1)) ** 2).sum()
        Pc = ((d @ X - d.sum() / inst.K) ** 2).sum()
        return float(C + self.A * Pa + self.lam * Pc)

    def self_test(self, n_random: int = 20000, seed: int = 0) -> float:
        rng = np.random.default_rng(seed)
        if self.n_vars <= 16:
            X = ((np.arange(1 << self.n_vars)[:, None] >> np.arange(self.n_vars)) & 1)
        else:
            X = rng.integers(0, 2, size=(n_random, self.n_vars))
        err = max(abs(self.energy(x) - self.cost_original(x)) for x in X)
        assert err < 1e-6, f"expansion mismatch: {err}"
        return err

    def summary(self) -> dict:
        kinds = self.pair_kind
        out = dict(encoding=self.encoding, n_vars=self.n_vars, lam=self.lam, A=self.A,
                   a_min=float(self.a.min()), a_max=float(self.a.max()),
                   b_max=float(self.B.max()), const=self.const)
        if kinds is not None:
            iu = np.triu_indices(self.n_vars, 1)
            out["pairs_same_truck"] = int((kinds[iu] == 1).sum())
            out["pairs_same_customer"] = int((kinds[iu] == 2).sum())
            out["pairs_zero"] = int((kinds[iu] == 0).sum())
        return out


# ---------------------------------------------------------------------------
def build_qubo(inst: Instance, lam: float, A: float = 0.0) -> QUBO:
    dist = inst.dist_matrix()
    d = np.asarray(inst.demands, float)
    D = d.sum()
    N, K = inst.N, inst.K
    S = dist.sum(axis=1)

    if K == 2:
        a = -S + lam * d * (d - D)
        B = 2 * dist + 2 * lam * np.outer(d, d)
        np.fill_diagonal(B, 0.0)
        const = np.triu(dist, 1).sum() + lam * D ** 2 / 4
        labels = [f"x{i}" for i in range(N)]
        kind = np.ones((N, N), int)
        np.fill_diagonal(kind, 0)
        return QUBO(inst, "onebit", lam, 0.0, a, B, float(const), labels, kind)

    n = N * K
    idx = lambda i, k: i * K + k  # noqa: E731
    a = np.zeros(n)
    B = np.zeros((n, n))
    kind = np.zeros((n, n), int)
    for i in range(N):
        for k in range(K):
            a[idx(i, k)] = -A + lam * d[i] * (d[i] - 2 * D / K)
    for k in range(K):
        for i in range(N):
            for j in range(i + 1, N):
                v = dist[i, j] + 2 * lam * d[i] * d[j]
                B[idx(i, k), idx(j, k)] = B[idx(j, k), idx(i, k)] = v
                kind[idx(i, k), idx(j, k)] = kind[idx(j, k), idx(i, k)] = 1
    for i in range(N):
        for k in range(K):
            for l in range(k + 1, K):
                B[idx(i, k), idx(i, l)] = B[idx(i, l), idx(i, k)] = 2 * A
                kind[idx(i, k), idx(i, l)] = kind[idx(i, l), idx(i, k)] = 2
    const = N * A + lam * D ** 2 / K
    labels = [f"x{i},{k}" for i in range(N) for k in range(K)]
    return QUBO(inst, "onehot", lam, A, a, B, float(const), labels, kind)


def variable_count_table() -> list[dict]:
    """Derive 4.1 table rows."""
    from .instances import TIERS
    rows = []
    for t, s in TIERS.items():
        N, K, Q = s["N"], s["K"], s["Q"]
        slack_bits = int(np.ceil(np.log2(Q + 1)))
        rows.append(dict(tier=t, onehot=N * K, slack=K * slack_bits, onehot_plus_slack=N * K + K * slack_bits,
                         ours=N if K == 2 else N * K))
    return rows
