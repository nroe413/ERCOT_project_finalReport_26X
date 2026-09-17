"""cct_firstslip_constP.py - the ten-inverter unlimited const-P theory
CCT re-derived under the EMT ladder's OWN loss-of-synchronism rule.

WHY THIS EXISTS (the definition-contamination finding, audit doc Sec 2):
the tier-3 classifier stable_net() judges only the POST-CLEARING
trajectory, relative to the state AT clearing - so a pole slip completed
DURING the fault (followed by a +360 deg relock after clearing) is
invisible to it. The EMT ladder classifier
(selfclear_ladder_10gfm.classify_rung) instead integrates each unit's
droop frequency against the unweighted fleet mean from t = 2.9 s
(prefault) and calls SLIP when the TERMINAL displacement exceeds
180 deg - a fault-phase slip therefore counts, because the relock parks
the unit ~360 deg from where it started. The old "theory CCT 2.338 s
(+40% vs EMT (1.6, 1.7])" is definition-contaminated. This script
computes the like-for-like number.

MATCHED RULE (mirror of classify_rung, applied to theory states):
    g_j(t) = theta_j(t) - mean_k theta_k(t)      [unweighted mean,
              matching the EMT's unweighted mean of frequencies]
    SLIP iff  any |g_j(end) - g_j(prefault)| > 180 deg at the end of a
              (t_cl + 10 s) horizon,
          or  std of fleet frequency over the last 1.5 s > 0.05 Hz
              (the EMT's secondary settled check).

Everything else (system, loads, const-P network, integrator) is
identical to cct_pebs_constP.py, so the ONLY change is the definition.

Usage:  python -u cct_firstslip_constP.py
Writes: results_firstslip.json
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT))  # all solver modules live in this folder
import ieee39_data as d39                                  # noqa: E402
import cct_pebs as cp                                      # noqa: E402
import cct_p39_tier3 as t3                                 # noqa: E402

GBUS = d39.GEN_BUSES
T_POST = 10.0            # EMT runs 15 s total, fault at 3.0 s
SETTLE_WIN = 1.5         # the EMT classifier's settled-check window (s)
SETTLE_STD = 0.05        # ... and its threshold (Hz)


def rel_deg(TH):
    """Per-unit angle vs the unweighted fleet mean, degrees."""
    return np.degrees(TH - TH.mean(axis=1, keepdims=True))


def firstslip_verdict(sys_, netF, netP, t_cl, E0, dt=1e-3):
    """(stable, detail) under the EMT-matched terminal-displacement
    rule. Integrates fault-on then post-fault, concatenates, and judges
    the END state against the PREFAULT state."""
    th0 = sys_.to_coi(sys_.d0)
    zeros = np.zeros(sys_.m)
    ts1, TH1, W1, ES1, _ = t3.integrate_net(
        sys_, netF, th0, zeros.copy(), E0.copy(), zeros, False,
        max(t_cl, 1e-3), dt=dt, record_every=20)
    ts2, TH2, W2, ES2, _ = t3.integrate_net(
        sys_, netP, TH1[-1], W1[-1], ES1[-1], zeros, False,
        T_POST, dt=dt, record_every=20)
    ts = np.concatenate([ts1, ts1[-1] + ts2[1:]])
    TH = np.vstack([TH1, TH2[1:]])
    W = np.vstack([W1, W2[1:]])
    g = rel_deg(TH)
    disp_end = np.abs(g[-1] - g[0])
    fhz = W / (2 * np.pi)
    tail = ts >= ts[-1] - SETTLE_WIN
    f_std = float(np.std(fhz[tail]))
    slipped = bool(disp_end.max() > 180.0)
    unsettled = bool(f_std > SETTLE_STD)
    # first time ANY unit's displacement passes 180 (for reporting)
    over = np.abs(g - g[0]).max(axis=1) > 180.0
    t180 = float(ts[np.argmax(over)]) if over.any() else None
    return (not slipped) and (not unsettled), {
        "max_end_displacement_deg": round(float(disp_end.max()), 1),
        "worst_unit_bus": int(GBUS[int(np.argmax(disp_end))]),
        "tail_freq_std_hz": round(f_std, 4),
        "first_t_beyond_180_s": None if t180 is None else round(t180, 3),
        "slipped": slipped, "unsettled": unsettled}


def main():
    loads = t3.read_model_loads()
    d39.LOADS = {b: (p, q) for b, (p, q, v) in loads.items()}
    sys_ = cp.GFMSystem()
    xg_vec = [d39.gfm_xg_sys(b, sys_.xg) for b in GBUS]
    t3.prog("first-slip re-derivation: PF resid %.1e" % sys_.pf_resid)

    netF = t3.ConstPNetwork(sys_, loads, fault_bus=14, xdp_vec=xg_vec)
    netP = t3.ConstPNetwork(sys_, loads, fault_bus=None, xdp_vec=xg_vec)
    E0 = sys_.E.copy()

    # context: on the PURE fault-on path, when does any unit pass 180?
    th0 = sys_.to_coi(sys_.d0)
    zeros = np.zeros(sys_.m)
    ts, TH, _, _, _ = t3.integrate_net(sys_, netF, th0, zeros.copy(),
                                       E0.copy(), zeros, False, 2.6,
                                       dt=1e-3, record_every=20)
    g = rel_deg(TH)
    over = np.abs(g - g[0]).max(axis=1) > 180.0
    t180_flt = float(ts[np.argmax(over)]) if over.any() else None
    t3.prog("fault-on path passes 180 deg at t = %s s"
            % ("never" if t180_flt is None else "%.3f" % t180_flt))

    lo, hi, tol = 0.05, 2.40, 5e-3
    t0 = time.time()
    ok, det = firstslip_verdict(sys_, netF, netP, hi, E0)
    t3.prog("test 1: t_cl=%.3f -> %s %s (%.0f s)"
            % (hi, "STABLE" if ok else "SLIP", det, time.time() - t0))
    hist = [(hi, ok, det)]
    if ok:
        raise SystemExit("hi=%.2f STABLE - raise hi" % hi)
    k = 1
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        t0 = time.time()
        ok, det = firstslip_verdict(sys_, netF, netP, mid, E0)
        k += 1
        hist.append((mid, ok, det))
        if ok:
            lo = mid
        else:
            hi = mid
        t3.prog("test %d: t_cl=%.3f -> %s  bracket (%.3f, %.3f]  "
                "end-disp %.0f deg  (%.0f s)"
                % (k, mid, "STABLE" if ok else "SLIP", lo, hi,
                   det["max_end_displacement_deg"], time.time() - t0))
    tcr = 0.5 * (lo + hi)
    fails = netF.fail_count + netP.fail_count
    t3.prog("MATCHED-DEFINITION theory CCT = %.3f s  (old post-clear-"
            "settling rule gave 2.338 s; EMT-measured (1.6, 1.7]; "
            "unconverged net solves: %d)" % (tcr, fails))

    out = {
        "note": "THEORY numbers. EMT-measured anchor (1.6, 1.7] s. "
                "Rule mirrors selfclear_ladder_10gfm.classify_rung: "
                "terminal displacement vs prefault > 180 deg = SLIP, "
                "fault phase included via concatenated trajectory.",
        "scenario": "bus14_noloss, unlimited const-P fleet",
        "tcr_firstslip_s": round(tcr, 4),
        "bracket_s": [round(lo, 4), round(hi, 4)],
        "tcr_postclear_settling_s": 2.338,
        "faulton_first_180_s": t180_flt,
        "emt_measured_bracket_s": [1.6, 1.7],
        "unconverged_solves": fails,
        "history": [{"t_cl": round(t, 4), "stable": bool(o), **d}
                    for t, o, d in hist],
    }
    (ROOT / "results_firstslip.json").write_text(json.dumps(out, indent=1))
    t3.prog("wrote results_firstslip.json")


if __name__ == "__main__":
    main()
