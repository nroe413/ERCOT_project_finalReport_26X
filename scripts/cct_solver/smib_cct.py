"""smib_cct.py - Sauer & Pai Ch. 9 energy-function CCT for the SMIB
synchronous-machine case (single_machine_infinite_bus_1syncMachineValidation).

The machine is the bus-39 GENROU (H = 5.46 s, D = 0, X'd = 0.26 pu on
2000 MVA) tied to a stiff 230 kV source; the fault is a bolted 3PG at the
POI that self-clears after T seconds (no line trips, no reclose - the
pre- and post-fault networks are identical). This is the cleanest possible
Sauer Ch. 9 problem:

  swing:      M ddot(delta) = Pm - Pmax sin(delta),   M = 2H/ws
  fault-on:   Pe ~ 0 (bolted terminal fault; measured P_mach = 0.004 pu)
              => delta(t) = d_s + (ws Pm / 4H) t^2  (closed form)
  energy:     V(delta,w) = 1/2 M w^2 - Pm (delta-d_s) - Pmax (cos d - cos d_s)
  critical:   V_cr = V(d_u, 0),  d_u = pi - d_s  (the controlling UEP)
  CCT:        V(delta(t_cr), w(t_cr)) = V_cr  <=>  equal-area criterion
              cos d_cr = (Pm/Pmax)(d_u - d_s) + cos d_u
              t_cr = sqrt( 4 H (d_cr - d_s) / (ws Pm) )

Operating point comes from the MEASURED June run (SMIB_1SYNC_3PG_PSD.csv
pre-fault means), not from the nominal init. The source (Vs, X_ext) is
identified from the two measured steady states (pre-fault + post-recovery),
which agree at Vs = 1.000, X_ext ~ 0.108 pu; sensitivity rows cover the
slider-math (0.0022) and physical-slider (0.025) alternatives.

Usage:  python smib_cct.py
Writes plots/smib_cct_theory.png, plots/smib_5cyc_overlay.png (if the June
CSV is present), plots/smib_cct_metrics.json.
"""
import json
import sys
import cmath
import numpy as np
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
PLOTS = ROOT / "plots"
SMIB_DIR = ROOT.parents[1] / "systems" / "smib_siib" / "runs" / "3PG_5cyc_SCR10_10s"   # measured 5-cycle record (operating point)

plt.rcParams.update({
    "font.family": "serif", "font.size": 12, "mathtext.fontset": "cm",
    "figure.dpi": 200, "axes.grid": True, "axes.unicode_minus": True,
})

# ---------------- machine + measured operating point ----------------------
WS = 2 * np.pi * 60.0        # rad/s
H = 5.46                     # s   (GENROU, .dyr, 2000 MVA base)
XDP = 0.26                   # pu  X'd (same base)
S_MVA = 2000.0
# pre-fault means measured over t = 2.5-2.98 s of the June 5-cycle run
VT_PRE, P_PRE, Q_PRE = 1.0301, 1005.59 / S_MVA, 587.71 / S_MVA
# post-recovery means (t > 8 s) - second steady state for the (Vs,Xext) fit
VT_END, P_END, Q_END = 1.0321, 946.35 / S_MVA, 624.14 / S_MVA
T_F = 3.0                    # fault application time in the PSCAD runs


def identify_xext():
    """Vs(X) from each measured steady state; their crossing is the fit."""
    def vs_of_x(V, P, Q, X):
        I = (P - 1j * Q) / V
        return abs(V - 1j * X * I)
    xs = np.linspace(0.0, 0.30, 6001)
    d = [vs_of_x(VT_PRE, P_PRE, Q_PRE, x) - vs_of_x(VT_END, P_END, Q_END, x)
         for x in xs]
    k = int(np.argmin(np.abs(d)))
    return float(xs[k]), float(vs_of_x(VT_PRE, P_PRE, Q_PRE, xs[k]))


