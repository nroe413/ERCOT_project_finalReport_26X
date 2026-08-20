"""Generate Case 1 (Voltage Step Down) plots for the NLR model.

Reads NLR_VoltDwn_PSD*.csv from the parent folder, produces one PNG per
quantity (V, I, P, Q, Freq) sized to match the PNNL slide format, and
writes them to ./plots/ with a per-run timestamp.

Plot window 4 -> 7 s, matching the timing the PNNL run was reconfigured
to (disturbance at t = 5 s, 1 s pre / 2 s post).
"""
import datetime
import glob
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RUN_TS = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 14,
    "axes.titlesize": 16,
    "axes.labelsize": 16,
    "xtick.labelsize": 13,
    "ytick.labelsize": 13,
    "legend.fontsize": 13,
    "mathtext.fontset": "cm",
    "axes.unicode_minus": True,
})

HERE = os.path.dirname(os.path.abspath(__file__))
CASE_DIR = os.path.dirname(HERE)
PLOT_DIR = os.path.join(HERE, "plots")
os.makedirs(PLOT_DIR, exist_ok=True)


def newest_pscad_csv(case_dir):
    candidates = glob.glob(os.path.join(case_dir, "NLR_VoltDwn_PSD*.csv"))
    if not candidates:
        raise FileNotFoundError("No NLR_VoltDwn_PSD*.csv found in " + case_dir)
    candidates.sort(key=os.path.getmtime, reverse=True)
    return candidates[0]


SIGNALS = [
    # Y-limits widened relative to the PNNL deck because the NLR model
    # exhibits larger transients on I, P, Q, and f at the disturbance.
    # Empirical 4–7 s spans (this run): I 0.61→1.18, P 0.22→0.93,
    # Q −0.15→1.11, f 59.91→60.11.
    ("V",    r"$V$ (pu)",     (0.9,   1.05),  f"v_pu_{RUN_TS}.png",    "V_pu"),
    ("I",    r"$I$ (pu)",     (0.5,   1.3),   f"i_pu_{RUN_TS}.png",    "I_pu"),
    ("P",    r"$P$ (pu)",     (0.0,   1.0),   f"p_pu_{RUN_TS}.png",    "P_pu"),
    ("Q",    r"$Q$ (pu)",     (-0.3,  1.3),   f"q_pu_{RUN_TS}.png",    "Q_pu"),
    ("Freq", r"Freq (Hz)",    (59.8,  60.2),  f"freq_hz_{RUN_TS}.png", "f_drp"),
]

XLIM = (4.0, 7.0)
NLR_STYLE = dict(color="blue", linestyle="-", linewidth=2.0, label="NLR PSCAD")


def plot_signal(df, ylabel, ylim, fname, col):
    fig, ax = plt.subplots(figsize=(8.0, 6.0), dpi=150)
    ax.plot(df["TIME"], df[col], **NLR_STYLE)
    ax.set_xlim(XLIM)
    ax.set_ylim(ylim)
    ax.set_xlabel(r"Time (s)")
    ax.set_ylabel(ylabel)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="best", framealpha=0.9)
    fig.tight_layout()
    out = os.path.join(PLOT_DIR, fname)
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def main():
    pscad_path = sys.argv[1] if len(sys.argv) > 1 else newest_pscad_csv(CASE_DIR)
    print(f"Reading NLR CSV: {pscad_path}")
    df = pd.read_csv(pscad_path)
    print(f"  rows={len(df)}  t={df.TIME.min():.3f} -> {df.TIME.max():.3f} s")

    for _key, ylabel, ylim, fname, col in SIGNALS:
        out = plot_signal(df, ylabel, ylim, fname, col)
        print(f"  wrote {out}")

    marker = os.path.join(PLOT_DIR, "latest_run.txt")
    with open(marker, "w") as f:
        f.write(RUN_TS + "\n")
    print(f"Latest run timestamp: {RUN_TS}")
    print("Done.")


if __name__ == "__main__":
    main()
