"""How far the realised couplings are from the wanted ones, and whether it matters."""
from __future__ import annotations

import numpy as np
from pulser import Register
from pulser.devices import AnalogDevice

from ..hardware import couplings


def validate_layout(coords: np.ndarray, labels=None) -> str:
    """Raise if pulser rejects the register; return 'ok' otherwise."""
    labels = labels or [str(i) for i in range(len(coords))]
    reg = Register({l: tuple(map(float, c)) for l, c in zip(labels, coords)})
    AnalogDevice.validate_register(reg)
    return "ok"


def fidelity(coords: np.ndarray, T: np.ndarray) -> dict:
    """eta = ||U - T||_F / ||T||_F over pairs; plus worst relative error on wanted pairs
    and the largest unwanted coupling (pairs with T = 0) relative to the smallest wanted one."""
    U = couplings(coords)
    iu = np.triu_indices(len(T), 1)
    u, t = U[iu], T[iu]
    want = t > 0
    eta = float(np.linalg.norm(u - t) / np.linalg.norm(t))
    rel = np.abs(u[want] - t[want]) / t[want]
    out = dict(eta=eta, worst_rel_err=float(rel.max()), median_rel_err=float(np.median(rel)),
               min_dist=float(np.min(np.linalg.norm(coords[iu[0]] - coords[iu[1]], axis=1))),
               max_radius=float(np.linalg.norm(coords, axis=1).max()))
    if (~want).any():
        out["max_unwanted_over_min_wanted"] = float(u[~want].max() / t[want].min())
    return out


def realised_qubo(coords: np.ndarray, delta_per_atom: np.ndarray):
    """The QUBO the hardware actually implements: a_hw = -delta_a, B_hw = C6/r^6."""
    return -delta_per_atom, couplings(coords)


def ground_state_preserved(q, coords, hmap, valid_only_states=None) -> dict:
    """Is the constrained optimum still the lowest realised energy among valid assignments?

    valid_only_states: array of bitstrings to compare (S: all 16; M: all valid assignments).
    Returns the rank of the model optimum under the realised energies.
    """
    a_hw, B_hw = realised_qubo(coords, hmap.delta_per_atom())
    X = np.asarray(valid_only_states, float)
    E = X @ a_hw + 0.5 * np.einsum("ma,ab,mb->m", X, B_hw, X)
    E_model = q.energies(X)
    order = np.argsort(E)
    best_model = int(np.argmin(E_model))
    rank = int(np.where(order == best_model)[0][0]) + 1
    return dict(rank_of_model_optimum=rank, realised_argmin=X[order[0]].astype(int).tolist(),
                preserved=(rank == 1))
