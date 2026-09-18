"""log_decrement_bandpass.py -- logarithmic decrement of the single-machine ring-down after a band-pass
filter (author request, 2026-09-18): a low-pass edge removes the 60 Hz meter ripple, a high-pass edge removes
the exciter's slow recovery, and the peaks of what is left (the electromechanical swing) are evaluated as in
https://en.wikipedia.org/wiki/Logarithmic_decrement:

    delta = (1/n) ln(a_0 / a_n),   zeta = delta / sqrt(4 pi^2 + delta^2),   sigma = delta f_d,   D = 4 H sigma

Filter: zero-phase Butterworth band-pass (second order each way, forward and backward), 0.5 to 5 Hz, so peak
times are not shifted; the swing is at 1.5 Hz.  A linear filter leaves the decay rate of a mode unchanged; its own
start-up transient (from the fault step) decays at about 2 1/s for a 0.5 Hz edge, so peaks are evaluated from
0.6 s after clearing and the result was cross-checked against an unfiltered peak-to-trough decrement (5 swings of
active power: delta 1.24, D = 42 per unit; results in log_decrement.csv).  Maxima and minima are evaluated separately.

Record: systems/smib_siib/runs/3PG_5cyc_SCR10_10s/SMIB_1SYNC_3PG_PSD.csv (bolted three-phase fault at
the point of interconnection, 5 cycles, network intact, infinite bus at SCR 10; GENROU H = 5.46 s, 0.50 pu).
Writes data/report_figure_data/log_decrement/log_decrement_bandpass_<band>.csv and .png.

Usage:  python log_decrement_bandpass.py [f_lo f_hi]
"""
import csv
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import butter, sosfiltfilt, find_peaks
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
REC = ROOT / "systems" / "smib_siib" / "runs" / "3PG_5cyc_SCR10_10s" / "SMIB_1SYNC_3PG_PSD.csv"
OUTDIR = ROOT / "data" / "report_figure_data" / "log_decrement"
H = 5.46
T_CLEAR = 3.0 + 0.0833
T_FROM = T_CLEAR + 0.6
F_LO, F_HI = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) > 2 else (0.5, 5.0)
SIGS = [("P2grid", "active power P"), ("Wpu", "rotor speed"), ("Q2grid", "reactive power Q"),
        ("VRMS2grid", "RMS voltage"), ("IRMS2grid", "RMS current"), ("TE", "electrical torque")]
FLOOR = 0.03            # stop at peaks below 3 % of the first one


def decrement(tp, ap):
    keep_t, keep_a = [tp[0]], [ap[0]]
    for tk, ak in zip(tp[1:], ap[1:]):
        if ak >= keep_a[-1] or ak < FLOOR * ap[0]:
            break
        keep_t.append(tk)
        keep_a.append(ak)
    n = len(keep_a) - 1
    if n < 2:
        return None
    delta = math.log(keep_a[0] / keep_a[-1]) / n
    fd = n / (keep_t[-1] - keep_t[0])
    return dict(n_peaks=n + 1, delta=delta, f_d_Hz=fd, zeta=delta / math.sqrt(4 * math.pi ** 2 + delta ** 2),
                sigma_per_s=delta * fd, D_pu=4.0 * H * fd * delta, t=keep_t, a=keep_a)


def main():
    df = pd.read_csv(REC)
    t = df["TIME"].values
    fs = 1.0 / (t[1] - t[0])
    sos = butter(2, [F_LO, F_HI], btype="bandpass", fs=fs, output="sos")
    rows = []
    fig, axes = plt.subplots(len(SIGS), 1, figsize=(7.0, 1.6 * len(SIGS)), sharex=True)
    print("band-pass %.2f-%.2f Hz, zero phase; peaks from %.2f s; H = %.2f s" % (F_LO, F_HI, T_FROM, H))
    for ax, (col, lab) in zip(axes, SIGS):
        if col not in df.columns:
            continue
        y = df[col].values
        m0 = t >= T_CLEAR + 0.02                       # filter the post-clearing record only (no fault step inside)
        yf = np.zeros_like(y)
        yf[m0] = sosfiltfilt(sos, y[m0] - y[m0][-1])
        m = t >= T_FROM
        tt, x = t[m], yf[m]
        dist = int(0.4 * fs)
        ax.plot(t[m0], yf[m0], lw=0.8, color="#1f77b4")
        ax.axvline(T_FROM, color="0.6", lw=0.6, ls=":")
        ax.grid(True, alpha=0.3)
        ax.set_ylabel(lab, fontsize=8)
        txt = []
        for sign, name, mk in ((1.0, "maxima", "^"), (-1.0, "minima", "v")):
            pk, _ = find_peaks(sign * x, distance=dist)
            pk = [i for i in pk if sign * x[i] > 0]
            r = decrement([tt[i] for i in pk], [sign * x[i] for i in pk]) if len(pk) >= 3 else None
            if r is None:
                print("   %-10s %-6s fewer than three decaying peaks" % (col, name))
                rows.append(dict(signal=col, peaks=name, n_peaks=len(pk), note="fewer than three decaying peaks"))
                continue
            ax.plot(r["t"], [sign * a for a in r["a"]], mk, ms=4, color="#c0392b")
            txt.append("%s: delta %.2f, D %.0f" % (name, r["delta"], r["D_pu"]))
            print("   %-10s %-6s %d peaks  delta %.3f  f_d %.3f Hz  zeta %.3f  sigma %.3f 1/s  D = %.1f pu"
                  % (col, name, r["n_peaks"], r["delta"], r["f_d_Hz"], r["zeta"], r["sigma_per_s"], r["D_pu"]))
            rows.append(dict(signal=col, peaks=name, n_peaks=r["n_peaks"], delta=round(r["delta"], 4), f_d_Hz=round(r["f_d_Hz"], 4),
                             zeta=round(r["zeta"], 4), sigma_per_s=round(r["sigma_per_s"], 4), D_pu=round(r["D_pu"], 2), note=""))
        ax.set_title("%s, band-passed   %s" % (col, " | ".join(txt)), fontsize=8, loc="left")
    axes[-1].set_xlabel("time (s)")
    axes[-1].set_xlim(3.0, 8.5)
    fig.tight_layout()
    os.makedirs(str(OUTDIR), exist_ok=True)
    tag = ("%gto%gHz" % (F_LO, F_HI)).replace(".", "p")
    fig.savefig(str(OUTDIR / ("log_decrement_bandpass_%s.png" % tag)), dpi=150)
    keys = ["signal", "peaks", "n_peaks", "delta", "f_d_Hz", "zeta", "sigma_per_s", "D_pu", "note"]
    with open(str(OUTDIR / ("log_decrement_bandpass_%s.csv" % tag)), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    good = [r for r in rows if r.get("D_pu") is not None]
    if good:
        d = np.array([r["D_pu"] for r in good]); s_ = np.array([r["sigma_per_s"] for r in good])
        print("all signals: sigma %.2f +/- %.2f 1/s, D %.1f +/- %.1f pu (mean +/- std over %d estimates)"
              % (s_.mean(), s_.std(), d.mean(), d.std(), len(good)))


if __name__ == "__main__":
    main()
