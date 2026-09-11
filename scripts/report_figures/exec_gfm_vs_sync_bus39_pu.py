"""Report-format regeneration of the bus-39 GFM-vs-sync per-unit
overview (report fig exec_gfm_vs_sync_bus39_pu, width=\\textwidth).

Reuses the data locations, per-unit bases, and channel math of the
original generator (sharp-jackson experiments/fault_3PG_bus39_GFMvsSync/
gfm_vs_sync_bus39_pu.py, imported as a module) and re-lays the four
panels at true print size: 6.5 in x 5.0 in, TeX Gyre Pagella 11 pt via
figstyle_26x. Each panel carries a transient zoom inset over
t in [2.8, 5.5] s, positioned over flat steady-state space, since the
main axes span the full 30 s window.

Per-unit base (documented in the report caption, not on the figure):
V_pu = V_LL/230 kV; I, P, Q on each device's own rating
(sync G1 2000 MVA, GFM 1667 MVA) referred to 230 kV.

Usage:  python exec_gfm_vs_sync_bus39_pu.py     (no args; 30 s window)
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

ORIG = rp.experiment(r"fault_3PG_bus39_GFMvsSync")
OUT = rp.OUT
sys.path.insert(0, str(ORIG))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Importing the original module must see no CLI args so its window
# defaults to "30s" (it reads sys.argv at import time).
_argv = sys.argv
sys.argv = [_argv[0]]
import gfm_vs_sync_bus39_pu as orig          # noqa: E402
sys.argv = _argv

import figstyle_26x as st                    # noqa: E402

st.apply()   # AFTER the orig import: it mutates rcParams at import time

FAULT_T = orig.FAULT_T
FAULT_DUR = 5.0 / 60.0                       # 5-cycle fault
ZOOM = (2.8, 5.5)
XMAX = 30.0
BLUE, RED = "#1f77b4", "#c0392b"


def load_leg(run_dir):
    csv = orig.newest(run_dir)
    print("reading", csv)
    df = pd.read_csv(csv, usecols=lambda c: c in orig.KEEP)
    return csv, df


def stride(n, cap):
    return max(1, n // cap)


def add_zoom(ax, rect, series, hide_conn=()):
    """Inset over ZOOM; series = [(t, y, color), ...].

    The inset patch is opaque white; the caller later lays an opaque
    white card (parent-axes coords) under the inset covering its
    tick-label margins so labels never sit on parent traces/spines.
    hide_conn: indices into indicate_inset_zoom's connector 4-tuple
    (lower_left, upper_left, lower_right, upper_right) to hide where
    a connector would strike labels or annotations.
    """
    axi = ax.inset_axes(rect)
    axi.patch.set_facecolor("white")
    axi.patch.set_alpha(1.0)
    for t, y, color in series:
        m = (t >= ZOOM[0]) & (t <= ZOOM[1])
        sz = stride(int(m.sum()), 15000)
        axi.plot(t[m][::sz], y[m][::sz], color=color, lw=0.7)
    axi.axvspan(FAULT_T, FAULT_T + FAULT_DUR, color="#fbd0c4",
                alpha=0.5, zorder=0)
    axi.set_xlim(*ZOOM)
    axi.tick_params(labelsize=8)
    _, conns = ax.indicate_inset_zoom(axi, edgecolor="0.35", lw=0.9)
    for i in hide_conn:
        conns[i].set_visible(False)
    return axi


def add_cards(fig, pairs, pad_pts=2.0):
    """Opaque white card under each inset (parent-axes coords) covering
    the inset frame plus its tick-label margins; zorder above the
    parent's traces/spines and below the inset axes (4.99)."""
    from matplotlib.patches import Rectangle
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    pad = pad_pts * fig.dpi / 72.0
    for ax, axi in pairs:
        bb = axi.get_tightbbox(renderer)
        inv = ax.transAxes.inverted()
        (x0, y0), (x1, y1) = inv.transform([(bb.x0 - pad, bb.y0 - pad),
                                            (bb.x1 + pad, bb.y1 + pad)])
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0,
                               transform=ax.transAxes, facecolor="white",
                               edgecolor="#9AA3A8", lw=0.5,
                               zorder=4.9, clip_on=False))


