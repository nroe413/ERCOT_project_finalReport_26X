"""Report-format 30-second system-response figures (2026-08-07 figure
standard): true print size, CMU Serif 11 pt, and a transient zoom
inset placed over the flat steady-state region of the 30 s window so
the figure shows both the ride-through transient (magnified) and the
steady-state stability without a double-wide canvas.

Reads the same per-run data_*.csv archives the original
plot_fault_traces.py figures were built from (B<N>{Vrms|Irms|P|Q}
channels); no smoothing beyond point-striding for raster economy.

Report invocations (confirmed 2026-09-18 by regenerating and comparing pixels with the report PNGs;
E = the experiments folder of the study, each CSV the newest data_*.csv of the run):
  Figures 19-22  single  E/fault_3PG_bus14_10GFM/runs/3PG_at_bus14_w_10GFM_at_bus30_..._bus39_t3p0s_5cyc_norecl_30s
                 Vrms allgfm_vrms | Irms allgfm_irms low | P allgfm_p low | Q allgfm_q low
  Figure 24      sweep   E/fault_3PG_bus14_0GFM/runs/3PG_at_bus14_t3p0s_5cyc_norecl_30s
                         E/fault_3PG_bus14_5GFM/runs/3PG_at_bus14_w_5GFM_at_bus30_bus32_bus33_bus35_bus37_t3p0s_5cyc_norecl_30s
                         E/fault_3PG_bus14_10GFM/runs/(the Figures 19-22 run)      sweep_0_5_10_GFM_vrms
The B<N> channels are the 230 kV meters at network buses 14-18 and 21 and on the 230 kV side of each
unit's step-up transformer (buses 30-39).

Modes:
  single  <csv> <signal> <out_stem>          one signal, one run
  grid    <csv> <out_stem>                   2x2 Vrms/Irms/P/Q
  sweep   <csv0> <csv5> <csv10> <out_stem>   Vrms stack, 0/5/10 GFM
"""
import csv as csvmod
import re
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
from matplotlib.patches import Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent))
import figstyle_26x as st   # noqa: E402

st.apply()
OUT = rp.OUT
FAULT_T, FAULT_DUR = 3.0, 5.0 / 60.0
ZOOM = (2.8, 5.5)               # transient window shown in the inset
YLBL = {"P": r"$P$ (MW)", "Q": r"$Q$ (MVAr)",
        "Vrms": r"$V_{\mathrm{rms}}$ (kV)",
        "Irms": r"$I_{\mathrm{rms}}$ (kA)"}


def load(csv_path, signals):
    """Load TIME + every B<N><signal> column, striding to plot scale."""
    with open(csv_path) as f:
        header = next(csvmod.reader(f))
    keep = ["TIME"]
    pat = re.compile(r"^B(\d+)(%s)$" % "|".join(signals))
    for c in header:
        if pat.match(c):
            keep.append(c)
    df = pd.read_csv(csv_path, usecols=keep, dtype="float32")
    return df


def buses_of(df, signal):
    bb = sorted(int(m.group(1)) for c in df.columns
                for m in [re.match(r"^B(\d+)%s$" % signal, c)] if m)
    return bb


