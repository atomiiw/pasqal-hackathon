"""Map our QUBO onto what the device can realise.

Device energy on a bitstring (laser off):
  E_hw(x) = sum_a (-delta_a) x_a + sum_{a<b} C6 / r_ab^6  x_a x_b
We want E_hw = s * Total + const, i.e.
  U_ab = C6 / r_ab^6 = s * b_ab        and      -delta_a = s * a_a
Limits (pulser AnalogDevice): r >= 5 um, radius <= 38 um, |delta| <= 125.66 rad/us,
Omega <= 12.57 rad/us, duration <= 6000 ns, C6 = 865723 rad/us um^6.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from pulser.devices import AnalogDevice

C6 = float(AnalogDevice.interaction_coeff)  # rad/us um^6
R_MIN = float(AnalogDevice.min_atom_distance)  # 5 um
R_MAX = float(AnalogDevice.max_radial_distance)  # 38 um
U_MAX = C6 / R_MIN ** 6  # strongest coupling, ~55.4 rad/us
OMEGA_MAX = float(AnalogDevice.channels["rydberg_global"].max_amp)  # 12.57
DELTA_MAX = float(AnalogDevice.channels["rydberg_global"].max_abs_detuning)  # 125.66
T_MAX = int(AnalogDevice.max_sequence_duration)  # 6000 ns
U_FAR = C6 / (2 * R_MAX) ** 6  # weakest coupling possible inside the register


@dataclass
class HardwareMap:
    s: float  # scale: hardware rad/us per unit of our cost
    delta_global: float  # final global detuning (rad/us)
    dmm_weights: np.ndarray | None  # eps_a in [0,1], None for global-only
    delta_dmm: float  # <= 0, extra detuning for eps_a = 1
    target_U: np.ndarray  # s * B, what the layout must reproduce
    target_delta: np.ndarray  # -s * a per atom (what we would want per atom)

    def delta_per_atom(self) -> np.ndarray:
        if self.dmm_weights is None:
            return np.full(len(self.target_delta), self.delta_global)
        return self.delta_global + self.dmm_weights * self.delta_dmm

    def linear_error(self) -> np.ndarray:
        """realised (-delta_a) minus wanted (s a_a), per atom."""
        return -self.delta_per_atom() + self.target_delta


def scale_bounds(a: np.ndarray, B: np.ndarray, dmm: bool) -> dict:
    """Upper bounds on s from each device limit."""
    b_max = B.max()
    out = {"min_spacing": U_MAX / b_max}
    want = -a  # wanted detuning per atom at s = 1
    if dmm:
        out["detuning_global"] = DELTA_MAX / max(want.max(), 1e-12)
        out["detuning_dmm"] = DELTA_MAX / max(want.max() - want.min(), 1e-12)
    else:
        out["detuning_global"] = DELTA_MAX / max(abs(want.mean()), 1e-12)
    return out


def make_map(a: np.ndarray, B: np.ndarray, dmm: bool, s_factor: float = 1.0) -> HardwareMap:
    """Choose s (largest allowed times s_factor) and the detunings.

    Global-only: one delta for all atoms = -s * mean(a).
    DMM: delta_a = delta_g + eps_a * delta_dmm with delta_dmm <= 0, so the atom
    that wants the largest detuning gets eps = 0 and the others are pulled down.
    """
    bounds = scale_bounds(a, B, dmm)
    s = s_factor * min(bounds.values())
    want = -s * a  # delta_a we would like
    if dmm:
        delta_g = float(want.max())
        delta_dmm = float(-(want.max() - want.min()))
        eps = (want.max() - want) / max(want.max() - want.min(), 1e-12)
        return HardwareMap(s, delta_g, eps, delta_dmm, s * B, want)
    return HardwareMap(s, float(want.mean()), None, 0.0, s * B, want)


def target_distances(target_U: np.ndarray) -> np.ndarray:
    """r*_ab = (C6 / U_ab)^(1/6); inf where U_ab = 0."""
    with np.errstate(divide="ignore"):
        r = (C6 / target_U) ** (1 / 6)
    r[~np.isfinite(r)] = np.inf
    np.fill_diagonal(r, 0.0)
    return r


def couplings(coords: np.ndarray) -> np.ndarray:
    """U_ab = C6 / r_ab^6 for a set of atom coordinates (um)."""
    r = np.linalg.norm(coords[:, None] - coords[None], axis=2)
    with np.errstate(divide="ignore"):
        U = C6 / r ** 6
    np.fill_diagonal(U, 0.0)
    return U
