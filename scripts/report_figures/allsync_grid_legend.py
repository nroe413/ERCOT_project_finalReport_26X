"""PK comment 33: the all-machine bus-14 2x2 figure (report
fig:allsync, file fig2_allSYNC_3PG_2x2.png) had no channel legend.
Same panels as aggregate_report.mode_grid (imported), plus a shared
bus legend under the grid.  Writes to report_26X/prism/figures.

Usage:  python allsync_grid_legend_prism.py
"""
import sys
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_paths as rp  # noqa: E402

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aggregate as ar                          # noqa: E402

OUT = rp.OUT
CSV = rp.experiment(r"fault_3PG_bus14_0GFM\runs\3PG_at_bus14_t3p0s_5cyc_norecl_30s\data_20260608_153845.csv")


def main():
    df = ar.load(CSV, ["Vrms", "Irms", "P", "Q"])
    s = ar.stride(df)
    fig, axes = plt.subplots(2, 2, figsize=(ar.st.TEXTWIDTH_IN, 5.0))
    rects = {"Vrms": [0.35, 0.10, 0.62, 0.52],
             "Irms": [0.35, 0.42, 0.62, 0.52],
             "P":    [0.35, 0.10, 0.62, 0.42],
             "Q":    [0.35, 0.55, 0.62, 0.40]}
    for ax, sig in zip(axes.flat, ["Vrms", "Irms", "P", "Q"]):
        ar.draw(ax, df, sig, s, lw=0.5)
        ar.add_zoom(ax, df, sig, rects[sig])
        ax.set_ylabel(ar.YLBL[sig], fontsize=9)
        ax.tick_params(labelsize=8)
    for ax in axes[1]:
        ax.set_xlabel("time (s)", fontsize=9)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=8, fontsize=7.5, frameon=False,
               loc="outside lower center", handlelength=1.6,
               columnspacing=1.0)
    fig.savefig(OUT / "fig2_allSYNC_3PG_2x2.png", dpi=600)
    print("wrote", OUT / "fig2_allSYNC_3PG_2x2.png", "buses:", labels)


if __name__ == "__main__":
    main()
