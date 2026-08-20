"""Report-format regeneration of narr_damping_vs_freq.png (report
fig:damping).

Equivalent damping vs frequency: the droop grid-forming inverter's
constant D_eq = 1/mP against the synchronous machine's GOVERNOR PATH
D_eqv(jw) = D + G(jw)/R_SG, imported from the original generator
sg_damping_quantification.py (experiments/cct_sweep_bus39, GGOV1 and
GENROU constants from "IEEE 39 bus TypicalGT.dyr"). Both curves are
analytic transfer-function evaluations, not measured data.

2026-08-11 review, third pass. Two defects, one of them substantive.

MISLEADING. The previous version put the inverter's TOTAL equivalent
damping (100 pu) beside the machine's GOVERNOR PATH alone and labelled
the latter "synchronous", inviting the reading that the machine has
essentially no damping at 1 Hz. It does not: its damper windings and
power-system stabiliser also contribute, and a measured ringdown on the
bus-39 island gives a NET 4.15 pu (sigma = 0.190 1/s, D_net = 4 H
sigma, H = 5.46 s). The governor path is what turns negative, not the
machine. This version says "governor path only" in the legend and plots
the measured net point alongside, so the two cannot be confused.

CONFUSING. On a single 0-110 linear axis the machine's whole structure,
20 pu falling through zero to -1.1, occupied the bottom fifth of the
plot and the sign change was invisible. Split into two panels: the top
carries the magnitude comparison, the bottom expands the machine's own
range so the crossing can actually be seen.

Also: the crossing is found by bisection rather than by argmax on the
plotting grid, which previously reported 0.71 Hz for a true 0.703 Hz,
and the anti-damping shading is clipped to the 0.1-3 Hz
electromechanical band instead of running to 16 Hz where nothing
electromechanical happens.

Sized 5.525 in x 4.2 in for width=0.85\\textwidth, Pagella 11 pt.

Placement history (bottom-panel annotations):
- 2026-08-11: "measured net damping" note at xytext=(0.0035, 15.5);
  the governor-path curve descends diagonally through its second line,
  overprinting "(damp" near the left end (pixel audit, 2026-08-12).
- 2026-08-12: kept the position (the open pocket below the curve at
  0.01-0.2 Hz is too narrow for the long second line) and instead gave
  the annotation an opaque white bbox with a thin #9AA3A8 edge, drawn
  above the curve (zorder=5), so no trace can cross the glyphs.
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SG_DIR = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
              r"\sharp-jackson-1e89b8\experiments\cct_sweep_bus39")
OUT = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
           r"\upbeat-jones-67c8d3\report_26X\overleaf\figures")
sys.path.insert(0, str(SG_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sg_damping_quantification as sg                 # noqa: E402
import figstyle_26x as st                              # noqa: E402

st.apply()   # AFTER the sg import: that module sets its own rcParams

BLUE, RED, INK = "#1f77b4", "#c0392b", "#2d3338"
BAND = "#fbd0c4"
NETC = "#2a7f7f"

# measured bus-39 island ringdown: sigma = 0.190 1/s at 1.66 Hz,
# H = 5.46 s, so the machine's NET damping there is 4 H sigma.
F_ISLAND, SIGMA, H_SG = 1.66, 0.190, 5.46
D_NET = 4.0 * H_SG * SIGMA

EM_LO, EM_HI = 0.1, 3.0        # electromechanical band


def re_gov(f):
    return sg.d_gov(2 * np.pi * f).real


def crossing(lo=0.3, hi=2.0, tol=1e-6):
    """Bisect for Re D_eqv = 0 rather than reading the plotting grid."""
    a, b = lo, hi
    if re_gov(a) < 0 or re_gov(b) > 0:
        raise SystemExit("crossing not bracketed by [%g, %g]" % (lo, hi))
    while b - a > tol:
        m = 0.5 * (a + b)
        if re_gov(m) > 0:
            a = m
        else:
            b = m
    return 0.5 * (a + b)


def main():
    f = np.logspace(-3, np.log10(16.0), 3000)
    re = np.array([re_gov(x) for x in f])
    f0 = crossing()
    print("Re(D_eqv) crosses zero at %.4f Hz" % f0)
    print("  Re at 1.0 Hz  = %+.2f pu (governor path)" % re_gov(1.0))
    print("  Re at 1.66 Hz = %+.2f pu (governor path)" % re_gov(F_ISLAND))
    print("  measured net at 1.66 Hz = %+.2f pu (4 H sigma)" % D_NET)
    print("  others (dampers + PSS) = %+.2f pu"
          % (D_NET - re_gov(F_ISLAND)))

    fig, (axT, axB) = plt.subplots(
        2, 1, figsize=(0.85 * st.TEXTWIDTH_IN, 4.2), sharex=True,
        gridspec_kw=dict(height_ratios=[1.0, 1.15], hspace=0.16))

    for ax in (axT, axB):
        ax.axvspan(f0, EM_HI, color=BAND, alpha=0.5, zorder=0)
        ax.axhline(0.0, color="0.55", lw=0.9, zorder=1)
        ax.semilogx(f, re, color=BLUE, lw=1.9, zorder=4)
        ax.grid(True, which="both", alpha=0.28)

    # ---- top: the magnitude comparison ----------------------------
    axT.semilogx(f, np.full_like(f, sg.D_GFM), color=RED, lw=2.0,
                 zorder=4,
                 label=r"grid-forming, total: $1/m_p = 100$ pu")
    axT.plot([], [], color=BLUE, lw=1.9,
             label="synchronous, governor path only")
    axT.plot([F_ISLAND], [D_NET], "D", ms=6, color=NETC, mec="k",
             mew=0.7, zorder=6,
             label=r"synchronous, measured net: 4.15 pu")
    axT.set_ylim(-8, 118)
    axT.set_yticks([0, 25, 50, 75, 100])
    axT.legend(loc="center left", fontsize=8, framealpha=0.95)
    axT.set_ylabel(r"$D_{\mathrm{eq}}$ (pu)")

    # ---- bottom: the machine's own range --------------------------
    axB.plot([F_ISLAND], [D_NET], "D", ms=6, color=NETC, mec="k",
             mew=0.7, zorder=6)
    axB.annotate("measured net damping, 4.15 pu\n"
                 "(dampers and PSS supply 5.4 pu here)",
                 xy=(F_ISLAND, D_NET), xytext=(0.0035, 15.5),
                 fontsize=8, color=INK, zorder=5,
                 bbox=dict(boxstyle="square,pad=0.25", facecolor="white",
                           edgecolor="#9AA3A8", linewidth=0.6),
                 arrowprops=dict(arrowstyle="-|>", lw=0.8, color="0.4"))
    axB.plot([1.0], [re_gov(1.0)], "o", ms=5.5, color=BLUE, mec="k",
             mew=0.7, zorder=6)
    axB.annotate(r"governor path $-1.1$ pu at 1.0 Hz",
                 xy=(1.0, re_gov(1.0)), xytext=(0.0035, -4.6),
                 fontsize=8, color=INK,
                 arrowprops=dict(arrowstyle="-|>", lw=0.8, color="0.4"))
    axB.text(f0 * 1.12, 19.0,
             "governor path anti-damping\n"
             r"(above %.3f Hz), inside the" "\n"
             "0.1 to 3 Hz swing band" % f0,
             fontsize=8, color="#8a3324", va="top")
    axB.set_ylim(-6.5, 23)
    axB.set_yticks([-5, 0, 5, 10, 15, 20])
    axB.set_ylabel(r"$D_{\mathrm{eq}}$ (pu), machine range")
    axB.set_xlabel("frequency (Hz)")
    axB.set_xlim(f[0], f[-1])

    fig.savefig(OUT / "narr_damping_vs_freq.png", dpi=600)
    print("wrote", OUT / "narr_damping_vs_freq.png")


if __name__ == "__main__":
    main()
