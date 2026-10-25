"""Figures and typeset equations for the Slides artifact (1920x1080 canvas).
Images are rendered at 2x: display width in canvas px = image width / 2 (written to artifact_figs/sizes.json).
Colour meaning: BLUE = fits Pasqal's energy, ORANGE = does not fit. Every number comes from instances/ or results/.
Run from the repo root: .venv\\Scripts\\python.exe -X utf8 presentation/artifact_figures.py
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from PIL import Image

from cvrp.instances import Instance
from cvrp.qubo import build_qubo
from cvrp.hardware import make_map, C6
from cvrp.pulse.sequence import PulseParams, build_sequence

OUT = ROOT / "presentation" / "artifact_figs"; OUT.mkdir(exist_ok=True)
RES = ROOT / "results"
INK = "#16202B"; MUTED = "#5B6675"; LINE = "#DDE1E6"; BLUE = "#2156A5"; ORANGE = "#C96A1B"; GREY = "#A7B0BA"
TRUCKS = ["#2156A5", "#C96A1B", "#3F8F7F", "#7D5BA6"]
PX = 2  # image px per canvas px
plt.rcParams.update({
    "font.family": "Arial", "mathtext.fontset": "cm", "text.color": INK, "axes.labelcolor": MUTED,
    "axes.edgecolor": GREY, "axes.linewidth": 1.2, "xtick.color": MUTED, "ytick.color": MUTED,
    "savefig.transparent": True, "figure.facecolor": "none", "axes.facecolor": "none",
})
sizes = {}


def save(fig, name):
    p = OUT / f"{name}.png"
    fig.savefig(p, dpi=72 * PX, bbox_inches="tight", pad_inches=0.04, transparent=True)
    plt.close(fig)
    w, h = Image.open(p).size
    sizes[name] = [round(w / PX), round(h / PX)]


def clean(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(length=0, labelsize=22, pad=8)


def equation(parts, name, size=46):
    """size = glyph size in canvas px. parts = [(tex, colour), ...] on one baseline."""
    fig = plt.figure(figsize=(40, 4), dpi=72 * PX)
    r = fig.canvas.get_renderer(); wpx = fig.bbox.width; x = 10.0
    for tex, col in parts:
        t = fig.text(x / wpx, 0.4, tex, fontsize=size, color=col, va="baseline")
        x += t.get_window_extent(r).width + size * 0.4 * PX
    save(fig, name)


# ---------------------------------------------------------------- equations
E = equation
E([(r"$\mathrm{Total\ Loss}\;=\;C_{\mathrm{cluster}}\;+\;\lambda\,P_{\mathrm{capacity}}$", INK)], "eq_loss", 76)
E([(r"$C_{\mathrm{cluster}}=\sum_{\mathrm{pairs}} d_{ij}\,(1-x_i-x_j+2x_ix_j)$", INK)], "eq_cluster", 64)
E([(r"$P_{\mathrm{capacity}}=(3x_A+4x_B+2x_C+3x_D-6)^2$", INK)], "eq_capacity", 64)
E([(r"$\mathrm{Total\ Loss}=\mathrm{const}\;+$", INK), (r"$\sum_i a_i\,x_i$", ORANGE), (r"$+$", INK),
   (r"$\sum_{i<j} b_{ij}\,x_ix_j$", BLUE)], "eq_expanded", 64)
E([(r"$a_i=-S_i+\lambda\,q_i(q_i-D)$", ORANGE)], "eq_a", 52)
E([(r"$b_{ij}=2d_{ij}+2\lambda\,q_iq_j$", BLUE)], "eq_b", 52)
E([(r"$E\;=$", INK), (r"$\sum_i(-\delta)\,x_i$", ORANGE), (r"$+$", INK),
   (r"$\sum_{i<j}\;\dfrac{C_6}{r_{ij}^{6}}\,x_ix_j$", BLUE)], "eq_pasqal", 68)
E([(r"$r=\left(\dfrac{C_6}{\mathrm{wanted\ coupling}}\right)^{1/6}$", INK)], "eq_distance", 64)
E([(r"$\mathrm{error}=\mathrm{Pasqal\ value}-\mathrm{our\ value\ (scaled)}$", INK)], "eq_error", 60)
E([(r"$E\;=$", INK), (r"$-\delta\sum_i x_i$", BLUE), (r"$+$", INK),
   (r"$\sum_{i<j}\;\dfrac{C_6}{(\alpha\,d_{ij})^{6}}\,x_ix_j$", BLUE)], "eq_seed", 64)

# before (meaning) -> after (bits), slide "Model A idea"
E([(r"$C=\sum_{i<j} d_{ij}\cdot[\,i,j\ \mathrm{same\ truck}\,]$", INK)], "eqA_c_before", 40)
E([(r"$[\,\mathrm{same\ truck}\,]=1-x_i-x_j+2x_ix_j$", BLUE)], "eqA_c_after", 40)
E([(r"$L_1=3x_A+4x_B+2x_C+3x_D,\quad 5\leq L_1\leq 7$", INK)], "eqA_p_before", 40)
E([(r"$P=(L_1-6)^2$", BLUE)], "eqA_p_after", 40)
E([(r"$\mathrm{Total\ Loss}=C+\lambda\,P$", INK)], "eqA_total", 44)

# derivation slide: C + lambda P -> one number per atom and per pair
E([(r"$x^2=x$", INK)], "eqX_rule", 38)
E([(r"$C=\mathrm{const}-\sum_i S_i\,x_i+\sum_{i<j}2d_{ij}\,x_ix_j$", INK)], "eqX_C", 38)
E([(r"$P=36+\sum_i q_i(q_i-12)\,x_i+\sum_{i<j}2q_iq_j\,x_ix_j$", INK)], "eqX_P", 38)
E([(r"$C+\lambda P=\mathrm{const}+$", INK), (r"$\sum_i a_i\,x_i$", ORANGE), (r"$+$", INK), (r"$\sum_{i<j}b_{ij}\,x_ix_j$", BLUE)], "eqX_total", 38)
E([(r"$b_{ij}=2d_{ij}+2\lambda\,q_iq_j$", BLUE)], "eqX_b", 38)
E([(r"$\dfrac{C_6}{r_{ij}^{6}}=s\cdot b_{ij}\quad\Rightarrow\quad r_{ij}=\left(\dfrac{C_6}{s\,b_{ij}}\right)^{1/6}$", INK)], "eqX_goal", 38)

# ---------------------------------------------------------------- data
insts = {t: Instance.load(ROOT / f"instances/{t}_seed0.json") for t in "SML"}
weights = json.loads((ROOT / "instances/weights.json").read_text())
layA_S = json.loads((RES / "layouts/S_seed0_A.json").read_text())
layB_M = json.loads((RES / "layouts/M_seed0_B.json").read_text())
layB_S = json.loads((RES / "layouts/S_seed0_B.json").read_text())

# ---------------------------------------------------------------- instance maps (one per tier)
for t, inst in insts.items():
    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    xy = np.asarray(inst.coords, float)
    for k, g in enumerate(inst.references["model_groups"]):
        ax.scatter(*xy[g].T, s=260, color=TRUCKS[k], edgecolor="white", lw=1.5, zorder=3)
    ax.scatter(*inst.depot, marker="s", s=220, color=INK, zorder=3)
    ax.set(xlim=(-5, 105), ylim=(-5, 105), xticks=[], yticks=[]); ax.set_aspect("equal")
    for s in ax.spines.values():
        s.set_color(LINE); s.set_linewidth(1.5)
    save(fig, f"map_{t}")

# ---------------------------------------------------------------- S layout (model A)
c = np.asarray(layA_S["coords"])
fig, ax = plt.subplots(figsize=(4.6, 4.6))
for i in range(4):
    for j in range(i + 1, 4):
        ax.plot(*c[[i, j]].T, color=LINE, lw=2.5, zorder=1)
    ax.add_patch(Circle(c[i], 2.5, fill=False, ls=(0, (3, 3)), lw=1.6, color=GREY))
    ax.scatter(*c[i], s=1500, color=BLUE, zorder=3)
    ax.text(*c[i], "ABCD"[i], color="white", ha="center", va="center", fontsize=30, weight="bold", zorder=4)
m = np.abs(c).max() + 3.2
ax.set(xlim=(-m, m), ylim=(-m, m), xticks=[], yticks=[]); ax.set_aspect("equal")
for s in ax.spines.values():
    s.set_visible(False)
save(fig, "s_layout")

# ---------------------------------------------------------------- M wanted distances (model A)
mi = insts["M"]; wM = weights[mi.name]; qM = build_qubo(mi, wM["lam"], wM["A"]); hM = make_map(qM.a, qM.B, False)
v = hM.target_U[np.triu_indices(len(hM.target_U), 1)]; r = (C6 / v[v > 0]) ** (1 / 6)
fig, ax = plt.subplots(figsize=(7.4, 4.4))
ax.axvspan(3.0, 5.0, color=ORANGE, alpha=0.10, lw=0)
ax.hist(r, bins=np.arange(5.0, 7.31, 0.15), color=BLUE, edgecolor="#F7F6F2", lw=1.5)
ax.axvline(5, color=ORANGE, lw=2.5)
ax.text(4.1, ax.get_ylim()[1] * 0.55, "closer than\n5 µm:\nforbidden", color=ORANGE, fontsize=22, ha="center", va="center")
ax.set(xlim=(3.2, 7.4)); ax.set_xlabel("wanted atom distance  (µm)", fontsize=22); ax.set_ylabel("atom pairs", fontsize=22)
clean(ax)
save(fig, "m_hist")

# ---------------------------------------------------------------- model B: map and atoms
bf = layB_M["brute_force"]["light"] if "brute_force" in layB_M else layB_M["brute_force_light"]
groups, seeds = bf["model_groups"], bf["model_seeds"]
xy = np.asarray(mi.coords, float); cb = np.asarray(layB_M["coords"]); Rb = layB_M["Rb"]
col = np.empty(mi.N, object)
for k, g in enumerate(groups):
    col[g] = TRUCKS[k]
for name, pts, extra in [("b_map", xy, None), ("b_atoms", cb, Rb)]:
    fig, ax = plt.subplots(figsize=(5.0, 5.0))
    if extra:
        for s in seeds:
            ax.add_patch(Circle(pts[s], extra, color=col[s], alpha=0.12, lw=0))
        ax.scatter(*pts.T, s=240, color=GREY, edgecolor="white", lw=1.5, zorder=3)
        m = np.abs(pts).max() + extra * 0.55
        ax.set(xlim=(-m, m), ylim=(-m, m))
    else:
        ax.scatter(*pts.T, s=240, c=list(col), edgecolor="white", lw=1.5, zorder=3)
        ax.scatter(*mi.depot, marker="s", s=200, color=INK)
        ax.set(xlim=(-5, 105), ylim=(-5, 105))
    ax.scatter(*pts[seeds].T, s=1100, marker="*", c=[col[s] for s in seeds], edgecolor=INK, lw=1.5, zorder=4)
    ax.set(xticks=[], yticks=[]); ax.set_aspect("equal")
    for s in ax.spines.values():
        s.set_color(LINE); s.set_linewidth(1.5)
    save(fig, name)

# ---------------------------------------------------------------- pulse that was run (S_seed0, model B)
import csv
rowsS = list(csv.DictReader((RES / "results_S.csv").open(encoding="utf-8")))
bS = next(r for r in rowsS if r["instance"] == "S_seed0" and r["method"] == "B-seeds-light")
pS = PulseParams(float(bS["omega_max"]), int(float(bS["duration"])), float(bS["delta_0"]), float(bS["delta_f"]))
seq = build_sequence(np.asarray(layB_S["coords"]), layB_S["labels"], pS)
pl = next(s.type for s in seq._schedule["ryd"] if hasattr(s.type, "amplitude"))
amp, det = np.array(pl.amplitude.samples), np.array(pl.detuning.samples); t = np.arange(len(amp)) / 1000
fig, axs = plt.subplots(2, 1, figsize=(9.6, 6.0), sharex=True, gridspec_kw=dict(hspace=0.18))
axs[0].fill_between(t, amp, color=BLUE, alpha=0.12, lw=0); axs[0].plot(t, amp, color=BLUE, lw=3.5)
axs[0].axhline(12.566, color=ORANGE, lw=2, ls=(0, (5, 4)))
axs[0].set_ylim(0, 14); axs[0].set_ylabel("Ω  (rad/µs)", fontsize=22)
axs[1].axhline(0, color=LINE, lw=1.5); axs[1].plot(t, det, color=INK, lw=3.5)
axs[1].set_ylabel("δ  (rad/µs)", fontsize=22); axs[1].set_xlabel("time  (µs)", fontsize=22)
for ax in axs:
    clean(ax)
save(fig, "pulse")

# ---------------------------------------------------------------- model B mechanism, M_seed0 (real shots)
from collections import Counter
from cvrp.seeds import SeedModel
from cvrp.reference import cluster_cost
from scipy.interpolate import PchipInterpolator

E([(r"$r_{ij}=\alpha\,d_{ij},\qquad \alpha=\dfrac{R_b}{r_c},\qquad R_b=\left(\dfrac{C_6}{\Omega}\right)^{1/6}$", INK)], "eq_layout", 56)
shots = json.loads((RES / "shots/M_seed0_B.json").read_text()); counts = shots["counts"]; pp = shots["params"]
sm = SeedModel(mi, blockade_radius=Rb, decoder="light-multi")
lab = [chr(65 + i) for i in range(mi.N)]
# 1 atoms with blockade discs (two discs overlap = closer than Rb = cannot both be seeds)
fig, ax = plt.subplots(figsize=(4.6, 4.6))
for i in range(mi.N):
    ax.add_patch(Circle(cb[i], Rb / 2, color=BLUE, alpha=0.08, lw=0))
    ax.add_patch(Circle(cb[i], Rb / 2, fill=False, color=BLUE, alpha=0.35, lw=1.2))
    ax.scatter(*cb[i], s=120, color=INK, zorder=3)
    ax.text(cb[i][0] + 0.6, cb[i][1] + 0.6, lab[i], fontsize=20, color=INK)
m = np.abs(cb).max() + Rb / 2 + 0.5
ax.set(xlim=(-m, m), ylim=(-m, m), xticks=[], yticks=[]); ax.set_aspect("equal")
for s in ax.spines.values():
    s.set_visible(False)
save(fig, "mech_atoms")
# 2 pulse
T = pp["duration"]; tt = np.linspace(0, T, 400)
om = PchipInterpolator([0, .1 * T, .9 * T, T], [0, pp["omega_max"], pp["omega_max"], 0])(tt)
de = PchipInterpolator([0, .1 * T, .9 * T, T], [pp["delta_0"], pp["delta_0"], pp["delta_f"], pp["delta_f"]])(tt)
fig, ax = plt.subplots(figsize=(4.8, 4.0))
ax.axhline(0, color=LINE, lw=1.5)
ax.plot(tt / 1000, om, color=BLUE, lw=3.5); ax.plot(tt / 1000, de, color=INK, lw=3.5)
ax.text(T / 2000, pp["omega_max"] + 0.35, "Ω", color=BLUE, fontsize=26, ha="center")
ax.text(T / 1000 * 0.32, pp["delta_0"] + 0.4, "δ", color=INK, fontsize=26)
ax.set_xlabel("time (µs)", fontsize=22); ax.set_ylabel("rad/µs", fontsize=22); clean(ax)
save(fig, "mech_pulse")
# 3 seeds per shot
hist = Counter()
for b, c in counts.items():
    hist[b.count("1")] += c
ks = list(range(0, max(hist) + 1))
fig, ax = plt.subplots(figsize=(4.8, 4.0))
bars = ax.bar(ks, [hist[k] for k in ks], color=[BLUE if k == mi.K else GREY for k in ks], width=0.7)
for b_, k in zip(bars, ks):
    ax.text(b_.get_x() + b_.get_width() / 2, b_.get_height() + 12, str(hist[k]), ha="center", fontsize=20, color=INK)
ax.set_xticks(ks); ax.set_yticks([]); ax.spines[["top", "right", "left"]].set_visible(False)
ax.tick_params(length=0, labelsize=22); ax.set_xlabel("seeds in the answer", fontsize=22)
save(fig, "mech_hist")
# 4 most frequent valid shot, decoded
for b, c in sorted(counts.items(), key=lambda kv: -kv[1]):
    x = np.array([int(ch) for ch in b])
    if sm.is_feasible(x):
        top = (b, c, sm.decode(x)); break
b, c, assign = top; sd = [i for i, ch in enumerate(b) if ch == "1"]
fig, ax = plt.subplots(figsize=(4.6, 4.6))
for i in range(mi.N):
    if i not in sd:
        s = sd[assign[i]]
        ax.annotate("", xy=xy[s], xytext=xy[i], arrowprops=dict(arrowstyle="-|>", color=TRUCKS[assign[i]], lw=2.2, mutation_scale=22, shrinkA=6, shrinkB=12))
for i in range(mi.N):
    ax.scatter(*xy[i], s=700 if i in sd else 200, marker="*" if i in sd else "o", color=TRUCKS[assign[i]], edgecolor=INK if i in sd else "white", lw=1.5, zorder=4)
    if i in sd:
        ax.text(xy[i][0] - 4, xy[i][1] - 9, lab[i], fontsize=22, color=INK, weight="bold", ha="center")
ax.set(xlim=(-5, 105), ylim=(-5, 105), xticks=[], yticks=[]); ax.set_aspect("equal")
for s in ax.spines.values():
    s.set_color(LINE); s.set_linewidth(1.5)
save(fig, "mech_decode")
loads = [sum(mi.demands[i] for i in range(mi.N) if assign[i] == t_) for t_ in range(mi.K)]
mech = dict(shot=b, times=c, valid=hist[mi.K], loads=loads, Q=mi.Q, cost=cluster_cost(assign, mi.dist_matrix()),
            optimum=mi.references["model_optimum"], params=pp, seeds=[lab[i] for i in sd])

meta = dict(sizes=sizes, mech=mech, pulse=dict(omega=pS.omega_max, T=pS.duration, d0=pS.delta_0, df=pS.delta_f),
            etaS=layA_S["fidelity"]["eta"], rankS=layA_S["ground_state"]["global"]["rank_of_model_optimum"],
            etaB=layB_M["fidelity"]["eta"], nopt=bf["n_optimal_seed_sets"], nsets=bf["n_seed_sets"], Rb=Rb,
            cstar={t: insts[t].references["model_optimum"] for t in "SML"})
(OUT / "sizes.json").write_text(json.dumps(meta, indent=1))
print(json.dumps(meta))
