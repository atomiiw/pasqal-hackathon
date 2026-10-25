"""Figures and a summary table from results/results.csv and results/layouts/*.json."""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .instances import Instance, INSTANCE_DIR, ROOT

RESULTS = ROOT / "results"
FIG = ROOT / "notes" / "figures"
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "text.color": INK, "figure.facecolor": SURF, "axes.facecolor": SURF})


def layouts_figure(insts):
    fig, axs = plt.subplots(3, 3, figsize=(12, 12))
    for ax, inst in zip(axs.ravel(), insts):
        p = RESULTS / "layouts" / f"{inst.name}_B.json"
        if not p.exists():
            ax.set_visible(False)
            continue
        L = json.loads(p.read_text())
        X = np.array(L["coords"])
        Rb = L["Rb"]
        groups = inst.references["model_groups"]
        col = {}
        for t, g in enumerate(groups):
            for i in g:
                col[i] = [BLUE, ORANGE, AQUA, YELLOW][t % 4]
        bf = L.get("brute_force", {}).get("light") or L.get("brute_force_light")
        seeds = bf["model_seeds"]
        for i, (x, y) in enumerate(X):
            ax.add_patch(plt.Circle((x, y), Rb / 2, fill=False, ls=":", color=GRID, lw=0.8))
            ax.scatter(x, y, s=110 if i in seeds else 45, color=col.get(i, INK2), zorder=5,
                       edgecolor=INK if i in seeds else SURF, lw=1.5)
            ax.annotate(chr(65 + i), (x, y), xytext=(4, 4), textcoords="offset points", fontsize=8)
        ax.set_aspect("equal")
        ax.set_title(f"{inst.name}: {len(X)} atoms, alpha={L['alpha']:.2f} um/unit, Rb={Rb} um, eta={L['fidelity']['eta']:.2f}",
                     loc="left", fontsize=8)
        ax.grid(color=GRID, lw=0.5)
        ax.set_xlabel("um")
    fig.suptitle("Model B layouts: atoms on the scaled customer map. Colour = optimal cluster; bold ring = an optimal seed set;\n"
                 "dotted circles of radius Rb/2 overlap when two customers cannot both be seeds", fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(FIG / "layouts_B.png", dpi=120)


def results_figure(df):
    sel = df[df.method.isin(["B-seeds-light", "B-seeds-light-multi", "B-seeds-exact", "A-direct-global", "A-direct-dmm"])].copy()
    sel = sel[sel.feasibility_rate.notna()]
    inst_order = [f"{t}_seed{s}" for t in "SML" for s in range(3)]
    fig, axs = plt.subplots(1, 2, figsize=(13, 5))
    methods = [("B-seeds-light", BLUE), ("B-seeds-light-multi", "#6250d6"), ("B-seeds-exact", AQUA),
               ("A-direct-global", ORANGE), ("A-direct-dmm", YELLOW)]
    methods = [m for m in methods if m[0] in set(sel.method)]
    for ax, metric, title in [(axs[0], "feasibility_rate", "Feasibility rate (share of shots that decode to a valid plan)"),
                              (axs[1], "p_reach_ref", "P(reach the proven optimum)")]:
        x = np.arange(len(inst_order))
        w = 0.8 / len(methods)
        for k, (m, c) in enumerate(methods):
            vals = [sel[(sel.instance == i) & (sel.method == m)][metric].max() for i in inst_order]
            vals = [v if pd.notna(v) else 0 for v in vals]
            ax.bar(x + (k - (len(methods) - 1) / 2) * w, vals, w, color=c, label=m, zorder=3, edgecolor=SURF)
        # fair baseline for B: uniform over K-subsets
        base = [sel[(sel.instance == i) & (sel.method == "B-seeds-light")]["p_reach_random_K" if metric == "p_reach_ref" else "feas_random_K"].max() for i in inst_order]
        ax.scatter(x, [b if pd.notna(b) else 0 for b in base], marker="_", s=300, color=INK, zorder=4,
                   label="uniform over K-subsets, light decode (analytic)")
        ax.set_xticks(x, inst_order, rotation=45)
        ax.set_ylim(0, 1.05)
        ax.set_title(title, loc="left", fontsize=10, fontweight="bold")
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    handles, labels_ = axs[0].get_legend_handles_labels()
    fig.legend(handles, labels_, frameon=False, fontsize=8, loc="lower center", ncol=5, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(FIG / "results_summary.png", dpi=130)


def summary_md(df):
    cols = ["instance", "method", "atoms", "feasibility_rate", "feas_random_K", "p_reach_ref", "p_reach_random_K",
            "p_reach_ratio_vs_random_K", "p_reach_given_feasible", "conditional_ratio_vs_random_K",
            "model_best_gap", "cvrp_best_gap", "eta", "gs_rank", "emulator", "notes"]
    cols = [c for c in cols if c in df.columns]
    d = df[df.method.isin(["B-seeds-light", "B-seeds-light-multi", "B-seeds-exact", "B-random-light",
                           "A-direct-global", "A-direct-dmm", "A-random", "A-qubosolver-default"])][cols].copy()
    for c in ["feasibility_rate", "feas_random_K", "p_reach_ref", "p_reach_random_K", "p_reach_given_feasible"]:
        if c in d:
            d[c] = d[c].map(lambda v: f"{100*v:.1f}%" if pd.notna(v) else "")
    for c in ["p_reach_ratio_vs_random_K", "conditional_ratio_vs_random_K"]:
        if c in d:
            d[c] = d[c].map(lambda v: f"{v:.1f}x" if pd.notna(v) else "")
    for c in ["model_best_gap", "cvrp_best_gap"]:
        d[c] = d[c].map(lambda v: f"{v:.1f}%" if pd.notna(v) else "undefined")
    d["eta"] = d["eta"].map(lambda v: f"{v:.2f}" if pd.notna(v) else "")
    d["gs_rank"] = d["gs_rank"].map(lambda v: f"{int(v)}" if pd.notna(v) else "")
    d["notes"] = d["notes"].fillna("").str.slice(0, 90)
    lines = ["# Results (Track A)", "", "Source: `results/results.csv`. Gaps are on feasible shots only; "
             "P(reach) counts shots whose decoded clustering equals the proven optimum (ε = 1e-6, relabelings equal). "
             "`feas_random_K` / `p_reach_random_K`: a sampler uniform over exactly-K seed sets with the same decode (analytic). "
             "", "![summary](figures/results_summary.png)", "", "![layouts](figures/layouts_B.png)", "",
             "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in d.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    (ROOT / "notes" / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "results.csv"
    df = pd.read_csv(RESULTS / name)
    insts = [Instance.load(INSTANCE_DIR / f"{t}_seed{s}.json") for t in "SML" for s in range(3)]
    FIG.mkdir(exist_ok=True)
    layouts_figure(insts)
    results_figure(df)
    summary_md(df)
    print("wrote notes/results.md and figures")
