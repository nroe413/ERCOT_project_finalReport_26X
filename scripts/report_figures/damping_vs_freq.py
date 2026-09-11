"""PK-review revision of narr_damping_vs_freq.png (report fig:damping),
written to report_26X/prism/figures.

What changed and why (2026-09-09):
- The previous figure's "measured net 4.15 pu" came from a 1.66 Hz
  ringdown fit that sg_damping_quantification.py itself later flagged
  as a peak-thinning artifact ("the FFT shows no 1.66 Hz content").
  The value here is refit directly from the all-machine bus-14 run
  (fault_3PG_bus14_0GFM, 30 s): FFT + log-decrement of the ten
  generator-bus P channels over 4-30 s. Eight machines share a
  0.85-1.0 Hz inter-machine mode with decay 0.063-0.101 1/s; the two
  nearest the fault (buses 31, 32) carry a faster local component and
  are excluded. Net modal damping D_net = 4 H sigma with H = 5.46 s:
  median 1.8 pu, range 1.4-2.2 pu.
- Legend no longer says "grid-forming, total"; it names the quantity:
  the filtered-droop coefficient 1/m_p of the reduced model.
- The gap between the net point and the governor path is labeled as
  not separately measured (damper windings, excitation, stabilizer),
  not attributed numerically.
Governor path: D + Re{G(j w)}/R_SG from the GGOV1 constants, imported
from sg_damping_quantification (no math copied).
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

SG_DIR = rp.experiment(r"cct_sweep_bus39")
OUT = rp.OUT
sys.path.insert(0, str(SG_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import sg_damping_quantification as sg                 # noqa: E402
import figstyle_26x as st                              # noqa: E402

st.apply()

BLUE, RED, INK = "#1f77b4", "#c0392b", "#2d3338"
BAND = "#fbd0c4"
NETC = "#2a7f7f"

# ringdown fit, all-machine bus-14 case (scratchpad data_checks.json)
H_SG = 5.46
SIGMAS = [0.087, 0.074, 0.074, 0.063, 0.065, 0.101, 0.091, 0.097]
F_LO, F_HI = 0.85, 1.0
D_NET = 4.0 * H_SG * float(np.median(SIGMAS))
D_LO, D_HI = 4.0 * H_SG * min(SIGMAS), 4.0 * H_SG * max(SIGMAS)
F_NET = 0.5 * (F_LO + F_HI)

EM_LO, EM_HI = 0.1, 3.0


def re_gov(f):
    return sg.d_gov(2 * np.pi * f).real


def crossing(lo=0.3, hi=2.0, tol=1e-6):
    a, b = lo, hi
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
    print("  Re at 1.0 Hz = %+.2f pu; at %.2f Hz = %+.2f pu"
          % (re_gov(1.0), F_NET, re_gov(F_NET)))
    print("  net from ringdown: %.2f pu (%.2f-%.2f)" % (D_NET, D_LO, D_HI))

    fig, (axT, axB) = plt.subplots(
        2, 1, figsize=(0.85 * st.TEXTWIDTH_IN, 4.2), sharex=True,
        gridspec_kw=dict(height_ratios=[1.0, 1.15], hspace=0.16))

    for ax in (axT, axB):
        ax.axvspan(f0, EM_HI, color=BAND, alpha=0.5, zorder=0)
        ax.axhline(0.0, color="0.55", lw=0.9, zorder=1)
        ax.semilogx(f, re, color=BLUE, lw=1.9, zorder=4)
        ax.grid(True, which="both", alpha=0.28)

    # ---- top: magnitude comparison -------------------------------
    axT.semilogx(f, np.full_like(f, sg.D_GFM), color=RED, lw=2.0,
                 zorder=4,
                 label=r"grid-forming, filtered-droop coefficient "
                       r"$1/m_p=100$ pu")
    axT.plot([], [], color=BLUE, lw=1.9,
             label="synchronous, governor path (GGOV1)")
    axT.errorbar([F_NET], [D_NET], yerr=[[D_NET - D_LO], [D_HI - D_NET]],
                 xerr=[[F_NET - F_LO], [F_HI - F_NET]], fmt="D", ms=6,
                 color=NETC, mec="k", mew=0.7, ecolor=NETC,
                 elinewidth=1.0, capsize=2.5, zorder=6,
                 label="synchronous, net from ringdown: %.1f pu" % D_NET)
    axT.set_ylim(-8, 118)
    axT.set_yticks([0, 25, 50, 75, 100])
    axT.legend(loc="center left", fontsize=8, framealpha=0.95)
    axT.set_ylabel(r"$D_{\mathrm{eq}}$ (pu)")

    # ---- bottom: the machine's own range -------------------------
    axB.errorbar([F_NET], [D_NET], yerr=[[D_NET - D_LO], [D_HI - D_NET]],
                 xerr=[[F_NET - F_LO], [F_HI - F_NET]], fmt="D", ms=6,
                 color=NETC, mec="k", mew=0.7, ecolor=NETC,
                 elinewidth=1.0, capsize=2.5, zorder=6)
    axB.annotate("net damping from ringdown, %.1f pu\n"
                 "(0.85 to 1.0 Hz mode, all-machine bus-14 case);\n"
                 "the excess over the governor path is not\n"
                 "separately measured" % D_NET,
                 xy=(F_NET, D_NET), xytext=(0.0035, 15.5),
                 fontsize=7.6, color=INK, zorder=5,
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
             "governor path negative\n"
             r"above %.3f Hz, inside the" "\n"
             "0.1 to 3 Hz swing band" % f0,
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
