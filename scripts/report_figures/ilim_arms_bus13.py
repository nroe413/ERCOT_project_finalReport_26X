"""Report figure narr_ilim_arms_bus13.png: the bus-13 3PG fault on the all-GFM fleet at four
transient current limits, ImaxF = 15 (no practical limit), 2.0, 1.5 and 1.2 pu.
Left: per-unit peak of the inverter's internal current magnitude (I_pu, pu on each unit's base)
with the three limit lines.  Right: I_pu of unit 32 through the fault for the four arms.

Runs from the shipped extracts data/report_figure_data/ilim_arms_bus13/<arm>.csv (TIME and the
ten I_pu channels over 2.9-4.0 s of each 10 s record).  With ERCOT_EXPERIMENTS set, missing
extracts are rebuilt from the full records (see DATA.md).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_paths as rp  # noqa: E402

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import figstyle_26x as st  # noqa: E402
st.apply()
import matplotlib.pyplot as plt  # noqa: E402

OUT = rp.OUT
SRC = rp.DATA / "ilim_arms_bus13"
RUNS = {"Iunl": "fault_3PG_bus13_10GFM_ilim_arms/runs/3PG_at_bus13_w_10GFM_Vsched_Iunl_t3p0s_5cyc_norecl_10s",
        "I2p0": "fault_3PG_bus13_10GFM_ilim_arms/runs/3PG_at_bus13_w_10GFM_Vsched_I2p0_t3p0s_5cyc_norecl_10s",
        "I1p5": "fault_loc_sweep_gfm32_Ilim1p5/runs/3PG_at_bus13_w_10GFM_Vsched_Ilim1p5_t3p0s_5cyc_norecl_10s",
        "I1p2": "fault_3PG_bus13_10GFM_ilim_arms/runs/3PG_at_bus13_w_10GFM_Vsched_I1p2_t3p0s_5cyc_norecl_10s"}
ARMS = [("Iunl", None, r"no practical limit ($I_{\max F}=15$ pu)", "#1f2f5c"),
        ("I2p0", 2.0, r"$I_{\max F}=2.0$ pu", "#7f7f7f"),
        ("I1p5", 1.5, r"$I_{\max F}=1.5$ pu", "#e08a1e"),
        ("I1p2", 1.2, r"$I_{\max F}=1.2$ pu", "#c0392b")]
GEN = list(range(30, 40))
BMAX = 32
PEAK = (2.95, 4.0)
TRACE = (2.9, 3.6)
EXTRACT = (2.9, 4.0)


def ipu(b):
    return "I_pu" if b == 32 else "I_pu%d" % b


def load(arm):
    ext = SRC / ("%s.csv" % arm)
    if ext.exists():
        return pd.read_csv(ext)
    d = rp.experiment(RUNS[arm])
    csv = sorted(d.glob("data_*.csv"), key=lambda p: p.stat().st_mtime)[-1]
    need = ["TIME"] + [ipu(b) for b in GEN]
    df = pd.read_csv(csv, usecols=lambda c: c in need)
    t = df["TIME"].values
    df = df[(t >= EXTRACT[0]) & (t <= EXTRACT[1])].reset_index(drop=True)
    SRC.mkdir(parents=True, exist_ok=True)
    df.to_csv(ext, index=False, float_format="%.6g")
    return df


def main():
    data = [(arm, lim, lab, col, load(arm)) for arm, lim, lab, col in ARMS]
    peaks = {}
    for arm, lim, lab, col, df in data:
        t = df["TIME"].values
        m = (t >= PEAK[0]) & (t <= PEAK[1])
        peaks[arm] = [float(np.abs(df[ipu(b)].values[m]).max()) for b in GEN]
    top = max(max(v) for v in peaks.values())

    fig, (ax, at) = plt.subplots(1, 2, figsize=(st.TEXTWIDTH_IN, 3.0),
                                 gridspec_kw=dict(width_ratios=[1.35, 1.0]))
    x = np.arange(len(GEN))
    w = 0.2
    for k, (arm, lim, lab, col, _) in enumerate(data):
        ax.bar(x + (k - 1.5) * w, peaks[arm], w, color=col, zorder=3, label=lab)
        if lim is not None:
            ax.axhline(lim, color=col, ls="--", lw=0.9, zorder=2)
    ax.set_xticks(x)
    ax.set_xticklabels([str(b) for b in GEN], fontsize=8)
    ax.set_xlabel("unit bus")
    ax.set_ylabel(r"peak $|I|$ (pu on unit base)")
    ax.set_ylim(0, np.ceil((top + 0.45) * 2) / 2)
    ax.grid(True, axis="y", alpha=0.3, zorder=0)
    ax.legend(loc="upper right", fontsize=7.2, ncol=2, framealpha=0.9,
              handlelength=1.2, columnspacing=0.8)

    for arm, lim, lab, col, df in data:
        t = df["TIME"].values
        m = (t >= TRACE[0]) & (t <= TRACE[1])
        at.plot(t[m], np.abs(df[ipu(BMAX)].values[m]), color=col, lw=1.0, label=lab)
    at.axvspan(3.0, 3.0833, color="#fbd0c4", alpha=0.6, zorder=0)
    at.set_xlim(*TRACE)
    at.set_xlabel("time (s)")
    at.set_ylabel(r"$|I|$, unit %d (pu)" % BMAX)
    at.grid(True, alpha=0.3)
    at.legend(loc="upper right", fontsize=7.2, framealpha=0.9)

    out = OUT / "narr_ilim_arms_bus13.png"
    fig.savefig(out, dpi=600)
    print("wrote", out)


if __name__ == "__main__":
    main()