def build_case(x_ext, VT=VT_PRE, P=P_PRE, Q=Q_PRE):
    """Classical SMIB quantities from a terminal state (default: June run)."""
    I = (P - 1j * Q) / VT                      # VT taken as angle datum
    Ep = VT + 1j * XDP * I                     # E' behind X'd
    Vs = VT - 1j * x_ext * I                   # source EMF
    d0 = cmath.phase(Ep) - cmath.phase(Vs)
    Pmax = abs(Ep) * abs(Vs) / (XDP + x_ext)
    return {"x_ext": x_ext, "Ep": abs(Ep), "Vs": abs(Vs),
            "Pmax": Pmax, "d0": d0, "Pm": P}


def cct_closed_form(c):
    """Equal-area CCT for Pe_fault = 0 (bolted terminal fault)."""
    Pm, Pmax = c["Pm"], c["Pmax"]
    ds = np.arcsin(Pm / Pmax)
    du = np.pi - ds
    cos_dcr = (Pm / Pmax) * (du - ds) + np.cos(du)
    dcr = float(np.arccos(cos_dcr))
    tcr = float(np.sqrt(4.0 * H * (dcr - ds) / (WS * Pm)))
    M = 2.0 * H / WS
    Vpe = lambda d: -Pm * (d - ds) - Pmax * (np.cos(d) - np.cos(ds))
    Vcr = float(Vpe(du))
    # cross-check: energy at the closed-form clearing state equals V_cr
    w_cl = WS * Pm / (2.0 * H) * tcr
    V_cl = 0.5 * M * w_cl ** 2 + Vpe(dcr)
    return {"ds": ds, "du": du, "dcr": dcr, "tcr": tcr, "Vcr": Vcr,
            "V_at_clear": float(V_cl), "M": M,
            "Ks": Pmax * np.cos(ds),
            "f_swing_Hz": float(np.sqrt(WS * Pmax * np.cos(ds) / (2 * H))
                                / (2 * np.pi))}


def integrate_two_stage(c, T, tmax=6.0, dt=2e-4, pe_fault=0.0):
    """RK4 of the undamped classical model: fault (Pe = pe_fault) then post."""
    Pm, Pmax = c["Pm"], c["Pmax"]
    ds = np.arcsin(Pm / Pmax)
    M = 2.0 * H / WS

    def f(y, fault):
        d, w = y
        pe = pe_fault if fault else Pmax * np.sin(d)
        return np.array([w, (Pm - pe) / M])

    n = int(round(tmax / dt))
    t = np.arange(n + 1) * dt
    Y = np.zeros((n + 1, 2))
    Y[0] = (ds, 0.0)
    for k in range(n):
        fault = t[k] < T
        y = Y[k]
        k1 = f(y, fault); k2 = f(y + 0.5 * dt * k1, fault)
        k3 = f(y + 0.5 * dt * k2, fault); k4 = f(y + dt * k3, fault)
        Y[k + 1] = y + dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
    return t, Y[:, 0], Y[:, 1]


def first_swing_stable(c, T):
    t, d, w = integrate_two_stage(c, T)
    du = np.pi - np.arcsin(c["Pm"] / c["Pmax"])
    return bool(np.max(d) < du)


