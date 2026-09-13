"""Report-format regeneration of the two as-shipped-GFL failure-mode
figures (report fig:gflpocket and fig:gfldeadlock):

  fig8a_gfl_pocket_vs_grid.png  -- one unmodified WECC GFL at bus 32:
      the surrounding grid recovers in under a second, the inverter's
      own bus never does (bus voltages, pu of 230 kV).
  fig8b_gfl_deadlock.png        -- the LVRT dip-latch deadlock
      mechanism: Vt vs the V_dip threshold, the WECC current commands,
      and P/Q at the POI.

Same data and content as the originals produced by
experiments/fault_3PG_bus14_1GFL/plot_failure_mode.py in the
compassionate-banach-aa8040 worktree (figures 1 and 2 there,
2026-07-21), restyled to the 2026-08-07 figure standard: true print
width \textwidth = 6.5 in, TeX Gyre Pagella 11 pt, exact-inch save,
no in-figure prose titles (the LaTeX captions carry them), annotations
kept to short 9 pt data callouts.

Data source (10 s window; latest export, as the original's
sorted(glob)[-1] picked):
  compassionate-banach-aa8040  experiments/fault_3PG_bus14_1GFL/runs/
  3PG_at_bus14_w_1GFL_at_bus32_t3p0s_5cyc_norecl_10s/data_*.csv
"""
import sys
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_paths as rp  # noqa: E402

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import figstyle_26x as st   # noqa: E402

st.apply()

RUN10 = rp.experiment(r"fault_3PG_bus14_1GFL\runs\3PG_at_bus14_w_1GFL_at_bus32_t3p0s_5cyc_norecl_10s")
OUT = rp.OUT

T_FAULT, T_CLEAR = 3.0, 3.0833
BLUE, RED = "#1f4e9c", "#c0392b"
ANN = dict(fontsize=9,
           arrowprops=dict(arrowstyle="->", color="k", lw=0.8))


def load(want):
    csv = sorted(RUN10.glob("data_*.csv"))[-1]
    wanted = set(want) | {"TIME"}
    df = pd.read_csv(csv, usecols=lambda c: c.strip('" ') in wanted,
                     dtype="float32")
    df.columns = [c.strip('" ') for c in df.columns]
    print("loaded %s (%d rows)" % (csv.name, len(df)))
    return df


def fault_band(ax):
    ax.axvspan(T_FAULT, T_CLEAR, color="#f8c8c8", alpha=0.55, zorder=0)
    for x in (T_FAULT, T_CLEAR):
        ax.axvline(x, color=RED, ls="--", lw=0.8, alpha=0.7)


