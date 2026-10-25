"""Figures and typeset equations for the Track A deck. One function per figure.

Colour meaning is fixed across the deck:
  BLUE  = our model      GREEN = matches Pasqal / model B
  AMBER = approximate    RED   = mismatch / device limit
"""
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.transforms import IdentityTransform

INK = "#17202A"; MUTED = "#5E6A78"; FAINT = "#A3ADB8"; LINE = "#E4E8ED"
BLUE = "#1D4E89"; GREEN = "#1E7B4F"; AMBER = "#B7791F"; RED = "#B42318"; GREY = "#9AA4AF"
TRUCKS = ["#3B6EA8", "#D08C3A", "#4E9F7E", "#8A6BBE"]
DPI = 300

plt.rcParams.update({
    "font.family": "Arial", "font.size": 13, "mathtext.fontset": "cm",
    "text.color": INK, "axes.labelcolor": MUTED, "axes.edgecolor": FAINT, "axes.linewidth": 0.8,
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 12, "ytick.labelsize": 12,
    "axes.labelsize": 13, "axes.titlesize": 13, "axes.titlecolor": INK, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "legend.frameon": False, "legend.fontsize": 12,
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white", "svg.fonttype": "none",
})


def _save(fig, out, name, transparent=False):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(out / f"{name}.{ext}", dpi=DPI, bbox_inches="tight", pad_inches=0.06, transparent=transparent)
    plt.close(fig)
    return out / f"{name}.png"


def _clean(ax, grid="y"):
    ax.spines[["top", "right"]].set_visible(False)
    if grid:
        ax.grid(axis=grid, color=LINE, lw=0.8); ax.set_axisbelow(True)


# ---------------------------------------------------------------- equations
def equation(parts, out, name, size=28):
    """Typeset one equation from coloured pieces [(tex, colour), ...] on a shared baseline.
    Saved at its natural size: 1 pt of `size` = 1 pt on the slide when placed at px/DPI inches."""
    fig = plt.figure(figsize=(30, 3), dpi=DPI)
    r = fig.canvas.get_renderer()
    wpx = fig.bbox.width
    x = 20.0
    for tex, col in parts:
        t = fig.text(x / wpx, 0.4, tex, fontsize=size, color=col, va="baseline", ha="left")
        x += t.get_window_extent(r).width + size * 0.35 * DPI / 72
    return _save(fig, out, name, transparent=True)


# ---------------------------------------------------------------- slide 1
def atom_counts(rows, out):
    fig, ax = plt.subplots(figsize=(6.4, 3.6), layout="constrained")
    x = np.arange(3); w = 0.26
    series = [("Textbook + slack bits", [r["onehot_plus_slack"] for r in rows], GREY),
              ("Direct QUBO (model A)", [r["ours"] for r in rows], BLUE),
              ("Seed model (model B)", [4, 10, 15], GREEN)]
    for j, (label, vals, col) in enumerate(series):
        bars = ax.bar(x + (j - 1) * w, vals, w * 0.92, color=col, label=label)
        ax.bar_label(bars, padding=3, fontsize=12, color=INK)
    ax.axhline(80, color=RED, ls=(0, (4, 3)), lw=1.1)
    ax.text(2.42, 82, "80-atom limit", color=RED, fontsize=11, ha="right", va="bottom")
    ax.set(xticks=x, xticklabels=["S  (N=4)", "M  (N=10)", "L  (N=15)"], ylabel="atoms", ylim=(0, 100))
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.02), ncol=3, fontsize=10.5, handlelength=1.2, columnspacing=1.2)
    _clean(ax)
    return _save(fig, out, "s1_atom_counts")


# ---------------------------------------------------------------- slide 2
def instance_maps(insts, out):
    fig, axs = plt.subplots(1, 3, figsize=(12.4, 3.9), layout="constrained")
    for ax, inst in zip(axs, insts):
        xy = np.asarray(inst.coords, float)
        for k, g in enumerate(inst.references["model_groups"]):
            ax.scatter(*xy[g].T, s=46, color=TRUCKS[k], edgecolor="white", lw=0.6, zorder=3)
        ax.scatter(*inst.depot, marker="s", s=48, color=INK, zorder=3)
        ax.set_title(f"{inst.tier}    N = {inst.N},  K = {inst.K},  Q = {inst.Q}", fontsize=13)
        ax.set(xlim=(-4, 104), ylim=(-4, 104), xticks=[0, 50, 100], yticks=[0, 50, 100])
        ax.set_aspect("equal"); _clean(ax, grid=None)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(LINE)
    return _save(fig, out, "s2_instances")


# ---------------------------------------------------------------- slide 5
def s_layout(coords, letters, out):
    c = np.asarray(coords)
    fig, ax = plt.subplots(figsize=(3.6, 3.4), layout="constrained")
    for i in range(len(c)):
        for j in range(i + 1, len(c)):
            ax.plot(*c[[i, j]].T, color=LINE, lw=1.2, zorder=1)
        ax.add_patch(Circle(c[i], 2.5, fill=False, ls=(0, (2, 2)), lw=0.8, color=FAINT))
        ax.scatter(*c[i], s=420, color=BLUE, zorder=3)
        ax.text(*c[i], letters[i], color="white", ha="center", va="center", fontsize=13, weight="bold", zorder=4)
    m = np.abs(c).max() + 3.5
    ax.set(xlim=(-m, m), ylim=(-m, m), xlabel="x / µm", ylabel="y / µm")
    ax.set_aspect("equal"); _clean(ax, grid=None)
    return _save(fig, out, "s5_S_layout")


