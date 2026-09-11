"""Report-format regeneration of the current-limit sweep
(report fig:ilimitsweep, file ilimit_sweep_meeting.png).

Same content as make_meeting_figs.ilimit_sweep(with_eq=False) in the
sharp-jackson cct_smib_sync experiment: EMT-measured CCT brackets
(results_limiter_decomp.json, stock + current-only arms), the FULLY
ANALYTIC current-limit law (analytic_ilimit.tcr_analytic, imported --
no math copied), and the limit-free 1.30 s analytical line (dashed).
The in-axes title is dropped (the report caption carries it) and the
figure is sized at its true print width 0.9*\\textwidth = 5.85 in.
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

SRC = rp.experiment(r"cct_smib_sync")
OUT = rp.OUT
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import analytic_ilimit as AI                           # noqa: E402
import figstyle_26x as st                              # noqa: E402

st.apply()                     # AFTER the SRC import (it sets rcParams)
matplotlib.rcParams["axes.grid"] = False


def main():
    dc = json.load(open(SRC / "results_limiter_decomp.json"))

    fig, ax = plt.subplots(figsize=(0.9 * st.TEXTWIDTH_IN, 3.4))
    ax.grid(alpha=0.3)

    # EMT brackets: stock + current-only arms (incl. the two beyond
    # the ~11.7 pu demand ceiling, where the limiter cannot engage)
    brk = [(2.0, dc["anchors"]["stock"])]
    for name, x in (("I2p5", 2.5), ("I3", 3.0), ("I4", 4.0),
                    ("I6", 6.0), ("I10", 10.0), ("I12", 12.0),
                    ("I15", 15.0)):
        brk.append((x, dc["arms"][name]["bracket"]))
    for i, (x, (lo, hi)) in enumerate(brk):
        ax.plot([x, x], [lo, hi], color="k", lw=5.0,
                solid_capstyle="butt",
                label="PSCAD EMT clearing-time bracket" if i == 0 else None)

    ax.set_xlabel(r"current limit $I_{\max F}$ (pu on own base)")
    ax.set_ylabel("critical clearing time (s)")
    ax.set_xlim(1.8, 15.8)
    ax.set_ylim(0.88, 1.22)
    ax.legend(fontsize=9, loc="lower right")

    fig.savefig(OUT / "ilimit_sweep_emt.png", dpi=600)
    print("wrote", OUT / "ilimit_sweep_emt.png")


if __name__ == "__main__":
    main()
