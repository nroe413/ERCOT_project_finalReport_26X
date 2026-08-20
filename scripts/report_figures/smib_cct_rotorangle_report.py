"""Report-format regeneration of the SMIB rotor-angle figure
(deck image14: "SMIB machine: rotor angle delta(t) vs synchronous
reference across the measured CCT (0.622, 0.625] s").

Content is figure 1 of make_rotor_angle_plot.py in the sharp-jackson
cct_smib_sync experiment, unchanged: the same five measured PSCAD rungs
(T = 0.550 / 0.600 / 0.622 / 0.625 / 0.650 s), the same rotor angle
reconstruction delta(t) = integral of ws (Wpu - 1) dt referenced to the
t = 3 s pre-fault state and offset by the theory delta_s, and the same
reference rails (delta_s, delta_cr, delta_u, delta_s + 360) taken from
smib_cct.cct_closed_form -- no numbers recomputed here.

This is the case where the classical energy method WORKS: the theory
rails bracket the EMT-measured CCT conservatively.

Only the presentation changes: true print inches (0.9 x textwidth),
report serif face, no in-figure title (the LaTeX caption carries it).

Usage:  python smib_cct_rotorangle_report.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
           r"\sharp-jackson-1e89b8\experiments\cct_smib_sync")
STYLE = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
             r"\upbeat-jones-67c8d3\report_26X\figures")
OUT = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
           r"\upbeat-jones-67c8d3\report_26X\overleaf\figures")
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(STYLE))

from smib_cct import identify_xext, build_case, cct_closed_form  # noqa: E402
import figstyle_26x as st                                        # noqa: E402

st.apply()                      # AFTER the SRC import (it sets rcParams)

T_F = 3.0
SMIB_RUNS = [("T0p55", 0.550, "#7fbf7f"), ("T0p6", 0.600, "#2ca02c"),
             ("T0p622", 0.622, "#1e6b1e"), ("T0p625", 0.625, "#e08214"),
             ("T0p65", 0.650, "#c0392b")]


def smib_delta(tag):
    """Identical to make_rotor_angle_plot.smib_delta."""
    df = pd.read_csv(SRC / "runs" / tag / ("SMIB_CCT_%s.csv" % tag))
    t = df["TIME"].values
    m = t >= 2.5
    t, w = t[m], df["Wpu"].values[m]
    dt = float(np.mean(np.diff(t)))
    d = np.degrees(2 * np.pi * 60.0 * np.cumsum(w - 1.0) * dt)
    d -= d[int(np.argmin(np.abs(t - T_F)))]
    return t, d


def main():
    c = build_case(identify_xext()[0])
    r = cct_closed_form(c)
    ds, dcr, du = (np.degrees(r[k]) for k in ("ds", "dcr", "du"))

    fig, ax = plt.subplots(figsize=(0.9 * st.TEXTWIDTH_IN, 3.4))
    for tag, T, col in SMIB_RUNS:
        t, d = smib_delta(tag)
        ax.plot(t, ds + d, lw=1.3, color=col,
                label="T = %.3f s%s" % (T, "" if T < 0.623 else " (slip)"))

    for y, lbl, xl, c_ in (
            (ds, "$x_s$: $\\delta_s$ = %.1f$^\\circ$" % ds, 9.45, "k"),
            (dcr, "$\\delta_{cr}$ = %.1f$^\\circ$ (max clearing angle)"
             % dcr, 9.45, "#666666"),
            (du, "$\\delta_u$ = %.1f$^\\circ$ (UEP)" % du, 6.55, "#c0392b"),
            (ds + 360, "$\\delta_s+360^\\circ$ (relock, one pole slipped)",
             9.45, "k")):
        ax.axhline(y, color=c_, lw=0.9, ls="--" if y in (dcr, du) else ":")
        ax.annotate(lbl, (xl, y + 9), fontsize=7.5, color=c_, ha="right")

    ax.axvspan(T_F, T_F + 0.65, color="#fbd0c4", alpha=0.35, zorder=0)
    ax.set_xlim(2.6, 9.5)
    ax.set_ylim(-60, 470)
    ax.set_yticks(range(0, 401, 100))
    ax.set_xlabel("time (s)")
    ax.set_ylabel("rotor angle $\\delta$ vs\nsynchronous reference (deg)")
    ax.legend(fontsize=7.5, loc="lower center", bbox_to_anchor=(0.5, 1.005),
              ncol=5, frameon=False, borderpad=0.2, columnspacing=1.1,
              handlelength=1.5, handletextpad=0.5)
    ax.grid(alpha=0.3, lw=0.5)

    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "smib_cct_rotorangle.png", dpi=600)
    print("wrote", OUT / "smib_cct_rotorangle.png")
    print("rails: delta_s = %.1f, delta_cr = %.1f, delta_u = %.1f deg"
          % (ds, dcr, du))


if __name__ == "__main__":
    main()
