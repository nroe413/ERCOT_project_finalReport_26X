"""Report-format regeneration of the two energy-surface case figures
(report figs energy_surface_below_cct / energy_surface_at_cct).

Both figures are the SAME two-panel plot -- the analytical potential
energy surface of the 39-bus system on the (gamma_31, gamma_32) slice,
all-synchronous fleet left, all-GFM fleet right, with the analytical
trajectory AND the recorded PSCAD EMT trajectory drawn on each -- and
differ only in how long the bus-14 fault is held:

  CASE A  energy_surface_below_cct.png
      each fleet cleared at its last stable measured rung
      (sync 0.237 s, all-GFM 1.6 s).  Both fleets return; analytical
      and EMT agree qualitatively.

  CASE B  energy_surface_at_cct.png
      each fleet cleared just under the ANALYTICAL critical time
      (sync 0.2455 s of 0.248 s, all-GFM 2.315 s of 2.34 s).  The sync
      system still returns, but the all-GFM EMT trajectory escapes over
      the ridge to the next well near 360 deg while the analytical
      model predicts it returns to the origin.  That contrast is the
      point of the pair: the classical energy method is
      anti-conservative for grid-forming inverters.

Physics/compute is the meeting script
    experiments/cct_energy_function_multiGFM/two_case_surfaces.py
imported unchanged (same surfaces, same model integration, same EMT
CSV harvest).  Only layout, sizing and text change here, per the
2026-08-07 figure standard:
  - exact print size (6.5 in wide, included at width=\\textwidth)
  - TeX Gyre Pagella at document sizes via figstyle_26x
  - savefig.bbox "standard" (no tight crop), 600 dpi
  - the on-figure CCT table of the meeting raster is DROPPED: at 6.5 in
    a monospace three-column table needs ~6 pt to fit inside the left
    panel, well under the document's smallest size.  Those numbers
    (sync analytical 0.248 s vs measured (0.237, 0.25]; all-GFM
    analytical 2.34 s vs measured (1.6, 1.7]) go in the LaTeX caption.

The four surfaces + model integrations take several minutes, so the
arrays are cached to an .npz.  Run with --recompute to rebuild them.

Usage:  python -u energy_surface_cases_report.py [--recompute]
"""
import os
import sys
import time
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator

SRC = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
           r"\sharp-jackson-1e89b8\experiments\cct_energy_function_multiGFM")
OUT = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
           r"\upbeat-jones-67c8d3\report_26X\overleaf\figures")
CACHE = Path(os.environ.get(
    "ENERGY_SURFACE_CACHE",
    Path(__file__).resolve().parent / "_energy_surface_cases_cache.npz"))

sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SRC.parent / "cct_structpres_39sync"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import two_case_surfaces as T                # noqa: E402  (original)
import figstyle_26x as st                    # noqa: E402

st.apply()          # AFTER T: its import sets meeting-format rcParams
np.seterr(all="ignore")

KINDS = ("sync", "gfm")
TITLES = {"sync": "all-synchronous-machine 39-bus",
          "gfm": "all-GFM 39-bus"}
TICKS = {"sync": 50.0, "gfm": 100.0}

# (stem, {kind: (fault duration s, EMT run tag, post-clear window s)})
CASES = [
    ("energy_surface_below_cct",
     {"sync": (0.237, "T0p237", 2.5),
      "gfm": (1.6, "T1p6", 8.0)}),
    ("energy_surface_at_cct",
     {"sync": (0.2455, "T0p2455", 8.0),
      "gfm": (2.315, "T2p315", 8.0)}),
]


