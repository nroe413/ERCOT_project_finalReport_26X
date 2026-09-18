"""Report figure fig:mqt (fig3_mqt_legacy_lvrt.png): PNNL REGFM_A1 under PMView 2.4 Test 2
(LVRT_ERCOT_Legacy), typeset from data in the same 2x3 layout as the machine's Figure 14
(fig_mqt_machine_report.py): V, I, E on top; P, Q, f on the bottom.

Until 2026-09-18 this figure was an archived raster whose run no longer existed.  The record is the
re-run of mqt/pmview24_regfm_a1/PMVIEW24_pnnl_GFM/pnnlREGFMA1mQT.pscx with the multiple-run range set to
test 2 (run_lvrt_headless.py there; Qreq 0.2), which reproduces the archived figure: P 0.60 and
Q 0.10 pu before the dip, Q 0.42 pu on the 0.90 pu plateau, P peak 1.01 pu at 4.15 s, recovery swings
to P -1.59 / +1.21 pu and Q -1.78 pu.

Channels: Vsource (PMView source voltage, pu), Ppoi and Qpoi (point of interconnection, pu), and the
model's own outputs I_pu (internal current magnitude, the quantity compared with ImaxF), E_drp
(internal voltage magnitude) and f_drp (droop frequency, Hz).  The first run from the study writes
the extract data/report_figure_data/mqt_regfma1_lvrt/test_02_LVRT_ERCOT_Legacy.csv (every second sample,
0.52 ms); later runs, and the public-repository copy of this script, read the extract.
"""
import sys
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import repo_paths as rp                         # noqa: E402
import figstyle_26x as st                       # noqa: E402

st.apply()

OUT = rp.OUT
SRC = rp.DATA / "mqt_regfma1_lvrt"
RUN = rp.EXPERIMENTS / "regfma1_pmview24_lvrt_rerun" / "runs" / "test_02_LVRT_ERCOT_Legacy"
COLS = ["TIME", "Vsource", "I_pu", "E_drp", "Ppoi", "Qpoi", "f_drp"]
RED = "#c0392b"
IMAXF = 2.0
DPI = 600
T0, T1 = 0.5, 33.0

LABEL = {"Vsource": "V (pu)", "I_pu": "I (pu)", "E_drp": r"$E$ (pu)",
         "Ppoi": "P (pu)", "Qpoi": "Q (pu)", "f_drp": "f (Hz)"}


def load():
    ext = SRC / "test_02_LVRT_ERCOT_Legacy.csv"
    if ext.exists():
        return pd.read_csv(ext)
    csv = sorted(RUN.glob("data_*.csv"), key=lambda p: p.stat().st_mtime)[-1]
    df = pd.read_csv(csv, usecols=COLS)[COLS].iloc[::2].reset_index(drop=True)
    SRC.mkdir(parents=True, exist_ok=True)
    df.to_csv(ext, index=False, float_format="%.6g")
    print("extract written:", ext, "from", csv.name)
    return df


def main():
    df = load()
    fig = plt.figure(figsize=(st.TEXTWIDTH_IN, 3.5))
    gs = fig.add_gridspec(2, 3)
    fig.legend(handles=[Line2D([], [], color=RED, lw=1.4, label="PNNL REGFM_A1 grid-forming inverter"),
                        Line2D([], [], color="0.35", lw=0.9, ls="--", label=r"$I_{\max F}=2.0$ pu")],
               loc="outside upper center", frameon=True, handlelength=2.0, borderpad=0.5, ncol=2)
    cells = {"Vsource": gs[0, 0], "I_pu": gs[0, 1], "E_drp": gs[0, 2],
             "Ppoi": gs[1, 0], "Qpoi": gs[1, 1], "f_drp": gs[1, 2]}
    w = df[(df.TIME >= T0) & (df.TIME <= T1)]
    for col, cell in cells.items():
        ax = fig.add_subplot(cell)
        ax.plot(w.TIME, w[col], color=RED, lw=1.0)
        if col == "I_pu":
            ax.axhline(IMAXF, color="0.35", lw=0.9, ls="--")
        ax.set_ylabel(LABEL[col])
        ax.set_xlim(0.0, T1)
        ax.set_xticks([0, 10, 20, 30])
        lo, hi = w[col].min(), w[col].max()
        pad = 0.10 * (hi - lo) if hi > lo else 0.05
        ax.set_ylim(lo - pad, hi + pad)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
        ax.grid(True, alpha=0.3)
        if cell.rowspan.start == 1:
            ax.set_xlabel("Time (s)")
        else:
            ax.tick_params(labelbottom=False)
    dst = OUT / "fig3_mqt_legacy_lvrt.png"
    fig.savefig(dst, dpi=DPI)
    plt.close(fig)
    print("wrote", dst)
    t = df.TIME.values
    pre = (t > 2.0) & (t < 2.9)
    print("  before the dip: V %.3f, I %.3f, E %.3f, P %.3f, Q %.3f pu; I max %.3f pu; f %.2f to %.2f Hz"
          % (df.Vsource[pre].mean(), df.I_pu[pre].mean(), df.E_drp[pre].mean(), df.Ppoi[pre].mean(), df.Qpoi[pre].mean(),
             w.I_pu.max(), w.f_drp.min(), w.f_drp.max()))


if __name__ == "__main__":
    main()
