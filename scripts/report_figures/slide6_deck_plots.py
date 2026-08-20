"""Deck slide-6 plots: all-GFM and all-synchronous active power at the
bus-10 three-phase fault, 30 s, per-unit on each generator's own base.

Regenerated to the 26X figure standard for the deck (2026-08-07): the
report body font (TeX Gyre Pagella), sized to the slide's picture box
(7.33 x 2.10 in), and with a transient zoom inset placed over the flat
steady-state stretch so the ride-through is legible at presentation
size.

Data and per-unit bases are the originals used by
make_bus10_sync_deck.py in sharp-jackson (agg_block); nothing in that
worktree is modified.
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SJ = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
          r"\sharp-jackson-1e89b8\experiments")
OUT = Path(r"C:\Users\roena\AppData\Local\Temp\claude"
           r"\C--UT-research-NateRoe-ERCOT-Project--claude-worktrees"
           r"-upbeat-jones-67c8d3\30e56d97-153f-4147-9c6f-ea52cf7ef0b9"
           r"\scratchpad\figexport")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import figstyle_26x as st        # noqa: E402

st.apply()

CASES = {
    # bus-10 fault (the deck's original pair)
    "bus10": {
        "sync": (SJ / "fault_3PG_bus10_sync_vs_GFM" / "runs"
                 / "3PG_at_bus10_sync_machines_t3p0s_5cyc_norecl_30s"
                 / "data_20260616_143335.csv"),
        "gfm": (SJ / "fault_loc_sweep_gfm32_Ilim1p5" / "runs"
                / "3PG_at_bus10_w_10GFM_Vsched_Ilim1p5"
                  "_t3p0s_5cyc_norecl_30s"
                / "data_20260609_141738.csv"),
        "note": True,     # Gen 32 is disconnected by the clearing
    },
    # bus-14 fault: the report's reference case, no unit lost
    "bus14": {
        "sync": (SJ / "fault_baseline_sync_machines" / "runs"
                 / "3PG_at_bus14_t3p0s_5cyc_norecl_30s"
                 / "data_20260530_115949.csv"),
        "gfm": (SJ / "fault_3PG_bus14_10GFM" / "runs"
                / "3PG_at_bus14_w_10GFM_at_bus30_bus31_bus32_bus33"
                  "_bus34_bus35_bus36_bus37_bus38_bus39"
                  "_t3p0s_5cyc_norecl_30s"
                / "data_20260602_233631.csv"),
        "note": False,
    },
}

MBASE_SYNC = {30: 250, 31: 600, 32: 650, 33: 650, 34: 525,
              35: 650, 36: 560, 37: 550, 38: 850, 39: 2000}
MBASE_GFM = {30: 417, 31: 997, 32: 1083, 33: 1053, 34: 847,
             35: 1083, 36: 933, 37: 900, 38: 1383, 39: 1667}

FAULT_T, FAULT_DUR = 3.0, 5.0 / 60.0
ZOOM = (2.8, 5.5)
BUSCOL = re.compile(r"^B(3[0-9])P$")

# slide picture box
W_IN, H_IN = 7.33, 2.10


def load(csv, mbase, sig="P", only=None):
    """Load B<N><sig> channels. For P, per-unit on each machine's own
    MVA base; other signals are left in their exported units. `only`
    restricts to an explicit bus list so two runs can be compared on
    exactly the same channel set."""
    pat = re.compile(r"^B(\d+)%s$" % sig)
    with open(csv) as f:
        header = next(f).rstrip("\n").split(",")
    cand = [c for c in header if pat.match(c)]
    if only is not None:
        cand = [c for c in cand if int(pat.match(c).group(1)) in only]
    elif sig == "P":
        cand = [c for c in cand
                if 30 <= int(pat.match(c).group(1)) <= 39]
    df = pd.read_csv(csv, usecols=["TIME"] + cand, dtype="float32")
    buses = sorted(int(pat.match(c).group(1)) for c in cand)
    if sig == "P":
        for b in buses:
            if b in mbase:
                df["B%dP" % b] = df["B%dP" % b] / mbase[b]
    return df, buses


def panel(csv, mbase, stem, title, note, sig="P", only=None,
          ylabel="P (pu of own base)", lab="Gen %d"):
    df, buses = load(csv, mbase, sig, only)
    s = max(1, len(df) // 20000)
    cmap = plt.get_cmap("tab10")
    fig, ax = plt.subplots(figsize=(W_IN, H_IN))
    col = "B%d" + sig
    for k, b in enumerate(buses):
        ax.plot(df["TIME"][::s], df[col % b][::s], lw=0.6,
                color=cmap(k % 10), label=lab % b)
    ax.axvspan(FAULT_T, FAULT_T + FAULT_DUR, color="#fbd0c4",
               alpha=0.6, zorder=0)
    ax.set_xlim(2.0, 30.0)
    ax.grid(alpha=0.3)
    ax.set_xlabel("time (s)", fontsize=9)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.tick_params(labelsize=8)

    # Gen 32 is radially connected to the faulted bus 10 through its
    # step-up transformer, so clearing without reclose disconnects it
    # (measured: I = 0, bus voltage healthy). Say so on the figure.
    ax.set_title(title, fontsize=11, loc="left", pad=4)
    if note:
        lo, hi = ax.get_ylim()
        ax.annotate("Gen 32 disconnected by the clearing",
                    xy=(8.0, 0.0), xytext=(6.0, lo + 0.30 * (hi - lo)),
                    fontsize=7.5, color="0.25", ha="left",
                    arrowprops=dict(arrowstyle="-|>", lw=0.8,
                                    color="0.35"))

    axi = ax.inset_axes([0.50, 0.30, 0.33, 0.52])
    m = (df["TIME"] >= ZOOM[0]) & (df["TIME"] <= ZOOM[1])
    dz = df[m]
    sz = max(1, len(dz) // 8000)
    for k, b in enumerate(buses):
        axi.plot(dz["TIME"][::sz], dz[col % b][::sz], lw=0.7,
                 color=cmap(k % 10))
    axi.axvspan(FAULT_T, FAULT_T + FAULT_DUR, color="#fbd0c4",
                alpha=0.6, zorder=0)
    axi.set_xlim(*ZOOM)
    axi.tick_params(labelsize=7)
    ax.indicate_inset_zoom(axi, edgecolor="0.35", lw=0.8)

    ax.legend(fontsize=6, ncol=5, loc="upper right", framealpha=0.85,
              handlelength=1.0, columnspacing=0.7, borderpad=0.3)
    fig.savefig(OUT / (stem + ".png"), dpi=600)
    print("wrote", OUT / (stem + ".png"))


if __name__ == "__main__":
    # bus-10: generator active power, all ten units (both runs have them)
    c = CASES["bus10"]
    panel(c["gfm"], MBASE_GFM, "slide6_bus10_gfm_p",
          "All AGS System", c["note"])
    panel(c["sync"], MBASE_SYNC, "slide6_bus10_sync_p",
          "All Synchronous Machine System", c["note"])

    # bus-14 (the report's reference fault): the all-synchronous run
    # only exported generator 30's power, so the like-for-like channel
    # set common to both runs is the seven monitored buses. Bus RMS
    # voltage is the right quantity there and is what the report uses
    # for this case.
    COMMON = [14, 15, 16, 17, 18, 21, 30]
    c = CASES["bus14"]
    panel(c["gfm"], MBASE_GFM, "slide6_bus14_gfm_v",
          "All AGS System", c["note"], sig="Vrms", only=COMMON,
          ylabel="Vrms (kV)", lab="Bus %d")
    panel(c["sync"], MBASE_SYNC, "slide6_bus14_sync_v",
          "All Synchronous Machine System", c["note"], sig="Vrms",
          only=COMMON, ylabel="Vrms (kV)", lab="Bus %d")
