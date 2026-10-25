"""Pasqal's own embedders on the same target matrix, for comparison.

qoolqit works in dimensionless units where C6 = 1 and distances are in units
of the device's min spacing (5 um). We hand it T / U_MAX (so the strongest
allowed coupling is 1) and multiply the coordinates it returns by 5 um.
"""
from __future__ import annotations

import numpy as np

from ..hardware import U_MAX, R_MIN


def blade(T: np.ndarray, seed: int = 0) -> np.ndarray:
    from qoolqit.embedding import Blade, BladeConfig
    from qoolqit import AnalogDevice as QDevice

    emb = Blade(BladeConfig(device=QDevice()))
    g = emb.embed(T / U_MAX)
    coords = np.array([g.nodes[i]["pos"] if "pos" in g.nodes[i] else g.coords[i] for i in range(len(T))], float)
    return coords * R_MIN


def interaction(T: np.ndarray, seed: int = 0) -> np.ndarray:
    from qoolqit.embedding import InteractionEmbedder, InteractionEmbedderConfig

    emb = InteractionEmbedder(InteractionEmbedderConfig(seed=seed))
    g = emb.embed(T / U_MAX)
    coords = np.array([g.nodes[i]["pos"] if "pos" in g.nodes[i] else g.coords[i] for i in range(len(T))], float)
    return coords * R_MIN


def greedy(T: np.ndarray, seed: int = 0) -> np.ndarray:
    import torch
    from qubosolver.embedding import greedy_layout
    from qubosolver import Instance
    from qoolqit import AnalogDevice as QDevice

    inst = Instance(torch.tensor(T / U_MAX, dtype=torch.float64))
    cfg = greedy_layout.Config.from_device(QDevice())
    out = greedy_layout.embed(inst, config=cfg)
    coords = np.asarray(out if isinstance(out, np.ndarray) else out.coords, float)
    return coords * R_MIN


BASELINES = {"blade": blade, "interaction": interaction, "greedy": greedy}
