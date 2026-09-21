"""Report-format regeneration of the three SMIB GFM-vs-sync comparison
figures (report fig6_smib_sync_vs_gfm_VI, narr_smib_sync_vs_gfm_Pf,
smib_IPIQ).

Data and channel handling are copied verbatim from the original
generator (sharp-jackson worktree,
experiments/smib_3PG_GFMvsSync/smib_gfm_vs_sync.py): identical SMIB
test, bolted 3PG at t = 3.0 s for 5 cycles, SCR = 10 / X/R = 20 on each
device's own base.  The original module is NOT imported because (a) its
import clobbers rcParams at module level and (b) its load_sync() writes
a record CSV inside the sharp-jackson worktree, which must stay
untouched.  Loading is replicated read-only with the same channel
selection; the canonical sync record CSV
(single_machine_infinite_bus_1syncMachineValidation/SMIB_1SYNC_3PG_PSD.csv,
same content as the runs/3PG_5cyc_SCR10_10s copy) is preferred, exactly
as the original prefers it over the live .gf46.

Print contract (figstyle_26x): TeX Gyre Pagella 11 pt, mathtext cm,
600 dpi, exact-inch save (no tight bbox).
  fig6  VI : 0.85*textwidth = 5.525 in wide, 4.0 in tall, 2x1
  narr  Pf : same size
  IPIQ     : textwidth = 6.5 in wide, 4.2 in tall, 2x1 sharex
Long prose titles / caption boxes of the meeting versions are dropped;
the LaTeX captions carry that text.
"""
import sys
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_paths as rp  # noqa: E402

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = rp.OUT
sys.path.insert(0, str(Path(__file__).resolve().parent))
import figstyle_26x as st  # noqa: E402

st.apply()

# both records ship with the single-device cases (systems/smib_siib), dispatch 0.50 pu on each device's own base
RUNS = rp.ROOT / "systems" / "smib_siib" / "runs" / "3PG_5cyc_SCR10_10s"
GFM_CSV = RUNS / "SMIB_1GFM_3PG_Preq0p5_PSD.csv"
SYNC_CSV = RUNS / "SMIB_1SYNC_3PG_PSD.csv"

FAULT_T, CLEAR_T = 3.0, 3.0833
BLUE, RED = "#1f77b4", "#c0392b"


def load():
    sync_src = SYNC_CSV
    sy = pd.read_csv(sync_src)
    gf = pd.read_csv(GFM_CSV)
    print("sync <- %s %s" % (sync_src, sy.shape))
    print("gfm  <- %s %s" % (GFM_CSV, gf.shape))
    return sy, gf


def style_axes(axes, xlim):
    for a in np.atleast_1d(axes):
        a.axvspan(FAULT_T, CLEAR_T, color="#fbd0c4", alpha=0.6, zorder=0)
        a.grid(True, alpha=0.3)
        a.set_xlim(*xlim)


def fig_vi(sy, gf):
    ts_, tg = sy["TIME"].values, gf["TIME"].values
    fig, ax = plt.subplots(2, 1, figsize=(0.85 * st.TEXTWIDTH_IN, 4.0),
                           sharex=True)
    style_axes(ax, (2.8, 6.0))
    ax[0].plot(ts_, sy["VRMS2grid"].values, color=BLUE, lw=1.0,
               label="Synchronous (bus-39 machine)")
    ax[0].plot(tg, gf["V_pu"].values, color=RED, lw=1.0,
               label="GFM (REGFM_A1)")
    ax[0].axhline(1.0, color="#999999", ls="--", lw=0.7)
    ax[0].set_ylabel("Terminal voltage (pu)")
    ax[0].set_ylim(0, 1.25)
    ax[0].legend(loc="lower right", fontsize=8)
    pk_s = float(np.nanmax(sy["IRMS2grid"].values))
    pk_g = float(np.nanmax(gf["I_pu"].values))
    ax[1].plot(ts_, sy["IRMS2grid"].values, color=BLUE, lw=1.0,
               label="Synchronous — unlimited (peak %.1f pu)" % pk_s)
    ax[1].plot(tg, gf["I_pu"].values, color=RED, lw=1.0,
               label="GFM — limited (peak %.2f pu)" % pk_g)
    ax[1].axhline(2.0, color=RED, ls="--", lw=0.8)
    ax[1].text(5.95, 2.25, "GFM $I_{\\max F}$ = 2.0 pu", color=RED,
               fontsize=8, ha="right", va="bottom")
    ax[1].set_ylabel("Current (pu of own rating)")
    ax[1].set_ylim(0, max(2.5, 1.12 * pk_s))
    ax[1].set_xlabel("Time (s)")
    ax[1].legend(loc="upper right", fontsize=8)
    fig.savefig(OUT / "fig6_smib_sync_vs_gfm_VI.png")
    plt.close(fig)
    print("wrote", OUT / "fig6_smib_sync_vs_gfm_VI.png")


