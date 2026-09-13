"""Report figure fig:damping (narr_damping_vs_freq.png), revision of 2026-09-12 (v3).

Synchronous machine: in-phase (damping) coefficient of the GGOV1 governor-and-
turbine path as configured in 'IEEE 39 bus TypicalGT.dyr' (Table 1),
evaluated from the PES-TR1 Figure 3-5 blocks with the electrical-power
feedback closed by the machine's own swing equation
(dPe = dPm - 2H s dw, the "swing closure"):

    D(s) = -dP_mech/dw
         = Kturb T [A C (1 - 2H R s F) - Wf0] / (1 + R F Kturb T A C)

    C = Kpgov + Kigov/s      A = 1/(1 + s Tact)     T = (1 + s Tc)/(1 + s Tb)
    F = 1/(1 + s Tpelec)     Wf0 = Wfnl + Pm0/Kturb (Flag = 1)

The factor (1 - 2H R s F) is 1 at zero frequency (1/R = 20 either way) and
0.47 - 0.09j at 1 Hz.  Band = fleet dispatch Pm0 0.50-1.00 pu, line = median.

Measured points: PSCAD frequency-modulation test on the single-machine case
(experiment smib_gov_damping_freqmod, 2026-09-12): infinite-bus frequency
60 + 0.05 sin(2 pi fm t) Hz, lock-in of mechanical torque on speed, governor
deadband removed from a copy of the record (db = 0); power-form coefficient
D_P = -Re(dTm/dw) - Pm0.

Net machine damping (diamond): all-machine bus-14 case (fault_3PG_bus14_0GFM,
30 s): 0.85-1.0 Hz inter-machine mode, decay 0.063-0.101 1/s on eight
machines, D_net = 4 H sigma with H = 5.46 s: median 1.8 pu, range 1.4-2.2 pu.
"""
import sys
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_paths as rp  # noqa: E402

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = rp.OUT
sys.path.insert(0, str(Path(__file__).resolve().parent))
import figstyle_26x as st                              # noqa: E402

st.apply()

BLUE, RED, INK = "#1f77b4", "#c0392b", "#2d3338"
BAND = "#fbd0c4"
NETC = "#2a7f7f"
MEAS = "#111111"

# GGOV1 / GENROU constants, TypicalGT.dyr (identical on all ten machines, Table 1)
R, Tpelec, Kpgov, Kigov = 0.05, 1.0, 10.0, 1.0
Tact, Kturb, Tb, Tc, Wfnl = 0.5, 1.5, 0.1, 0.0, 0.2
H = 5.46
D_GFM = 100.0                       # 1/m_p

PM0 = {30: 1.00, 31: 0.95, 32: 1.00, 33: 0.97, 34: 0.97,
       35: 1.00, 36: 0.93, 37: 0.90, 38: 0.98, 39: 0.50}
PM0_LO, PM0_HI, PM0_MED = min(PM0.values()), max(PM0.values()), float(np.median(list(PM0.values())))

# PSCAD measurements (deadband = 0), power-form in-phase coefficient
MEAS_050 = {0.3: 2.29, 0.5: -0.86, 0.7: -1.43, 1.0: -1.42, 1.5: -1.10, 2.0: -0.82}
MEAS_095 = {0.3: 1.78, 0.5: -1.33, 0.7: -1.80, 1.0: -1.68, 1.5: -1.34, 2.0: -0.98}
# GFM (REGFM_A1, m_p = 0.01, T_Pf = 0.01 s) on the single-inverter case, same test, dispatch 0.50 and
# 0.60 pu (identical to 0.01): in-phase coefficient of the terminal power on the internal droop
# frequency; the filtered droop power gives exactly 100 at every frequency.
MEAS_GFM = {0.3: 99.9, 0.5: 99.8, 0.7: 99.6, 1.0: 99.2, 1.5: 98.3, 2.0: 97.0}

H_SG = 5.46
SIGMAS = [0.087, 0.074, 0.074, 0.063, 0.065, 0.101, 0.091, 0.097]
F_LO, F_HI = 0.85, 1.0
D_NET = 4.0 * H_SG * float(np.median(SIGMAS))
D_LO, D_HI = 4.0 * H_SG * min(SIGMAS), 4.0 * H_SG * max(SIGMAS)
F_NET = 0.5 * (F_LO + F_HI)
EM_LO, EM_HI = 0.1, 3.0


def d_gov(f, pm0):
    s = 2j * np.pi * np.asarray(f, dtype=float)
    C = Kpgov + Kigov / s
    A = 1.0 / (1.0 + s * Tact)
    T = Kturb * (1.0 + s * Tc) / (1.0 + s * Tb)
    F = 1.0 / (1.0 + s * Tpelec)
    wf0 = Wfnl + pm0 / Kturb
    return (T * (A * C * (1.0 - 2.0 * H * R * s * F) - wf0) / (1.0 + R * F * T * A * C)).real


def crossing(pm0, lo=0.2, hi=2.0, tol=1e-6):
    a, b = lo, hi
    while b - a > tol:
        m = 0.5 * (a + b)
        if d_gov(m, pm0) > 0:
            a = m
        else:
            b = m
    return 0.5 * (a + b)


