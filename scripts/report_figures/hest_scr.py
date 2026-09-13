"""Report figure fig:hestscr (narr_hest_vs_scr.png): the PMView inertia estimate of the
droop-controlled inverter versus short-circuit ratio, referred to the imposed ramp
(report Eq. 9) and to the inverter's internal droop frequency (experiment
agsesr_inertia_SCR_fdrp on SOW_task_4, 2026-09-12; comment 56).

Input: data/report_figure_data/hest_scr/hest_internal_metrics.json (from experiments/agsesr_inertia_SCR_fdrp on SOW_task_4)
(per SCR: H_imp(T), H_int(T), rocof_int(T), track_err_Hz(T) for T = 0.1..0.5 s).
Size 0.8 textwidth x 3.0 in, figstyle contract.
"""
import json
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
import figstyle_26x as st  # noqa: E402

st.apply()
BLUE, RED, INK = "#1f77b4", "#c0392b", "#2d3338"
H_THEORY = 0.010 / (2 * 0.01) + 0.5 / (4 * 0.01)     # H + T/(4 m_p) at T = 0.5 s = 13.0 s


def main():
    m = json.load(open(rp.DATA / "hest_scr" / "hest_internal_metrics.json"))   # shipped metrics of the SCR sweep
    scr = np.array(sorted(float(k) for k in m))
    key = lambda s: "%g" % s
    h_imp = np.array([m[key(s)]["H_imp"][-1] for s in scr])
    h_int = np.array([m[key(s)]["H_int"][-1] for s in scr])
    roc = np.array([-m[key(s)]["rocof_int"][-1] for s in scr])
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(0.95 * st.TEXTWIDTH_IN, 3.0), gridspec_kw=dict(width_ratios=[1.35, 1.0]))
    ax.plot(scr, h_imp, "o-", color=BLUE, lw=1.6, ms=5, label="referred to the imposed $-1$ Hz/s ramp (Eq.~9)")
    ax.plot(scr, h_int, "s-", color=RED, lw=1.6, ms=5, label="referred to the internal droop frequency")
    ax.axhline(H_THEORY, color=INK, ls=":", lw=1.0, label="analytic $H_{\\mathrm{eq}}+T/(4m_{\\mathrm{p}})=13.0$ s")
    ax.set_xscale("log")
    ax.set_xticks(scr); ax.set_xticklabels(["%g" % s for s in scr])
    ax.set_xlabel("short-circuit ratio")
    ax.set_ylabel(r"$H_{\mathrm{est}}$ (s)")
    ax.set_ylim(5, 14)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="lower right", fontsize=7.4, framealpha=0.95)
    ax.set_title("(a) inertia estimate, 0.5 s window", fontsize=9, loc="left")
    ax2.plot(scr, roc, "d-", color=RED, lw=1.6, ms=5)
    ax2.axhline(1.0, color=BLUE, ls="--", lw=1.0)
    ax2.text(2.1, 1.008, "imposed ramp, 1 Hz/s", fontsize=7.4, color=BLUE, va="bottom")
    ax2.set_xscale("log")
    ax2.set_xticks(scr); ax2.set_xticklabels(["%g" % s for s in scr])
    ax2.set_xlabel("short-circuit ratio")
    ax2.set_ylabel("internal frequency ramp (Hz/s)")
    ax2.set_ylim(0.6, 1.05)
    ax2.grid(True, which="both", alpha=0.3)
    ax2.set_title("(b) slope of the droop frequency", fontsize=9, loc="left")
    fig.savefig(OUT / "narr_hest_vs_scr.png", dpi=600)
    print("wrote", OUT / "narr_hest_vs_scr.png")
    for s, a, b, c in zip(scr, h_imp, h_int, roc):
        print("  SCR %4g  H_imp %.2f  H_int %.2f  rocof_int %.3f" % (s, a, b, c))


if __name__ == "__main__":
    main()
