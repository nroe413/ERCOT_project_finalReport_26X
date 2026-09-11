"""Figure 13 of the 26X report: bus RMS voltages under the reference
bus-14 fault at the first two steps of the machine-for-inverter
progression (one machine replaced, two machines replaced).

Rebuilt 2026-08-11 for a STACKED layout.  The previous pair was created
6.5 in wide and included at 0.85\\textwidth, a 15 % LaTeX downscale that
pushed the legend to 5.95 pt and the ticks to 8.5 pt.  These are built
at the true printed width (0.85 * 6.5 = 5.525 in), so source points are
printed points: 11 pt axis labels, 10 pt ticks, 9 pt legend, 8.5 pt
inset ticks.

Both panels share identical x and y limits, and identical inset limits,
so the two penetration levels can be compared directly.

Source data (PSCAD EMT, 5 us step, channels at 5 kHz, 3PG at bus 14 at
t = 3.0 s for 5 cycles, reclose disabled, 30 s window):

  1 GFM   experiments/fault_baseline_sync_machines/runs/
          3PG_at_bus14_w_1GFM_at_bus32_t3p0s_5cyc_norecl_30s/
          data_20260601_150554.csv
  2 GFM   experiments/fault_3PG_bus14_2GFM/runs/
          3PG_at_bus14_w_2GFM_at_bus32_and_bus33_t3p0s_5cyc_norecl_30s/
          data_20260526_224733.csv

Nothing is smoothed; the traces are the recorded B<N>Vrms channels,
strided for raster economy only.  Run with --refresh to re-extract the
Vrms columns from the 1.9 GB run archives (otherwise a local .npz cache
of just those columns is used).
"""
import csv as csvmod
import re
import sys
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_paths as rp  # noqa: E402

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import figstyle_26x as st   # noqa: E402

EXP = rp.experiment(r"experiments")
OUT = rp.OUT
# the Vrms columns only, cached outside the repo so the 1.9 GB run
# archives are read once; delete it or pass --refresh to re-extract
CACHE = Path(tempfile.gettempdir()) / "vrms12gfm_channel_cache"

CASES = [
    dict(stem="vrms_1gfm",
         title="One machine replaced (bus 32)",
         csv=EXP / "fault_baseline_sync_machines" / "runs"
             / "3PG_at_bus14_w_1GFM_at_bus32_t3p0s_5cyc_norecl_30s"
             / "data_20260601_150554.csv"),
    dict(stem="vrms_2gfm",
         title="Two machines replaced (buses 32 and 33)",
         csv=EXP / "fault_3PG_bus14_2GFM" / "runs"
             / "3PG_at_bus14_w_2GFM_at_bus32_and_bus33_t3p0s_5cyc_"
               "norecl_30s" / "data_20260526_224733.csv"),
]

FAULT_T, FAULT_DUR = 3.0, 5.0 / 60.0
ZOOM = (2.8, 5.5)               # transient window, right-hand panel
XLIM = (0.0, 30.0)
YLIM = (-10.0, 272.0)           # shared by every panel of both figures

WIDTH_IN = st.TEXTWIDTH_IN * 0.85       # 5.525 in, the printed width
HEIGHT_IN = 2.35

# explicit margins (constrained_layout is off, so the hand-placed
# labels and the exact-inch contract cannot fight each other)
MARG = dict(left=0.104, right=0.987, top=0.878, bottom=0.182,
            wspace=0.055)


def extract(csv_path, stem):
    """TIME + every B<N>Vrms column, cached as a small .npz."""
    npz = CACHE / (stem + ".npz")
    if npz.exists() and "--refresh" not in sys.argv:
        z = np.load(npz)
        return {k: z[k] for k in z.files}
    with open(csv_path) as f:
        header = next(csvmod.reader(f))
    pat = re.compile(r"^B(\d+)Vrms$")
    keep = ["TIME"] + [c for c in header if pat.match(c)]
    print("extracting %d columns from %s" % (len(keep), csv_path.name))
    df = pd.read_csv(csv_path, usecols=keep, dtype="float32")
    CACHE.mkdir(exist_ok=True)
    d = {c: df[c].to_numpy() for c in keep}
    np.savez_compressed(npz, **d)
    return d