def m_wanted_distances(target_U, C6, out):
    v = target_U[np.triu_indices(len(target_U), 1)]
    r = (C6 / v[v > 0]) ** (1 / 6)
    fig, ax = plt.subplots(figsize=(4.2, 3.3), layout="constrained")
    ax.axvspan(3.5, 5, color=RED, alpha=0.07, lw=0)
    ax.hist(r, bins=np.arange(5.0, 7.31, 0.15), color=BLUE, edgecolor="white", lw=0.8)
    ax.axvline(5, color=RED, lw=1.2, ls=(0, (4, 3)))
    ax.text(4.6, ax.get_ylim()[1] * 0.5, "not\nallowed", color=RED, fontsize=11, ha="center", va="center")
    ax.set(xlim=(4.2, 7.4), xlabel="wanted atom distance r / µm", ylabel="atom pairs")
    _clean(ax)
    return _save(fig, out, "s5_M_wanted")


# ---------------------------------------------------------------- slide 6
def model_b(inst, layout, out):
    bf = layout["brute_force_light"]
    groups, seeds = bf["model_groups"], bf["model_seeds"]
    xy = np.asarray(inst.coords, float); c = np.asarray(layout["coords"]); Rb = layout["Rb"]
    col = np.empty(inst.N, object)
    for k, g in enumerate(groups):
        col[g] = TRUCKS[k]
    fig, axs = plt.subplots(1, 2, figsize=(8.6, 3.9), layout="constrained")
    ax = axs[0]
    ax.scatter(*xy.T, s=60, c=list(col), edgecolor="white", lw=0.6, zorder=3)
    ax.scatter(*xy[seeds].T, s=260, marker="*", c=[col[s] for s in seeds], edgecolor=INK, lw=0.8, zorder=4)
    ax.scatter(*inst.depot, marker="s", s=48, color=INK)
    ax.set_title("Customer map (best answer)")
    ax.set(xlim=(-4, 104), ylim=(-4, 104), xticks=[0, 50, 100], yticks=[0, 50, 100]); ax.set_aspect("equal"); _clean(ax, grid=None)
    ax = axs[1]
    for s in seeds:
        ax.add_patch(Circle(c[s], Rb, color=col[s], alpha=0.10, lw=0))
    ax.scatter(*c.T, s=60, color=FAINT, edgecolor="white", lw=0.6, zorder=3)
    ax.scatter(*c[seeds].T, s=260, marker="*", c=[col[s] for s in seeds], edgecolor=INK, lw=0.8, zorder=4)
    m = np.abs(c).max() + Rb * 0.6
    ax.set_title(f"Atoms (shaded: blockade radius {Rb:.0f} µm)")
    ax.set(xlim=(-m, m), ylim=(-m, m), xlabel="x / µm", ylabel="y / µm"); ax.set_aspect("equal"); _clean(ax, grid=None)
    return _save(fig, out, "s6_model_b")


# ---------------------------------------------------------------- slide 7
def pulse(amp, det, out, omega_max, T):
    t = np.arange(len(amp)) / 1000
    fig, axs = plt.subplots(2, 1, figsize=(6.6, 3.8), sharex=True, layout="constrained")
    axs[0].fill_between(t, amp, color=BLUE, alpha=0.12, lw=0); axs[0].plot(t, amp, color=BLUE, lw=2)
    axs[0].axhline(12.566, color=RED, lw=1, ls=(0, (4, 3))); axs[0].text(t[-1], 12.0, "device max", color=RED, fontsize=10, ha="right", va="top")
    axs[0].set(ylabel="Ω  (rad/µs)", ylim=(0, 14))
    axs[1].axhline(0, color=LINE, lw=1); axs[1].plot(t, det, color=GREEN, lw=2)
    axs[1].set(ylabel="δ  (rad/µs)", xlabel="time (µs)")
    for ax in axs:
        _clean(ax)
    return _save(fig, out, "s7_pulse")


# ---------------------------------------------------------------- slide 8
def results(rows, out):
    """rows: list of dicts with name, b, rand_k, a, qs (P(reach)) and b_feas, randk_feas, a_feas, qs_feas."""
    names = [r["name"] for r in rows]; x = np.arange(len(rows)); w = 0.2
    series = [("Model B (this work)", "b", GREEN), ("Random seed sets", "rand_k", GREY),
              ("Model A, direct QUBO", "a", BLUE), ("qubo-solver default (DMM)", "qs", AMBER)]
    fig, axs = plt.subplots(1, 2, figsize=(11.4, 3.6), layout="constrained")
    for ax, suffix, title in [(axs[0], "_feas", "Feasible shots"), (axs[1], "", "Shots that hit the proven optimum")]:
        for j, (label, key, colr) in enumerate(series):
            vals = [np.nan if r.get(key + suffix) is None else 100 * r[key + suffix] for r in rows]
            ax.bar(x + (j - 1.5) * w, vals, w * 0.92, color=colr, label=label)
        ax.set(xticks=x, xticklabels=names, ylim=(0, 105), ylabel="% of 1000 shots"); ax.set_title(title)
        _clean(ax)
    axs[1].legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=11)
    return _save(fig, out, "s8_results")