def stride(df, n_target=24000):
    return max(1, len(df) // n_target)


def draw(ax, df, signal, s, lw=0.6):
    cmap = plt.get_cmap("tab10")
    bb = buses_of(df, signal)
    for k, bus in enumerate(bb):
        ax.plot(df["TIME"][::s], df["B%d%s" % (bus, signal)][::s],
                color=cmap(k % 10), lw=lw, label="Bus %d" % bus)
    ax.axvspan(FAULT_T, FAULT_T + FAULT_DUR, color="#fbd0c4",
               alpha=0.5, zorder=0)
    ax.set_xlim(float(df["TIME"].iloc[0]), float(df["TIME"].iloc[-1]))
    ax.grid(alpha=0.3)
    return bb


def add_zoom(ax, df, signal, rect):
    # Keep the inset's below-frame tick-label strip inside the parent
    # axes (never straddling the parent's bottom spine): raise the inset
    # bottom if the ~0.26 in label strip would not fit under it.
    fig = ax.figure
    bb = ax.get_position()
    pad_frac = 0.26 / (fig.get_figheight() * bb.height)
    rect = list(rect)
    rect[1] = max(rect[1], pad_frac + 0.012)
    axi = ax.inset_axes(rect)
    m = (df["TIME"] >= ZOOM[0]) & (df["TIME"] <= ZOOM[1])
    dz = df[m]
    sz = max(1, len(dz) // 12000)
    cmap = plt.get_cmap("tab10")
    for k, bus in enumerate(buses_of(df, signal)):
        axi.plot(dz["TIME"][::sz], dz["B%d%s" % (bus, signal)][::sz],
                 color=cmap(k % 10), lw=0.7)
    axi.axvspan(FAULT_T, FAULT_T + FAULT_DUR, color="#fbd0c4",
                alpha=0.5, zorder=0)
    axi.set_xlim(*ZOOM)
    axi.tick_params(labelsize=8)
    axi.patch.set_facecolor("white")
    axi.patch.set_alpha(1.0)
    ind = ax.indicate_inset_zoom(axi, edgecolor="0.35", lw=0.9)
    _inset_card(ax, axi, ind)
    return axi


def _inset_card(ax, axi, ind):
    """Opaque white card under the zoom inset (frame + tick-label
    margins) so inset tick labels sit on white, never on the parent's
    traces; hide any zoom connector that would cross that label strip."""
    fig = ax.figure
    fig.canvas.draw()                 # realize tick labels for measuring
    ren = fig.canvas.get_renderer()
    inv = ax.transAxes.inverted()
    tb = axi.get_tightbbox(ren)       # frame + tick labels, display px
    (x0, y0), (x1, y1) = inv.transform([[tb.x0, tb.y0], [tb.x1, tb.y1]])
    mg = 0.006                        # small breathing margin
    x0, y0, x1, y1 = x0 - mg, y0 - mg, x1 + mg, y1 + mg
    card = Rectangle((x0, y0), x1 - x0, y1 - y0,
                     transform=ax.transAxes, facecolor="white",
                     edgecolor="#9AA3A8", lw=0.5, zorder=4.5)
    ax.add_patch(card)
    # inset frame rectangle in parent-axes fraction (slightly expanded)
    eps = 0.004
    (fx0, fy0) = inv.transform(axi.transAxes.transform((0, 0)))
    (fx1, fy1) = inv.transform(axi.transAxes.transform((1, 1)))
    fx0, fy0, fx1, fy1 = fx0 - eps, fy0 - eps, fx1 + eps, fy1 + eps
    for c in ind.connectors:
        if not c.get_visible():
            continue
        p1 = inv.transform(c.coords1.transform(c.xy1))
        p2 = inv.transform(c.coords2.transform(c.xy2))
        t = np.linspace(0.02, 0.98, 300)[:, None]
        pts = p1[None, :] * (1 - t) + p2[None, :] * t
        in_card = ((pts[:, 0] > x0) & (pts[:, 0] < x1) &
                   (pts[:, 1] > y0) & (pts[:, 1] < y1))
        in_frame = ((pts[:, 0] > fx0) & (pts[:, 0] < fx1) &
                    (pts[:, 1] > fy0) & (pts[:, 1] < fy1))
        if np.any(in_card & ~in_frame):
            c.set_visible(False)      # it would strike the label strip


def mode_single(csv_path, signal, out_stem, inset_rect, legend_loc):
    df = load(csv_path, [signal])
    s = stride(df)
    fig, ax = plt.subplots(figsize=(st.TEXTWIDTH_IN, 2.9))
    draw(ax, df, signal, s)
    add_zoom(ax, df, signal, inset_rect)
    ax.set_xlabel("time (s)")
    ax.set_ylabel(YLBL[signal])
    ax.legend(fontsize=7, ncol=4, loc=legend_loc, framealpha=0.85,
              handlelength=1.1, columnspacing=0.8)
    fig.savefig(OUT / (out_stem + ".png"), dpi=600)
    print("wrote", OUT / (out_stem + ".png"))


def mode_grid(csv_path, out_stem):
    df = load(csv_path, ["Vrms", "Irms", "P", "Q"])
    s = stride(df)
    fig, axes = plt.subplots(2, 2, figsize=(st.TEXTWIDTH_IN, 4.9))
    rects = {"Vrms": [0.35, 0.10, 0.62, 0.52],
             "Irms": [0.35, 0.42, 0.62, 0.52],
             "P":    [0.35, 0.10, 0.62, 0.42],
             "Q":    [0.35, 0.55, 0.62, 0.40]}
    for ax, sig in zip(axes.flat, ["Vrms", "Irms", "P", "Q"]):
        draw(ax, df, sig, s, lw=0.5)
        add_zoom(ax, df, sig, rects[sig])
        ax.set_ylabel(YLBL[sig], fontsize=9)
        ax.tick_params(labelsize=8)
    for ax in axes[1]:
        ax.set_xlabel("time (s)", fontsize=9)
    fig.savefig(OUT / (out_stem + ".png"), dpi=600)
    print("wrote", OUT / (out_stem + ".png"))


def mode_sweep(paths, out_stem):
    labels = ["0 grid-forming units", "5 grid-forming units",
              "10 grid-forming units"]
    fig, axes = plt.subplots(3, 1, figsize=(st.TEXTWIDTH_IN, 5.6),
                             sharex=True)
    for ax, p, lab in zip(axes, paths, labels):
        df = load(p, ["Vrms"])
        s = stride(df, 16000)
        draw(ax, df, "Vrms", s, lw=0.5)
        add_zoom(ax, df, "Vrms", [0.40, 0.10, 0.57, 0.55])
        ax.set_ylabel(r"$V_{\mathrm{rms}}$ (kV)", fontsize=9)
        ax.set_title(lab, fontsize=10, loc="left")
        ax.tick_params(labelsize=8)
    axes[-1].set_xlabel("time (s)")
    fig.savefig(OUT / (out_stem + ".png"), dpi=600)
    print("wrote", OUT / (out_stem + ".png"))


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "single":
        rect = [0.40, 0.10, 0.57, 0.55]
        loc = "upper right"
        if len(sys.argv) > 5 and sys.argv[5] == "low":
            rect = [0.40, 0.38, 0.57, 0.55]
            loc = "lower right"
        mode_single(sys.argv[2], sys.argv[3], sys.argv[4], rect, loc)
    elif mode == "grid":
        mode_grid(sys.argv[2], sys.argv[3])
    elif mode == "sweep":
        mode_sweep(sys.argv[2:5], sys.argv[5])
