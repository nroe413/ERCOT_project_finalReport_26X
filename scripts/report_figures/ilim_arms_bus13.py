"""Report figure fig:ilimarms13 (narr_ilim_arms_bus13.png): the bus-13 3PG fault on the all-GFM
fleet at five transient current limits, ImaxF = 15 (no practical limit), 2.0, 1.5, 1.2 and 1.1 pu
(a sixth run at 1.0 pu, which does not recover, is drawn in panel (e) only).
Panel (e) shows the 230 kV voltage of unit 32 over the whole record.
(a) per-unit peak of the inverter's internal current magnitude (I_pu, pu on each unit's base) with
the three limit lines; (b) I_pu of unit 32 through the fault for the four arms; (c) the first two and
a half cycles after fault inception, where the limits take hold.

Data: experiment fault_3PG_bus13_10GFM_ilim_arms (10 s records; the 1.5 arm is the bus-13 run of
fault_loc_sweep_gfm32_Ilim1p5).  The first run from the study writes the extracts
data/report_figure_data/ilim_arms_bus13/<arm>.csv (TIME, the ten I_pu channels and B32Irms over 2.9-4.0 s); later
runs, and the public-repository copy of this script, read the extracts.  Same style contract as the
bus-14 figure (experiments/fault_3PG_bus14_10GFM_Vsched_Ilim1p2/make_ilim_arms_report_fig.py).
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
        "I1p2": "fault_3PG_bus13_10GFM_ilim_arms/runs/3PG_at_bus13_w_10GFM_Vsched_I1p2_t3p0s_5cyc_norecl_10s",
        "I1p1": "fault_3PG_bus13_10GFM_ilim_arms/runs/3PG_at_bus13_w_10GFM_Vsched_I1p1_t3p0s_5cyc_norecl_10s",
        "I1p0": "fault_3PG_bus13_10GFM_ilim_arms/runs/3PG_at_bus13_w_10GFM_Vsched_I1p0_t3p0s_5cyc_norecl_10s"}
# (arm, limit, legend label, colour); the three limited arms keep the colours of the bus-14 figure
ARMS = [("Iunl", None, r"$I_{\max F}=15$ pu", "#1f2f5c"),
        ("I2p0", 2.0, r"$I_{\max F}=2.0$ pu", "#7f7f7f"),
        ("I1p5", 1.5, r"$I_{\max F}=1.5$ pu", "#e08a1e"),
        ("I1p2", 1.2, r"$I_{\max F}=1.2$ pu", "#c0392b"),
        ("I1p1", 1.1, r"$I_{\max F}=1.1$ pu", "#6a3d9a")]
# a sixth run, ImaxF = 1.0 pu, does not recover; it appears in panel (e) only
EXTRA_E = ("I1p0", r"$I_{\max F}=1.0$ pu: no recovery", "#111111")
GEN = list(range(30, 40))
BMAX = 32
MBASE32_MVA = 1083.0                                  # REGFM_A1 Mbase_PNNL of the bus-32 unit
IBASE32_KA = MBASE32_MVA / (3 ** 0.5 * 230.0)          # 2.72 kA at 230 kV
T0 = 3.0
PEAK = (2.95, 4.0)
TRACE = (2.9, 3.6)
ZOOM_MS = (-2.0, 42.0)          # panel (c): time after fault inception
CYCLE_MS = 1000.0 / 60.0
EXTRACT = (2.9, 4.0)


def ipu(b):
    return "I_pu" if b == 32 else "I_pu%d" % b


def load(arm):
    ext = SRC / ("%s.csv" % arm)
    if ext.exists():
        return pd.read_csv(ext)
    d = rp.experiment(RUNS[arm])
    csv = sorted(d.glob("data_*.csv"), key=lambda p: p.stat().st_mtime)[-1]
    need = ["TIME", "B32Irms"] + [ipu(b) for b in GEN]
    df = pd.read_csv(csv, usecols=lambda c: c in need)
    t = df["TIME"].values
    df = df[(t >= EXTRACT[0]) & (t <= EXTRACT[1])].reset_index(drop=True)
    SRC.mkdir(parents=True, exist_ok=True)
    df.to_csv(ext, index=False, float_format="%.6g")
    return df


def load_v(arm):
    ext = SRC / ("%s_v.csv" % arm)
    if ext.exists():
        return pd.read_csv(ext)
    d = RUNS[arm] if isinstance(RUNS[arm], Path) else rp.experiment(RUNS[arm])
    csv = sorted(d.glob("data_*.csv"), key=lambda p: p.stat().st_mtime)[-1]
    df = pd.read_csv(csv, usecols=["TIME", "B32Vrms"])
    df = df[df.TIME >= 2.5].iloc[::25].reset_index(drop=True)
    df.to_csv(ext, index=False, float_format="%.6g")
    print("extract written:", ext, "from", csv.name)
    return df


def main():
    data = [(arm, lim, lab, col, load(arm)) for arm, lim, lab, col in ARMS]
    peaks = {}
    for arm, lim, lab, col, df in data:
        t = df["TIME"].values
        m = (t >= PEAK[0]) & (t <= PEAK[1])
        peaks[arm] = [float(np.abs(df[ipu(b)].values[m]).max()) for b in GEN]
    top = max(max(v) for v in peaks.values())

    plt.rcParams["figure.constrained_layout.use"] = False   # manual grid below
    fig = plt.figure(figsize=(st.TEXTWIDTH_IN, 7.4))
    gs = fig.add_gridspec(3, 2, width_ratios=[1.35, 1.0], height_ratios=[1.0, 0.9, 0.75],
                          left=0.09, right=0.972, top=0.965, bottom=0.06, hspace=0.55, wspace=0.28)
    ax = fig.add_subplot(gs[0, 0])
    at = fig.add_subplot(gs[0, 1])
    az = fig.add_subplot(gs[1, :])
    ad = fig.add_subplot(gs[2, 0])
    ae = fig.add_subplot(gs[2, 1])

    # (a) per-unit peaks
    x = np.arange(len(GEN))
    w = 0.8 / len(data)
    for k, (arm, lim, lab, col, _) in enumerate(data):
        ax.bar(x + (k - (len(data) - 1) / 2.0) * w, peaks[arm], w, color=col, zorder=3, label=lab)
        if lim is not None:
            ax.axhline(lim, color=col, ls="--", lw=0.9, zorder=2)
    ax.set_xticks(x)
    ax.set_xticklabels([str(b) for b in GEN], fontsize=8)
    ax.set_xlabel("unit bus")
    ax.set_ylabel(r"peak $|I|$ (pu on unit base)")
    ax.set_ylim(0, np.ceil((top + 0.45) * 2) / 2)
    ax.grid(True, axis="y", alpha=0.3, zorder=0)
    ax.set_title("(a) peak current of each unit", fontsize=8.5, loc="left")

    # (b) unit 32 through the fault
    for arm, lim, lab, col, df in data:
        t = df["TIME"].values
        m = (t >= TRACE[0]) & (t <= TRACE[1])
        at.plot(t[m], np.abs(df[ipu(BMAX)].values[m]), color=col, lw=1.0, label=lab)
    at.axvspan(3.0, 3.0833, color="#fbd0c4", alpha=0.6, zorder=0)
    at.set_xlim(*TRACE)
    at.set_xlabel("time (s)")
    at.set_ylabel(r"$|I|$, unit %d (pu)" % BMAX)
    at.grid(True, alpha=0.3)
    at.set_title("(b) unit 32 through the fault", fontsize=8.5, loc="left")
    at.legend(loc="upper right", fontsize=7.0, framealpha=0.92, handlelength=1.4)

    # (c) the first cycles after inception: reaction time of the limiter for each setpoint
    w_cyc = None
    for arm, lim, lab, col, df in data:
        tm_all = (df["TIME"].values - T0) * 1e3
        x_all = np.abs(df[ipu(BMAX)].values)
        if w_cyc is None:
            w_cyc = int(round(CYCLE_MS / (tm_all[1] - tm_all[0])))
        m = (tm_all >= ZOOM_MS[0]) & (tm_all <= ZOOM_MS[1])
        text = lab
        if lim is not None:
            az.axhline(lim, color=col, ls="--", lw=0.9, zorder=2)
            win = (tm_all >= 0) & (tm_all <= 100.0)
            above = np.where(win & (x_all > lim))[0]
            if len(above) == 0:
                text = lab + ": limit not reached"
            else:
                first = tm_all[above[0]]
                ipk = np.where(win)[0][int(np.argmax(x_all[win]))]
                back = None
                for i in range(ipk, len(x_all) - w_cyc):
                    if np.all(x_all[i:i + w_cyc] <= 1.02 * lim):
                        back = tm_all[i]
                        break
                cyc = back / CYCLE_MS
                text = lab + ": above from %.1f ms, back at %.1f ms (%.2f cycle%s)" % (
                    first, back, cyc, "" if cyc <= 1 else "s")
                az.plot([first], [lim], "o", ms=4.5, mfc="white", mec=col, mew=1.2, zorder=6)
                az.plot([back], [x_all[np.argmin(np.abs(tm_all - back))]], "o", ms=4.5, color=col, zorder=6)
                print("  reaction %s: first above %.1f ms, back at limit %.1f ms (%.2f cycles)" % (arm, first, back, cyc))
        az.plot(tm_all[m], x_all[m], color=col, lw=1.2, label=text)
    for k in (1, 2):
        az.axvline(k * CYCLE_MS, color="0.55", lw=0.8, ls=":")
        az.text(k * CYCLE_MS + 0.4, 1.76, "%d cycle%s" % (k, "" if k == 1 else "s"), fontsize=7.5,
                color="0.35", ha="left", va="bottom")
    az.axvline(0.0, color="k", lw=0.8)
    az.set_xlim(*ZOOM_MS)
    az.set_ylim(0.0, 1.95)
    az.set_xlabel("time after fault inception (ms)")
    az.set_ylabel(r"$|I|$, unit %d (pu)" % BMAX)
    az.grid(True, alpha=0.3)
    az.set_title("(c) current limiter reaction time for various setpoints", fontsize=8.5, loc="left")
    az.legend(loc="lower center", fontsize=6.6, framealpha=0.92, handlelength=1.4, ncol=2, columnspacing=1.2)

    # (d) RMS current of unit 32 on the 230 kV side of its step-up transformer, per unit of the unit rating
    for arm, lim, lab, col, df in data:
        t = df["TIME"].values
        m = (t >= TRACE[0]) & (t <= TRACE[1])
        ad.plot(t[m], df["B32Irms"].values[m] / IBASE32_KA, color=col, lw=1.1, label=lab)
    ad.axvspan(3.0, 3.0833, color="#fbd0c4", alpha=0.6, zorder=0)
    ad.set_xlim(*TRACE)
    ad.set_xlabel("time (s)")
    ad.set_ylabel("RMS current, unit %d (pu)" % BMAX)
    ad.grid(True, alpha=0.3)
    ad.set_title("(d) unit 32 RMS current, 230 kV side (pu of 1083 MVA)", fontsize=8.5, loc="left")

    # (e) the whole record: voltage of unit 32 on the 230 kV side
    for arm, lim, lab, col, _ in data:
        dv = load_v(arm)
        ae.plot(dv["TIME"].values, dv["B32Vrms"].values / 230.0, color=col, lw=1.0, label=lab)
    dv = load_v(EXTRA_E[0])
    ae.plot(dv["TIME"].values, dv["B32Vrms"].values / 230.0, color=EXTRA_E[2], lw=1.0, ls="--", label=EXTRA_E[1])
    hh, ll = ae.get_legend_handles_labels()
    ae.legend(hh[-1:], ll[-1:], loc="lower right", fontsize=6.6, framealpha=0.92, handlelength=1.6)
    ae.axvspan(3.0, 3.0833, color="#fbd0c4", alpha=0.6, zorder=0)
    ae.set_xlim(2.5, 10.0)
    ae.set_ylim(0.0, 1.15)
    ae.set_xlabel("time (s)")
    ae.set_ylabel("voltage, unit %d (pu)" % BMAX)
    ae.grid(True, alpha=0.3)
    ae.set_title("(e) unit 32 voltage, 230 kV side", fontsize=8.5, loc="left")

    out = OUT / "narr_ilim_arms_bus13.png"
    fig.savefig(out, dpi=600)
    print("wrote", out)
    for arm, lim, lab, col, _ in data:
        pk = peaks[arm]
        print("  %-5s limit %s: unit-32 peak %.3f, max peak %.3f (bus %d), units within 0.02 of limit: %s"
              % (arm, lim, pk[GEN.index(32)], max(pk), GEN[int(np.argmax(pk))],
                 sum(p > lim - 0.02 for p in pk) if lim else "-"))


if __name__ == "__main__":
    main()
