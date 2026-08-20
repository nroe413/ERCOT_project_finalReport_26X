"""Report-format regeneration of fig7_smib_gfm_panel (report
fig:smibgfm): single REGFM_A1 on an infinite bus through a bolted 3PG
fault -- V, I, P, Q and droop frequency, five stacked rows.

The historical PNG (smib_1gfm_3pg_panel.png, origin/SOW_task_4) was the
"companion panel" of plot_smib_fault.py rendered at 11x10 in / 150 dpi.
This regeneration reuses that module's constants and its data file
SMIB_1GFM_3PG_PSD.csv (written by run_3PG_fault.py; live copy in the
sharp-jackson-1e89b8 worktree, read-only here) and re-renders at the
true print size: the report includes it at width=0.72\\textwidth
= 4.68 in.  Same content: fault window shaded, x limited to 2 s ..
fault+7 s, one blue trace per row.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

SRC = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
           r"\sharp-jackson-1e89b8\single_machine_infinite_bus_1GFMvalidation")
OUT = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
           r"\upbeat-jones-67c8d3\report_26X\overleaf\figures")

sys.path.insert(0, str(SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plot_smib_fault as psf                   # noqa: E402
import figstyle_26x as st                       # noqa: E402

st.apply()   # AFTER importing plot_smib_fault (it clobbers rcParams)

BLUE = "#1f77b4"


def main():
    df = pd.read_csv(psf.CSV)                   # sharp-jackson data file
    t = df["TIME"].values
    t_end = float(t[-1])

    sigs = [("V_pu", "V (pu)"), ("I_pu", "I (pu)"), ("P_pu", "P (pu)"),
            ("Q_pu", "Q (pu)"), ("f_drp", "f (Hz)")]
    sigs = [(c, lbl) for c, lbl in sigs if c in df.columns]

    width = 0.72 * st.TEXTWIDTH_IN              # 4.68 in
    fig, axes = plt.subplots(len(sigs), 1, figsize=(width, 5.0),
                             sharex=True)
    for ax, (c, lbl) in zip(np.atleast_1d(axes), sigs):
        ax.axvspan(psf.FAULT_T, psf.FAULT_T + psf.FAULT_DUR,
                   color="#cccccc", alpha=0.5)
        ax.plot(t, df[c].values, color=BLUE, lw=0.8)
        ax.set_ylabel(lbl)
        ax.grid(True, alpha=0.3)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
        ax.tick_params(labelsize=9)
    np.atleast_1d(axes)[-1].set_xlabel("Time (s)")
    np.atleast_1d(axes)[-1].set_xlim(2.0, min(t_end, psf.FAULT_T + 7.0))

    out = OUT / "fig7_smib_gfm_panel.png"
    fig.savefig(out, dpi=600)
    print("wrote", out)


if __name__ == "__main__":
    main()
