"""Split the old two-panel fig3_mqt_pair into two full-width figures.

The composite gave each panel roughly half of \\textwidth, so the
regenerated right panel was typeset at 7-8 pt source sizes squeezed
into 2.3 in of width -- the report audit measured its legend at 2.6 pt
equivalent and flagged it as the worst figure in the document.  The
cure is to stop sharing the text block:

  fig3_mqt_legacy_lvrt.png
      The archival PMView raster (Test 2, LVRT ERCOT Legacy, POI P & Q
      with source voltage), copied BYTE-FOR-BYTE from
      figures/source/fig3_mqt_lvrt_pq_vrms.png.  The underlying run is
      lost -- every branch in the repo carries this test only as PNGs
      (checked: no .out/.csv/.inf under any r00002_LVRT* path on any
      ref) -- so it cannot be re-typeset, only shown larger.  At
      2673x1414 px placed at width=\\textwidth it lands at 411 dpi
      instead of the 629 dpi it had inside the composite, i.e. its
      lettering grows 1.53x.

  fig3_mqt_pnnl_vs_nlr.png
      The 1.02 pu voltage-step cross-check, rebuilt from the CSVs at
      6.5 x 3.2 in with every string at the document's own sizes
      (11 pt labels, 10 pt ticks and legend) -- nothing is shrunk to
      make it fit.  Five signals laid out as a 2x3 small-multiple grid
      (V, I on top; P, Q, f on the bottom) with the legend occupying
      the free top-right cell, so each panel is ~1.5 x 1.3 in instead
      of the old 2.3 x 0.35 in slivers.

Data provenance (unchanged from fig3_mqt_pair_report.py):
    PNNL REGFM_A1 : 2. Voltage Step Up_pnnl/A1_VoltUp_PSD_20260513_132718.csv
    NLR Kenyon    : 2. Voltage Step Up_NLR/NLR_VoltUp_PSD_20260513_133002.csv
Both live under SOW_task_2/PMView2.4/pnnlAndNLRBench/4. PSCAD_PSSE_Validation/
on origin/gfm_validation_task_2 and are git-show'n into figures/source/
(the gfm_validation_task_2_ro worktree the old script read from has
since been removed).  Values are plotted as recorded; the only viewing
change is that the y axes now bound the plotted 4-7 s window instead
of the whole 0-7 s record, whose start-up transient previously pinned
every axis to zero and flattened the response into a hairline.
"""
import struct
import sys
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_paths as rp  # noqa: E402

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator

REPO = rp.ROOT
SRC = rp.DATA
OUT = rp.OUT





CSV_PNNL = SRC / "A1_VoltUp_PSD_20260513_132718.csv"
CSV_NLR = SRC / "NLR_VoltUp_PSD_20260513_133002.csv"



sys.path.insert(0, str(Path(__file__).resolve().parent))
import figstyle_26x as st                       # noqa: E402

st.apply()

RED, BLUE = "#d62728", "#1f77b4"
DPI = 600
T0, T1 = 4.0, 7.0



def png_size(path):
    b = path.read_bytes()[:24]
    return struct.unpack(">II", b[16:24])


def make_legacy():
    """fig3_mqt_legacy_lvrt.png is typeset from the 2026-09-18 re-run of the test by
    fig_mqt_regfma1_lvrt.py and is not written here."""
    return rp.OUT / "fig3_mqt_legacy_lvrt.png"


def make_overlay():
    dp = pd.read_csv(CSV_PNNL)
    dn = pd.read_csv(CSV_NLR)
    wp = dp[(dp.TIME >= T0) & (dp.TIME <= T1)]
    wn = dn[(dn.TIME >= T0) & (dn.TIME <= T1)]

    fig = plt.figure(figsize=(st.TEXTWIDTH_IN, 3.2))
    gs = fig.add_gridspec(2, 3)
    cells = {"V_pu": gs[0, 0], "I_pu": gs[0, 1],
             "P_pu": gs[1, 0], "Q_pu": gs[1, 1], "f_drp": gs[1, 2]}
    label = {"V_pu": "V (pu)", "I_pu": "I (pu)", "P_pu": "P (pu)",
             "Q_pu": "Q (pu)", "f_drp": "f (Hz)"}
    bottom = {"P_pu", "Q_pu", "f_drp"}

    for col, cell in cells.items():
        ax = fig.add_subplot(cell)
        ax.plot(wp.TIME, wp[col], color=RED, lw=1.1)
        ax.plot(wn.TIME, wn[col], color=BLUE, lw=1.1, ls="--")
        ax.set_ylabel(label[col])
        ax.set_xlim(T0, T1)
        ax.set_xticks([4, 5, 6, 7])
        # bound y to the plotted window, not the 0-7 s start-up record
        lo = min(wp[col].min(), wn[col].min())
        hi = max(wp[col].max(), wn[col].max())
        pad = 0.10 * (hi - lo) if hi > lo else 0.05
        ax.set_ylim(lo - pad, hi + pad)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
        ax.grid(True, alpha=0.3)
        if col in bottom:
            ax.set_xlabel("Time (s)")
        else:
            ax.tick_params(labelbottom=False)

    ax_leg = fig.add_subplot(gs[0, 2])
    ax_leg.axis("off")
    ax_leg.legend(
        handles=[Line2D([], [], color=RED, lw=1.4, label="PNNL REGFM_A1"),
                 Line2D([], [], color=BLUE, lw=1.4, ls="--",
                        label="NLR GFM model")],
        loc="center", frameon=True, handlelength=2.0, borderpad=0.7,
        labelspacing=0.8)

    dst = OUT / "fig3_mqt_pnnl_vs_nlr.png"
    fig.savefig(dst, dpi=DPI)
    plt.close(fig)
    w, h = png_size(dst)
    print("overlay %s  %d x %d px  (%.2f x %.2f in at %d dpi)"
          % (dst.name, w, h, w / DPI, h / DPI, DPI))
    return dst


if __name__ == "__main__":
    make_legacy()
    make_overlay()