# --------------------------------------------------------------- data
def compute():
    """Surfaces + analytical paths + EMT paths for both cases.

    Order (sync surface, then GFM surface, in one process) is the order
    of the meeting script, so the cached arrays reproduce the meeting
    rasters exactly.
    """
    t0 = time.time()
    out = {}
    surf = {}
    for kind in KINDS:
        T.log("surface: %s ..." % kind)
        surf[kind] = T.compute_surface(kind)
        sys_, netP, netF, U, failm, mask, grid = surf[kind]
        out["%s_U" % kind] = U
        out["%s_failm" % kind] = failm
        out["%s_mask" % kind] = mask
        out["%s_grid" % kind] = grid
    for stem, spec in CASES:
        for kind in KINDS:
            dur, tag, t_post = spec[kind]
            T.log("paths: %s / %s ..." % (stem, kind))
            sys_, netP, netF, U, failm, mask, grid = surf[kind]
            (f31, f32), (p31, p32) = T.model_path(
                sys_, netF, netP, dur, t_post)
            e31, e32 = (T.emt_path_sync(tag) if kind == "sync"
                        else T.emt_path_gfm(tag))
            # FINAL analytical position.  The classical machine model is
            # undamped (D = 0): below its CCT it rings forever, so its
            # last sample is a random phase point on the orbit -- take
            # the orbit centre (post-clear time average).  The damped
            # GFM genuinely settles, so its last point is the answer.
            if kind == "sync":
                m31, m32 = float(np.mean(p31)), float(np.mean(p32))
            else:
                m31, m32 = float(p31[-1]), float(p32[-1])
            k = "%s_%s" % (stem, kind)
            for name, arr in (("f31", f31), ("f32", f32),
                              ("p31", p31), ("p32", p32),
                              ("e31", e31), ("e32", e32),
                              ("m", np.array([m31, m32]))):
                out["%s_%s" % (k, name)] = np.asarray(arr)
    np.savez_compressed(CACHE, **out)
    T.log("cached -> %s  (%.0f s)" % (CACHE, time.time() - t0))
    return out


def load(recompute=False):
    if CACHE.exists() and not recompute:
        T.log("using cache %s" % CACHE)
        return dict(np.load(CACHE))
    return compute()


