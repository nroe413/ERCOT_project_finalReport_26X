"""cct_pebs_constP.py - re-derivation of the multi-GFM 39-bus CCTs with
CONSTANT-POWER loads (the EMT model's actual load law - the stage-3
lesson from the all-sync campaign: the const-Z assumption was 2x
anti-conservative there; every const-Z number in results.json is
superseded pending this re-derivation).

Same 10-REGFM_A1 fleet as cct_pebs.py (droop swing, H_eq 0.5 s,
D = 1/mp uniform); loads parsed from the ieee39_sz-lineage model pscx
(incl. the bus-4 Q / bus-5 capacitor / bus-23 P corrections vs case39);
network layer = ConstPNetwork from the stage-3 toolchain (adaptive
fixed point WITH convergence diagnostics - unconverged solves are
counted and reported, never silently classified).

Scenarios (the EMT-anchored set): bus14_noloss, bus14_norecl (lines
4-14/13-14/14-15 out + bus 14 dead), bus16_noloss, bus26_noloss.
True CCT by bisection (damped GFM dynamics, bounded-spread criterion).

Usage:  python -u cct_pebs_constP.py [--dscale A] [--scenario NAME ...] [--lo S]
        --dscale scales every GFM damping D_i by A (0 = undamped; default 1.0,
        which leaves results_constP.json and the published numbers unchanged);
        with A != 1 the output is results_constP_D<A>.json.  Progress via prog().
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT))  # all solver modules live in this folder
import ieee39_data as d39                                  # noqa: E402
import cct_pebs as cp                                      # noqa: E402
import cct_p39_tier3 as t3                                 # noqa: E402

GBUS = d39.GEN_BUSES


def branches_without(pairs):
    gone = {tuple(sorted(p)) for p in pairs}
    return [b for b in d39.BRANCHES
            if tuple(sorted((b[0], b[1]))) not in gone]


def main(dscale=1.0, scenarios=None, lo=0.05):
    loads = t3.read_model_loads()
    d39.LOADS = {b: (p, q) for b, (p, q, v) in loads.items()}
    sys_ = cp.GFMSystem()
    if dscale != 1.0:
        # mirrors cct_sp39.py (sys_.D[k] = 0.0 for the classical machine): scale the
        # droop damping after construction; D_i/M_i stays uniform so the COI form holds
        sys_.D = sys_.D * dscale
    xg_vec = [d39.gfm_xg_sys(b, sys_.xg) for b in GBUS]
    t3.prog("GFM fleet const-P re-derivation: PF resid %.1e, xg %.3f "
            "pu-Mbase, damping scale %g" % (sys_.pf_resid, sys_.xg, dscale))

    netP0 = t3.ConstPNetwork(sys_, loads, fault_bus=None, xdp_vec=xg_vec)
    Pe0, _, _ = netP0.pe_id(sys_.d0, sys_.E)
    t3.prog("prefault |Pe - Pm| max = %.2e pu"
            % float(np.max(np.abs(Pe0 - sys_.Pm))))

    scen = [
        ("bus14_noloss", 14, d39.BRANCHES, ()),
        ("bus14_norecl", 14,
         branches_without([(4, 14), (13, 14), (14, 15)]), (14,)),
        ("bus16_noloss", 16, d39.BRANCHES, ()),
        ("bus26_noloss", 26, d39.BRANCHES, ()),
    ]
    oldZ = {"bus14_noloss": float("inf"), "bus14_norecl": float("inf"),
            "bus16_noloss": 2.908, "bus26_noloss": 2.240}
    out = {}
    zeros = np.zeros(sys_.m)
    for label, fb, post, dead in scen:
        if scenarios and label not in scenarios:
            continue
        netF = t3.ConstPNetwork(sys_, loads, fault_bus=fb, xdp_vec=xg_vec)
        netP = t3.ConstPNetwork(sys_, loads, fault_bus=None, xdp_vec=xg_vec,
                                branches=post, dead_buses=dead)
        tcr = t3.true_cct_net(sys_, netF, netP, sys_.E.copy(), zeros,
                              decay=False, lo=lo, hi=4.5,
                              label=label)
        fails = netF.fail_count + netP.fail_count
        t3.prog("[%s] const-P true CCT = %s  (const-Z was %s)  "
                "unconverged solves: %d  [damping scale %g]"
                % (label,
                   "inf" if tcr == float("inf") else "%.3f s" % tcr,
                   "inf" if oldZ[label] == float("inf")
                   else "%.3f" % oldZ[label], fails, dscale))
        out[label] = {"tcr_constP_s": None if tcr == float("inf") else tcr,
                      "tcr_constZ_s": None if oldZ[label] == float("inf")
                      else oldZ[label],
                      "unconverged_solves": fails}
    name = "results_constP.json" if dscale == 1.0 else "results_constP_D%g.json" % dscale
    (ROOT / name).write_text(json.dumps(out, indent=1))
    t3.prog("wrote " + name)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dscale", type=float, default=1.0, help="scale all GFM damping D_i (0 = undamped)")
    ap.add_argument("--scenario", nargs="*", default=None, help="subset of scenario labels")
    ap.add_argument("--lo", type=float, default=0.05, help="lower end of the bisection window (s)")
    a = ap.parse_args()
    main(a.dscale, a.scenario, a.lo)
