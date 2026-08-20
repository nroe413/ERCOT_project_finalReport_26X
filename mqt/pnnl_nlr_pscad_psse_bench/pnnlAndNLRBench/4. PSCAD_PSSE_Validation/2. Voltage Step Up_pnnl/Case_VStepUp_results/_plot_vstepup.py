"""Generate Case 2 (Voltage Step Up) plots from PSCAD CSV.

Reads the PNNL REGFM_A1 PSCAD output (A1_VoltUp_PSD*.csv) from the parent
folder and writes one PNG per quantity (V, I, P, Q, Freq) to ./plots/.

Y-limits match Figure 3 (page 3) of the validation PDF. Plot window
is shifted to 4 -> 7 s (disturbance at t = 5 s) to align with the NLR
deck's timing, which uses 5 s of warmup before the disturbance.
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
    candidates = glob.glob(os.path.join(case_dir, "A1_VoltUp_PSD*.csv"))
    if not candidates:
        raise FileNotFoundError("No A1_VoltUp_PSD*.csv found in " + case_dir)
    candidates.sort(key=os.path.getmtime, reverse=True)
    return candidates[0]


# (key, ylabel, ylim, filename, csv_column) — y-limits per page-3 reference.
SIGNALS = [
    ("V",    r"$V$ (pu)",     (0.9,   1.05),  f"v_pu_{RUN_TS}.png",    "V_pu"),
    ("I",    r"$I$ (pu)",     (0.6,   0.9),   f"i_pu_{RUN_TS}.png",    "I_pu"),
    ("P",    r"$P$ (pu)",     (0.5,   0.7),   f"p_pu_{RUN_TS}.png",    "P_pu"),
    ("Q",    r"$Q$ (pu)",     (-0.6,  0.0),   f"q_pu_{RUN_TS}.png",    "Q_pu"),
    ("Freq", r"Freq (Hz)",    (59.95, 60.05), f"freq_hz_{RUN_TS}.png", "f_drp"),
]

XLIM = (4.0, 7.0)
PSCAD_STYLE = dict(color="red", linestyle="-", linewidth=2.0, label="PNNL PSCAD")


def plot_signal(df, ylabel, ylim, fname, col):
    fig, ax = plt.subplots(figsize=(8.0, 6.0), dpi=150)
    ax.plot(df["TIME"], df[col], **PSCAD_STYLE)
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
    print(f"Reading PNNL CSV: {pscad_path}")
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