# --------------------------------------------------------------- draw
def arrows(ax, x, y, color, fracs, z=8):
    """Direction arrowheads along a path, sized for the 6.5 in print."""
    x, y = np.asarray(x), np.asarray(y)
    for f in fracs:
        i = int(f * (len(x) - 1))
        j = min(i + max(1, len(x) // 100), len(x) - 1)
        if abs(x[j] - x[i]) + abs(y[j] - y[i]) < 1e-6:
            continue
        ax.annotate("", xy=(x[j], y[j]), xytext=(x[i], y[i]),
                    arrowprops=dict(arrowstyle="-|>", color=color,
                                    lw=0.9, mutation_scale=9),
                    zorder=z)


def draw_panel(ax, D, kind, stem, vlo, vhi):
    grid = D["%s_grid" % kind]
    GX, GY = np.meshgrid(grid, grid)
    Ushow = np.where(D["%s_failm" % kind], np.nan,
                     np.clip(D["%s_U" % kind], vlo, vhi))
    mask = D["%s_mask" % kind]
    cs = ax.contourf(GX, GY, Ushow, levels=30, cmap="viridis")
    ax.contour(GX, GY, Ushow, levels=15, colors="k", linewidths=0.18,
               alpha=0.4)
    ax.contourf(GX, GY, mask, levels=[0.5, 1.5], colors=["w"],
                alpha=0.14)
    ax.contour(GX, GY, mask, levels=[0.5], colors="w", linewidths=1.3)

    k = "%s_%s" % (stem, kind)
    f31, f32 = D["%s_f31" % k], D["%s_f32" % k]
    p31, p32 = D["%s_p31" % k], D["%s_p32" % k]
    e31, e32 = D["%s_e31" % k], D["%s_e32" % k]
    m31, m32 = D["%s_m" % k]

    ax.plot(f31, f32, color="w", ls=":", lw=1.3)
    ax.plot(p31, p32, color="w", lw=0.8, alpha=0.95)
    arrows(ax, f31, f32, "w", (0.55,))
    arrows(ax, p31, p32, "w", (0.25,))
    ax.plot(f31[-1], f32[-1], marker="o", ms=4.6, color="w", mec="k",
            mew=0.7, zorder=9)
    ax.plot(np.clip(m31, grid[0], grid[-1]),
            np.clip(m32, grid[0], grid[-1]), marker="s", ms=6.0,
            color="w", mec="k", mew=0.9, zorder=10)
    ax.plot(e31, e32, color="cyan", ls="--", lw=1.15, zorder=6)
    arrows(ax, e31, e32, "cyan", (0.2, 0.55))
    ax.plot(np.clip(e31[-1], grid[0], grid[-1]),
            np.clip(e32[-1], grid[0], grid[-1]), marker="X", ms=7.5,
            color="cyan", mec="k", mew=0.7, zorder=10)
    ax.plot(0, 0, "o", ms=5.6, mfc="none", mec="w", mew=1.3, zorder=9)

    ax.set_xlabel(r"$\gamma_{31}$ (deg)", labelpad=1.5)
    ax.set_title(TITLES[kind], pad=3.5)
    ax.set_xlim(grid[0], grid[-1])
    ax.set_ylim(grid[0], grid[-1])
    ax.xaxis.set_major_locator(MultipleLocator(TICKS[kind]))
    ax.yaxis.set_major_locator(MultipleLocator(TICKS[kind]))
    ax.tick_params(length=2.4, width=0.6, pad=1.8)
    for sp in ax.spines.values():
        sp.set_linewidth(0.7)
    return cs


LEGEND = [
    ("analytical: basin border",
     dict(color="w", lw=1.3)),
    ("analytical: fault-on",
     dict(color="w", ls=":", lw=1.3)),
    ("analytical: after clearing",
     dict(color="w", lw=0.9)),
    ("analytical: at clearing",
     dict(color="w", marker="o", ls="none", ms=4.6, mec="k", mew=0.7)),
    ("analytical: final position",
     dict(color="w", marker="s", ls="none", ms=6.0, mec="k", mew=0.9)),
    ("start",
     dict(color="w", marker="o", ls="none", ms=5.6, mfc="none",
          mew=1.3)),
    ("PSCAD (EMT)",
     dict(color="cyan", ls="--", lw=1.15)),
    ("PSCAD: final position",
     dict(color="cyan", marker="X", ls="none", ms=7.5, mec="k",
          mew=0.7)),
]


def make_figure(D, stem, vlo, vhi):
    fig, axes = plt.subplots(
        1, 2, figsize=(st.TEXTWIDTH_IN, 3.2), layout="none",
        gridspec_kw=dict(left=0.077, right=0.855, top=0.930,
                         bottom=0.355, wspace=0.215))
    sets = {}
    for ax, kind in zip(axes, KINDS):
        sets[kind] = draw_panel(ax, D, kind, stem, vlo, vhi)
    axes[0].set_ylabel(r"$\gamma_{32}$ (deg)", labelpad=1.5)

    # NOTE (matches the meeting original): contourf(levels=30) picks its
    # 30 levels over each panel's OWN clipped range, so the two panels do
    # not share a mapping -- the sync surface spans about [-35.7, 4.8] pu
    # and the GFM surface about [-71.6, 16.2] pu.  The bar is keyed to the
    # LEFT (sync) panel, as in the meeting figure this reproduces.
    box = axes[1].get_position()
    cax = fig.add_axes([0.878, box.y0, 0.021, box.height])
    cb = fig.colorbar(sets["sync"], cax=cax)
    cb.set_label("potential energy $U$ (pu)",
                 size=matplotlib.rcParams["ytick.labelsize"],
                 labelpad=2.0)
    cb.outline.set_linewidth(0.7)
    cax.tick_params(length=2.4, width=0.6, pad=1.8)

    handles = [Line2D([], [], label=lab, **kw) for lab, kw in LEGEND]
    leg = fig.legend(handles=handles, ncol=3, loc="lower center",
                     bbox_to_anchor=(0.5, 0.004), handlelength=1.7,
                     handletextpad=0.5, columnspacing=1.1,
                     labelspacing=0.30, borderpad=0.45,
                     borderaxespad=0.0)
    leg.get_frame().set_facecolor("#8f9a9e")
    leg.get_frame().set_edgecolor("0.45")
    leg.get_frame().set_linewidth(0.7)

    fig.canvas.draw()
    w = leg.get_window_extent().width / fig.dpi
    T.log("  legend width %.2f in of %.2f in" % (w, st.TEXTWIDTH_IN))
    fig.savefig(OUT / (stem + ".png"), dpi=600)
    plt.close(fig)
    T.log("wrote %s" % (OUT / (stem + ".png")))


def main():
    D = load("--recompute" in sys.argv)
    vals = [np.where(D["%s_failm" % k], np.nan, D["%s_U" % k])
            for k in KINDS]
    vhi = max(np.nanpercentile(v, 98) for v in vals)
    vlo = min(np.nanpercentile(v, 2) for v in vals)
    for stem, _ in CASES:
        make_figure(D, stem, vlo, vhi)


if __name__ == "__main__":
    main()
