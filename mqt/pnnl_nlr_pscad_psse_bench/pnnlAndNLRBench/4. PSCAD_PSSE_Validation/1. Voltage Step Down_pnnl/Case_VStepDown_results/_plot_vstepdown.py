"""Generate Case 1 (Voltage Step Down) plots from PSCAD CSV.

Reads the PNNL REGFM_A1 PSCAD output (A1_VoltDwn_PSD*.csv) from the parent
folder, produces one PNG per quantity (V, I, P, Q, Freq) sized to match
the page-2 reference figure, and writes them to ./plots/.

Designed so an NLR-PSCAD trace can later be added by passing a second CSV
to the plot_signal() helper.
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

# Mathtext for inline LaTeX-style symbols ($V$, $P$, ...) without needing
# an external LaTeX install. Use a serif family so labels read like LaTeX.
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
    """Pick the most-recent A1_VoltDwn_PSD*.csv (timestamped or plain)."""
    candidates = glob.glob(os.path.join(case_dir, "A1_VoltDwn_PSD*.csv"))
    if not candidates:
        raise FileNotFoundError("No A1_VoltDwn_PSD*.csv found in " + case_dir)
    candidates.sort(key=os.path.getmtime, reverse=True)
    return candidates[0]


# ---------- signal definitions ----------
# Each entry: (key, ylabel, ylim, filename, csv_column)
# y-limits and x-limits chosen to match the PDF reference (Figure 2, page 2).
SIGNALS = [
    ("V",    r"$V$ (pu)",     (0.9,   1.05),  f"v_pu_{RUN_TS}.png",    "V_pu"),
    ("I",    r"$I$ (pu)",     (0.6,   0.9),   f"i_pu_{RUN_TS}.png",    "I_pu"),
    ("P",    r"$P$ (pu)",     (0.5,   0.7),   f"p_pu_{RUN_TS}.png",    "P_pu"),
    ("Q",    r"$Q$ (pu)",     (-0.2,  0.6),   f"q_pu_{RUN_TS}.png",    "Q_pu"),
    ("Freq", r"Freq (Hz)",    (59.95, 60.05), f"freq_hz_{RUN_TS}.png", "f_drp"),
]

XLIM = (4.0, 7.0)
PSCAD_STYLE = dict(color="red",   linestyle="-",  linewidth=2.0, label="PNNL PSCAD")
NLR_STYLE   = dict(color="blue",  linestyle="--", linewidth=2.0, label="NLR PSCAD")


def plot_signal(pscad_df, ylabel, ylim, fname, col, nlr_df=None):
    fig, ax = plt.subplots(figsize=(8.0, 6.0), dpi=150)  # 4:3, big & not stretched

    ax.plot(pscad_df["TIME"], pscad_df[col], **PSCAD_STYLE)
    if nlr_df is not None and col in nlr_df.columns:
        ax.plot(nlr_df["TIME"], nlr_df[col], **NLR_STYLE)

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
    print(f"Reading PSCAD CSV: {pscad_path}")
    pscad_df = pd.read_csv(pscad_path)
    print(f"  rows={len(pscad_df)}  t={pscad_df.TIME.min():.3f} -> {pscad_df.TIME.max():.3f} s")

    nlr_df = None  # populate later when NLR data is available

    for _key, ylabel, ylim, fname, col in SIGNALS:
        out = plot_signal(pscad_df, ylabel, ylim, fname, col, nlr_df=nlr_df)
        print(f"  wrote {out}")

    # Drop a marker so _make_pptx_vstepdown.py can pick the matching set.
    marker = os.path.join(PLOT_DIR, "latest_run.txt")
    with open(marker, "w") as f:
        f.write(RUN_TS + "\n")
    print(f"Latest run timestamp: {RUN_TS}")
    print("Done.")


if __name__ == "__main__":
    main()
