"""Classical solvers for the QUBO: brute force, exact MILP (CPLEX), SA / tabu (qubo-solver).

Used for (1) tuning penalty weights, (2) model references of the penalized QUBO,
(3) the ground-state-preserved check of realized hardware energies.
"""
from __future__ import annotations

import time

import numpy as np

from .qubo import QUBO


def brute_force_min(a: np.ndarray, B: np.ndarray, const: float = 0.0):
    n = len(a)
    assert n <= 20
    X = ((np.arange(1 << n)[:, None] >> np.arange(n)) & 1).astype(float)
    E = const + X @ a + 0.5 * np.einsum("ma,ab,mb->m", X, B, X)
    i = int(E.argmin())
    return float(E[i]), X[i].astype(int), E


def milp_min(a: np.ndarray, B: np.ndarray, const: float = 0.0, time_limit: float = 120.0,
             symmetry_fix: tuple | None = None):
    """Exact minimum of const + a.x + sum_{i<j} B_ij x_i x_j with all B_ij >= 0.

    Linearised: y_ij >= x_i + x_j - 1, y >= 0, minimise sum B_ij y_ij.
    Only pairs with B_ij > 0 get a y variable (keeps us under the CPLEX
    community limits of 1000 variables / 1000 constraints).
    """
    from docplex.mp.model import Model

    n = len(a)
    assert (B >= -1e-12).all(), "MILP linearisation needs non-negative couplings"
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n) if B[i, j] > 1e-12]
    m = Model("qubo")
    x = [m.binary_var(name=f"x{i}") for i in range(n)]
    y = {p: m.continuous_var(lb=0, name=f"y{p[0]}_{p[1]}") for p in pairs}
    for (i, j), v in y.items():
        m.add_constraint(v >= x[i] + x[j] - 1)
    if symmetry_fix is not None:
        var, val = symmetry_fix
        m.add_constraint(x[var] == val)
    m.minimize(m.sum(float(a[i]) * x[i] for i in range(n)) + m.sum(float(B[i, j]) * y[i, j] for (i, j) in pairs))
    m.parameters.timelimit = time_limit
    t0 = time.time()
    sol = m.solve()
    if sol is None:
        raise RuntimeError("CPLEX found no solution")
    xs = np.array([int(round(sol.get_value(v))) for v in x])
    info = dict(status=str(m.solve_details.status), time_s=round(time.time() - t0, 2),
                n_vars=n + len(pairs), n_cons=len(pairs) + (symmetry_fix is not None))
    return float(const + sol.objective_value), xs, info


def exact_min(q: QUBO, time_limit: float = 120.0):
    """Exact QUBO minimiser: brute force when small, CPLEX MILP otherwise."""
    if q.n_vars <= 16:
        e, x, _ = brute_force_min(q.a, q.B, q.const)
        return e, x, dict(status="brute force")
    return milp_min(q.a, q.B, q.const, time_limit)


def qubo_solver_classical(q: QUBO, algorithm: str = "simulated_annealing", **kw):
    """Run Pasqal's qubo-solver classical algorithms on our QUBO (for the SA/tabu baselines).

    qubo-solver's cost is x^T Q x (off-diagonals counted twice), so Q_ij = B_ij / 2.
    """
    import torch
    from qubosolver import Instance, Solver, SolverConfig, ClassicalSolvingConfig

    Qm = 0.5 * q.B.copy()
    np.fill_diagonal(Qm, q.a)
    inst = Instance(torch.tensor(Qm, dtype=torch.float64))
    cfg = SolverConfig(solving=ClassicalSolvingConfig(algorithm=algorithm, **kw),
                       preprocessing=False, postprocessing=False)
    sol = Solver(inst, cfg).solve()
    x = np.asarray(sol.bitstrings[0].tolist(), int)
    return float(q.energy(x)), x, sol


def simulated_annealing(q: QUBO, starts: int = 20, max_iter: int = 2000, initial_temp: float = 5.0,
                        final_temp: float = 1e-3, seed: int = 0):
    """qubo-solver SA with explicit parameters (reported in results)."""
    import torch
    from qubosolver import Instance
    from qubosolver.solving.classical import simulated_annealing as sa

    Qm = 0.5 * q.B.copy()
    np.fill_diagonal(Qm, q.a)
    inst = Instance(torch.tensor(Qm, dtype=torch.float64))
    rng = np.random.default_rng(seed)
    sol = sa.solve(inst, starts=starts, max_iter=max_iter, initial_temp=initial_temp,
                   final_temp=final_temp, rng=rng)
    x = np.asarray(sol.bitstrings[0].tolist(), int)
    params = dict(starts=starts, max_iter=max_iter, sa_initial_temp=initial_temp, sa_final_temp=final_temp,
                  sa_alpha=(final_temp / initial_temp) ** (1 / (max_iter - 1)), seed=seed)
    return float(q.energy(x)), x, params
