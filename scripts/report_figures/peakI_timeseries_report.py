"""Time-domain complement to fig:peaki (narr_peakI_pair): the ten
REGFM_A1 control-current magnitudes |I| (native pu on each unit's own
Mbase, the base the limiter acts on) through the same bus-10 bolted
three-phase fault (t = 3.0 s, 5 cycles, no reclose), showing that the
sub-cycle 1.70 pu excursion at bus 32 and the 1.49 pu touch at bus 31
are the only visits to the I_maxF = 1.5 pu dial, and that every unit
sits well under it for the remaining 27 s.

Bus 32's trace falls to zero after the fault. That is NOT a trip
(REGFM_A1 has no protection logic): bus 10 is GFM-32's only network
tie through its GSU, and clearing the fault opens both lines at bus 10
with reclose disabled, so the unit is islanded on a dead bus (stated in
the run's setup.json: "expect collapse/island, not ride-through"). The
fault-location sweep marched the fault toward the inverter to drive
its current into the limit; this is the endpoint of that march.

Two panels: (left) 2.9-4.0 s zoom around the fault, (right) the full
0-30 s record; dashed line at the 1.5 pu dial in both. Near-fault units
(31, 32) drawn in the report's GFM red / a dark accent, the other eight
in muted grey so the two that matter read at a glance.

Data: fault_loc_sweep_gfm32_Ilim1p5/runs/
      3PG_at_bus10_w_10GFM_Vsched_Ilim1p5_t3p0s_5cyc_norecl_30s
      channels PGB(166..220 step 6) = I_pu39, I_pu31, I_pu38, I_pu37,
      I_pu36, I_pu35, I_pu30, I_pu34, I_pu33, I_pu (bus 32), read from
      the raw .out chunks (the stitched CSV's bus-32 channel is
      truncated after the fault window). Chunk k = channels 10(k-1)+1
      .. 10k, column 0 = time.
Sized 6.5 in x 2.7 in for width=\\textwidth, TeX Gyre Pagella 11 pt.
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator

RUN = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
           r"\sharp-jackson-1e89b8\experiments\fault_loc_sweep_gfm32_Ilim1p5"
           r"\runs\3PG_at_bus10_w_10GFM_Vsched_Ilim1p5_t3p0s_5cyc_norecl_30s")
OUT = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
           r"\upbeat-jones-67c8d3\report_26X\overleaf\figures")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import figstyle_26x as st                       # noqa: E402

st.apply()
GFM_RED, ACCENT, GREY, INK = "#d62728", "#7b3294", "#9a9a9a", "#222222"
IMAXF = 1.5

CH = {39: 166, 31: 172, 38: 178, 37: 184, 36: 190, 35: 196,
      30: 202, 34: 208, 33: 214, 32: 220}


def load():
    cache = {}
    def chunk(k):
        if k not in cache:
            cache[k] = np.loadtxt(RUN / ("IEEE39_acLine1_%02d.out" % k),
                                  skiprows=1)
        return cache[k]
    t = None
    traces = {}
    for bus, pgb in CH.items():
        k, col = (pgb - 1) // 10 + 1, (pgb - 1) % 10 + 1
        arr = chunk(k)
        if t is None:
            t = arr[:, 0]
        traces[bus] = arr[:len(t), col]
    return t, traces


def main():
    t, tr = load()
    fig, (axz, axf) = plt.subplots(
        1, 2, figsize=(st.TEXTWIDTH_IN, 2.7),
        gridspec_kw={"width_ratios": [1.0, 1.35]})
    order = [b for b in tr if b not in (31, 32)] + [31, 32]
    style = {31: dict(color=ACCENT, lw=1.3, zorder=4),
             32: dict(color=GFM_RED, lw=1.3, zorder=5)}
    for ax, (t0, t1) in ((axz, (2.9, 4.0)), (axf, (0.0, 30.0))):
        m = (t >= t0) & (t <= t1)
        for b in order:
            kw = style.get(b, dict(color=GREY, lw=0.8, zorder=2))
            ax.plot(t[m], tr[b][m], **kw)
        ax.axhline(IMAXF, color=INK, lw=1.0, ls="--", zorder=6)
        ax.set_xlim(t0, t1)
        ax.set_ylim(0, 1.85)
        ax.set_xlabel("Time (s)")
        ax.grid(True, alpha=0.3)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
    axz.set_ylabel(r"$|I|$ (pu of unit rating)")
    axz.set_xticks([3.0, 3.5, 4.0])
    axf.set_xticks([0, 10, 20, 30])
    axf.tick_params(labelleft=False)
    axz.text(3.995, IMAXF + 0.04, r"$I_{\max F}=1.5$ pu", ha="right",
             va="bottom", fontsize=9)
    axf.legend(handles=[
        Line2D([], [], color=GFM_RED, lw=1.3, label="bus 32 (GSU on the faulted bus)"),
        Line2D([], [], color=ACCENT, lw=1.3, label="bus 31"),
        Line2D([], [], color=GREY, lw=0.8, label="other eight units")],
        loc="upper right", frameon=True, fontsize=9)
    dst = OUT / "narr_peakI_timeseries.png"
    fig.savefig(dst, dpi=600)
    plt.close(fig)
    pk32 = tr[32][(t > 2.95) & (t < 4.0)].max()
    late = max(tr[b][t > 4.0].max() for b in tr)
    print("wrote", dst.name, "| bus32 peak %.2f | fleet max after 4 s %.2f"
          % (pk32, late))


if __name__ == "__main__":
    main()