def main():
    f = np.logspace(-3, np.log10(16.0), 3000)
    re_lo, re_hi, re_med = d_gov(f, PM0_LO), d_gov(f, PM0_HI), d_gov(f, PM0_MED)
    f0_hi_disp, f0_lo_disp = crossing(PM0_HI), crossing(PM0_LO)
    f0_min, f0_max = min(f0_hi_disp, f0_lo_disp), max(f0_hi_disp, f0_lo_disp)
    print("zero crossing: %.3f Hz (Pm0 %.2f) to %.3f Hz (Pm0 %.2f)" % (f0_hi_disp, PM0_HI, f0_lo_disp, PM0_LO))
    print("in-phase at 1.0 Hz: %+.2f (Pm0 %.2f) .. %+.2f (Pm0 %.2f); median %+.2f"
          % (d_gov(1.0, PM0_LO), PM0_LO, d_gov(1.0, PM0_HI), PM0_HI, d_gov(1.0, PM0_MED)))
    print("at %.3f Hz: %+.2f .. %+.2f" % (F_NET, d_gov(F_NET, PM0_LO), d_gov(F_NET, PM0_HI)))

    fig, (axT, axB) = plt.subplots(
        2, 1, figsize=(0.85 * st.TEXTWIDTH_IN, 4.6), sharex=True,
        gridspec_kw=dict(height_ratios=[1.0, 1.2], hspace=0.30))

    for ax in (axT, axB):
        ax.axvspan(f0_min, EM_HI, color=BAND, alpha=0.5, zorder=0)
        ax.axhline(0.0, color="0.55", lw=0.9, zorder=1)
        ax.fill_between(f, np.minimum(re_lo, re_hi), np.maximum(re_lo, re_hi),
                        color=BLUE, alpha=0.22, lw=0, zorder=3)
        ax.semilogx(f, re_med, color=BLUE, lw=1.9, zorder=4)
        ax.grid(True, which="both", alpha=0.28)

    axT.semilogx(f, np.full_like(f, D_GFM), color=RED, lw=2.0, zorder=4,
                 label=r"grid-forming, analytic: filtered-droop coefficient $1/m_{\mathrm{p}}=100$ pu")
    axT.plot(list(MEAS_GFM), list(MEAS_GFM.values()), "o", ms=5.5, color=RED, mfc="white", mew=1.1, zorder=7,
             label="grid-forming, measured: PSCAD frequency-modulation test,\nterminal power, 0.50 and 0.60 pu")
    axT.plot([], [], color=BLUE, lw=1.9,
             label="synchronous, analytic: GGOV1 governor and turbine path\n"
                   "(band: fleet dispatch 0.50 to 1.00 pu)")
    axT.errorbar([F_NET], [D_NET], yerr=[[D_NET - D_LO], [D_HI - D_NET]],
                 xerr=[[F_NET - F_LO], [F_HI - F_NET]], fmt="D", ms=6,
                 color=NETC, mec="k", mew=0.7, ecolor=NETC,
                 elinewidth=1.0, capsize=2.5, zorder=6,
                 label="synchronous, measured: net damping of the post-fault\n"
                       "oscillation, all-machine bus-14 case (%.1f pu)" % D_NET)
    axT.set_ylim(-8, 118)
    axT.set_yticks([0, 25, 50, 75, 100])
    axT.legend(loc="upper left", bbox_to_anchor=(0.005, 0.87), fontsize=6.4, framealpha=0.92,
               handlelength=1.6, labelspacing=0.35, borderpad=0.4)
    axT.set_title("(a) both technologies, full scale", fontsize=8.5, loc="left")
    axT.set_ylabel(r"$D_{\mathrm{eq}}$ (pu)")

    axB.errorbar([F_NET], [D_NET], yerr=[[D_NET - D_LO], [D_HI - D_NET]],
                 xerr=[[F_NET - F_LO], [F_HI - F_NET]], fmt="D", ms=6,
                 color=NETC, mec="k", mew=0.7, ecolor=NETC,
                 elinewidth=1.0, capsize=2.5, zorder=6)
    axB.plot(list(MEAS_050), list(MEAS_050.values()), "o", ms=5.5, color=MEAS, mfc="white", mew=1.1, zorder=7,
             label="synchronous, measured: PSCAD frequency-modulation test, 0.50 pu")
    axB.plot(list(MEAS_095), list(MEAS_095.values()), "s", ms=5.2, color=MEAS, mfc=MEAS, mew=0.8, zorder=7,
             label="synchronous, measured: PSCAD frequency-modulation test, 0.95 pu")
    axB.legend(loc="upper right", fontsize=6.8, framealpha=0.92, handlelength=1.6, labelspacing=0.35, borderpad=0.4)
    axB.set_title("(b) synchronous machine only, expanded scale (same curve and points as in (a))", fontsize=8.5, loc="left")
    axB.set_ylim(-6.0, 23)
    axB.set_yticks([-5, 0, 5, 10, 15, 20])
    axB.set_ylabel(r"$D_{\mathrm{eq}}$ (pu)")
    axB.set_xlabel("perturbation frequency (Hz)")
    axB.set_xlim(f[0], f[-1])

    fig.savefig(OUT / "narr_damping_vs_freq.png", dpi=600)
    print("wrote", OUT / "narr_damping_vs_freq.png")


if __name__ == "__main__":
    main()
