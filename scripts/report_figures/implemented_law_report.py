"""Report-format regeneration of the revised-model practical-range
sweep (report fig:implpractical). Same model curve and measured
brackets as the meeting figure (analytic_implemented_law.py), with the
printed closed-form equation block REMOVED per the 2026-08-07 review
(the closed form is Eq. (34) in the report text) and the figure sized
at its true print width (0.9\\textwidth = 5.85 in), CMU Serif 11 pt.
"""
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
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analytic_implemented_law import tcr_implemented   # noqa: E402
import figstyle_26x as st                              # noqa: E402

st.apply()

# EMT brackets, vendor-default arms (verbatim from
# analytic_implemented_law.main(); practical arms measured 2026-08-05)
EMT_STOCK = {1.0: (0.640, 0.643), 1.2: (0.744, 0.747),
             1.5: (0.840, 0.843),
             2.0: (0.925, 0.931), 2.5: (0.975, 0.982),
             3.0: (1.006, 1.012), 4.0: (1.050, 1.056),
             6.0: (1.100, 1.150), 10.0: (1.150, 1.163),
             12.0: (1.163, 1.169), 15.0: (1.163, 1.169)}


def main():
    kk = np.linspace(1.0, 8.0, 160)
    tt = np.array([tcr_implemented(k, 1.15)[0] for k in kk])
    fig, ax = plt.subplots(figsize=(0.9 * st.TEXTWIDTH_IN, 3.4))
    ax.grid(alpha=0.3)
    ax.axhline(1.30, color="k", ls="--", lw=1.3,
               label="limit-free Sauer & Pai analytical: 1.30 s")
    ax.plot(kk, tt, color="tab:blue", lw=2.0,
            label=r"analytical model, $E_{\max}=1.15$ (vendor dials)")
    first = True
    for k, (lo, hi) in sorted(EMT_STOCK.items()):
        if k > 8:
            continue
        ax.plot([k, k], [lo, hi], color="k", lw=5.0,
                solid_capstyle="butt",
                label="PSCAD (EMT) CCT, vendor default"
                if first else None)
        first = False
    ax.set_xlabel(r"current limit $I_{\max F}$ (pu on own base)")
    ax.set_ylabel("CCT (s)")
    ax.set_xlim(0.8, 8.2)
    ax.set_ylim(0.58, 1.33)
    ax.legend(loc="lower right", fontsize=9)
    fig.savefig(OUT / "implemented_law_practical_meeting.png", dpi=600)
    print("wrote", OUT / "implemented_law_practical_meeting.png")


if __name__ == "__main__":
    main()
