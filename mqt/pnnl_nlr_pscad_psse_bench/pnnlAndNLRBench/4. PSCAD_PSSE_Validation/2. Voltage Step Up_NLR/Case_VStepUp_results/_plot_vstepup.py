"""Generate Case 2 (Voltage Step Up) plots for the NLR model.

Reads NLR_VoltUp_PSD*.csv from the parent folder and writes one PNG per
quantity (V, I, P, Q, Freq) to ./plots/.

Plot window 4 -> 7 s, matching the PNNL run (disturbance at t = 5 s).
The 5 s of warmup is needed for the NLR-side operating point to settle.
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
    candidates = glob.glob(os.path.join(case_dir, "NLR_VoltUp_PSD*.csv"))
    if not candidates:
        raise FileNotFoundError("No NLR_VoltUp_PSD*.csv found in " + case_dir)
    candidates.sort(key=os.path.getmtime, reverse=True)
    return candidates[0]


# Y-limits widened to capture the sustained limit-cycle oscillation the
# NLR model exhibits post-disturbance. Empirical 4-7 s spans (this run):
# V 1.00->1.07, I 0.56->1.20, P -1.17->0.60, Q -1.05->0.85, f 59.86->60.07.
SIGNALS = [
    ("V",    r"$V$ (pu)",     (0.9,   1.10),  f"v_pu_{RUN_TS}.png",    "V_pu"),
    ("I",    r"$I$ (pu)",     (0.3,   1.3),   f"i_pu_{RUN_TS}.png",    "I_pu"),
    ("P",    r"$P$ (pu)",     (-1.3,  1.0),   f"p_pu_{RUN_TS}.png",    "P_pu"),
    ("Q",    r"$Q$ (pu)",     (-1.5,  1.0),   f"q_pu_{RUN_TS}.png",    "Q_pu"),
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
