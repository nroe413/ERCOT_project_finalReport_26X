"""Report figure narr_allsync_ringdown.png: the post-fault power oscillation of the ten synchronous
machines in the all-machine bus-14 case and the modal decay rates behind the net damping of
Table 4 (D_net = 4 H sigma).

Data: data/report_figure_data/ringdown/allsync_bus14_30s_genP_MW.csv, the TIME column and the
ten machine active-power channels (Desc="P", groups G_30 ... G_39) extracted from the 30 s record
of the all-machine bus-14 fault case (5 kHz). The fitted modes are written next to it as
allsync_bus14_ringdown_fit.json.

Method (per machine):
  1. block-average 5 kHz -> 100 Hz and remove the slow trend with a zero-phase Butterworth
     band-pass, 0.5-2 Hz, fourth order (second-order sections);
  2. fit the 6-30 s window with a sum of damped sinusoids by the matrix-pencil method
     (order 6, half-length pencil); keep the modes between 0.5 and 2 Hz whose amplitude is at
     least 20 % of the machine's largest mode and at least 2 MW;
  3. classify: inter-machine modes at 0.85 Hz and 1.02 Hz; faster local components above
     1.07 Hz on the units nearest the fault;
  4. D_net = 4 H sigma with H = 5.46 s, from the inter-machine modes.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_paths as rp  # noqa: E402

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfiltfilt

import figstyle_26x as st  # noqa: E402

st.apply()

DATA = rp.DATA / "ringdown"
SRC = DATA / "allsync_bus14_30s_genP_MW.csv"
OUT = rp.OUT

H_SG = 5.46
T0, T1 = 6.0, 30.0
BAND = (0.5, 2.0)
DECIM = 50
ORDER = 6
BUSES = list(range(30, 40))
NAVY, RED, GREY = "#1f2f5c", "#c0392b", "#9a9a9a"


def decimate(v):
    n = (len(v) // DECIM) * DECIM
    return v[:n].reshape(-1, DECIM).mean(axis=1)


def bandpass(p, dt):
    fs = 1.0 / dt
    sos = butter(4, [BAND[0] / (fs / 2), BAND[1] / (fs / 2)], btype="band", output="sos")
    return sosfiltfilt(sos, p - p.mean())


def matrix_pencil(y, dt, order=ORDER):
    N = len(y); L = N // 2
    Y = np.array([y[i:i + N - L] for i in range(L + 1)])
    _, _, Vh = np.linalg.svd(Y, full_matrices=False)
    Vs = Vh[:order].T
    z = np.linalg.eigvals(np.linalg.pinv(Vs[:-1]) @ Vs[1:])
    lam = np.log(z) / dt
    Z = np.vander(z, N, increasing=True).T
    amp = np.linalg.lstsq(Z, y.astype(complex), rcond=None)[0]
    modes = [(lk.imag / (2 * np.pi), -lk.real, 2 * abs(ak)) for lk, ak in zip(lam, amp) if lk.imag > 0]
    return sorted(modes, key=lambda m: -m[2])


def classify(f):
    if 0.78 <= f <= 0.92: return "0.85"
    if 0.95 <= f < 1.07: return "1.02"
    return "fast"


def main():
    df = pd.read_csv(SRC)
    m = ((df.TIME >= T0) & (df.TIME <= T1)).values
    t = decimate(df.TIME.values[m]); dt = t[1] - t[0]
    res = {}
    for b in BUSES:
        x = bandpass(decimate(df["P_G%d" % b].values[m]), dt)
        modes = [mo for mo in matrix_pencil(x, dt) if BAND[0] <= mo[0] <= BAND[1]]
        amax = modes[0][2]
        modes = [mo for mo in modes if mo[2] >= max(0.2 * amax, 2.0)]
        res[b] = dict(x=x, modes=modes)
        print("G%d: " % b + " | ".join("%.3f Hz  sigma %.3f  %.1f MW  [%s]" % (mo[0], mo[1], mo[2], classify(mo[0])) for mo in modes))
    inter = [(b, mo) for b in BUSES for mo in res[b]["modes"] if classify(mo[0]) != "fast"]
    fast = [(b, mo) for b in BUSES for mo in res[b]["modes"] if classify(mo[0]) == "fast"]
    sig = np.array([mo[1] for _, mo in inter]); fr = np.array([mo[0] for _, mo in inter])
    summary = {"window_s": [T0, T1], "inter_machine_modes": [{"bus": b, "f_Hz": round(mo[0], 3), "sigma_1_per_s": round(mo[1], 4), "amp_MW": round(mo[2], 1)} for b, mo in inter],
               "fast_local_modes": [{"bus": b, "f_Hz": round(mo[0], 3), "sigma_1_per_s": round(mo[1], 4), "amp_MW": round(mo[2], 1)} for b, mo in fast],
               "inter_sigma_range": [round(sig.min(), 3), round(sig.max(), 3)], "inter_sigma_median": round(float(np.median(sig)), 3),
               "inter_f_range": [round(fr.min(), 3), round(fr.max(), 3)],
               "D_net_median": round(4 * H_SG * float(np.median(sig)), 2), "D_net_range": [round(4 * H_SG * sig.min(), 2), round(4 * H_SG * sig.max(), 2)]}
    (DATA / "allsync_bus14_ringdown_fit.json").write_text(json.dumps(summary, indent=1))
    print("inter-machine modes: f %.3f-%.3f Hz, sigma %.3f-%.3f (median %.3f) -> D_net %.2f (%.2f-%.2f)" % (
        fr.min(), fr.max(), sig.min(), sig.max(), np.median(sig), 4 * H_SG * np.median(sig), 4 * H_SG * sig.min(), 4 * H_SG * sig.max()))

    fig, (axA, axB) = plt.subplots(1, 2, figsize=(0.95 * st.TEXTWIDTH_IN, 4.2), gridspec_kw=dict(width_ratios=[1.25, 1.0], wspace=0.3))
    for k, b in enumerate(BUSES):
        y = res[b]["x"] / np.max(np.abs(res[b]["x"]))
        off = -2.3 * k
        axA.plot(t, y + off, color=NAVY, lw=0.6)
        axA.text(T0 - 0.35, off, "G%d" % b, ha="right", va="center", fontsize=7.5, color=NAVY)
    axA.set_xlim(T0 - 2.3, T1)
    axA.set_yticks([])
    axA.set_xlabel("time (s)")
    axA.set_title("(a) band-passed active power, each scaled to its maximum", fontsize=8.5, loc="left")
    axA.grid(False)
    for b, mo in inter:
        col = NAVY if classify(mo[0]) == "0.85" else RED
        axB.plot(b, mo[1], "o", ms=3.0 + 0.09 * min(mo[2], 60), color=col, alpha=0.8, mec="white", mew=0.4)
    for b, mo in fast:
        axB.plot(b, mo[1], "s", ms=3.0 + 0.09 * min(mo[2], 60), color=GREY, alpha=0.8, mec="white", mew=0.4)
    axB.axhspan(sig.min(), sig.max(), color=NAVY, alpha=0.10, lw=0)
    axB.plot([], [], "o", color=NAVY, ms=5, label="0.85 Hz inter-machine mode")
    axB.plot([], [], "o", color=RED, ms=5, label="1.02 Hz inter-machine mode")
    axB.plot([], [], "s", color=GREY, ms=5, label="faster local component")
    axB.set_xticks(BUSES); axB.set_xticklabels(["G%d" % b for b in BUSES], fontsize=7)
    axB.set_ylabel(r"decay rate $\sigma$ (s$^{-1}$)")
    axB.set_ylim(0, 0.45)
    axB.set_title("(b) fitted modes; marker size shows amplitude", fontsize=8.5, loc="left")
    axB.legend(fontsize=7, loc="upper right", framealpha=0.95)
    axB.grid(True, alpha=0.3)
    fig.savefig(OUT / "narr_allsync_ringdown.png", dpi=600)
    print("wrote", OUT / "narr_allsync_ringdown.png")


if __name__ == "__main__":
    main()
