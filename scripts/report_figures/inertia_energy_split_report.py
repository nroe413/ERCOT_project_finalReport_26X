r"""Explanatory figure: where the energy-based inertia test picks up droop.

This is NOT a data plot.  Nothing here comes from a PSCAD run or from a
measurement file; every curve is drawn straight from the closed-form
algebra of the inertia-estimation note (resources/Inertia_estimation_3.pdf,
Figure 1 on p. 7), so the shapes are schematic and the vertical scale is
arbitrary.

The algebra it draws.  During a constant-RoCoF ramp the active-power
deviation of a droop-controlled device is, in per-unit swing form
(Eq. 39 of the note),

    dp(t) = (2H/f_n) df/dt  +  (D/f_n) (df/dt) t,
            \______________/    \_________________/
             constant, inertial   linear in t, droop

so integrating over the test window [0, T] (Eq. 40) gives an energy that
splits into a RECTANGLE of height (2H/f_n) df/dt, the true inertial
energy, and a TRIANGLE above it that is droop energy and whose area grows
with the window.  Feeding the whole area to the classical estimator
(Eq. 41) yields the bias of Eq. 42,

    H_est = H + D T / 4,

which for a droop GFM with D = 1/m_p is H + T/(4 m_p) (Eq. 46).

The reading the figure has to force: the energy method integrates the
WHOLE area, so it books the triangle as inertia when the triangle is
droop.

Companion measured figure: hest_corrected.png (hest_corrected_report.py),
which shows the same law against the PSCAD window sweep.
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")

OUT = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
           r"\upbeat-jones-67c8d3\report_26X\overleaf\figures")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import figstyle_26x as st                               # noqa: E402

st.apply()
import matplotlib.pyplot as plt                         # noqa: E402

INK = "#2d3338"          # text and axes
DROOP = "#c0504d"        # muted red: the droop / GFM element
INERTIA = "#2a7f7f"      # muted teal: the inertia / synchronous element

# printed size: included at width=0.8\textwidth
FIGW, FIGH = 0.8 * st.TEXTWIDTH_IN, 2.6

# Schematic proportions only.  H0 is the constant inertial height
# (2H/f_n) df/dt; SLOPE is the droop rate (D/f_n) df/dt.  Their ratio sets
# how big the mis-attributed triangle looks, and is chosen so the
# rectangle stays tall enough to hold its own label.
H0 = 0.85
SLOPE = 2.2
YMAX = 3.35        # just enough headroom for the takeaway line


def main():
    fig, ax = plt.subplots(figsize=(FIGW, FIGH))

    t = np.linspace(0.0, 1.0, 400)
    total = H0 + SLOPE * t

    # inertial rectangle: constant height, the only part that is inertia
    ax.fill_between(t, 0.0, H0, color=INERTIA, alpha=0.22, lw=0)
    # droop triangle: everything between the rectangle and the total
    ax.fill_between(t, H0, total, color=DROOP, alpha=0.18, lw=0)

    ax.plot(t, total, color=DROOP, lw=1.6, solid_capstyle="round")
    ax.plot([0, 1], [H0, H0], color=INERTIA, ls="--", lw=1.0)

    # direct labels rather than a legend: at 5.2 in a legend box would
    # cover the empty upper-left wedge that the takeaway line needs, and
    # each fill is big enough to carry its own words.
    ax.text(0.5, 0.5 * H0,
            r"inertia energy   $(2H/f_{\mathrm{n}})\,\mathrm{d}f/\mathrm{d}t$",
            ha="center", va="center", fontsize=9, color=INERTIA)
    ax.text(0.70, 1.45,
            r"droop energy   $(D/f_{\mathrm{n}})(\mathrm{d}f/\mathrm{d}t)\,t$"
            "\n"
            r"grows with the window $T$",
            ha="center", va="center", fontsize=9, color=DROOP,
            linespacing=1.45)
    ax.text(0.99, H0 + SLOPE + 0.06, r"total $\Delta p(t)$",
            ha="right", va="bottom", fontsize=9, color=DROOP)

    ax.text(0.015, YMAX - 0.08,
            "the energy test integrates both areas over $[0,T]$,\n"
            r"so it reports $H_{\mathrm{est}} = H + DT/4$",
            ha="left", va="top", fontsize=9, color=INK, linespacing=1.45)

    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, YMAX)
    ax.set_xticks([0.0, 1.0])
    ax.set_xticklabels(["0", "$T$"])
    ax.set_yticks([])
    ax.set_xlabel("time during the ramp, $t$")
    ax.set_ylabel(r"power deviation $\Delta p$")

    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK)
        ax.spines[side].set_linewidth(0.9)
    ax.tick_params(colors=INK, length=3, width=0.9)
    ax.xaxis.label.set_color(INK)
    ax.yaxis.label.set_color(INK)

    out = OUT / "inertia_energy_split.png"
    fig.savefig(out, dpi=600)
    print("figure size: %.2f x %.2f in" % (FIGW, FIGH))
    print("schematic heights: rectangle %.2f, droop at T %.2f, total at T %.2f"
          % (H0, SLOPE, H0 + SLOPE))
    print("wrote", out)


if __name__ == "__main__":
    main()
