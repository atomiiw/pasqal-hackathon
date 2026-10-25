"""One figure that shows how model B works, on real data: map -> atoms -> laser -> shots -> decode."""
from __future__ import annotations

import json
import sys
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import PchipInterpolator

from .instances import Instance, INSTANCE_DIR, ROOT
from .seeds import SeedModel

RESULTS = ROOT / "results"
FIG = ROOT / "notes" / "figures"
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
COLS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "text.color": INK, "figure.facecolor": SURF, "axes.facecolor": SURF})


def main(name="M_seed0"):
    inst = Instance.load(INSTANCE_DIR / f"{name}.json")
    L = json.loads((RESULTS / "layouts" / f"{name}_B.json").read_text())
    S = json.loads((RESULTS / "shots" / f"{name}_B.json").read_text())
    X = np.array(L["coords"])
    Rb, p, counts = L["Rb"], S["params"], S["counts"]
    sm = SeedModel(inst, blockade_radius=Rb, decoder="light-multi")
    P = np.asarray(inst.coords, float)
    lab = [chr(65 + i) for i in range(inst.N)]

    fig, axs = plt.subplots(2, 3, figsize=(15, 10.5))
    ax = axs[0, 0]
    ax.scatter(P[:, 0], P[:, 1], s=60, color=INK2, zorder=4)
    ax.scatter(50, 50, marker="s", s=70, color=INK, zorder=5)
    for i in range(inst.N):
        ax.annotate(f"{lab[i]} ({inst.demands[i]})", P[i], xytext=(4, 4), textcoords="offset points")
    ax.set_xlim(-5, 105); ax.set_ylim(-5, 105); ax.set_aspect("equal"); ax.grid(color=GRID, lw=0.5)
    ax.set_title(f"1. Instance: {inst.N} customers (demand),\n   {inst.K} trucks, capacity {inst.Q}", loc="left", fontweight="bold")

    ax = axs[0, 1]
    for i in range(inst.N):
        ax.add_patch(plt.Circle(X[i], Rb / 2, fill=True, color=COLS[0], alpha=0.07, lw=0))
        ax.add_patch(plt.Circle(X[i], Rb / 2, fill=False, ls=":", color=INK2, lw=0.7))
        ax.scatter(*X[i], s=60, color=INK, zorder=5)
        ax.annotate(lab[i], X[i], xytext=(4, 4), textcoords="offset points")
    ax.set_aspect("equal"); ax.grid(color=GRID, lw=0.5); ax.set_xlabel("µm")
    ax.set_title(f"2. Atoms on the same map (x{L['alpha']:.2f} µm/unit)\n   circles overlap (Rb = {Rb} µm): not both seeds",
                 loc="left", fontweight="bold")

    ax = axs[0, 2]
    T = p["duration"]; t = np.linspace(0, T, 400)
    om = PchipInterpolator([0, 0.1 * T, 0.9 * T, T], [0, p["omega_max"], p["omega_max"], 0])(t)
    de = PchipInterpolator([0, 0.1 * T, 0.9 * T, T], [p["delta_0"], p["delta_0"], p["delta_f"], p["delta_f"]])(t)
    ax.plot(t, om, color=COLS[0], lw=2, label=f"laser strength Ω(t), max {p['omega_max']:.2f} rad/µs")
    ax.plot(t, de, color=COLS[1], lw=2, label=f"detuning δ(t): {p['delta_0']:.1f} → {p['delta_f']:.2f} rad/µs")
    ax.axhline(0, color=GRID, lw=1)
    ax.set_xlabel("time (ns)"); ax.set_ylabel("rad/µs"); ax.legend(frameon=False, loc="lower right", fontsize=8)
    ax.grid(color=GRID, lw=0.5)
    ax.set_title(f"3. Laser pulse, {T} ns: all atoms start at 0,\n   δ sweeps up, then read 0/1 per atom", loc="left", fontweight="bold")

    ax = axs[1, 0]
    hist = Counter()
    for b, c in counts.items():
        hist[b.count("1")] += c
    ks = sorted(hist)
    bars = ax.bar(ks, [hist[k] for k in ks], color=[COLS[0] if k == inst.K else GRID for k in ks], zorder=3)
    for b_, k in zip(bars, ks):
        ax.text(b_.get_x() + b_.get_width() / 2, b_.get_height() + 10, str(hist[k]), ha="center", fontsize=8)
    ax.set_xlabel("number of atoms read as 1 (= number of seeds)"); ax.set_ylabel("shots out of 1000")
    ax.set_title(f"4. 1000 shots: {hist[inst.K]} have exactly K = {inst.K} seeds,\n   the rest are discarded", loc="left", fontweight="bold")
    ax.grid(axis="y", color=GRID, lw=0.5); ax.set_axisbelow(True)

    # most frequent feasible shot
    best = None
    for b, c in sorted(counts.items(), key=lambda kv: -kv[1]):
        x = np.array([int(ch) for ch in b])
        if sm.is_feasible(x):
            best = (b, c, sm.decode(x)); break
    b, c, assign = best
    seeds = [i for i, ch in enumerate(b) if ch == "1"]
    ax = axs[1, 1]
    for i in range(inst.N):
        t_ = assign[i]
        ax.scatter(P[i, 0], P[i, 1], s=160 if i in seeds else 55, color=COLS[t_ % 4], zorder=5,
                   edgecolor=INK if i in seeds else SURF, lw=1.5)
        ax.annotate(lab[i], P[i], xytext=(4, 4), textcoords="offset points")
        if i not in seeds:
            s = seeds[t_]
            ax.annotate("", xy=P[s], xytext=P[i], arrowprops=dict(arrowstyle="->", color=COLS[t_ % 4], lw=1.2, alpha=0.8))
    loads = [sum(inst.demands[i] for i in range(inst.N) if assign[i] == t_) for t_ in range(inst.K)]
    ax.set_xlim(-5, 105); ax.set_ylim(-5, 105); ax.set_aspect("equal"); ax.grid(color=GRID, lw=0.5)
    ax.set_title(f"5. Most frequent valid shot {b} ({c}x)\n   bold = seeds, others join nearest seed with room\n   loads {loads} ≤ {inst.Q}",
                 loc="left", fontweight="bold")

    ax = axs[1, 2]
    groups = inst.references["model_groups"]
    col = {i: t_ for t_, g in enumerate(groups) for i in g}
    for i in range(inst.N):
        ax.scatter(P[i, 0], P[i, 1], s=60, color=COLS[col[i] % 4], zorder=5, edgecolor=SURF)
        ax.annotate(lab[i], P[i], xytext=(4, 4), textcoords="offset points")
    same = groups == __import__("cvrp.reference", fromlist=["assignment_to_groups"]).assignment_to_groups(assign, inst.K)
    ax.set_xlim(-5, 105); ax.set_ylim(-5, 105); ax.set_aspect("equal"); ax.grid(color=GRID, lw=0.5)
    ax.set_title(f"6. Proven optimum (exhaustive search)\n   cost {inst.references['model_optimum']:.1f}; "
                 f"panel 5 {'IS' if same else 'is NOT'} this optimum", loc="left", fontweight="bold")
    fig.tight_layout(h_pad=2.0, w_pad=1.5)
    out = FIG / f"mechanism_B_{name}.png"
    fig.savefig(out, dpi=140)
    print("wrote", out, "| shot", b, "x", c, "| optimum reached:", same)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "M_seed0")
