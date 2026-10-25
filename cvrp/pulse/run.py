"""Run a sequence on an emulator and return bitstring counts (bit order = register order).

<= 12 atoms : pulser-simulation (QuTiP, exact)
<= 20 atoms : emu-sv (state vector, exact)
 > 20 atoms : emu-mps (tensor network; bond dimension is reported)
"""
from __future__ import annotations

import sys
import time

from pulser import Sequence

# emu-sv / emu-mps log progress with Greek letters; the Windows console default (cp1252) chokes on them
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_sequence(seq: Sequence, shots: int = 1000, backend: str | None = None, bond_dim: int = 64,
                 sampling_rate: float = 0.25) -> tuple[dict, dict]:
    n = len(seq.register.qubits)
    backend = backend or ("qutip" if n <= 12 else "emu-sv" if n <= 20 else "emu-mps")
    t0 = time.time()
    if backend == "qutip":
        from pulser_simulation import QutipEmulator

        sim = QutipEmulator.from_sequence(seq, sampling_rate=sampling_rate)
        res = sim.run()
        counts = dict(res.sample_final_state(N_samples=shots))
        info = dict(emulator="pulser-simulation", bond_dim=None)
    else:
        from pulser.backend import BitStrings

        if backend == "emu-sv":
            from emu_sv import SVBackend, SVConfig

            cfg = SVConfig(observables=[BitStrings(evaluation_times=[1.0], num_shots=shots)], dt=10)
            res = SVBackend(seq, config=cfg).run()
            info = dict(emulator="emu-sv", bond_dim=None)
        else:
            from emu_mps import MPSBackend, MPSConfig

            cfg = MPSConfig(observables=[BitStrings(evaluation_times=[1.0], num_shots=shots)], dt=10,
                            max_bond_dim=bond_dim)
            res = MPSBackend(seq, config=cfg).run()
            info = dict(emulator="emu-mps", bond_dim=bond_dim)
        counts = dict(res.final_bitstrings)
    info.update(shots=shots, wall_s=round(time.time() - t0, 1), atoms=n)
    return counts, info
