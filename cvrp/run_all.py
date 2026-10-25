"""One command: instances -> references -> models -> layouts -> pulses -> results.csv

  python -m cvrp.run_all --tier S            # minutes
  python -m cvrp.run_all --all               # S, M, L

Writes results/results.csv (one row per instance x method x seed: the selected pulse)
and results/runs_log.csv (every grid point), plus results/layouts/*.json.
"""
from __future__ import annotations

import argparse
import json
import time
import warnings
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

from .classical import exact_min
from .embedding.fidelity import fidelity, ground_state_preserved, validate_layout
from .embedding.ours import embed
from .evaluate import evaluate_shots
from .hardware import make_map
from .instances import Instance, INSTANCE_DIR, ROOT, generate_all
from .pulse.search import (INSTANCE_GRID, TIER_GRID_A, TIER_GRID_B, qubo_params, random_row, run_point,
                           score_key, seed_params)
from .qubo import build_qubo
from .reference import compute_references
from .seeds import SeedModel
from .tune import WEIGHTS_FILE, tune

warnings.filterwarnings("ignore")
RESULTS = ROOT / "results"
LAYOUTS = RESULTS / "layouts"
COLUMNS = ["instance", "tier", "seed", "model", "method", "variant", "decoder", "atoms", "lam", "A", "alpha", "r_c",
           "eta", "gs_rank", "gs_preserved", "omega_max", "duration", "delta_0", "delta_f", "Rb", "emulator",
           "bond_dim", "shots", "feasibility_rate", "p_reach_ref", "feas_random_K", "p_reach_random_K",
           "p_reach_ratio_vs_random_K", "eps", "model_best_gap", "cvrp_best_gap",
           "best_groups", "model_optimum", "cvrp_optimum", "reference_status", "selected_by", "notes"]


def ensure_instances(tiers, verbose=True):
    insts = []
    for inst in generate_all():
        if inst.tier not in tiers:
            continue
        p = INSTANCE_DIR / f"{inst.name}.json"
        if p.exists() and Instance.load(p).references:
            inst = Instance.load(p)
        else:
            compute_references(inst, verbose=verbose)
            inst.save()
        insts.append(inst)
    return insts


def ensure_weights(insts):
    weights = json.loads(WEIGHTS_FILE.read_text()) if WEIGHTS_FILE.exists() else {}
    for inst in insts:
        if inst.name not in weights:
            weights[inst.name] = tune(inst)
            WEIGHTS_FILE.write_text(json.dumps(weights, indent=1))
    return weights


def base_row(inst, model_name, method, **kw):
    r = dict(instance=inst.name, tier=inst.tier, seed=inst.seed, model=model_name, method=method,
             model_optimum=inst.references["model_optimum"], cvrp_optimum=inst.references["cvrp_optimum"],
             reference_status=inst.references["status"], eps=1e-6)
    r.update(kw)
    return r


