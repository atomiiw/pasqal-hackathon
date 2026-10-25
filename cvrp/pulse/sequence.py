"""Build a pulser Sequence: adiabatic sweep, global channel, optional DMM (emulation only).

Amplitude:  0 -> Omega_max (rise) -> hold -> 0 (fall), smooth (PCHIP).
Detuning:   delta_0 (negative) during the rise, linear sweep to delta_f during the hold, hold.
DMM:        constant delta_dmm <= 0 with per-atom weights eps_a in [0, 1], whole sequence.
pulser validates every limit of AnalogDevice when the sequence is built.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace

import numpy as np
from pulser import Pulse, Register, Sequence
from pulser.channels.dmm import DMM
from pulser.devices import AnalogDevice
from pulser.waveforms import ConstantWaveform, InterpolatedWaveform

from ..hardware import DELTA_MAX, OMEGA_MAX, T_MAX

CLOCK = 4  # ns


def dmm_device():
    """AnalogDevice plus one DMM channel, exactly as qoolqit.AnalogDeviceWithDMM builds it."""
    dmm = DMM(clock_period=4, min_duration=16, max_duration=6000, mod_bandwidth=8,
              bottom_detuning=-2 * math.pi * 20, total_bottom_detuning=-2 * math.pi * 20)
    return replace(AnalogDevice.to_virtual(), dmm_objects=(dmm,), name="AnalogDeviceWithDMM")


@dataclass
class PulseParams:
    omega_max: float  # rad/us
    duration: int  # ns
    delta_0: float  # rad/us, start (negative)
    delta_f: float  # rad/us, final global detuning
    rise_frac: float = 0.1
    delta_dmm: float = 0.0  # <= 0
    dmm_weights: np.ndarray | None = None  # eps_a in [0,1]; None = global only

    @property
    def variant(self) -> str:
        return "dmm" if self.dmm_weights is not None else "global"


def _round_clock(t: float) -> int:
    return max(16, int(round(t / CLOCK)) * CLOCK)


def build_sequence(coords: np.ndarray, labels, p: PulseParams) -> Sequence:
    assert p.omega_max <= OMEGA_MAX + 1e-9 and abs(p.delta_0) <= DELTA_MAX + 1e-9 and abs(p.delta_f) <= DELTA_MAX + 1e-9
    T = min(_round_clock(p.duration), T_MAX)
    rise = _round_clock(p.rise_frac * T)
    t1, t2 = rise / T, 1 - rise / T
    reg = Register({str(l): (float(x), float(y)) for l, (x, y) in zip(labels, coords)})
    device = dmm_device() if p.dmm_weights is not None else AnalogDevice
    seq = Sequence(reg, device)
    seq.declare_channel("ryd", "rydberg_global")
    amp = InterpolatedWaveform(T, [0.0, p.omega_max, p.omega_max, 0.0], times=[0.0, t1, t2, 1.0])
    det = InterpolatedWaveform(T, [p.delta_0, p.delta_0, p.delta_f, p.delta_f], times=[0.0, t1, t2, 1.0])
    seq.add(Pulse(amp, det, 0.0), "ryd")
    if p.dmm_weights is not None:
        dmap = reg.define_detuning_map({str(l): float(w) for l, w in zip(labels, p.dmm_weights)})
        seq.config_detuning_map(dmap, "dmm_0")
        seq.add_dmm_detuning(ConstantWaveform(T, p.delta_dmm), "dmm_0")
    seq.measure("ground-rydberg")
    return seq
