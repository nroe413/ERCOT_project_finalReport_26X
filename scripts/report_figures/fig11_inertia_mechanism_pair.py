"""Report-format regeneration of fig11_inertia_mechanism_pair.png (report
fig:hmech), single panel, 0.8*6.5 = 5.2 in wide.

The measured "inertia" H(T) grows with the averaging window T for all four
device models, while the true (configured) H sits far below - the signature
of the DT/4 bias term of Eq. (11), H_est = H + DT/4.

Data: each experiment's plots/window_sweep_metrics.json, written by its
window_sweep.py in the sharp-jackson-1e89b8 worktree.  No synthesized data.

History: this file used to draw a 1x2 pair whose right panel decomposed the
REGFM_A1 response into P = a + b|df| (slope 1.27 pu/Hz, intercept ~ 0).  That
panel did not read, and was dropped 2026-08-11; the filename is kept so
main.tex still resolves.  Nothing about the left panel's data changed.
"""
import sys
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_paths as rp  # noqa: E402

import matplotlib
matplotlib.use("Agg")

EXPD = rp.experiment(r"experiments")
OUT = rp.OUT
sys.path.insert(0, str(Path(__file__).resolve().parent))

import figstyle_26x as st                               # noqa: E402

st.apply()
import matplotlib.pyplot as plt                         # noqa: E402

GRAY = "#7f7f7f"

# printed size: included at width=0.8\textwidth
FIGW, FIGH = 0.8 * st.TEXTWIDTH_IN, 3.2

XLO, XHI = 0.055, 0.605     # data axis limits
XDIV = 0.535                # divider between the curves and the true-H column
XSTAR = 0.572               # centre of the true-H column
DX = 0.017                  # horizontal spread for coincident true-H values

# (experiment dir, color, marker, short label) - order and colors from the
# original compare_window_sweep.py
MODELS = [
    ("agsesr_inertia_response_GFM",     "#d62728", "o", r"A1 droop, $m_{\mathrm{p}}{=}0.01$"),
    ("agsesr_inertia_mp0p1",            "#ff9896", "D", r"A1 droop, $m_{\mathrm{p}}{=}0.1$"),
    ("regfm_b1_vsm_inertia_validation", "#e08214", "s", r"B1 VSM"),
    ("typicalgt_inertia_validation",    "#1f77b4", "^", r"sync (TypicalGT)"),
]


def star_x(cfgs):
    """Spread stars horizontally when several models share a true H, so a
    coincident pair (the two droop models, both 0 s) stays visible."""
    xs = []
    for i, c in enumerate(cfgs):
        tie = [j for j, o in enumerate(cfgs) if abs(o - c) < 1e-9]
        k = tie.index(i)
        xs.append(XSTAR + (k - (len(tie) - 1) / 2.0) * DX)
    return xs


def main():
    fig, ax = plt.subplots(figsize=(FIGW, FIGH))
    ax.grid(alpha=0.3)

    series = []
    for d, c, mk, lbl in MODELS:
        m = json.loads((EXPD / d / "plots" / "window_sweep_metrics.json")
                       .read_text())
        series.append((m["T_list_s"], m["H_python_s"],
                       m["configured_inertia_s"], c, mk, lbl))

    xs = star_x([s[2] for s in series])

    for (T, H, cfg, c, mk, lbl), xstar in zip(series, xs):
        ax.plot(T, H, marker=mk, color=c, lw=1.6, ms=4.5,
                # "configured", not "true": the plotted value is the
                # model's inertia DIAL. A droop model has no such dial,
                # so its configured value is 0, which is not the same
                # statement as its swing-form equivalent inertia
                # H_eq = T_Pf/(2 m_p) being 0. Labelling this "true H"
                # read as a contradiction of the 0.5 s quoted in the
                # body text.
                label="%s   configured $H$ = %.4g s" % (lbl, cfg))
        ax.plot(xstar, cfg, marker="*", color=c, ms=11, mec="k", mew=0.4,
                zorder=6)

    # 2.5 s criterion, drawn only under the curves (not the configured-H column)
    ax.plot([XLO, XDIV], [2.5, 2.5], color=GRAY, ls=":", lw=1.1, zorder=1)
    ax.text(XDIV - 0.008, 2.62, "criterion 2.5 s", color=GRAY, fontsize=8.5,
            ha="right", va="bottom")

    # the configured-H column: a shaded gutter outside the T axis, so the
    # stars are not misread as a sixth window.  The header is set on two
    # lines because "configured H" on one line is wider than the gutter and
    # gets clipped by the right spine.
    ax.axvspan(XDIV, XHI, color="#000000", alpha=0.045, lw=0, zorder=0)
    ax.axvline(XDIV, color="#bbbbbb", lw=0.9, zorder=0)
    ax.text(XSTAR, 8.62, "configured\n$H$", color="#333333", ha="center",
            va="center", fontsize=8, linespacing=1.25)
    ax.annotate("", xy=(XSTAR, 5.95), xytext=(XSTAR, 7.85),
                arrowprops=dict(arrowstyle="-|>", lw=0.8, color="#999999",
                                shrinkA=0, shrinkB=0))

    ax.set_xlim(XLO, XHI)
    ax.set_ylim(-0.45, 9.25)
    ax.set_xticks([0.1, 0.2, 0.3, 0.4, 0.5])
    ax.set_yticks([0, 2, 4, 6, 8])
    ax.set_xlabel("averaging window $T$ (s)")
    ax.set_ylabel(r"estimated equivalent inertia $H_{\mathrm{est}}$ (s)")
    ax.set_title("Estimated equivalent inertia versus averaging window")
    ax.legend(loc="upper left", fontsize=8.5, handlelength=1.7,
              labelspacing=0.35, borderaxespad=0.4, borderpad=0.4,
              framealpha=1.0, edgecolor="#bbbbbb")

    out = OUT / "fig11_inertia_mechanism_pair.png"
    fig.savefig(out, dpi=600)
    print("figure size: %.2f x %.2f in" % (FIGW, FIGH))
    for T, H, cfg, _c, _mk, lbl in series:
        print("  %-24s configured H = %-6.4g  H(%.1f) = %.3f  H(%.1f) = %.3f"
              % (lbl, cfg, T[0], H[0], T[-1], H[-1]))
    print("wrote", out)


if __name__ == "__main__":
    main()