# ---------------------------------------------------------------------------
# Model B: seeds
# ---------------------------------------------------------------------------
def run_model_b(insts, shots, log, out, verbose=True):
    by_tier = {}
    for inst in insts:
        by_tier.setdefault(inst.tier, []).append(inst)
    for tier, group in by_tier.items():
        group.sort(key=lambda i: i.seed)
        # --- tier-level grid on seed 0, light decode
        lead = group[0]
        best_cfg, best_key = None, None
        for Rb, T in product(TIER_GRID_B["Rb"], TIER_GRID_B["T"]):
            sm = SeedModel(lead, blockade_radius=Rb, decoder="light")
            X, _ = sm.layout()
            row = run_point(lead, sm, X, seed_params(sm, X, Rb, T), shots)
            log.append(base_row(lead, "B-seeds", "B-grid-tier", variant="global", decoder="light", atoms=lead.N,
                                Rb=Rb, **{k: row[k] for k in ("omega_max", "duration", "delta_0", "delta_f", "emulator",
                                                              "bond_dim", "shots", "feasibility_rate", "p_reach_ref",
                                                              "model_best_gap", "cvrp_best_gap")}))
            if verbose:
                print(f"  [B tier {tier}] Rb={Rb} T={T}: feas={row['feasibility_rate']:.2f} P={row['p_reach_ref']:.2f} gap={row['model_best_gap']}")
            key = score_key(row)
            if best_key is None or key < best_key:
                best_key, best_cfg = key, (Rb, T)
        Rb, T = best_cfg
        if verbose:
            print(f"  [B tier {tier}] selected Rb={Rb} T={T}")
        # --- per instance: delta_f multiplier; both decoders evaluated on the same shots
        for inst in group:
            sm_light = SeedModel(inst, blockade_radius=Rb, decoder="light")
            sm_exact = SeedModel(inst, blockade_radius=Rb, decoder="exact")
            X, linfo = sm_light.layout()
            validate_layout(X, sm_light.labels)
            f = fidelity(X, sm_light.target_U)
            delta_nom = sm_light.delta_nominal(X)
            bf_l = sm_light.brute_force(X, delta_nom)
            bf_e = sm_exact.brute_force(X, delta_nom)
            (LAYOUTS / f"{inst.name}_B.json").write_text(json.dumps(dict(
                coords=X.tolist(), labels=sm_light.labels, alpha=sm_light.alpha, r_c=sm_light.r_c, Rb=Rb,
                target_U=sm_light.target_U.tolist(), fidelity=f, delta_window=sm_light.delta_window(X),
                brute_force_light=bf_l, brute_force_exact=bf_e), indent=1))
            best = None
            for c in INSTANCE_GRID["c"]:
                p = seed_params(sm_light, X, Rb, T, c)
                row = run_point(inst, sm_light, X, p, shots)
                log.append(base_row(inst, "B-seeds", "B-grid-instance", variant="global", decoder="light", atoms=inst.N,
                                    Rb=Rb, **{k: row[k] for k in ("omega_max", "duration", "delta_0", "delta_f", "emulator",
                                                                  "bond_dim", "shots", "feasibility_rate", "p_reach_ref",
                                                                  "model_best_gap", "cvrp_best_gap")}))
                if verbose:
                    print(f"  [B {inst.name}] c={c}: feas={row['feasibility_rate']:.2f} P={row['p_reach_ref']:.2f} gap={row['model_best_gap']}")
                if best is None or score_key(row) < score_key(best):
                    best = row
            common = dict(atoms=inst.N, alpha=sm_light.alpha, r_c=sm_light.r_c, eta=f["eta"], Rb=Rb,
                          omega_max=best["omega_max"], duration=best["duration"], delta_0=best["delta_0"],
                          delta_f=best["delta_f"], emulator=best["emulator"], bond_dim=best["bond_dim"], shots=best["shots"],
                          selected_by="P(reach), then best gap, then feasibility; Rb,T on seed 0; c per instance")
            def k_uniform(bf):
                """Fair baseline: a sampler uniform over exactly-K seed sets, same decode (analytic)."""
                opt = sum(1 for _ in [0]) and bf["n_optimal_seed_sets"]  # seed sets decoding to the optimum
                return dict(feas_random_K=bf["n_feasible"] / bf["n_seed_sets"], p_reach_random_K=opt / bf["n_seed_sets"])

            kl, ke = k_uniform(bf_l), k_uniform(bf_e)
            gs_ok = lambda bf: bool(bf["hardware_ground_state_feasible"] and bf["hardware_ground_state_cost"] is not None  # noqa: E731
                                    and abs(bf["hardware_ground_state_cost"] - inst.references["model_optimum"]) < 1e-6)
            out.append(base_row(inst, "B-seeds", "B-seeds-light", variant="global", decoder="light",
                                gs_rank=bf_l["rank_of_model_optimum"], gs_preserved=gs_ok(bf_l),
                                feasibility_rate=best["feasibility_rate"], p_reach_ref=best["p_reach_ref"],
                                p_reach_ratio_vs_random_K=(best["p_reach_ref"] / kl["p_reach_random_K"]) if kl["p_reach_random_K"] else None,
                                model_best_gap=best["model_best_gap"], cvrp_best_gap=best["cvrp_best_gap"],
                                best_groups=best["best_groups"],
                                notes=f"seed-model optimum (light decode) {bf_l['model_optimum']:.2f}; {bf_l['n_optimal_seed_sets']} of {bf_l['n_seed_sets']} seed sets decode to the optimum",
                                **common, **kl))
            ev_e = evaluate_shots(inst, sm_exact, best["counts"])
            out.append(base_row(inst, "B-seeds", "B-seeds-exact", variant="global", decoder="exact",
                                gs_rank=bf_e["rank_of_model_optimum"], gs_preserved=gs_ok(bf_e),
                                feasibility_rate=ev_e["feasibility_rate"], p_reach_ref=ev_e["p_reach_ref"],
                                p_reach_ratio_vs_random_K=(ev_e["p_reach_ref"] / ke["p_reach_random_K"]) if ke["p_reach_random_K"] else None,
                                model_best_gap=ev_e["model_best_gap"], cvrp_best_gap=ev_e["cvrp_best_gap"],
                                best_groups=ev_e["best_groups"],
                                notes=f"same shots as light row; exact decode = best feasible assignment to the seeds (classical post-processing); {bf_e['n_optimal_seed_sets']} of {bf_e['n_seed_sets']} seed sets decode to the optimum",
                                **common, **ke))
            for dec, sm in (("light", sm_light), ("exact", sm_exact)):
                rr = random_row(inst, sm, shots)
                out.append(base_row(inst, "B-seeds", f"B-random-{dec}", variant="random", decoder=dec, atoms=inst.N,
                                    emulator=rr["emulator"], shots=shots, feasibility_rate=rr["feasibility_rate"],
                                    p_reach_ref=rr["p_reach_ref"], model_best_gap=rr["model_best_gap"],
                                    cvrp_best_gap=rr["cvrp_best_gap"], notes="uniform random bitstrings, same decode"))


