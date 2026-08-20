"""Report-format regeneration of the energy-surface juxtaposition
figure (report fig:juxtapose). Reuses the physics/compute of the
sharp-jackson meeting script unchanged; only the layout, sizing, and
text change per the 2026-08-07 figure standard:
- exact print size (6.5 in wide, included at width=\\textwidth)
- CMU Serif, 11 pt to match the document
- minimal on-figure text (explanations live in the LaTeX caption)
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

SRC = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
           r"\sharp-jackson-1e89b8\experiments\cct_energy_function_multiGFM")
OUT = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
           r"\upbeat-jones-67c8d3\report_26X\overleaf\figures")
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SRC.parent / "cct_structpres_39sync"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import juxtapose_sync_vs_gfm_surface as J   # noqa: E402  (original)
import figstyle_26x as st                   # noqa: E402

st.apply()          # CMU Serif, 11 pt, exact-inch save contract
np.seterr(all="ignore")


def main():
    panels = []
    for label, kind, emt, th_cct, grid in J.CASES:
        print("[%s] build + surface..." % kind, flush=True)
        sys_, netP, netF, loads_, xg_ = J.build(kind)
        U, failm = J.slice_surface(sys_, netP, grid)
        Uw = np.where(failm, 1e6, U)
        lab = J.basins(Uw)
        i0 = int(np.argmin(np.abs(grid)))
        mask = (lab == lab[i0, i0]).astype(float)
        ts, g31, g32, THf, Wf = J.fault_path(sys_, netF, th_cct * 1.15)
        panels.append((label, kind, emt, th_cct, grid, U, failm, mask,
                       ts, g31, g32))
        print("[%s] done" % kind, flush=True)

    vmax = max(np.nanpercentile(np.where(p[6], np.nan, p[5]), 98)
               for p in panels)
    vmin = min(np.nanpercentile(np.where(p[6], np.nan, p[5]), 2)
               for p in panels)

    fig, axes = plt.subplots(
        1, 2, figsize=(st.TEXTWIDTH_IN, 3.3), layout="none",
        gridspec_kw=dict(left=0.085, right=0.985, top=0.90,
                         bottom=0.305, wspace=0.24))
    for ax, (label, kind, emt, th_cct, grid, U, failm, mask, ts, g31,
             g32) in zip(axes, panels):
        GX, GY = np.meshgrid(grid, grid)
        Ushow = np.where(failm, np.nan, np.clip(U, vmin, vmax))
        cs = ax.contourf(GX, GY, Ushow, levels=30, cmap="viridis")
        ax.contour(GX, GY, Ushow, levels=15, colors="k",
                   linewidths=0.25, alpha=0.4)
        ax.contourf(GX, GY, mask, levels=[0.5, 1.5], colors=["w"],
                    alpha=0.14)
        ax.contour(GX, GY, mask, levels=[0.5], colors="w",
                   linewidths=1.8)
        ax.plot(g31, g32, color="w", ls=":", lw=1.4)
        blo = (np.interp(emt[0], ts, g31), np.interp(emt[0], ts, g32))
        bhi = (np.interp(emt[1], ts, g31), np.interp(emt[1], ts, g32))
        ax.plot([blo[0], bhi[0]], [blo[1], bhi[1]], color="w", lw=7.0,
                solid_capstyle="butt", zorder=7)
        ax.plot([blo[0], bhi[0]], [blo[1], bhi[1]], color="k", lw=4.5,
                solid_capstyle="butt", zorder=8)
        tp = (np.interp(th_cct, ts, g31), np.interp(th_cct, ts, g32))
        ax.plot(tp[0], tp[1], marker="D", ms=7, color="tab:red",
                mec="w", mew=0.9, zorder=9)
        ax.plot(0, 0, "o", ms=8, mfc="none", mec="w", mew=1.7)
        if kind == "sync":
            axi = ax.inset_axes([0.54, 0.54, 0.43, 0.43])
            axi.contourf(GX, GY, Ushow, levels=30, cmap="viridis")
            axi.contourf(GX, GY, mask, levels=[0.5, 1.5],
                         colors=["w"], alpha=0.14)
            axi.plot(g31, g32, color="w", ls=":", lw=1.8)
            axi.plot([blo[0], bhi[0]], [blo[1], bhi[1]], color="k",
                     lw=8.0, solid_capstyle="butt", zorder=8)
            axi.plot(tp[0], tp[1], marker="D", ms=8,
                     color="tab:red", mec="w", mew=0.9, zorder=9)
            axi.set_xlim(tp[0] - 9, tp[0] + 9)
            axi.set_ylim(tp[1] - 9, tp[1] + 9)
            axi.set_xticks([])
            axi.set_yticks([])
            for sp in axi.spines.values():
                sp.set_color("w")
                sp.set_linewidth(1.2)
            ax.indicate_inset_zoom(axi, edgecolor="w", lw=1.0)
            ms_ = J.measured_path_sync()
            if ms_ is not None:
                tm_s, s31, s32 = ms_
                i_cl = int(np.argmin(np.abs(tm_s - 0.25)))
                ax.plot(s31[i_cl], s32[i_cl], marker="*", ms=12,
                        color="cyan", mec="k", mew=0.7, zorder=9)
        if kind == "gfm":
            tm, m31, m32 = J.measured_path_gfm()
            i_cl = int(np.argmin(np.abs(tm - 1.7)))
            ax.plot(m31[i_cl], m32[i_cl], marker="*", ms=12,
                    color="cyan", mec="k", mew=0.7, zorder=9)
        ax.set_xlabel(r"$\gamma_{31}$ (deg)")
        ax.set_title(label)
        ax.set_xlim(grid[0], grid[-1])
        ax.set_ylim(grid[0], grid[-1])
    axes[0].set_ylabel(r"$\gamma_{32}$ (deg)")
    fig.colorbar(cs, ax=axes, label="$U$ (pu)", shrink=0.9, pad=0.015)
    handles = [
        Line2D([], [], color="w", lw=1.8, label="basin border (model)"),
        Line2D([], [], color="w", ls=":", lw=1.4,
               label="fault-on trajectory (model)"),
        Line2D([], [], color="tab:red", marker="D", ls="none", ms=7,
               mec="w", label="model CCT"),
        Line2D([], [], color="k", lw=4.0,
               label="model position at EMT CCT"),
        Line2D([], [], color="cyan", marker="*", ls="none", ms=11,
               mec="k", label="EMT state at its CCT"),
        Line2D([], [], color="w", marker="o", ls="none", ms=7,
               mfc="none", mew=1.5, label="start")]
    leg = fig.legend(handles=handles, ncol=3, loc="lower center",
                     bbox_to_anchor=(0.5, 0.005), fontsize=9,
                     handlelength=1.6, columnspacing=1.1)
    leg.get_frame().set_facecolor("#8f9a9e")
    fig.savefig(OUT / "juxtapose_sync_vs_gfm_meeting.png", dpi=600)
    print("wrote", OUT / "juxtapose_sync_vs_gfm_meeting.png")


if __name__ == "__main__":
    main()