def fig8a():
    d = load(("B32Vrms", "B15Vrms", "B16Vrms", "B30Vrms"))
    w = d[(d.TIME >= 2.5) & (d.TIME <= 10.0)]
    s = max(1, len(w) // 24000)
    fig, ax = plt.subplots(figsize=(st.TEXTWIDTH_IN, 2.9))
    for col, c, lw in (("B15Vrms", "#9db6d8", 1.0),
                       ("B16Vrms", "#6f93c4", 1.0),
                       ("B30Vrms", BLUE, 1.0)):
        ax.plot(w.TIME[::s], w[col][::s] / 230.0, color=c, lw=lw,
                label=col.replace("Vrms", ""))
    ax.plot(w.TIME[::s], w.B32Vrms[::s] / 230.0, color=RED, lw=1.6,
            label="B32 (GFL bus)")
    ax.axhline(1.0, color="k", ls=":", lw=1.0)
    fault_band(ax)
    ax.annotate("grid recovers to ~1.0 pu in < 1 s", xy=(4.2, 0.965),
                xytext=(5.2, 0.62), **ANN)
    ax.annotate("bus-32 pocket held at 0.2-0.3 pu\nby the latched unit itself",
                xy=(7.5, 0.27), xytext=(3.3, 0.035), zorder=6,
                bbox=dict(boxstyle="square,pad=0.25", facecolor="white",
                          edgecolor="none", alpha=1.0), **ANN)
    ax.grid(alpha=0.3)
    ax.set_xlim(2.5, 10.0)
    ax.set_ylim(0, 1.15)
    ax.set_xlabel("time (s)")
    ax.set_ylabel("bus voltage (pu of 230 kV)")
    ax.legend(loc="center right", fontsize=9, framealpha=0.9)
    fig.savefig(OUT / "fig8a_gfl_pocket_vs_grid.png", dpi=600)
    plt.close(fig)
    print("wrote", OUT / "fig8a_gfl_pocket_vs_grid.png")


def fig8b():
    d = load(("Vt_filt", "V32", "Ipcmd", "Iqcmd", "P32", "Q32"))
    w = d[(d.TIME >= 2.5) & (d.TIME <= 10.0)]
    s = max(1, len(w) // 24000)
    t = w.TIME[::s]
    fig, ax = plt.subplots(3, 1, figsize=(st.TEXTWIDTH_IN, 4.9),
                           sharex=True)

    ax[0].plot(t, w.Vt_filt[::s], color=RED, lw=1.4,
               label=r"$V_{\mathrm{t}}$ (REEC filtered)")
    ax[0].plot(t, w.V32[::s], color=BLUE, lw=0.9, ls="--",
               label=r"$V_{32}$ POI (pu of 10 kV)")
    ax[0].axhline(0.5, color="k", ls=":", lw=1.2)
    ax[0].text(3.30, 0.53, r"$V_{\mathrm{dip}}=0.5$ (dip-state threshold)",
               ha="left", va="bottom", fontsize=9, zorder=6,
               bbox=dict(boxstyle="square,pad=0.2", facecolor="white",
                         edgecolor="none", alpha=1.0))
    ax[0].annotate(r"latched: $V_{\mathrm{t}}$ never re-crosses 0.5",
                   xy=(6.5, 0.22), xytext=(5.1, 0.72), **ANN)
    ax[0].set_ylabel("voltage (pu)")
    ax[0].set_ylim(0, 1.28)
    ax[0].legend(loc="upper right", fontsize=9, framealpha=0.95)

    ax[1].plot(t, w.Ipcmd[::s], color=BLUE, lw=1.4,
               label=r"$I_{p,\mathrm{cmd}}$ (active)")
    ax[1].plot(t, w.Iqcmd[::s], color=RED, lw=1.4,
               label=r"$I_{q,\mathrm{cmd}}$ (reactive)")
    ax[1].annotate("correct WECC LVRT:\n$I_{\\mathrm{p}}\\!\\to\\!0$, $I_{\\mathrm{q}}\\!\\to\\!1$",
                   xy=(3.25, 0.97), xytext=(4.5, 0.70), **ANN)
    ax[1].annotate("dip logic times out;\ncommands stay zero",
                   xy=(4.55, 0.03), xytext=(6.3, 0.42), **ANN)
    ax[1].set_ylabel("current command (pu)")
    ax[1].set_ylim(-0.1, 1.15)
    ax[1].legend(loc="center right", fontsize=9, framealpha=0.9)

    ax[2].plot(t, w.P32[::s], color=BLUE, lw=1.2, label=r"$P_{32}$ (MW)")
    ax[2].plot(t, w.Q32[::s], color=RED, lw=1.2, label=r"$Q_{32}$ (MVAr)")
    ax[2].axhline(0, color="k", lw=0.8)
    ax[2].annotate("650 MW export", xy=(2.75, 620), xytext=(3.6, 500),
                   **ANN)
    ax[2].annotate("dead unit absorbs 50-170 MW\n(filter/damping stays connected)",
                   xy=(7.0, -130), xytext=(5.7, 280), **ANN)
    ax[2].set_ylabel("POI power")
    ax[2].set_xlabel("time (s)")
    ax[2].set_ylim(-300, 730)
    ax[2].legend(loc="upper right", fontsize=9, framealpha=0.95)

    for a in ax:
        a.grid(alpha=0.3)
        fault_band(a)
        a.set_xlim(2.5, 10.0)
    fig.savefig(OUT / "fig8b_gfl_deadlock.png", dpi=600)
    plt.close(fig)
    print("wrote", OUT / "fig8b_gfl_deadlock.png")


if __name__ == "__main__":
    fig8a()
    fig8b()
