"""cct_e39_tier2.py - TIER-2 multi-machine energy function: the E' field-
decay correction (stage-2 theory task from the stage-1 falsifier).

Model upgrade over the classical constant-E' system: each machine keeps
the one-axis flux-decay state (Sauer & Pai one-axis model)

    T'do dE'_i/dt = E_fd,i - E'_i - (xd - x'd)_i * id_i(delta, E')

with id_i from the NETWORK solution (terminal voltage reconstructed from
the retained network), so machines electrically close to the fault decay
fastest - the mechanism stage 1 implicated for the +96% anti-
conservatism. Exciter model per the stage-0 measurement: E_fd = 0
during the fault (bus-fed ESST4B loses supply), E_fd = prefault value
post-clear (NO boost credit - conservative). No braking/governor terms
(they helped the SMIB; negligible on the 0.2-0.3 s multi-machine
timescale). Parameters from the model's own .dyr: T'do = 7.61 s,
xd = 1.99, x'd = 0.26 (machine base, all units).

Two deliverables:
 1. tier-2 TRUE CCT - bisection on the (delta, w, E') model: fault-on
    with decay, post-clear with rebuild, stability = bounded COI spread.
 2. tier-2 PEBS SCREEN - shrinking-rim energy method: along the
    sustained-fault decaying trajectory, V_cr(t) is recomputed at each
    sample by running the PEBS detection on the E'(t)-FROZEN landscape
    (aux constant-E fault trajectory from the SEP); t_cr = first
    V(t) >= V_cr(t). The exact multi-machine generalization of the
    SMIB tier-2 time-varying rim.

PRE-REGISTERED EXPECTATION (before running): decay to clearing at
~0.24 s is E'/E0 ~ exp(-0.24/T'd_eff); well depth ~ E^2 shrinks the rim
several tens of percent; tier-2 should move 0.479 DOWN toward the
measured (0.237, 0.25] - success = closing most of the +96% gap;
landing inside +-20% of the bracket would mirror the SMIB tier-2's
+2.2% quality.

Usage:  python cct_e39_tier2.py
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
MGFM = ROOT.parent / "cct_energy_function_multiGFM"
sys.path.insert(0, str(MGFM))
sys.path.insert(0, str(ROOT))
import ieee39_data as d39                                  # noqa: E402
import cct_pebs as cp                                      # noqa: E402
from cct_sp39 import build_sync_system, MBASE              # noqa: E402

NB, WS = 39, d39.WS
GBUS = d39.GEN_BUSES
TDO_P = 7.61            # s (machine base .dyr)
XD_M, XDP_M = 1.99, 0.26


def x_sys(bus, x_mach):
    return x_mach * d39.SBASE / MBASE[bus]


# ---------------- E-parametric network / swing pieces ----------------------

def pe_vec_E(sys_, delta, E, G, B):
    Cm = np.outer(E, E) * B
    Dm = np.outer(E, E) * G
    dd = delta[:, None] - delta[None, :]
    S = Cm * np.sin(dd) + Dm * np.cos(dd)
    return E**2 * np.diag(G) + np.sum(S, axis=1) - np.diag(S)


def f_coi_E(sys_, th, E, G, B):
    Pe = pe_vec_E(sys_, th, E, G, B)
    Pi = sys_.Pm - E**2 * np.diag(G)
    Dm = np.outer(E, E) * G
    dd = th[:, None] - th[None, :]
    Pcoi = np.sum(Pi) - np.sum(np.triu(2.0 * Dm * np.cos(dd), 1))
    return sys_.Pm - Pe - sys_.M / sys_.MT * Pcoi


def make_id_fun(sys_, fault_bus):
    """id_i(delta, E) from the reconstructed machine-bus voltages."""
    map_other, R = sys_.recon_ops(d39.BRANCHES, fault_bus=fault_bus)
    rows = {}
    for j, node in enumerate(map_other):
        rows[node] = j
    gsel = []
    for b in GBUS:
        gsel.append(rows.get(b - 1, -1))     # -1 -> faulted/deleted (V=0)
    xdp = np.array([x_sys(b, XDP_M) for b in GBUS])

    def id_of(delta, E):
        Eph = E * np.exp(1j * delta)
        Vo = R @ Eph
        idv = np.zeros(len(GBUS))
        for k in range(len(GBUS)):
            Vb = Vo[gsel[k]] if gsel[k] >= 0 else 0.0 + 0j
            # one-axis: E'q = Vq + x'd id, Vq = |V| cos(delta - theta)
            vq = abs(Vb) * np.cos(delta[k] - np.angle(Vb)) if abs(Vb) > 0 \
                else 0.0
            idv[k] = (E[k] - vq) / xdp[k]
        return idv
    return id_of


def integrate_E(sys_, th0, w0, E0, Efd, G, B, id_of, t_end, dt=2e-4,
                record_every=5):
    """RK4 of the (delta, w, E') system in COI."""
    th, w, E = th0.copy(), w0.copy(), E0.copy()
    Minv = 1.0 / sys_.M
    xd_m_xdp = np.array([x_sys(b, XD_M) - x_sys(b, XDP_M) for b in GBUS])

    def rhs(th, w, E):
        dE = (Efd - E - xd_m_xdp * id_of(th, E)) / TDO_P
        return w, (f_coi_E(sys_, th, E, G, B)) * Minv, dE

    ts, THS, WS_, ES = [0.0], [th.copy()], [w.copy()], [E.copy()]
    n = int(round(t_end / dt))
    for k in range(1, n + 1):
        k1 = rhs(th, w, E)
        k2 = rhs(th + 0.5 * dt * k1[0], w + 0.5 * dt * k1[1],
                 E + 0.5 * dt * k1[2])
        k3 = rhs(th + 0.5 * dt * k2[0], w + 0.5 * dt * k2[1],
                 E + 0.5 * dt * k2[2])
        k4 = rhs(th + dt * k3[0], w + dt * k3[1], E + dt * k3[2])
        th = th + dt / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
        w = w + dt / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
        E = np.maximum(E + dt / 6 * (k1[2] + 2 * k2[2] + 2 * k3[2] + k4[2]),
                       0.05)
        if k % record_every == 0:
            ts.append(k * dt); THS.append(th.copy())
            WS_.append(w.copy()); ES.append(E.copy())
    return (np.array(ts), np.array(THS), np.array(WS_), np.array(ES))


# ------------------------------ tier-2 true --------------------------------

def stable_t2(sys_, t_cl, Efd0, id_flt, id_post, GF, BF, GP, BP,
              t_post=8.0):
    th0 = sys_.to_coi(sys_.d0)
    E0 = sys_.E.copy()
    ts, TH, W, ES = integrate_E(sys_, th0, np.zeros(sys_.m), E0,
                                np.zeros(sys_.m), GF, BF, id_flt,
                                max(t_cl, 1e-3), record_every=50)
    ts2, TH2, W2, ES2 = integrate_E(sys_, TH[-1], W[-1], ES[-1], Efd0,
                                    GP, BP, id_post, t_post,
                                    record_every=50)
    # bounded relative to the CONSTANT-E0 postfault SEP neighborhood
    spread = float(np.max(TH2, axis=0).max() - np.min(TH2, axis=0).min())
    drift = float(np.max(np.abs(TH2[-1] - TH2[0])))
    return (spread < 2 * np.pi and drift < np.pi), spread


def tier2_true(sys_, Efd0, id_flt, id_post, GF, BF, GP, BP,
               lo=0.05, hi=0.6, tol=5e-3):
    ok, _ = stable_t2(sys_, hi, Efd0, id_flt, id_post, GF, BF, GP, BP)
    if ok:
        return float("inf")
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        ok, _ = stable_t2(sys_, mid, Efd0, id_flt, id_post, GF, BF, GP, BP)
        if ok:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# --------------------------- tier-2 PEBS screen ----------------------------

def pebs_vcr_frozen(sys_, E, GF, BF, GP, BP, ths_guess, t_int=2.5):
    """V_cr of the E-FROZEN landscape: constant-E sustained-fault aux
    trajectory from the (frozen-E) postfault SEP -> PEBS crossing."""
    Efix = E.copy()
    Esave = sys_.E
    sys_.E = Efix
    try:
        ths, _ = sys_.sep(GP, BP, ths_guess)
        ts, TH, W = cp.integrate(sys_, ths + (sys_.to_coi(sys_.d0) - ths) * 1e-3
                                 + 0, np.zeros(sys_.m), GF, BF, t_int)
        # start from prefault angles for the aux run (standard PEBS)
        ts, TH, W = cp.integrate(sys_, sys_.to_coi(sys_.d0),
                                 np.zeros(sys_.m), GF, BF, t_int)
        VPE = np.zeros(len(ts)); g = np.zeros(len(ts))
        for k in range(len(ts)):
            _, Vp = sys_.energy_terms(TH[k], W[k], ths, GP, BP)
            VPE[k] = Vp
            g[k] = float(np.sum(sys_.f_coi(TH[k], GP, BP) * (TH[k] - ths)))
        Vd = cp.vd_trapezoid(sys_, TH, ths, TH[0], GP, BP)
        VPE = VPE + Vd
        for k in range(1, len(ts)):
            if g[k - 1] < 0.0 <= g[k]:
                return float(VPE[k]), ths
        return float(np.max(VPE)), ths
    finally:
        sys_.E = Esave


def main():
    sys_ = build_sync_system()
    GF, BF = sys_.reduced_Y(d39.BRANCHES, fault_bus=14)
    GP, BP = sys_.reduced_Y(d39.BRANCHES, fault_bus=None)
    id_flt = make_id_fun(sys_, fault_bus=14)
    id_post = make_id_fun(sys_, fault_bus=None)

    # prefault field voltage from one-axis equilibrium
    E0 = sys_.E.copy()
    th_abs0 = sys_.d0
    id0 = id_post(th_abs0, E0)
    xd_m_xdp = np.array([x_sys(b, XD_M) - x_sys(b, XDP_M) for b in GBUS])
    Efd0 = E0 + xd_m_xdp * id0
    print("prefault Efd0:", np.round(Efd0, 3))

    # ---- decaying sustained-fault trajectory (the tier-2 fault-on) ----
    th0 = sys_.to_coi(sys_.d0)
    ts, TH, W, ES = integrate_E(sys_, th0, np.zeros(sys_.m), E0,
                                np.zeros(sys_.m), GF, BF, id_flt, 1.0)
    k24 = int(np.argmin(np.abs(ts - 0.24)))
    print("E' at t=0.24 s (per machine):", np.round(ES[k24], 3))
    print("  critical group: E31 %.3f  E32 %.3f (E0 %.3f/%.3f)"
          % (ES[k24][1], ES[k24][2], E0[1], E0[2]))

    # ---- deliverable 1: tier-2 TRUE CCT ----
    t2 = tier2_true(sys_, Efd0, id_flt, id_post, GF, BF, GP, BP)
    print("[tier-2 TRUE, flux-decay model] t_cr = %.3f s" % t2)

    # ---- deliverable 2: shrinking-rim PEBS screen ----
    ths_c, _ = sys_.sep(GP, BP, th0)
    Vt = np.zeros(len(ts)); Vcr_t = []
    # V(t) on the decaying trajectory against the E(t)-frozen landscape
    samples = list(range(0, len(ts), max(1, len(ts) // 24)))
    tcr_screen = None
    ths_guess = ths_c
    for k in samples:
        Vcr_k, ths_guess = pebs_vcr_frozen(sys_, ES[k], GF, BF, GP, BP,
                                           ths_guess)
        Esave = sys_.E; sys_.E = ES[k].copy()
        try:
            VKE, Vp = sys_.energy_terms(TH[k], W[k], ths_guess, GP, BP)
        finally:
            sys_.E = Esave
        Vk = VKE + Vp          # lossless part vs frozen landscape
        Vcr_t.append((float(ts[k]), Vk, Vcr_k))
        if tcr_screen is None and Vk >= Vcr_k:
            k0 = samples[max(0, samples.index(k) - 1)]
            tcr_screen = float(0.5 * (ts[k0] + ts[k]))
    print("[tier-2 PEBS screen, shrinking rim] t_cr ~ %s s"
          % ("%.3f" % tcr_screen if tcr_screen else ">1.0"))

    # ---- sensitivity: no exciter collapse (Efd stays at Efd0 in fault) ----
    ts_b, TH_b, W_b, ES_b = integrate_E(sys_, th0, np.zeros(sys_.m), E0,
                                        Efd0, GF, BF, id_flt, 1.0)
    kb = int(np.argmin(np.abs(ts_b - 0.24)))
    print("sensitivity (Efd held at Efd0): E31/E32 at 0.24 s = %.3f/%.3f"
          % (ES_b[kb][1], ES_b[kb][2]))

    out = {"tier2_true_s": t2,
           "tier2_pebs_screen_s": tcr_screen,
           "E_at_0p24": [round(float(x), 4) for x in ES[k24]],
           "Efd0": [round(float(x), 4) for x in Efd0],
           "vcr_curve": [(round(a, 3), round(b, 3), round(c, 3))
                         for a, b, c in Vcr_t],
           "measured_bracket_s": [0.237, 0.25],
           "tier0_classical_s": 0.479, "tier0_pebs_s": 0.521}
    (ROOT / "results_tier2.json").write_text(json.dumps(out, indent=1))
    print("wrote results_tier2.json")


if __name__ == "__main__":
    main()
