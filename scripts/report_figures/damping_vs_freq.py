"""Report figure fig:damping (narr_damping_vs_freq.png), revision of 2026-09-12.
Repository copy: writes to report/figures via repo_paths; needs no run data.

What is plotted
---------------
Synchronous machine: the in-phase (damping) coefficient of the GGOV1
governor-and-turbine path as configured in 'IEEE 39 bus TypicalGT.dyr'
(Table 1 of the report), evaluated analytically from the block diagram of
IEEE PES-TR1 Figure 3-5:

    D_gov(s) = -dP_mech/dw
             = Kturb*T(s)*[A(s)*PID(s) - Wf0] / (1 + R*F(s)*Kturb*T(s)*A(s)*PID(s))

    PID(s) = Kpgov + Kigov/s        (Kdgov = 0)
    A(s)   = 1/(1 + s*Tact)         actuator lag (1/Tact with stroke feedback)
    T(s)   = (1 + s*Tc)/(1 + s*Tb)  turbine lead-lag
    F(s)   = 1/(1 + s*Tpelec)       electrical-power droop feedback (Rselect = 1)
    Wf0    = Wfnl + Pm0/Kturb       pre-disturbance fuel flow, from Flag = 1
                                    (fuel flow = valve stroke x speed)

The droop feedback is closed with the quasi-static assumption dP_e = dP_mech,
which fixes the zero-frequency value 1/R = 20; above 0.3 Hz the feedback term
|R F H| is below 0.05.  Wf0 depends on the unit's dispatch Pm0 on its own MVA
base; the 39-bus fleet spans 0.50 (bus 39) to 1.00 pu, so the curve is a band
with the median-dispatch line.

Grid-forming inverter: the filtered-droop coefficient 1/m_p of the reduced
model, a constant.

Net machine damping (diamond): from the all-machine bus-14 reference fault
(experiment fault_3PG_bus14_0GFM, 30 s record): FFT + log decrement of the
generator-bus active-power channels over 4-30 s, eight machines sharing the
0.85-1.0 Hz inter-machine mode with decay 0.063-0.101 1/s; D_net = 4 H sigma
with H = 5.46 s: median 1.8 pu, range 1.4-2.2 pu.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_paths as rp  # noqa: E402

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import figstyle_26x as st                              # noqa: E402

OUT = rp.OUT
st.apply()

BLUE, RED, INK = "#1f77b4", "#c0392b", "#2d3338"
BAND = "#fbd0c4"
NETC = "#2a7f7f"

# GGOV1 constants, TypicalGT.dyr (identical on all ten machines, Table 1)
R, Tpelec, Kpgov, Kigov = 0.05, 1.0, 10.0, 1.0
Tact, Kturb, Tb, Tc, Wfnl = 0.5, 1.5, 0.1, 0.0, 0.2
D_GFM = 100.0                       # 1/m_p

# fleet dispatch on each machine's own MVA base (case39 dispatch / MBASE)
PM0 = {30: 1.00, 31: 0.95, 32: 1.00, 33: 0.97, 34: 0.97,
       35: 1.00, 36: 0.93, 37: 0.90, 38: 0.98, 39: 0.50}
PM0_LO, PM0_HI, PM0_MED = min(PM0.values()), max(PM0.values()), float(np.median(list(PM0.values())))

# ringdown fit, all-machine bus-14 case (fault_3PG_bus14_0GFM, 30 s)
H_SG = 5.46
SIGMAS = [0.087, 0.074, 0.074, 0.063, 0.065, 0.101, 0.091, 0.097]
F_LO, F_HI = 0.85, 1.0
D_NET = 4.0 * H_SG * float(np.median(SIGMAS))
D_LO, D_HI = 4.0 * H_SG * min(SIGMAS), 4.0 * H_SG * max(SIGMAS)
F_NET = 0.5 * (F_LO + F_HI)

EM_LO, EM_HI = 0.1, 3.0


def d_gov(f, pm0):
    """In-phase governor-path coefficient at frequency f (Hz), dispatch pm0."""
    s = 2j * np.pi * np.asarray(f, dtype=float)
    pid = Kpgov + Kigov / s
    A = 1.0 / (1.0 + s * Tact)
    T = Kturb * (1.0 + s * Tc) / (1.0 + s * Tb)
    F = 1.0 / (1.0 + s * Tpelec)
    wf0 = Wfnl + pm0 / Kturb
    return (T * (A * pid - wf0) / (1.0 + R * F * T * A * pid)).real


def crossing(pm0, lo=0.3, hi=2.0, tol=1e-6):
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
    f0_lo, f0_hi = crossing(PM0_HI), crossing(PM0_LO)
    print("zero crossing: %.3f Hz (Pm0 = %.2f) to %.3f Hz (Pm0 = %.2f)" % (f0_lo, PM0_HI, f0_hi, PM0_LO))
    print("in-phase at 1.0 Hz: %+.2f (Pm0 %.2f) .. %+.2f (Pm0 %.2f)" % (d_gov(1.0, PM0_LO), PM0_LO, d_gov(1.0, PM0_HI), PM0_HI))
    print("net from the post-fault oscillation: %.2f pu (%.2f-%.2f)" % (D_NET, D_LO, D_HI))

    fig, (axT, axB) = plt.subplots(
        2, 1, figsize=(0.85 * st.TEXTWIDTH_IN, 4.2), sharex=True,
        gridspec_kw=dict(height_ratios=[1.0, 1.15], hspace=0.16))

    for ax in (axT, axB):
        ax.axvspan(f0_lo, EM_HI, color=BAND, alpha=0.5, zorder=0)
        ax.axhline(0.0, color="0.55", lw=0.9, zorder=1)
        ax.fill_between(f, np.minimum(re_lo, re_hi), np.maximum(re_lo, re_hi),
                        color=BLUE, alpha=0.22, lw=0, zorder=3)
        ax.semilogx(f, re_med, color=BLUE, lw=1.9, zorder=4)
        ax.grid(True, which="both", alpha=0.28)

    axT.semilogx(f, np.full_like(f, D_GFM), color=RED, lw=2.0, zorder=4,
                 label=r"grid-forming, filtered-droop coefficient $1/m_p=100$ pu")
    axT.plot([], [], color=BLUE, lw=1.9,
             label="synchronous, governor and turbine path (GGOV1),\n"
                   "band = fleet dispatch 0.50 to 1.00 pu")
    axT.errorbar([F_NET], [D_NET], yerr=[[D_NET - D_LO], [D_HI - D_NET]],
                 xerr=[[F_NET - F_LO], [F_HI - F_NET]], fmt="D", ms=6,
                 color=NETC, mec="k", mew=0.7, ecolor=NETC,
                 elinewidth=1.0, capsize=2.5, zorder=6,
                 label="synchronous, net damping of the post-fault\n"
                       "oscillation (all-machine bus-14 case): %.1f pu" % D_NET)
    axT.set_ylim(-8, 118)
    axT.set_yticks([0, 25, 50, 75, 100])
    axT.legend(loc="center left", fontsize=7.6, framealpha=0.95)
    axT.set_ylabel(r"$D_{\mathrm{eq}}$ (pu)")

    axB.errorbar([F_NET], [D_NET], yerr=[[D_NET - D_LO], [D_HI - D_NET]],
                 xerr=[[F_NET - F_LO], [F_HI - F_NET]], fmt="D", ms=6,
                 color=NETC, mec="k", mew=0.7, ecolor=NETC,
                 elinewidth=1.0, capsize=2.5, zorder=6)
    axB.annotate("net damping of the 0.85 to 1.0 Hz post-fault\n"
                 "oscillation, %.1f pu (all-machine bus-14 case);\n"
                 "the excess over the governor path is not\n"
                 "separately measured" % D_NET,
                 xy=(F_NET, D_NET), xytext=(0.0035, 15.5),
                 fontsize=7.6, color=INK, zorder=5,
                 bbox=dict(boxstyle="square,pad=0.25", facecolor="white",
                           edgecolor="#9AA3A8", linewidth=0.6),
                 arrowprops=dict(arrowstyle="-|>", lw=0.8, color="0.4"))
    axB.plot([1.0], [d_gov(1.0, PM0_MED)], "o", ms=5.5, color=BLUE, mec="k",
             mew=0.7, zorder=6)
    axB.annotate(r"governor path $%.1f$ to $%.1f$ pu at 1.0 Hz"
                 % (d_gov(1.0, PM0_LO), d_gov(1.0, PM0_HI)),
                 xy=(1.0, d_gov(1.0, PM0_MED)), xytext=(0.0035, -4.8),
                 fontsize=8, color=INK,
                 arrowprops=dict(arrowstyle="-|>", lw=0.8, color="0.4"))
    axB.text(f0_lo * 1.12, 19.0,
             "governor path negative\n"
             "above %.2f to %.2f Hz,\n"
             "inside the 0.1 to 3 Hz\nswing band" % (f0_lo, f0_hi),
             fontsize=8, color="#8a3324", va="top")
    axB.set_ylim(-6.5, 23)
    axB.set_yticks([-5, 0, 5, 10, 15, 20])
    axB.set_ylabel(r"$D_{\mathrm{eq}}$ (pu), machine range")
    axB.set_xlabel("perturbation frequency (Hz)")
    axB.set_xlim(f[0], f[-1])

    fig.savefig(OUT / "narr_damping_vs_freq.png", dpi=600)
    print("wrote", OUT / "narr_damping_vs_freq.png")


if __name__ == "__main__":
    main()
