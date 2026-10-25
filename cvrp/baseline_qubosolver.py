"""Pasqal's qubo-solver on our model-A QUBO, default quantum pipeline (its own embedder + drive)."""
from __future__ import annotations

import numpy as np


def run_qubosolver(q, shots: int = 1000, embedding: str = "blade", drive: str = "local_energy_scale"):
    """Returns (counts, info). qubo-solver's cost is x^T Q x, so Q_ij = B_ij / 2 off-diagonal."""
    import torch
    from qubosolver import Instance, Solver, SolverConfig, QuantumSolvingConfig, EmbeddingConfig, DriveShapingConfig
    from qubosolver import LocalEmulator

    Qm = 0.5 * q.B.copy()
    np.fill_diagonal(Qm, q.a)
    inst = Instance(torch.tensor(Qm, dtype=torch.float64))
    cfg = SolverConfig(solving=QuantumSolvingConfig(embedding=EmbeddingConfig(algorithm=embedding),
                                                    drive_shaping=DriveShapingConfig(algorithm=drive),
                                                    backend=LocalEmulator(num_shots=shots)),
                       preprocessing=False, postprocessing=False)
    sol = Solver(inst, cfg).solve()
    counts = {}
    for bits, cnt in zip(sol.bitstrings.tolist(), sol.counts.tolist()):
        counts["".join(str(int(b)) for b in bits)] = int(cnt)
    info = dict(emulator=f"qubo-solver[{embedding}+{drive}]", shots=int(sum(counts.values())))
    return counts, info
