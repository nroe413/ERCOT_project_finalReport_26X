"""Report-format regeneration of narr_peakI_pair.png (report fig:peaki).

1x2 bar-chart pair, peak fault current per unit for the bus-10 3PG
fault (t=3.0 s, 5 cycles, no reclose, 30 s):
  left  - all-GFM system (REGFM_A1, ImaxF=1.5): peak of each inverter's
          native control current |I_pu| over 2.95-4.0 s, pu on its own
          Mbase_PNNL (the base the limiter acts on);
  right - all-synchronous system: peak of each machine's terminal RMS
          current B<N>Irms over the same window, pu on its own .RAW
          nameplate MVA (machines are UNLIMITED).

Data loading and the peak/pre-fault computation are IMPORTED verbatim
from the original deck generator (make_bus10_sync_deck.py: load_gens,
peak_current_pu, ibase, PEAK_WIN=(2.95,4.0), PRE_WIN=(2.5,2.95)), so
the base conversions are identical to the meeting figure. Runs:
  sync: fault_3PG_bus10_sync_vs_GFM/runs/
        3PG_at_bus10_sync_machines_t3p0s_5cyc_norecl_30s
  GFM : fault_loc_sweep_gfm32_Ilim1p5/runs/
        3PG_at_bus10_w_10GFM_Vsched_Ilim1p5_t3p0s_5cyc_norecl_30s
Sized 6.5 in x 2.6 in for width=\\textwidth, TeX Gyre Pagella 11 pt.
"""
import sys
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_paths as rp  # noqa: E402

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

DECK_DIR = rp.experiment(r"fault_3PG_bus10_sync_vs_GFM")
OUT = rp.OUT
sys.path.insert(0, str(DECK_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import make_bus10_sync_deck as deck                    # noqa: E402
import figstyle_26x as st                              # noqa: E402

st.apply()   # AFTER the deck import: the deck module sets its own rcParams

GFM_RED, SYNC_BLUE = "#d62728", "#4575b4"


def peaks(df, mbase, is_gfm):
    pk, pr = [], []
    for b in deck.GENS:
        p, q = deck.peak_current_pu(df, b, mbase, is_gfm)
        pk.append(p)
        pr.append(q)
    return np.array(pk), np.array(pr)


def main():
    s = deck.load_gens(deck.SYNC_RUN, "sync")
    g = deck.load_gens(deck.GFM_RUN, "GFM", with_ipu=True)
    if s is None or g is None:
        raise SystemExit("run data missing - refusing to draw")
    pk_g, pre_g = peaks(g, deck.MBASE_GFM, True)
    pk_s, pre_s = peaks(s, deck.MBASE_SYNC, False)

    x = np.arange(len(deck.GENS))
    fig, (ag, asy) = plt.subplots(1, 2, figsize=(st.TEXTWIDTH_IN, 2.6),
                                  sharey=True)
    # small ylim headroom bump (4.0 -> 4.3) so the peak-value label above
    # the tallest sync bar sits inside the frame, clear of the top spine
    ymax = 4.3

    for ax, pk, pre, color in ((ag, pk_g, pre_g, GFM_RED),
                               (asy, pk_s, pre_s, SYNC_BLUE)):
        ax.bar(x, pk, 0.62, color=color, zorder=3)
        for i in range(len(x)):
            ax.hlines(pre[i], x[i] - 0.31, x[i] + 0.31, color="black",
                      lw=1.1, zorder=5)
        ax.set_xticks(x)
        ax.set_xticklabels(["%d" % b for b in deck.GENS])
        ax.set_xlabel("generator")
        ax.set_ylim(0, ymax)
        ax.grid(True, axis="y", alpha=0.3)
        imax = int(np.nanargmax(pk))
        ax.text(x[imax], pk[imax] + 0.08, "%.2f" % pk[imax],
                ha="center", va="bottom", fontsize=9)

    ag.axhline(deck.IMAXF, color="black", ls="--", lw=1.2, zorder=4)
    ag.set_ylabel("peak current (pu of own base)")
    ag.set_title("grid-forming ($I_{\\max F} = %.1f$ pu)" % deck.IMAXF)
    asy.set_title("synchronous (no current limit)")
    ag.legend(handles=[
        Line2D([], [], color="black", ls="--", lw=1.2,
               label="$I_{\\max F} = %.1f$ pu" % deck.IMAXF),
        Line2D([], [], color="black", lw=1.1, label="pre-fault level")],
        loc="upper right", fontsize=8, framealpha=0.9)

    fig.savefig(OUT / "narr_peakI_pair.png", dpi=600)
    print("wrote", OUT / "narr_peakI_pair.png")
    for lbl, pk in (("GFM ", pk_g), ("sync", pk_s)):
        print("  %s peaks: %s" % (lbl, "  ".join("%.3f" % v for v in pk)))


if __name__ == "__main__":
    main()
