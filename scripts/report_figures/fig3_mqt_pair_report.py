"""Report-format regeneration of fig3_mqt_pair (report fig:mqt) at its
true print width (\\textwidth = 6.5 in), replacing the 200-dpi PNG
re-tile from build_assets.py.

LEFT panel -- representative PMView DWG test on REGFM_A1: Test 2
  (LVRT, ERCOT Legacy), POI P & Q with source voltage.
  DATA LOST -- placed as the historical raster (no added text, never
  above native resolution).  Provenance: the committed
  plots/r00002_LVRT_ERCOT_Legacy/pq_vrms_overlay.png was made at
  commit a4b8e3a (2026-04-21) by plot_gfm_tests.py, but the r00002
  .out files committed at a4b8e3a are a *V-step-up* run, the ones at
  85c5558/9ec00df are a *multi-fault* run, and no other copy of the
  LVRT run exists on disk or in any branch (all committed
  pnnlREGFMA1mQT runs probed for the LVRT signature: none match).
  The PSCAD runs were overwritten between plotting and committing, so
  the LVRT panel exists ONLY as this PNG.  Its inner fonts therefore
  cannot be restyled.  The blob is fetched binary-safe from
  origin/gfm_validation_task_2 into figures/source/ (idempotent, same
  destination gather_figures.sh uses).

RIGHT panel -- the PNNL-vs-NLR overlay behind
  Case2_PNNL_vs_NLR_1p02_overlay.png (committed 16b52e5 without a
  script): regenerated as a true matplotlib panel.  Runs identified by
  settled values (V/I/P/Q at t about 7 s match the historical PNG):
    PNNL REGFM_A1 : 2. Voltage Step Up_pnnl/A1_VoltUp_PSD_20260513_132718.csv
    NLR Kenyon    : 2. Voltage Step Up_NLR/NLR_VoltUp_PSD_20260513_133002.csv
  1.02 pu source step at t = 5 s, plotted 4-7 s, five stacked rows
  (V, I, P, Q, f), PNNL red solid / NLR blue dashed as in the source.
  Data read from the read-only gfm_validation_task_2_ro worktree.

Layout note: the raster caps the left panel at 2673x1414 px, i.e. at
600 dpi it may occupy at most 4.45 x 2.36 in; the script asserts the
placed size stays at or below native resolution.
"""
import subprocess
import sys
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.image import imread
from matplotlib.ticker import MaxNLocator

W2 = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
          r"\gfm_validation_task_2_ro\SOW_task_2\PMView2.4")
VAL_DIR = W2 / "pnnlAndNLRBench" / "4. PSCAD_PSSE_Validation"
CSV_PNNL = (VAL_DIR / "2. Voltage Step Up_pnnl"
            / "A1_VoltUp_PSD_20260513_132718.csv")
CSV_NLR = (VAL_DIR / "2. Voltage Step Up_NLR"
           / "NLR_VoltUp_PSD_20260513_133002.csv")

REPO = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
            r"\upbeat-jones-67c8d3")
SRC = REPO / "report_26X" / "figures" / "source"
OUT = REPO / "report_26X" / "overleaf" / "figures"
LVRT_PNG = SRC / "fig3_mqt_lvrt_pq_vrms.png"
LVRT_GIT = ("origin/gfm_validation_task_2:SOW_task_2/PMView2.4/"
            "PMVIEW24_pnnl_GFM/plots/r00002_LVRT_ERCOT_Legacy/"
            "pq_vrms_overlay.png")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import figstyle_26x as st                       # noqa: E402

st.apply()

RED, BLUE = "#d62728", "#1f77b4"
DPI = 600


def fetch_lvrt_png():
    """git-show the historical LVRT overlay blob (idempotent)."""
    if LVRT_PNG.exists() and LVRT_PNG.stat().st_size > 100:
        return
    LVRT_PNG.parent.mkdir(parents=True, exist_ok=True)
    with open(LVRT_PNG, "wb") as fh:
        subprocess.run(["git", "show", LVRT_GIT], cwd=str(REPO),
                       stdout=fh, check=True)
    print("fetched", LVRT_PNG.name, LVRT_PNG.stat().st_size, "B")


def main():
    fetch_lvrt_png()
    im = imread(LVRT_PNG)
    ny, nx = im.shape[0], im.shape[1]          # 1414 x 2673 native

    fig = plt.figure(figsize=(st.TEXTWIDTH_IN, 3.2),
                     constrained_layout=False)

    # ---- left: historical raster, no added text, no upscale ---------
    box_w, box_h = 0.655, 0.96                  # figure fractions
    ax_img = fig.add_axes([0.0, 0.02, box_w, box_h])
    ax_img.imshow(im)
    ax_img.axis("off")
    # placed size in px at 600 dpi (image fills the box by width;
    # imshow keeps aspect, so height follows)
    placed_w_px = box_w * st.TEXTWIDTH_IN * DPI
    placed_h_px = placed_w_px * ny / nx
    assert placed_w_px <= nx and placed_h_px <= ny, (
        "raster would be upscaled beyond native resolution")
    print("left raster placed at %.0f x %.0f px (native %d x %d)"
          % (placed_w_px, placed_h_px, nx, ny))

    # ---- right: regenerated 1.02 pu PNNL-vs-NLR overlay -------------
    dp = pd.read_csv(CSV_PNNL)
    dn = pd.read_csv(CSV_NLR)
    rows = [("V_pu", "V (pu)"), ("I_pu", "I (pu)"), ("P_pu", "P (pu)"),
            ("Q_pu", "Q (pu)"), ("f_drp", "f (Hz)")]
    x0, xw = 0.755, 0.235
    y_top, y_bot, gap = 0.865, 0.13, 0.028
    row_h = (y_top - y_bot - 4 * gap) / 5
    axes = []
    for i, (col, lbl) in enumerate(rows):
        y = y_top - (i + 1) * row_h - i * gap
        ax = fig.add_axes([x0, y, xw, row_h],
                          sharex=axes[0] if axes else None)
        ax.plot(dp["TIME"], dp[col], color=RED, lw=0.8, label="PNNL")
        ax.plot(dn["TIME"], dn[col], color=BLUE, lw=0.8, ls="--",
                label="NLR")
        ax.set_ylabel(lbl, fontsize=8)
        ax.set_xlim(4.0, 7.0)
        ax.grid(True, alpha=0.3)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=3))
        ax.tick_params(labelsize=8)
        if i < 4:
            ax.tick_params(labelbottom=False)
        axes.append(ax)
    axes[0].set_title("1.02 pu step: PNNL vs NLR", fontsize=9)
    axes[0].legend(loc="lower right", fontsize=7, ncol=2,
                   borderpad=0.2, handlelength=1.4, columnspacing=0.8)
    axes[-1].set_xlabel("Time (s)", fontsize=9)

    out = OUT / "fig3_mqt_pair.png"
    fig.savefig(out, dpi=DPI)
    print("wrote", out)


if __name__ == "__main__":
    main()
