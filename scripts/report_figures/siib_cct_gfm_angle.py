"""Report-format regeneration of the droop-GFM SIIB angle figure
(file siib_cct_gfm_angle.png).

Same content and same data path as make_gfm_rotor_angle_plot.py in the
sharp-jackson cct_smib_sync experiment: the GFM internal angle against
the infinite bus, integrated from the droop frequency channel f_drp,
for the two measured CCT brackets -- stock limits (0.925, 0.931] s and
relaxed limits (1.069, 1.075] s -- with the effective limiter-set rims
and the pure-droop theory rim drawn as references.  The point is that
BOTH measured rims sit far inside the 171 deg pure-droop rim, so the
energy/droop CCT theory is anti-conservative for a GFM on an infinite
bus.

Data: read-only from the sharp-jackson worktree; nothing there is
modified.  True print width 0.9 * \\textwidth = 5.85 in.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                          # noqa: E402

SRC = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
           r"\sharp-jackson-1e89b8\experiments\cct_smib_sync")
OUT = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
           r"\upbeat-jones-67c8d3\report_26X\overleaf\figures")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import figstyle_26x as st                                # noqa: E402

st.apply()

T_F = 3.0                      # fault application time (s)
T_CLR_RELAXED = 1.072          # midpoint of the measured (1.069, 1.075] s
DELTA_S = 6.0                  # steady-state angle offset (deg)

RUNS = [("runs_gfm", "T0p925", 0.925, "#2ca02c", "-",
         "stock, T = 0.925 s (stable)"),
        ("runs_gfm", "T0p931", 0.931, "#e08214", "-",
         "stock, T = 0.931 s (slip)"),
        ("runs_gfm_relaxed", "T1p069", 1.069, "#1e6b1e", "--",
         "relaxed, T = 1.069 s (stable)"),
        ("runs_gfm_relaxed", "T1p075", 1.075, "#c0392b", "--",
         "relaxed, T = 1.075 s (slip)")]


def angle(runs_dir, tag):
    """Angle vs the infinite bus, deg, referenced to zero at fault-on."""
    df = pd.read_csv(SRC / runs_dir / tag / ("GFM_CCT_%s.csv" % tag))
    t = df["TIME"].values
    f = df["f_drp"].values
    m = t >= 2.5
    t, f = t[m], f[m]
    dt = float(np.mean(np.diff(t)))
    d = 360.0 * np.cumsum(f - 60.0) * dt
    d -= d[int(np.argmin(np.abs(t - T_F)))]
    return t, d


def main():
    fig, ax = plt.subplots(figsize=(0.9 * st.TEXTWIDTH_IN, 3.4))
    ax.axvspan(T_F, T_F + T_CLR_RELAXED, color="#fbd0c4", alpha=0.30,
               lw=0, zorder=0)

    for runs_dir, tag, T, col, ls, lbl in RUNS:
        t, d = angle(runs_dir, tag)
        ax.plot(t, d + DELTA_S, lw=1.3, color=col, ls=ls, label=lbl)
        k = int(np.argmin(np.abs(t - (T_F + T))))
        ax.plot(t[k], d[k] + DELTA_S, "*", ms=9, color=col, mec="k",
                mew=0.5, zorder=6)

    rims = ((DELTA_S, "$x_s$: $\\delta_s$ = 6$^\\circ$", "k", ":", 9),
            (120, "stock rim ~120$^\\circ$ (ImaxF = 2)", "#e08214",
             "--", -26),
            (139, "relaxed rim ~139$^\\circ$ (ImaxF = 3)", "#c0392b",
             "--", 9),
            (171, "pure-droop rim $\\delta_u-3^\\circ$ = 171$^\\circ$ "
             "(theory 1.30 s)", "#1f77b4", "--", 9),
            (366, "$\\delta_s+360^\\circ$: next well (slip-relock)",
             "k", ":", 9))
    for y, lbl, c_, ls, dy in rims:
        ax.axhline(y, color=c_, lw=0.9, ls=ls)
        ax.annotate(lbl, (9.42, y + dy), fontsize=7.2, color=c_,
                    ha="right")

    ax.annotate("fault-on drift 129.6$^\\circ$/s\n($\\star$ = clearing)",
                (3.62, 232), fontsize=7.6, color="#7a2318", ha="center")
    ax.set_xlim(2.6, 9.5)
    ax.set_ylim(-45, 480)
    ax.set_yticks(range(0, 401, 100))
    ax.set_xlabel("time (s)")
    ax.set_ylabel("GFM angle vs infinite bus (deg)")
    ax.legend(fontsize=7.4, loc="upper left", framealpha=0.95,
              borderpad=0.4, labelspacing=0.35, handlelength=2.0)
    ax.grid(alpha=0.3)

    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "siib_cct_gfm_angle.png", dpi=600)
    print("wrote", OUT / "siib_cct_gfm_angle.png")


if __name__ == "__main__":
    main()