def main():
    gfm_csv, g = load_leg(orig.GFM_DIR)
    sync_csv, s = load_leg(orig.SYNC_DIR)
    tg, ts_ = g["TIME"].values, s["TIME"].values

    # per-unit conversions (per-device rating) — same math as the original
    gv = g["B39Vrms"].values / orig.VBASE_LL
    sv = s["B39Vrms"].values / orig.VBASE_LL
    gi = g["B39Irms"].values / orig.IBASE_GFM
    si = s["B39Irms"].values / orig.IBASE_SYNC
    gp = g["B39P"].values / orig.S_GFM
    sp = s["B39P"].values / orig.S_SYNC
    gq = g["B39Q"].values / orig.S_GFM
    sq = s["B39Q"].values / orig.S_SYNC

    fig, ax = plt.subplots(2, 2, figsize=(st.TEXTWIDTH_IN, 5.0))
    card_pairs = []

    def panel(a, ys, yg, ylab, title, zoom_rect, hide_conn=()):
        ks = stride(len(ts_), 60000)
        kg = stride(len(tg), 60000)
        a.plot(ts_[::ks], ys[::ks], color=BLUE, lw=0.8,
               label="100% synchronous (G1)")
        a.plot(tg[::kg], yg[::kg], color=RED, lw=0.8,
               label="grid-forming (GFM)")
        a.axvline(FAULT_T, color="#888888", ls=":", lw=0.8)
        a.set_xlim(2.0, XMAX)
        a.set_ylabel(ylab, fontsize=9)
        a.set_title(title, fontsize=10)
        a.tick_params(labelsize=8)
        a.grid(True, alpha=0.3)
        axi = add_zoom(a, zoom_rect,
                       [(ts_, ys, BLUE), (tg, yg, RED)],
                       hide_conn=hide_conn)
        card_pairs.append((a, axi))
        return axi

    # ---- voltage: steady curves sit near 1.0 pu; space is below ----
    a = ax[0, 0]
    panel(a, sv, gv, "Voltage (pu of 230 kV)",
          "Bus-39 voltage (pu)", [0.35, 0.10, 0.62, 0.52],
          hide_conn=(0, 2))
    a.axhline(1.0, color="#999999", ls="--", lw=0.7)
    a.set_ylim(0, 1.35)

    # ---- current: fault peaks are early-left; space is upper-right ----
    a = ax[0, 1]
    axi = panel(a, si, gi, "Current (pu of own rating)",
                "Bus-39 RMS current (pu)", [0.35, 0.40, 0.62, 0.55],
                hide_conn=(2,))
    a.axhline(1.5, color="#888888", ls="--", lw=0.8)
    a.set_ylim(0, max(6.4, float(np.nanmax(si)) * 1.05))
    axi.axhline(1.5, color="#888888", ls="--", lw=0.6)
    a.text(29.3, 1.36, r"GFM $I_{\max F}=1.5$", ha="right", va="top",
           fontsize=8, color="#555555",
           bbox=dict(facecolor="white", edgecolor="none", pad=1.0))

    # ---- P: settles mid-scale; free space at the bottom ----
    a = ax[1, 0]
    panel(a, sp, gp, "P (pu of own rating)",
          "Bus-39 active power (pu)", [0.35, 0.10, 0.62, 0.45],
          hide_conn=(0, 2))
    a.axhline(0, color="#999999", lw=0.6)

    # ---- Q: settles near 0; free space at the top ----
    a = ax[1, 1]
    panel(a, sq, gq, "Q (pu of own rating)",
          "Bus-39 reactive power (pu)", [0.35, 0.52, 0.62, 0.43],
          hide_conn=(2,))
    a.axhline(0, color="#999999", lw=0.6)

    for a in ax[1]:
        a.set_xlabel("Time (s)", fontsize=9)
    ax[0, 0].legend(loc="upper right", fontsize=8, framealpha=0.9,
                    handlelength=1.4)

    add_cards(fig, card_pairs)

    out_png = OUT / "exec_gfm_vs_sync_bus39_pu.png"
    fig.savefig(out_png, dpi=600)
    plt.close(fig)
    print("wrote", out_png)
    print("GFM  csv:", gfm_csv)
    print("SYNC csv:", sync_csv)


if __name__ == "__main__":
    main()
