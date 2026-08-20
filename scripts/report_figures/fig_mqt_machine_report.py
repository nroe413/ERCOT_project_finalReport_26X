"""Machine counterparts of the Sec. 2.3 model-quality figures, from the
typicalgt_mqt_battery experiment (DWG tests 1-9 on the Gen-32
synchronous machine, claude/sharp-jackson-1e89b8, runs of 2026-08-13).

  fig3_mqt_machine_lvrt.png
      Test 2 (LVRT ERCOT Legacy) on the machine, the analog of the
      archival GFM raster fig3_mqt_legacy_lvrt -- but re-typeset from
      data, which the GFM figure never could be (its run is lost).
      2x3 small multiples over the full 40 s record: V, I, Ef on top;
      P, Q, f on the bottom.  The Ef panel carries the battery's
      headline finding: the ETRAN-converted ESST4B field voltage rails
      at its ceiling at the first transient and does not return after
      the voltage recovers.

  fig3_mqt_machine_vstep.png
      Test 5 (small voltage step up, 1.00 -> 1.03 pu at t = 3 s) in
      the same 2x3 layout and 3-s viewing window as the
      fig3_mqt_pnnl_vs_nlr cross-check, so the machine's step response
      reads side-by-side with the GFM one.  The profiles differ
      (PMView 3.5 steps to 1.03; the 2.4 benchmark stepped to 1.02),
      so this is a layout twin, not an identical-drive overlay.

Machine channels are recorded in physical units; converted to pu on
the machine base (650 MVA, 230 kV L-L RMS -> Ibase 1.6319 kA).
"""
import sys
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator

REPO = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
            r"\upbeat-jones-67c8d3")
EXP = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
           r"\sharp-jackson-1e89b8\experiments\typicalgt_mqt_battery")
OUT = REPO / "report_26X" / "overleaf" / "figures"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import figstyle_26x as st                       # noqa: E402

st.apply()

BLUE = "#1f77b4"
DPI = 600
SBASE = 650.0
VBASE = 230.0
IBASE = SBASE / (3.0 ** 0.5 * VBASE)


def load(test_dir):
    csv = sorted((EXP / "runs" / test_dir).glob("data_*.csv"))[-1]
    df = pd.read_csv(csv)
    return pd.DataFrame({
        "TIME": df["TIME"],
        "V_pu": df["PMView.Vsource"] / VBASE,
        "I_pu": df["PMView.Ipoi"] / IBASE,
        "P_pu": df["PMView.Ppoi"] / SBASE,
        "Q_pu": df["PMView.Qpoi"] / SBASE,
        "f_poi": df["PMView.Fpoi"],
        "Ef_pu": df["G_32_0_1_DYR.Ef"],
    })


LABEL = {"V_pu": "V (pu)", "I_pu": "I (pu)", "Ef_pu": r"$E_f$ (pu)",
         "P_pu": "P (pu)", "Q_pu": "Q (pu)", "f_poi": "f (Hz)"}


def grid_figure(df, t0, t1, xticks, dst_name, height=3.5):
    fig = plt.figure(figsize=(st.TEXTWIDTH_IN, height))
    gs = fig.add_gridspec(2, 3)
    # figstyle turns on constrained layout, which ignores gridspec
    # margins; "outside" is the CL-aware way to reserve legend space
    fig.legend(
        handles=[Line2D([], [], color=BLUE, lw=1.4,
                        label="Gen-32 synchronous generator "
                              "(GENROU + ESST4B)")],
        loc="outside upper center", frameon=True,
        handlelength=2.0, borderpad=0.5)
    cells = {"V_pu": gs[0, 0], "I_pu": gs[0, 1], "Ef_pu": gs[0, 2],
             "P_pu": gs[1, 0], "Q_pu": gs[1, 1], "f_poi": gs[1, 2]}
    w = df[(df.TIME >= t0) & (df.TIME <= t1)]
    for col, cell in cells.items():
        ax = fig.add_subplot(cell)
        ax.plot(w.TIME, w[col], color=BLUE, lw=1.1)
        ax.set_ylabel(LABEL[col])
        ax.set_xlim(t0, t1)
        ax.set_xticks(xticks)
        lo, hi = w[col].min(), w[col].max()
        pad = 0.10 * (hi - lo) if hi > lo else 0.05
        ax.set_ylim(lo - pad, hi + pad)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
        ax.grid(True, alpha=0.3)
        if cell.rowspan.start == 1:
            ax.set_xlabel("Time (s)")
        else:
            ax.tick_params(labelbottom=False)
    dst = OUT / dst_name
    fig.savefig(dst, dpi=DPI)
    plt.close(fig)
    print("wrote", dst_name)
    return dst


if __name__ == "__main__":
    # LVRT: full record, latch visible after the 27 s recovery
    grid_figure(load("test_02_LVRT_ERCOT_Legacy"), 0.5, 40.0,
                [0, 10, 20, 30, 40], "fig3_mqt_machine_lvrt.png")
    # V-step: the machine's excitation response is far slower than the
    # GFM's, so the window runs to the profile's second step at 23 s
    # rather than the GFM cross-check's 3-s span
    grid_figure(load("test_05_V_Up"), 2.0, 20.0, [5, 10, 15, 20],
                "fig3_mqt_machine_vstep.png")
