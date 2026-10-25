"""Render notes/instances.md and a map figure from instances/*.json."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .instances import Instance, INSTANCE_DIR, TIERS, ROOT, RHO_MIN, RHO_MAX

NOTES = ROOT / "notes"
FIG = NOTES / "figures"
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]


def label(i: int) -> str:
    return chr(ord("A") + i)


def fmt_groups(groups) -> str:
    return " / ".join("{" + ",".join(label(i) for i in g) + "}" for g in groups)


def fmt_tours(tours) -> str:
    return " / ".join("0→" + "→".join(label(i) for i in t) + "→0" for t in tours)


def load_all() -> list[Instance]:
    return [Instance.load(p) for p in sorted(INSTANCE_DIR.glob("*.json"))]


def draw_maps(insts: list[Instance]) -> Path:
    FIG.mkdir(parents=True, exist_ok=True)
    fig, axs = plt.subplots(3, 3, figsize=(12, 12), facecolor="#fcfcfb")
    order = [i for t in TIERS for i in insts if i.tier == t]
    for ax, inst in zip(axs.ravel(), order):
        ax.set_facecolor("#fcfcfb")
        P = np.asarray(inst.coords)
        groups = inst.references.get("model_groups", [])
        for t, g in enumerate(groups):
            ax.scatter(P[g, 0], P[g, 1], s=60, color=COLORS[t % 4], zorder=4, edgecolor="white")
        for i, (x, y) in enumerate(P):
            ax.annotate(f"{label(i)}({inst.demands[i]})", (x, y), xytext=(4, 4),
                        textcoords="offset points", fontsize=8)
        ax.scatter(*inst.depot, marker="s", s=70, color="black", zorder=5)
        ax.set_xlim(-5, 105); ax.set_ylim(-5, 105); ax.set_aspect("equal")
        ax.set_title(f"{inst.name}  rho={inst.rho:.2f}  model*={inst.references.get('model_optimum', 0):.1f}",
                     fontsize=9, loc="left")
        ax.tick_params(labelsize=7); ax.grid(color="#e4e3df", lw=0.5)
    fig.suptitle("Instances, coloured by the optimal clustering under our model (label = customer(demand))", fontsize=10)
    fig.tight_layout()
    out = FIG / "instances_map.png"
    fig.savefig(out, dpi=120, facecolor="#fcfcfb")
    return out


def render(insts: list[Instance]) -> str:
    lines = ["# Instances (A2)", ""]
    lines += [f"Depot (50, 50). Coordinates: uniform integers in [0,100]². Demands: uniform in the tier range. "
              f"Accepted only if an exact packing exists and ρ = D/(K·Q) ∈ [{RHO_MIN}, {RHO_MAX}]. "
              f"RNG: `numpy.random.default_rng([ord(tier), seed])`.", ""]
    lines += ["Reference method: set-partition DP (proven optimum). TSP per group: Held-Karp (exact). "
              "Cross-checks: brute force over all assignments (S, M) and CPLEX MILP (all tiers). "
              "Vehicle relabelings count as one solution.", ""]
    lines += ["Customers are labelled A, B, …; the depot is 0 in tours.", "", "![maps](figures/instances_map.png)", ""]
    for tier, spec in TIERS.items():
        lines += [f"## Tier {tier}: N={spec['N']}, K={spec['K']}, Q={spec['Q']}, demands {spec['dmin']}..{spec['dmax']}", ""]
        lines += ["| seed | coords (A, B, …) | demands | ρ | d_max/Q | certificate (truck per customer) | optimal clustering (model) | model cost | CVRP optimum (tours) | CVRP length | #opt (model / CVRP) | CPLEX agrees | status |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for inst in insts:
            if inst.tier != tier:
                continue
            r = inst.references
            coords = " ".join(f"({x},{y})" for x, y in inst.coords)
            lines.append(
                f"| {inst.seed} | {coords} | {inst.demands} | {inst.rho:.3f} | {inst.dmax_ratio:.2f} | {inst.certificate} "
                f"| {fmt_groups(r['model_groups'])} | {r['model_optimum']:.2f} | {fmt_tours(r['cvrp_tours'])} | {r['cvrp_optimum']:.2f} "
                f"| {r['model_n_optimal']} / {r['cvrp_n_optimal']} | {r.get('cplex_agrees')} | {r['status']} |")
        lines.append("")
    lines += ["## Decomposition gap (model optimum routed exactly vs CVRP optimum)", "",
              "| instance | model optimum routed exactly | CVRP optimum | gap |", "|---|---|---|---|"]
    for inst in insts:
        r = inst.references
        lines.append(f"| {inst.name} | {r['model_routed_exactly']:.2f} | {r['cvrp_optimum']:.2f} | {r['decomposition_gap_pct']:.2f}% |")
    lines += ["", "Instance files: `instances/<tier>_seed<n>.json` (coords, demands, certificate, references). "
              "Regenerate with `python -m cvrp.instances && python -m cvrp.reference`."]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    insts = load_all()
    draw_maps(insts)
    out = NOTES / "instances.md"
    out.write_text(render(insts), encoding="utf-8")
    print("wrote", out)