# ---------------------------------------------------------------------------
# Model A: direct QUBO (pulses only where the emulator can run it: tier S)
# ---------------------------------------------------------------------------
def run_model_a(insts, weights, shots, log, out, run_pulses_on=("S",), verbose=True):
    by_tier = {}
    for inst in insts:
        by_tier.setdefault(inst.tier, []).append(inst)
    for tier, group in by_tier.items():
        group.sort(key=lambda i: i.seed)
        prepared = {}
        for inst in group:
            w = weights[inst.name]
            q = build_qubo(inst, w["lam"], w["A"])
            q.self_test()
            maps = {v: make_map(q.a, q.B, dmm=(v == "dmm")) for v in ("global", "dmm")}
            X, einfo = embed(maps["global"].target_U, restarts=20 if q.n_vars <= 8 else 6)
            validate_layout(X, q.labels)
            f = fidelity(X, maps["global"].target_U)
            # ground-state check on valid assignments (S: all strings; M: all valid assignments; L: skipped)
            gs = {}
            if inst.N * (1 if inst.K == 2 else inst.K) <= 30:
                if q.encoding == "onebit":
                    states = ((np.arange(1 << inst.N)[:, None] >> np.arange(inst.N)) & 1)
                else:
                    states = np.array([q.encode(a) for a in product(range(inst.K), repeat=inst.N)])
                for v, hm in maps.items():
                    gs[v] = ground_state_preserved(q, X, hm, states)
            (LAYOUTS / f"{inst.name}_A.json").write_text(json.dumps(dict(
                coords=X.tolist(), labels=q.labels, lam=w["lam"], A=w["A"], fidelity=f, embed=einfo,
                s={v: hm.s for v, hm in maps.items()}, delta_global={v: hm.delta_global for v, hm in maps.items()},
                ground_state=gs), indent=1))
            prepared[inst.name] = (q, maps, X, f, gs)
            for v in ("global", "dmm"):
                out.append(base_row(inst, "A-direct", f"A-direct-{v}" + ("" if tier in run_pulses_on else "-layout-only"),
                                    variant=v, atoms=q.n_vars, lam=w["lam"], A=w["A"], eta=f["eta"],
                                    gs_rank=gs.get(v, {}).get("rank_of_model_optimum"),
                                    gs_preserved=gs.get(v, {}).get("preserved"),
                                    notes="penalty loss %.1f%%" % (100 * (w["model_cost"] - w["model_optimum"]) / w["model_optimum"])
                                    + ("; no pulse run: layout does not preserve the ground state and the register is too large for exact emulation" if tier not in run_pulses_on else "")))
        if tier not in run_pulses_on:
            continue
        # pulses: tier grid on seed 0 (global), then per instance c, both variants
        lead = group[0]
        q, maps, X, f, gs = prepared[lead.name]
        best_cfg, best_key = None, None
        for of, T in product(TIER_GRID_A["omega_frac"], TIER_GRID_A["T"]):
            row = run_point(lead, q, X, qubo_params(q, maps["global"], of, T), shots)
            log.append(base_row(lead, "A-direct", "A-grid-tier", variant="global", atoms=q.n_vars,
                                **{k: row[k] for k in ("omega_max", "duration", "delta_0", "delta_f", "emulator", "bond_dim",
                                                       "shots", "feasibility_rate", "p_reach_ref", "model_best_gap", "cvrp_best_gap")}))
            if verbose:
                print(f"  [A tier {tier}] omega_frac={of} T={T}: feas={row['feasibility_rate']:.2f} P={row['p_reach_ref']:.2f} gap={row['model_best_gap']}")
            key = score_key(row)
            if best_key is None or key < best_key:
                best_key, best_cfg = key, (of, T)
        of, T = best_cfg
        for inst in group:
            q, maps, X, f, gs = prepared[inst.name]
            for v in ("global", "dmm"):
                best = None
                for c in INSTANCE_GRID["c"]:
                    row = run_point(inst, q, X, qubo_params(q, maps[v], of, T, c), shots)
                    log.append(base_row(inst, "A-direct", "A-grid-instance", variant=v, atoms=q.n_vars,
                                        **{k: row[k] for k in ("omega_max", "duration", "delta_0", "delta_f", "emulator", "bond_dim",
                                                               "shots", "feasibility_rate", "p_reach_ref", "model_best_gap", "cvrp_best_gap")}))
                    if best is None or score_key(row) < score_key(best):
                        best = row
                # replace the layout-only row of this (inst, variant) with the measured one
                for r in out:
                    if r["instance"] == inst.name and r["method"] == f"A-direct-{v}":
                        r.update(omega_max=best["omega_max"], duration=best["duration"], delta_0=best["delta_0"],
                                 delta_f=best["delta_f"], emulator=best["emulator"], bond_dim=best["bond_dim"],
                                 shots=best["shots"], feasibility_rate=best["feasibility_rate"],
                                 p_reach_ref=best["p_reach_ref"], model_best_gap=best["model_best_gap"],
                                 cvrp_best_gap=best["cvrp_best_gap"], best_groups=best["best_groups"],
                                 selected_by="P(reach), then best gap, then feasibility; omega,T on seed 0; c per instance")
            rr = random_row(inst, q, shots)
            out.append(base_row(inst, "A-direct", "A-random", variant="random", atoms=q.n_vars, emulator=rr["emulator"],
                                shots=shots, feasibility_rate=rr["feasibility_rate"], p_reach_ref=rr["p_reach_ref"],
                                model_best_gap=rr["model_best_gap"], cvrp_best_gap=rr["cvrp_best_gap"],
                                notes="uniform random bitstrings"))
            try:
                from .baseline_qubosolver import run_qubosolver

                counts, info = run_qubosolver(q, shots)
                ev = evaluate_shots(inst, q, counts)
                out.append(base_row(inst, "A-direct", "A-qubosolver-default", variant="dmm", atoms=q.n_vars,
                                    emulator=info["emulator"], shots=info["shots"], feasibility_rate=ev["feasibility_rate"],
                                    p_reach_ref=ev["p_reach_ref"], model_best_gap=ev["model_best_gap"],
                                    cvrp_best_gap=ev["cvrp_best_gap"], best_groups=ev["best_groups"],
                                    notes="Pasqal qubo-solver default quantum pipeline (its embedder, its drive, DMM device)"))
            except Exception as e:  # keep going; record in the friction log
                out.append(base_row(inst, "A-direct", "A-qubosolver-default", variant="dmm", atoms=q.n_vars,
                                    notes=f"qubo-solver failed: {type(e).__name__}: {str(e)[:200]}"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", default="S")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--shots", type=int, default=1000)
    ap.add_argument("--skip-a", action="store_true")
    args = ap.parse_args()
    tiers = ["S", "M", "L"] if args.all else [args.tier]
    RESULTS.mkdir(exist_ok=True)
    LAYOUTS.mkdir(exist_ok=True)
    t0 = time.time()
    insts = ensure_instances(tiers)
    weights = ensure_weights(insts) if not args.skip_a else {}
    out, log = [], []
    run_model_b(insts, args.shots, log, out)
    if not args.skip_a:
        run_model_a(insts, weights, args.shots, log, out)
    suffix = "" if args.all else f"_{args.tier}"
    df = pd.DataFrame(out).reindex(columns=COLUMNS)
    df.to_csv(RESULTS / f"results{suffix}.csv", index=False)
    pd.DataFrame(log).to_csv(RESULTS / f"runs_log{suffix}.csv", index=False)
    print(df[["instance", "method", "atoms", "feasibility_rate", "p_reach_ref", "model_best_gap", "cvrp_best_gap", "eta", "gs_rank"]].to_string())
    print(f"done in {time.time() - t0:.0f}s -> {RESULTS / f'results{suffix}.csv'}")


if __name__ == "__main__":
    main()
