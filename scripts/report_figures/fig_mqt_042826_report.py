"""Two Sec. 2.3 model-quality figures rebuilt from data in the report's
figure standard, from the 2026-04-28 ERCOT meeting deck (slides 5, 6, 8
of presentations/ercot_meetings/042826/meeting_update_042826_r2.pptx).

  fig3_mqt_vstep_down.png   (slides 5 + 6 as one two-panel figure)
      POI voltage of PNNL REGFM_A1 (left) and NLR Kenyon (right) after
      the same 1.00 -> 0.97 pu voltage step at t = 5 s in the PMView 2.4
      harness. Same y-axis on both panels so the NLR limit cycle reads
      against the PNNL settle directly.
      Data: A1_VoltDwn_PSD_20260428_095922.csv and
            NLR_VoltDwn_PSD_20260428_102111.csv (the newest CSVs before
            the deck's 11:29 save; their traces match the slides).

  fig3_mqt_nlr_limiter_chatter.png   (slide 8)
      NLR Kenyon HVRT (legacy) run, current-limiter feedback loop:
      voltage-loop error, dq current against the limiter ceiling, and
      the limiter status flag. Data: MQT_r00002 channels 96, 134-136
      (+ Vsource 6) extracted to nlr_hvrt_limiter_signals.csv from the
      gfm_validation_task_2 branch. The transition count is computed
      here from the status channel (the deck quoted 199 with an
      unstated threshold; the 0.5 threshold gives the number printed).

Both are re-typeset: TeX Gyre Pagella, document font sizes, no titles
(the caption carries them), colors matching fig3_mqt_pnnl_vs_nlr
(PNNL red, NLR blue).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

REPO = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
            r"\upbeat-jones-67c8d3")
SRC = REPO / "report_26X" / "figures" / "source"
OUT = REPO / "report_26X" / "overleaf" / "figures"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import figstyle_26x as st                       # noqa: E402

st.apply()
RED, BLUE, GREEN, INK = "#d62728", "#1f77b4", "#2ca02c", "#333333"
DPI = 600


def vstep_down():
    dp = pd.read_csv(SRC / "A1_VoltDwn_PSD_20260428_095922.csv")
    dn = pd.read_csv(SRC / "NLR_VoltDwn_PSD_20260428_102111.csv")
    T0, T1 = 4.0, 7.0
    wp = dp[(dp.TIME >= T0) & (dp.TIME <= T1)]
    wn = dn[(dn.TIME >= T0) & (dn.TIME <= T1)]
    fig, axes = plt.subplots(1, 2, figsize=(st.TEXTWIDTH_IN, 2.5),
                             sharey=True)
    for ax, w, c, lab in [(axes[0], wp, RED, "PNNL REGFM_A1"),
                          (axes[1], wn, BLUE, "NLR Kenyon")]:
        ax.plot(w.TIME, w.V_pu, color=c, lw=1.1, label=lab)
        ax.set_xlim(T0, T1)
        ax.set_xticks([4, 5, 6, 7])
        ax.set_xlabel("Time (s)")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="upper right", frameon=True)
    axes[0].set_ylabel("V (pu)")
    axes[0].set_ylim(0.94, 1.02)
    axes[0].yaxis.set_major_locator(MaxNLocator(nbins=5))
    dst = OUT / "fig3_mqt_vstep_down.png"
    fig.savefig(dst, dpi=DPI)
    plt.close(fig)
    print("wrote", dst.name)


def limiter_chatter():
    d = pd.read_csv(SRC / "nlr_hvrt_r00002" / "nlr_hvrt_limiter_signals.csv")
    T1 = 35.0
    d = d[d.TIME <= T1]
    st_flag = (d.Status > 0.5).astype(int)
    n_trans = int((st_flag.diff().abs() > 0).sum())
    ibase_ka = 1.0  # plotted in kA as recorded (limiter ceiling is a
    #                 physical-unit dial in this model)
    fig, axes = plt.subplots(3, 1, figsize=(st.TEXTWIDTH_IN, 4.6),
                             sharex=True,
                             gridspec_kw={"height_ratios": [1, 1.2, 0.6]})
    ax = axes[0]
    ax.plot(d.TIME, d.V_error, color=RED, lw=0.7)
    ax.set_ylabel(r"$V_{\mathrm{err}}$ (pu)")
    ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
    ax = axes[1]
    ax.plot(d.TIME, d.Idq / 1e3, color=BLUE, lw=0.7, label=r"$I_{dq}$")
    ax.plot(d.TIME, d.Idq_limit / 1e3, color=GREEN, lw=1.2, ls="--",
            label=r"$I_{dq}$ limit")
    ax.set_ylabel("Current (kA)")
    ax.legend(loc="upper left", frameon=True)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
    ax = axes[2]
    ax.plot(d.TIME, st_flag, color=RED, lw=0.7)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["off", "active"])
    ax.set_ylabel("Limiter")
    ax.set_xlabel("Time (s)")
    ax.set_xlim(0, T1)
    ax.text(0.99, 0.82, "%d limiter transitions" % n_trans,
            transform=ax.transAxes, ha="right", va="top", fontsize=9)
    for a in axes:
        a.grid(True, alpha=0.3)
    dst = OUT / "fig3_mqt_nlr_limiter_chatter.png"
    fig.savefig(dst, dpi=DPI)
    plt.close(fig)
    print("wrote", dst.name, "transitions =", n_trans)
    return n_trans


if __name__ == "__main__":
    vstep_down()
    limiter_chatter()