def fig_pf(sy, gf):
    ts_, tg = sy["TIME"].values, gf["TIME"].values
    fig, ax = plt.subplots(2, 1, figsize=(0.85 * st.TEXTWIDTH_IN, 4.0),
                           sharex=True)
    style_axes(ax, (2.5, 10.0))
    ax[0].plot(ts_, sy["P2grid"].values, color=BLUE, lw=1.0,
               label="Synchronous (dispatch 0.50 pu)")
    ax[0].plot(tg, gf["P_pu"].values, color=RED, lw=1.0,
               label="GFM ($P_{\\mathrm{req}}$ = 0.50 pu)")
    ax[0].set_ylabel("Active power (pu)")
    ax[0].legend(loc="lower right", fontsize=8)
    ax[1].plot(ts_, sy["Wpu"].values * 60.0, color=BLUE, lw=1.0,
               label="Synchronous (rotor speed)")
    ax[1].plot(tg, gf["f_drp"].values, color=RED, lw=1.0,
               label="GFM (droop frequency)")
    ax[1].axhline(60.0, color="#999999", ls="--", lw=0.7)
    ax[1].set_ylabel("Frequency (Hz)")
    ax[1].set_xlabel("Time (s)")
    ax[1].legend(loc="lower right", fontsize=8)
    fig.savefig(OUT / "narr_smib_sync_vs_gfm_Pf.png")
    plt.close(fig)
    print("wrote", OUT / "narr_smib_sync_vs_gfm_Pf.png")


def fig_ipiq(sy, gf):
    ts_, tg = sy["TIME"].values, gf["TIME"].values

    def decomp(t, P, Q, V):
        """I_P = P/V and I_Q = Q/V, blanked where the ratio means
        nothing: while V < 0.2 pu the quotient is ill-conditioned, and
        during the fault window itself it is a division artifact even
        before V has fully collapsed (the spike the un-masked version
        drew at exactly t = 3.0 was P/V with V passing through 0.2, not
        a current). Returns the blank mask so the caller can shade
        exactly what is blanked."""
        t = np.asarray(t, float)
        v = np.asarray(V, float)
        ip = np.asarray(P, float) / v
        iq = np.asarray(Q, float) / v
        bad = (v < 0.2) | ((t >= FAULT_T) & (t <= CLEAR_T))
        ip[bad] = np.nan
        iq[bad] = np.nan
        return ip, iq, bad

    sIp, sIq, sbad = decomp(ts_, sy["P2grid"].values,
                            sy["Q2grid"].values, sy["VRMS2grid"].values)
    gIp, gIq, gbad = decomp(tg, gf["P_pu"].values, gf["Q_pu"].values,
                            gf["V_pu"].values)

    # Shade exactly the blanked span (fault application to the last
    # blanked sample of either device), and say inside the band why it
    # is blank, so the gap reads as a definition boundary rather than
    # missing data.
    t_end = CLEAR_T
    for t, bad in ((ts_, sbad), (tg, gbad)):
        inwin = bad & (t >= FAULT_T)
        if inwin.any():
            t_end = max(t_end, float(t[inwin].max()))

    fig, ax = plt.subplots(2, 1, figsize=(st.TEXTWIDTH_IN, 4.2),
                           sharex=True)
    for a in ax:
        a.axvspan(FAULT_T, t_end, color="#fbd0c4", alpha=0.6, zorder=0)
        a.set_xlim(2.8, 5.5)
        a.grid(alpha=0.3)
    # Placement history, so this does not regress: centred on the band
    # the text ran into the GFM recovery spike (1.53 pu at 3.11 s);
    # left of the band it does not fit (the pre-fault window is 0.2 s
    # and the line needs ~0.9 s at this scale), so it clipped either
    # the frame or the ticks. The open region is right of the spike,
    # below the legend, above the settled traces; "(shaded)" ties the
    # note to the band without an arrow.
    ax[0].annotate("bolted fault (shaded):\n$V\\approx0$, so $P/V$ is "
                   "undefined",
                   xy=(3.55, 1.52), fontsize=7.5,
                   color="#8a3324", ha="left", va="top")
    ax[0].plot(ts_, sIp, color=BLUE, lw=1.1,
               label="Synchronous (bus-39 machine)")
    ax[0].plot(tg, gIp, color=RED, lw=1.1, label="GFM (REGFM_A1)")
    ax[0].axhline(0.0, color="#999999", ls="--", lw=0.7)
    ax[0].set_ylabel("Active current\n$I_{\\mathrm{P}} = P/V$  (pu)")
    ax[0].legend(loc="upper right", fontsize=8)
    ax[0].set_ylim(-0.3, 1.8)
    ax[1].plot(ts_, sIq, color=BLUE, lw=1.1,
               label="Synchronous (bus-39 machine)")
    ax[1].plot(tg, gIq, color=RED, lw=1.1, label="GFM (REGFM_A1)")
    ax[1].axhline(0.0, color="#999999", ls="--", lw=0.7)
    ax[1].set_ylabel("Reactive current\n$I_{\\mathrm{Q}} = Q/V$  (pu)")
    ax[1].set_xlabel("Time (s)")
    ax[1].set_ylim(-1.2, 1.2)
    ax[1].legend(loc="upper right", fontsize=8)
    fig.savefig(OUT / "smib_IPIQ.png")
    plt.close(fig)
    print("wrote", OUT / "smib_IPIQ.png")


def main():
    sy, gf = load()
    fig_vi(sy, gf)
    fig_pf(sy, gf)
    fig_ipiq(sy, gf)


if __name__ == "__main__":
    main()