def cct_corrected(c, Pb=0.211, k_gov=0.101, dt=2e-4):
    """Tier-1.5 theory: same 2-state energy-function framework, plus the two
    dropped mechanisms MEASURED in the stage-0 ladder (critical rung):

      Pb    - braking power during the fault (mean TE = 0.211 pu: DC-offset
              braking + stator I^2 R at ~6 pu; equivalent to Ra_eff ~ 0.006
              pu times the fault current squared),
      k_gov - GGOV1 droop ramp, Pm(t) = Pm0 - k*t during the fault (TM
              measured 0.506 -> 0.443 over 0.622 s); held at the clearing
              value afterwards (conservative).

    E' decay vs exciter rebuild is left out: the fault kills the bus-fed
    ESST4B (Ef -> 0) but it rebuilds within ~0.2 s of recovery; the net was
    measured at ~-3.5% (the residual between the impulse-scaled prediction
    0.645 and the EMT 0.623). Returns the bisected critical duration."""
    Pm0, Pmax = c["Pm"], c["Pmax"]
    ds = float(np.arcsin(Pm0 / Pmax))
    du = np.pi - ds
    M = 2.0 * H / WS

    def stable(T):
        d, w = ds, 0.0
        n = int(round((T + 4.0) / dt))
        for i in range(n):
            tt = i * dt
            fault = tt < T
            pm = Pm0 - k_gov * min(tt, T)
            pe = Pb if fault else Pmax * np.sin(d)
            a = (pm - pe) / M
            # RK2 (midpoint) is plenty at this dt
            dm = d + 0.5 * dt * w
            wm = w + 0.5 * dt * a
            pe_m = Pb if fault else Pmax * np.sin(dm)
            d += dt * wm
            w += dt * (pm - pe_m) / M
            if d > du:
                return False
        return True

    lo, hi = 0.30, 1.20
    for _ in range(24):
        mid = 0.5 * (lo + hi)
        if stable(mid):
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def cct_corrected2(c, Pb=0.211, k_gov=0.101, Td_flt=0.994, tau_reb=1.5,
                   dt=2e-4):
    """Tier-2: tier-1.5 plus the field-decay channel. During the terminal
    fault the bus-fed ESST4B loses supply (measured Ef -> 0), so E' decays
    with the short-circuit field constant T'd = T'do X'd/Xd = 0.994 s;
    after clearing it rebuilds toward E'0 with an effective tau_reb
    (~1-2 s: even at Ef ceiling the rebuild rate is T'do-limited). Pmax
    scales with E'(t)/E'0. The rim delta_u(t) is time-varying."""
    Pm0, Pmax0 = c["Pm"], c["Pmax"]
    ds = float(np.arcsin(Pm0 / Pmax0))
    M = 2.0 * H / WS

    def stable(T):
        d, w, ef = ds, 0.0, 1.0          # ef = E'(t)/E'0
        n = int(round((T + 5.0) / dt))
        for i in range(n):
            tt = i * dt
            fault = tt < T
            ef += dt * ((-ef / Td_flt) if fault
                        else (1.0 - ef) / tau_reb)
            pmx = Pmax0 * ef
            pm = Pm0 - k_gov * min(tt, T)
            pe = Pb if fault else pmx * np.sin(d)
            dm = d + 0.5 * dt * w
            wm = w + 0.5 * dt * (pm - pe) / M
            pe_m = Pb if fault else pmx * np.sin(dm)
            d += dt * wm
            w += dt * (pm - pe_m) / M
            if not fault:
                if pm >= pmx:            # well vanished
                    return False
                if d > np.pi - np.arcsin(pm / pmx):
                    return False
        return True

    lo, hi = 0.30, 1.20
    for _ in range(24):
        mid = 0.5 * (lo + hi)
        if stable(mid):
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def main():
    PLOTS.mkdir(exist_ok=True)
    x_fit, vs_fit = identify_xext()
    print("identified from measured steady states: X_ext = %.4f pu, "
          "Vs = %.4f pu" % (x_fit, vs_fit))

    # X_ext candidates. The fit from the June run's two steady states lands
    # at 0.1075 = Zg(SCR 10 at 230 kV / 2000 MVA) 0.100 + a small machine-
    # side residual. (Battery probe 2026-07-19: flows scale exactly 1/X and
    # the ETRAN interface XPU is NOT in circuit in machine mode; the June
    # run was made with panel sliders at V_base 230 / Mbase 2000 / SCR 10,
    # which did not persist - .pscx Values fixed accordingly.)
    cases = [("fit from June run (Vs=1.000)", x_fit),
             ("SCR-10 grid Zg 0.100 + residual", 0.1050),
             ("grid-only, no residual", 0.1000)]
    rows = []
    for name, x in cases:
        c = build_case(x)
        r = cct_closed_form(c)
        rows.append({"case": name, "x_ext": round(x, 4),
                     "Ep": round(c["Ep"], 4), "Vs": round(c["Vs"], 4),
                     "Pmax": round(c["Pmax"], 4),
                     "delta_s_deg": round(np.degrees(r["ds"]), 3),
                     "delta_cr_deg": round(np.degrees(r["dcr"]), 3),
                     "delta_u_deg": round(np.degrees(r["du"]), 3),
                     "V_cr_pu": round(r["Vcr"], 4),
                     "t_cr_s": round(r["tcr"], 4),
                     "f_swing_Hz": round(r["f_swing_Hz"], 3)})
        # consistency: Pm = Pmax sin(ds) must reproduce the dispatch
        assert abs(c["Pmax"] * np.sin(r["ds"]) - c["Pm"]) < 1e-9
        assert abs(r["V_at_clear"] - r["Vcr"]) < 1e-6
    for r in rows:
        print("%-32s X=%.4f  Pmax=%.3f  d_s=%6.2f  d_cr=%7.2f  "
              "t_cr=%.4f s  f_sw=%.2f Hz"
              % (r["case"], r["x_ext"], r["Pmax"], r["delta_s_deg"],
                 r["delta_cr_deg"], r["t_cr_s"], r["f_swing_Hz"]))

    # headline case (identified source) + AVR-boost sensitivity
    c = build_case(x_fit)
    r = cct_closed_form(c)
    c_boost = dict(c); c_boost["Pmax"] = c["Pmax"] * 1.10
    r_boost = cct_closed_form(c_boost)
    print("with E' boosted 10%% (fast AVR proxy): t_cr %.4f -> %.4f s "
          "(theory should UNDER-predict the EMT CCT)"
          % (r["tcr"], r_boost["tcr"]))

    # corrected-theory tiers: restore the measured dropped mechanisms
    t_corr = cct_corrected(c)
    print("TIER-1.5 corrected theory (braking 0.211 pu + governor ramp "
          "0.101 pu/s, both measured): t_cr = %.3f s  "
          "[classical 0.474; EMT measured 0.623]" % t_corr)
    t_corr2 = cct_corrected2(c)
    for tr in (1.0, 1.5, 2.0):
        print("TIER-2 (+ field decay T'd = 0.994 s, rebuild tau = %.1f s): "
              "t_cr = %.3f s" % (tr, cct_corrected2(c, tau_reb=tr)))

    # dispatch-matched source (G_volt = 236.8 kV): TRIED AND REVERTED
    # 2026-07-19 - the GGOV1 load controller walks the operating point
    # continuously (June: P 0.503 -> 0.473 over 10 s; with the jolted
    # source: P 0.41, Q -0.37 at fault time), so no source setting holds a
    # target Q, and the G_volt -> Vs mapping measured nonlinear anyway
    # (236.8 kV gave ~1.0397 pu, not 1.0296). Config is back at
    # G_volt = 230; the ladder anchors to the measured t = 3 state above.
    # The number below is kept for the record only.
    c_disp = build_case(0.105, VT=1.03, P=P_PRE, Q=35.8 / S_MVA)
    r_disp = cct_closed_form(c_disp)
    print("dispatch-matched source (SUPERSEDED - reverted to G_volt = 230; "
          "see PLAN): would have been t_cr = %.4f s" % r_disp["tcr"])

    # numeric verdict ladder (undamped classical model)
    ladder = {}
    for T in (0.40, 0.45, 0.46, 0.47, 0.474, 0.48, 0.50, 0.525, 0.55, 0.60):
        ladder["%.3f" % T] = "STABLE" if first_swing_stable(c, T) else "UNSTABLE"
    print("classical-model verdicts:", ladder)

    # ------------------------- figure --------------------------------------
    Pm, Pmax = c["Pm"], c["Pmax"]
    ds, dcr, du, tcr = r["ds"], r["dcr"], r["du"], r["tcr"]
    fig, axes = plt.subplots(1, 3, figsize=(16.5, 5.0))

    ax = axes[0]
    dd = np.linspace(0, np.pi, 400)
    ax.plot(np.degrees(dd), Pmax * np.sin(dd), lw=2.0, color="#1f77b4",
            label="post-fault  $P_{max}\\sin\\delta$")
    ax.axhline(Pm, color="#404040", lw=1.5, ls="--", label="$P_m$ = %.3f pu" % Pm)
    ax.axhline(0, color="#c0392b", lw=2.0,
               label="fault-on  $P_e \\approx 0$ (measured 0.004)")
    m1 = (dd >= ds) & (dd <= dcr)
    ax.fill_between(np.degrees(dd[m1]), 0, Pm, color="#c0392b", alpha=0.25)
    m2 = (dd >= dcr) & (dd <= du)
    ax.fill_between(np.degrees(dd[m2]), Pm, Pmax * np.sin(dd[m2]),
                    color="#2ca02c", alpha=0.25)
    ax.annotate("$A_1$ (gained)", (np.degrees((ds + dcr) / 2), 0.22),
                ha="center", fontsize=11, color="#7a2318")
    ax.annotate("$A_2$ (recoverable)", (np.degrees((dcr + du) / 2), Pm + 0.55),
                ha="center", fontsize=11, color="#1e6b1e")
    for x, lbl in ((ds, "$\\delta_s$"), (dcr, "$\\delta_{cr}$"),
                   (du, "$\\delta_u$")):
        ax.axvline(np.degrees(x), color="k", lw=0.8, ls=":")
        ax.annotate(lbl, (np.degrees(x) + 2, Pmax * 0.94), fontsize=12)
    ax.set_xlabel("$\\delta$ (deg)")
    ax.set_ylabel("P (pu of 2000 MVA)")
    ax.set_title("(a) equal-area at the CCT:  $A_1 = A_2$\n"
                 "$\\delta_{cr}$ = %.1f$^\\circ$" % np.degrees(dcr), fontsize=12)
    ax.legend(fontsize=9, loc="upper left")

    ax = axes[1]
    dd = np.linspace(-0.6, 2 * np.pi, 600)
    Vpe = -Pm * (dd - ds) - Pmax * (np.cos(dd) - np.cos(ds))
    ax.plot(np.degrees(dd), Vpe, lw=2.0, color="#1f77b4")
    ax.axhline(r["Vcr"], color="#c0392b", lw=1.5, ls="--",
               label="$V_{cr}$ = %.3f pu" % r["Vcr"])
    for x, lbl, va in ((ds, "$\\delta_s$ (well)", "bottom"),
                       (du, "$\\delta_u$ (rim = controlling UEP)", "bottom")):
        k = np.argmin(np.abs(dd - x))
        ax.plot(np.degrees(x), Vpe[k], "o", ms=8, color="k")
        ax.annotate(lbl, (np.degrees(x) + 6, Vpe[k] + 0.15), fontsize=10.5,
                    va=va)
    ax.annotate("fault injects\n$\\frac{1}{2}M\\omega^2$ + climb",
                (np.degrees(dcr) - 55, 1.8), fontsize=10.5, color="#7a2318")
    ax.set_xlabel("$\\delta$ (deg)")
    ax.set_ylabel("$V_{PE}$ (pu$\\cdot$rad)")
    ax.set_title("(b) energy landscape: one well, one rim\n"
                 "(1-DOF: PEBS = exact, no slice caveats)", fontsize=12)
    ax.legend(fontsize=10)

    ax = axes[2]
    for T, col in ((0.40, "#2ca02c"), (0.45, "#7fbf7f"), (0.474, "#404040"),
                   (0.50, "#e08214"), (0.55, "#c0392b")):
        t, d, w = integrate_two_stage(c, T, tmax=3.0)
        stable = np.max(d) < du
        ax.plot(t, np.degrees(d), lw=1.8, color=col,
                label="T = %.3f s (%s)" % (T, "stable" if stable else "unstable"))
    ax.axhline(np.degrees(du), color="k", lw=1.0, ls=":")
    ax.annotate("$\\delta_u$ = %.1f$^\\circ$" % np.degrees(du),
                (2.0, np.degrees(du) + 8), fontsize=10)
    ax.set_ylim(-30, 400)
    ax.set_xlabel("time since fault-on (s)")
    ax.set_ylabel("$\\delta$ (deg)")
    ax.set_title("(c) classical trajectories across the boundary\n"
                 "$t_{cr}$ = %.3f s" % tcr, fontsize=12)
    ax.legend(fontsize=9, loc="upper left")

    fig.suptitle("SMIB energy-function CCT - bus-39 GENROU (H = 5.46 s, "
                 "$X'_d$ = 0.26) vs 1.00-pu source through $X_{ext}$ = %.3f pu"
                 % c["x_ext"], fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(PLOTS / "smib_cct_theory.png", dpi=450, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print("saved plots/smib_cct_theory.png")

    # ---------------- overlay vs the existing 5-cycle run -------------------
    # Finding: on a 5-cycle timescale the measured rotor BARELY moves
    # (integrated Wpu stays within ~0.6 deg) because the subtransient
    # DC-offset braking/pulsating torque (TE spikes to +4.9/-3.1 pu at 60 Hz)
    # cancels the classical acceleration. That torque decays with the
    # armature time constant (~10 cycles), so it delays - not prevents -
    # acceleration during CCT-length faults: one more reason the EMT CCT
    # should sit AT OR ABOVE the classical estimate.
    csv = SMIB_DIR / "SMIB_1SYNC_3PG_PSD.csv"
    overlay = None
    if csv.exists():
        import pandas as pd
        df = pd.read_csv(csv, usecols=["TIME", "Wpu", "TE", "TM"])
        t_m = df["TIME"].values
        m = (t_m > 2.5) & (t_m < 7.0)
        t_m, wpu = t_m[m], df["Wpu"].values[m]
        te, tmch = df["TE"].values[m], df["TM"].values[m]
        dtm = float(np.mean(np.diff(t_m)))
        d_meas = np.degrees(WS * np.cumsum(wpu - 1.0) * dtm)
        d_meas -= d_meas[int(np.argmin(np.abs(t_m - T_F)))]
        tt, d, w = integrate_two_stage(c, 0.0833, tmax=4.0)

        fig, axes = plt.subplots(1, 2, figsize=(14.0, 4.8))
        ax = axes[0]
        ax.plot(t_m - T_F, d_meas, lw=1.4, color="#1f77b4",
                label="measured rotor angle ($\\int\\omega_s(W_{pu}-1)\\,dt$)")
        ax.plot(tt, np.degrees(d - c_deg0(c)), lw=1.8, ls="--",
                color="#c0392b", label="classical model (undamped, $E'$ frozen)")
        ax.axvspan(0, 0.0833, color="#fbd0c4", alpha=0.6)
        ax.set_xlim(-0.5, 4.0)
        ax.set_ylim(-11, 14)
        ax.annotate("measured forward swing only +0.5$^\\circ$: DC-offset "
                    "braking torque cancels\nthe classical acceleration at "
                    "5 cycles (back-swing = recovery pulse + governor)",
                    (-0.45, 13.4), fontsize=9.5, color="#1f4e79", va="top",
                    ha="left")
        ax.set_xlabel("time since fault-on (s)")
        ax.set_ylabel("rotor angle swing (deg)")
        ax.set_title("(a) 5-cycle fault: classical first swing is an upper\n"
                     "envelope at short durations", fontsize=12)
        ax.legend(fontsize=9.5, loc="upper right")

        ax = axes[1]
        ax.plot(t_m - T_F, te, lw=1.0, color="#1f77b4", label="TE (air-gap)")
        ax.plot(t_m - T_F, tmch, lw=1.6, color="#404040", ls="--",
                label="TM (mechanical)")
        ax.axvspan(0, 0.0833, color="#fbd0c4", alpha=0.6)
        ax.set_xlim(-0.1, 0.5)
        ax.annotate("60-Hz pulsating + braking torque\n(decays with the "
                    "armature time constant\n~10 cycles $\\Rightarrow$ gone "
                    "on the CCT timescale)", (0.13, 3.3), fontsize=10,
                    color="#7a2318")
        ax.set_xlabel("time since fault-on (s)")
        ax.set_ylabel("torque (pu)")
        ax.set_title("(b) why: the torque the classical model drops",
                     fontsize=12)
        ax.legend(fontsize=9.5)
        fig.tight_layout()
        fig.savefig(PLOTS / "smib_5cyc_overlay.png", dpi=450,
                    bbox_inches="tight", facecolor="white")
        plt.close(fig)
        pk_model = float(np.degrees(np.max(d) - np.arcsin(Pm / c["Pmax"])))
        mk = (t_m > T_F) & (t_m < T_F + 1.0)
        pk_fwd = float(np.max(d_meas[mk]))
        pk_back = float(np.min(d_meas[mk]))
        overlay = {"peak_swing_model_deg": round(pk_model, 2),
                   "peak_fwd_measured_deg": round(pk_fwd, 2),
                   "peak_back_measured_deg": round(pk_back, 2),
                   "note": "forward swing all but cancelled by subtransient "
                           "DC-offset braking (TE +4.9/-3.1 pu at 60 Hz, "
                           "absent from the classical model, decayed by the "
                           "CCT timescale); the negative excursion is the "
                           "post-clear recovery-torque pulse + GGOV1 pulling "
                           "TM down"}
        print("5-cycle first swing: model peak %.2f deg, measured fwd %.2f / "
              "back %.2f deg (braking-torque effect)"
              % (pk_model, pk_fwd, pk_back))
        print("saved plots/smib_5cyc_overlay.png")

    met = {"machine": {"H_s": H, "Xdp_pu": XDP, "S_MVA": S_MVA, "D": 0},
           "operating_point_measured": {"VT": VT_PRE, "P_pu": round(P_PRE, 5),
                                        "Q_pu": round(Q_PRE, 5)},
           "identified_source": {"Vs_pu": round(vs_fit, 4),
                                 "X_ext_pu": round(x_fit, 4)},
           "cases": rows,
           "headline": {"t_cr_s": rows[0]["t_cr_s"],
                        "band_s": [min(x["t_cr_s"] for x in rows),
                                   max(x["t_cr_s"] for x in rows)],
                        "t_cr_dispatch_matched_s_SUPERSEDED": round(
                            r_disp["tcr"], 4),
                        "t_cr_Eboost10pct_s": round(r_boost["tcr"], 4),
                        "expected_EMT_bias": "EMT CCT >= theory (AVR boosts "
                        "E' during the fault; T'do = 7.61 s keeps flux up; "
                        "PSS adds damping) - the CONSERVATIVE direction, "
                        "opposite to the all-GFM bus-16 finding"},
           "classical_ladder_verdicts": ladder,
           "overlay_5cyc": overlay}
    (PLOTS / "smib_cct_metrics.json").write_text(json.dumps(met, indent=1))
    print("saved plots/smib_cct_metrics.json")


def c_deg0(c):
    return np.arcsin(c["Pm"] / c["Pmax"])


if __name__ == "__main__":
    main()