def buses_of(d):
    return sorted(int(m.group(1)) for c in d
                  for m in [re.match(r"^B(\d+)Vrms$", c)] if m)


def draw(ax, d, mask, s, lw, label=False):
    cmap = plt.get_cmap("tab10")
    t = d["TIME"][mask]
    for k, bus in enumerate(buses_of(d)):
        ax.plot(t[::s], d["B%dVrms" % bus][mask][::s],
                color=cmap(k % 10), lw=lw,
                label=("Bus %d" % bus) if label else None,
                solid_joinstyle="round", solid_capstyle="round")
    ax.axvspan(FAULT_T, FAULT_T + FAULT_DUR, color="#f6a68f",
               alpha=0.75, lw=0, zorder=0)
    ax.set_ylim(*YLIM)
    ax.grid(alpha=0.3)


def build(case):
    d = extract(case["csv"], case["stem"])
    t = d["TIME"]

    fig, (axL, axR) = plt.subplots(
        1, 2, figsize=(WIDTH_IN, HEIGHT_IN), sharey=True,
        gridspec_kw=dict(width_ratios=[1.52, 1.0]))
    fig.subplots_adjust(**MARG)

    # left: the whole 30 s window
    full = np.ones(len(t), dtype=bool)
    draw(axL, d, full, max(1, len(t) // 14000), lw=0.75, label=True)
    axL.set_xlim(*XLIM)
    axL.set_xticks([0, 10, 20, 30])
    # mark what the right-hand panel magnifies
    axL.axvspan(*ZOOM, color="0.55", alpha=0.13, lw=0, zorder=0)
    axL.set_ylabel(r"$V_{\mathrm{rms}}$ (kV)")
    axL.set_title(case["title"], fontsize=10, loc="left", pad=4)

    # right: the fault and recovery, same y scale
    zm = (t >= ZOOM[0]) & (t <= ZOOM[1])
    draw(axR, d, zm, max(1, int(zm.sum()) // 9000), lw=0.75)
    axR.set_xlim(*ZOOM)
    axR.set_xticks([3, 4, 5])
    axR.set_title("detail: 2.8 to 5.5 s", fontsize=9, loc="left",
                  pad=4, color="0.25")

    # one shared time axis label, centred under the pair
    fig.text(0.5 * (MARG["left"] + MARG["right"]), 0.012, "time (s)",
             ha="center", va="bottom")

    # legend inside the left panel: between the faulted bus 14 trace
    # (~30 kV) and the recovered buses (~230 kV) the panel is empty
    leg = axL.legend(loc="center right", bbox_to_anchor=(0.992, 0.40),
                     ncol=3, fontsize=9, frameon=True, framealpha=0.9,
                     edgecolor="none", handlelength=1.4,
                     handletextpad=0.45, columnspacing=1.05,
                     labelspacing=0.32, borderpad=0.35)
    leg.get_frame().set_linewidth(0)

    # the legend sits inside the data area, so prove it fits there
    fig.canvas.draw()
    lb = leg.get_window_extent().transformed(axL.transAxes.inverted())
    print("   legend in axes fraction: x %.3f-%.3f  y %.3f-%.3f"
          % (lb.x0, lb.x1, lb.y0, lb.y1))
    assert lb.x0 > 0.02 and lb.x1 < 1.0, "legend overflows the panel"
    assert lb.y0 > 0.19 and lb.y1 < 0.80, "legend hits the traces"

    p = OUT / (case["stem"] + ".png")
    fig.savefig(p, dpi=600)
    plt.close(fig)
    print("wrote %s  (%.3f x %.3f in)" % (p, WIDTH_IN, HEIGHT_IN))


if __name__ == "__main__":
    st.apply()
    # the shared style turns constrained_layout on; these panels place a
    # legend outside the axes, so margins are set by hand instead (the
    # exact-inch contract still holds, savefig.bbox stays "standard")
    matplotlib.rcParams["figure.constrained_layout.use"] = False
    for c in CASES:
        build(c)
