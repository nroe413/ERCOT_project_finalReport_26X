"""Report figure fig:limitspdelta (limits_pdelta_080626.png): what the
device limits do to the transfer curve, and the direct evidence that
the current limiter is what does it.

2026-08-07 review, third pass. The single-panel version showed only
P(delta) and a reviewer could not see any limiting action in it. The
reason is that the limiter binds almost immediately: for the stock
arm the current demand at delta = 40-60 deg is 5.2 pu against a 2 pu
dial, so essentially the WHOLE descending branch is the limited
branch, and there is no visible "kink" to point at. The fix is to
plot the measured current beside the power:

  top    P(delta), raw samples, against the limit-free model
  bottom |I|(delta), raw samples, against each arm's ImaxF dial and
         the current the same swing would demand with no limiter

Every plotted point in both panels is one raw, unfiltered EMT sample
of the post-clear swing (no boxcar, no binning, no interpolation);
the full angle range is kept, ring-down included. The 4-degree bin
average is computed only to read the unstable-equilibrium angles and
is not drawn.

True print width 0.9*\\textwidth = 5.85 in.
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
OUT = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
           r"\upbeat-jones-67c8d3\report_26X\overleaf\figures")
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import make_mechanism_fig as M                         # noqa: E402
from analytic_implemented_law import p_unlimited       # noqa: E402
import figstyle_26x as st                              # noqa: E402

st.apply()
matplotlib.rcParams["axes.grid"] = False

DS_DEG = 5.9                       # prefault angle (audit constant)
R1, XL, XG, VS, EMAX = 0.03, 0.15, 0.025, 1.0, 1.15
ZMAG = abs(complex(R1, XL + XG))
MOVING_DEG_S = 3.0

CFG = [
    ("runs_gfm_decomp_I6", "T1p1", "T1p15", 1.100, 1.150,
     "#f4a582", "current limit 6 pu", 6.0),
    ("runs_gfm_decomp_I4", "T1p05", "T1p056", 1.050, 1.056,
     "#e08050", "current limit 4 pu", 4.0),
    # runs_gfm_relaxed is the ALL-RELAXED arm: its boundary pair
    # (1.069, 1.075] matches the "all-relaxed (had I = 3)" row of
    # tab:decomp, and its measured current sits at ~2.9 pu, which
    # independently identifies the 3 pu dial. The meeting figure
    # labelled it "volt/reactive wide", which is the OTHER arm
    # (bracket (0.975, 0.982]); corrected here 2026-08-07.
    ("runs_gfm_relaxed", "T1p069", "T1p075", 1.069, 1.075,
     "tab:blue", "all limits relaxed (current limit 3 pu)", 3.0),
    ("runs_gfm", "T0p925", "T0p931", 0.925, 0.931,
     "tab:red", "stock (current limit 2 pu)", 2.0),
]


def load_raw(runs_dir, tag, T):
    """Raw post-clear (delta, P, |I|, rate). Nothing is filtered."""
    df = pd.read_csv(SRC / runs_dir / tag / ("GFM_CCT_%s.csv" % tag))
    t = df["TIME"].values
    f = df["f_drp"].values
    m0 = t >= 2.5
    t, f = t[m0], f[m0]
    p = df["P_pu"].values[m0]
    cur = df["I_pu"].values[m0]
    dt = float(np.mean(np.diff(t)))
    d = np.degrees(np.radians(360.0 * np.cumsum(f - 60.0) * dt)) + DS_DEG
    rate = np.abs(360.0 * (f - 60.0))
    m = (t > 3.0 + T + 0.02) & (t < 9.5)
    return d[m], p[m], cur[m], rate[m]


def arc(runs, ts, tl, Ts, Tl):
    ds, ps, cs, rs = [], [], [], []
    for tag, T in ((ts, Ts), (tl, Tl)):
        d, p, c, r = load_raw(runs, tag, T)
        ds.append(d), ps.append(p), cs.append(c), rs.append(r)
    d = np.concatenate(ds)
    p = np.concatenate(ps)
    c = np.concatenate(cs)
    r = np.concatenate(rs)
    k = (d >= 0) & (d <= 185)
    d, p, c, r = d[k], p[k], c[k], r[k]
    mov = r > MOVING_DEG_S
    bins = np.arange(0, 188, 4.0)
    cen, mean = [], []
    for i in range(len(bins) - 1):
        m = mov & (d >= bins[i]) & (d < bins[i + 1])
        if m.sum() > 5:
            cen.append(0.5 * (bins[i] + bins[i + 1]))
            mean.append(float(np.mean(p[m])))
    return d, p, c, np.array(cen), np.array(mean)


def main():
    fig, (axP, axI) = plt.subplots(
        2, 1, figsize=(0.9 * st.TEXTWIDTH_IN, 5.0), sharex=True,
        gridspec_kw=dict(height_ratios=[1.0, 0.85], hspace=0.13))

    dd = np.linspace(0, 185, 600)
    axP.plot(dd, [p_unlimited(np.radians(x), EMAX) for x in dd],
             color="0.35", ls="-.", lw=1.5, zorder=5,
             label=r"no current limit (model, $E_{\max}=1.15$)")
    # current the same swing would demand with no limiter
    i_dem = np.abs(EMAX * np.exp(1j * np.radians(dd)) - VS) / ZMAG
    axI.plot(dd, i_dem, color="0.35", ls="-.", lw=1.5, zorder=5,
             label="demand with no current limit (model)")

    rims = {}
    for runs, ts, tl, Ts, Tl, col, lab, dial in CFG:
        d, p, c, cen, mean = arc(runs, ts, tl, Ts, Tl)
        s = max(1, len(d) // 26000)
        axP.plot(d[::s], p[::s], ".", color=col, ms=1.5, alpha=0.55,
                 zorder=3, rasterized=True, markeredgewidth=0,
                 label=lab)
        axI.plot(d[::s], c[::s], ".", color=col, ms=1.5, alpha=0.55,
                 zorder=3, rasterized=True, markeredgewidth=0)
        axI.axhline(dial, color=col, ls=":", lw=1.1, zorder=4)
        axI.annotate(r"$I_{\max F}=%g$" % dial, (183, dial),
                     fontsize=7.5, color=col, ha="right", va="bottom")
        rims[lab] = M.rim_of(cen, mean)

    axP.axhline(M.PREF, color="0.35", lw=1.0, zorder=2)
    axP.text(168, M.PREF + 0.14, r"$P_{\mathrm{ref}}$", fontsize=9,
             color="0.3")
    for runs, ts, tl, Ts, Tl, col, lab, dial in CFG:
        axP.plot(rims[lab], M.PREF, "v", ms=7, color=col, mec="k",
                 mew=0.6, zorder=9)
    for lab, col in (("stock (current limit 2 pu)", "tab:red"),
                     ("all limits relaxed (current limit 3 pu)",
                      "tab:blue")):
        axP.text(rims[lab], 0.95, "%.0f$^\\circ$" % rims[lab],
                 ha="center", fontsize=8.5, color=col)

    axP.set_ylabel(r"delivered power $P(\delta)$ (pu)")
    axP.set_ylim(-0.3, 6.1)
    axP.grid(alpha=0.25)
    h, l = axP.get_legend_handles_labels()
    order = [1, 2, 3, 4, 0]
    leg = axP.legend([h[i] for i in order], [l[i] for i in order],
                     fontsize=8, loc="upper right", framealpha=0.92,
                     title="every point is one raw EMT sample",
                     title_fontsize=8, markerscale=6,
                     handletextpad=0.6)
    for lh in leg.legend_handles:
        try:
            lh.set_alpha(1.0)
        except Exception:
            pass

    axI.set_xlabel(r"angle $\delta$ (deg)")
    axI.set_ylabel(r"current $|I|$ (pu)")
    axI.set_xlim(0, 185)
    axI.set_ylim(0, 11.5)
    axI.grid(alpha=0.25)
    axI.legend(fontsize=8, loc="upper left", framealpha=0.92)

    fig.savefig(OUT / "limits_pdelta_080626.png", dpi=600)
    print("wrote", OUT / "limits_pdelta_080626.png")
    for k, v in rims.items():
        print("  rim %-34s %6.1f deg" % (k, v))


if __name__ == "__main__":
    main()
