"""Report-format regeneration of the E_max-saturation figure (report
fig:edrp). Same raw measured channels as the meeting figure -- the
T = 0.925 s boundary run's E_drp and V_pu columns read directly from
GFM_CCT_T0p925.csv with no smoothing or interpolation -- resized to
its true print width (0.85\\textwidth = 5.52 in), CMU Serif 11 pt.
Annotation text trimmed; the mechanism narrative lives in the caption.
"""
import csv
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
           r"\sharp-jackson-1e89b8\experiments\cct_smib_sync")
OUT = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
           r"\upbeat-jones-67c8d3\report_26X\overleaf\figures")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import figstyle_26x as st   # noqa: E402

st.apply()
CSV = SRC / "runs_gfm" / "T0p925" / "GFM_CCT_T0p925.csv"
EMAX, T_FLT, T_DUR = 1.15, 3.0, 0.925


def main():
    t, e, v = [], [], []
    with open(CSV) as f:
        for row in csv.DictReader(f):
            t.append(float(row["TIME"]))
            e.append(float(row["E_drp"]))
            v.append(float(row["V_pu"]))
    t, e, v = np.array(t), np.array(e), np.array(v)

    fig, ax = plt.subplots(figsize=(0.85 * st.TEXTWIDTH_IN, 3.1))
    ax.grid(alpha=0.3)
    ax.axvspan(T_FLT, T_FLT + T_DUR, color="0.85", zorder=0)
    ax.axhline(EMAX, color="k", ls="--", lw=1.4,
               label=r"$E_{\max}$ dial = 1.15 pu")
    ax.plot(t, e, color="tab:red", lw=1.6,
            label=r"PSCAD (EMT): command $E_{\mathrm{drp}}$")
    ax.plot(t, v, color="tab:blue", lw=1.1, alpha=0.65,
            label=r"PSCAD (EMT): terminal $V_t$")
    ax.axhline(0.999, color="tab:blue", ls=":", lw=1.0,
               label=r"$V_{req}$ = 0.999 pu")
    ax.text(T_FLT + 0.5 * T_DUR, 0.15, "fault\n(0.925 s)",
            ha="center", fontsize=9, color="0.25")
    ax.annotate("railed at $E_{\\max}$ through\nthe post-clear swing",
                xy=(5.1, 1.148), xytext=(5.4, 0.72),
                fontsize=9,
                arrowprops=dict(arrowstyle="-|>", lw=1.2,
                                color="0.25"))
    ax.set_xlabel("time (s)")
    ax.set_ylabel("voltage (pu, device base)")
    ax.set_xlim(2.0, 9.5)
    ax.set_ylim(0.0, 1.32)
    ax.legend(fontsize=8.5, loc="lower right")
    fig.savefig(OUT / "edrp_saturation_meeting.png", dpi=600)
    print("wrote", OUT / "edrp_saturation_meeting.png")


if __name__ == "__main__":
    main()
