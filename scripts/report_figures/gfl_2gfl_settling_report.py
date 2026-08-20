"""Report-format regeneration of gfl_2gfl_settling (report fig:gfl2).

Same content as the original settling_compare_30s.png produced by
experiments/fault_3PG_bus14_2GFL/analyze_settling_30s.py in the
compassionate-banach-aa8040 worktree (2026-07-22): four stacked 30 s
panels (system f, bus-16 Vrms, bus-32 Vrms, bus-32 P) comparing the
all-synchronous baseline, 2 GFM (REGFM_A1 at buses 32+33) and 2 GFL
(PNNL WECC GFL at buses 32+33) under the identical 3PG at bus 14
(5 cycles, no reclose).

Differences from the original, per the 2026-08-07 figure standard:
- true print size 0.9*\textwidth = 5.85 in, TeX Gyre Pagella 11 pt;
- transient zoom insets (2.8-5.5 s) on the voltage / power panels
  (aggregate_report.py pattern) instead of a separate "late" figure;
- no in-figure prose title/footnote (the LaTeX caption carries it).

Data sources (the original loaded the SAME runs, via archived .out
chunks for sync/2GFM; here the per-run data_*.csv exports are used):
  sync : sharp-jackson-1e89b8  experiments/fault_baseline_sync_machines/
         runs/3PG_at_bus14_t3p0s_5cyc_norecl_30s/data_*.csv
  2GFM : sharp-jackson-1e89b8  experiments/fault_3PG_bus14_2GFM/
         runs/3PG_at_bus14_w_2GFM_at_bus32_and_bus33_t3p0s_5cyc_norecl_30s/data_*.csv
  2GFL : compassionate-banach-aa8040  experiments/fault_3PG_bus14_2GFL/
         runs/3PG_at_bus14_w_2GFL_at_bus32_and_bus33_t3p0s_5cyc_norecl_30s/data_*.csv
"""
import sys
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import figstyle_26x as st   # noqa: E402

st.apply()

WT = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees")
RUN_SYNC = (WT / "sharp-jackson-1e89b8" / "experiments"
            / "fault_baseline_sync_machines" / "runs"
            / "3PG_at_bus14_t3p0s_5cyc_norecl_30s")
RUN_GFM = (WT / "sharp-jackson-1e89b8" / "experiments"
           / "fault_3PG_bus14_2GFM" / "runs"
           / "3PG_at_bus14_w_2GFM_at_bus32_and_bus33_t3p0s_5cyc_norecl_30s")
RUN_GFL = (WT / "compassionate-banach-aa8040" / "experiments"
           / "fault_3PG_bus14_2GFL" / "runs"
           / "3PG_at_bus14_w_2GFL_at_bus32_and_bus33_t3p0s_5cyc_norecl_30s")
OUT = (WT / "upbeat-jones-67c8d3" / "report_26X" / "overleaf" / "figures"
       / "gfl_2gfl_settling.png")

VBASE_KV = 230.0
T_FAULT, T_CLEAR = 3.0, 3.0833
XLIM = (2.0, 30.0)
ZOOM = (2.8, 5.5)


def load(run_dir, want):
    csv = sorted(run_dir.glob("data_*.csv"))[-1]
    wanted = set(want) | {"TIME"}
    df = pd.read_csv(csv, usecols=lambda c: c.strip('" ') in wanted,
                     dtype="float32")
    df.columns = [c.strip('" ') for c in df.columns]
    print("loaded %s (%d rows)" % (csv.name, len(df)))
    return df


def fault_band(ax):
    ax.axvspan(T_FAULT, T_CLEAR, color="red", alpha=0.15, lw=0, zorder=0)


def main():
    sync = load(RUN_SYNC, ("f", "B16Vrms"))
    gfm = load(RUN_GFM, ("f", "B16Vrms", "B32Vrms", "B32P"))
    gfl = load(RUN_GFL, ("f", "B16Vrms", "B32Vrms", "B32P"))
    systems = [("all-sync", sync, "0.45"),
               ("2 GFM", gfm, "tab:blue"),
               ("2 GFL", gfl, "tab:red")]

    fig, axes = plt.subplots(4, 1, figsize=(0.9 * st.TEXTWIDTH_IN, 7.0),
                             sharex=True)
    panels = [("f", 1.0, "f (Hz)"),
              ("B16Vrms", VBASE_KV, r"bus 16 $V_\mathrm{rms}$ (pu)"),
              ("B32Vrms", VBASE_KV, r"bus 32 $V_\mathrm{rms}$ (pu)"),
              ("B32P", 1.0, "bus 32 P (MW)")]
    # transient zoom insets (aggregate_report.py pattern); rects tuned
    # to sit below the sustained 2GFL oscillation band in each panel
    rects = {"B16Vrms": [0.32, 0.14, 0.40, 0.48],
             "B32Vrms": [0.34, 0.12, 0.40, 0.46],
             "B32P":    [0.34, 0.10, 0.40, 0.46]}

    for ax, (sig, base, ylab) in zip(axes, panels):
        for name, d, c in systems:
            if sig not in d.columns:
                continue
            s = max(1, len(d) // 24000)
            ax.plot(d["TIME"][::s], d[sig][::s] / base, color=c, lw=0.7,
                    label=name)
        fault_band(ax)
        ax.grid(alpha=0.3)
        ax.set_ylabel(ylab)
        ax.set_xlim(*XLIM)
        if sig in rects:
            # opaque white card under the inset: covers the inset frame
            # plus its tick-label margins so tick labels sit on white,
            # never on parent traces or the parent spine
            rx, ry, rw, rh = rects[sig]
            pad_l, pad_b, pad_r, pad_t = 0.055, 0.13, 0.030, 0.006
            card = Rectangle((rx - pad_l, ry - pad_b),
                             rw + pad_l + pad_r, rh + pad_b + pad_t,
                             transform=ax.transAxes, facecolor="white",
                             edgecolor="#9AA3A8", lw=0.6, zorder=4.4,
                             clip_on=False)
            ax.add_patch(card)
            axi = ax.inset_axes(rects[sig])
            axi.patch.set_facecolor("white")
            axi.patch.set_alpha(1.0)
            for name, d, c in systems:
                if sig not in d.columns:
                    continue
                m = (d["TIME"] >= ZOOM[0]) & (d["TIME"] <= ZOOM[1])
                dz = d[m]
                sz = max(1, len(dz) // 12000)
                axi.plot(dz["TIME"][::sz], dz[sig][::sz] / base,
                         color=c, lw=0.7)
            fault_band(axi)
            axi.set_xlim(*ZOOM)
            axi.tick_params(labelsize=8)
            ax.indicate_inset_zoom(axi, edgecolor="0.35", lw=0.9)
    # zorder above the inset card so the note's tail is not occluded;
    # the tail lands on the card's empty lower-left margin (white)
    axes[2].text(0.02, 0.03, "all-sync case has no bus-32 meter",
                 transform=axes[2].transAxes, ha="left", fontsize=8,
                 color="0.45", zorder=6)
    axes[0].legend(loc="lower right", fontsize=9, ncol=3)
    axes[-1].set_xlabel("time (s)")
    fig.savefig(OUT, dpi=600)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
