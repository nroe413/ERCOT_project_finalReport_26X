"""Per-test figures for the synchronous-machine MQT battery, in the
SAME style as the GFM campaign's plot_gfm_tests.py
(origin/gfm_validation_task_2): same rcParams, same colors, same plot
groups and output filenames, so machine and GFM figures are
one-for-one comparable.

Differences from the GFM script, all deliberate:
  - reads the stitched per-test CSVs (runs/test_NN_<name>/data_*.csv)
    instead of raw .out chunks;
  - the "model_pmu_power" group is skipped (this rig records no
    P_PMU/Pmodel channels), and one extra machine-internals group is
    added (rotor speed, field, torques) that the GFM had no analogue
    for;
  - this rig records physical units (kV, MW/MVAr, kA), so each channel
    carries a divisor to land on the pu bases the GFM figures used
    (Sbase = 650 MVA, Vbase = 230 kV L-L RMS -> 187.79 kV peak phase,
    Ibase = 1.6319 kA);
  - plotting starts at t = 0.5 s: the first ~0.2 s is the EMTDC
    numerical initialisation spike (P ~ -10 GW), which is meaningless
    and destroys the autoscale.
"""
import re
import sys
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"
PLOTS = HERE / "plots"

plt.rcParams.update({
    "text.usetex": False,
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 11,
    "axes.labelsize": 13,
    "axes.titlesize": 14,
    "legend.fontsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.grid": True,
    "grid.alpha": 0.3,
    "lines.linewidth": 0.8,
})

COLORS = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd",
          "#8c564b"]

SBASE = 650.0                      # MVA
VBASE_RMS = 230.0                  # kV L-L RMS (Vsource units)
VBASE_PK = 230.0 * (2.0 / 3.0) ** 0.5   # 187.79 kV peak phase (Vinst)
IBASE = SBASE / (3.0 ** 0.5 * VBASE_RMS)  # 1.6319 kA

T_START = 0.5   # s; skip the EMTDC numerical initialisation spike

# (filename, title, [(channel, label, divisor)], ylabel)
PLOT_GROUPS = [
    ("vinst_3phase", "POI Instantaneous Voltage (3-Phase)",
     [("PMView.Vinst:1", r"$V_a$", VBASE_PK),
      ("PMView.Vinst:2", r"$V_b$", VBASE_PK),
      ("PMView.Vinst:3", r"$V_c$", VBASE_PK)], "Voltage (pu)"),
    ("vsource", "Source Voltage",
     [("PMView.Vsource", r"$V_{source}$", VBASE_RMS)], "Voltage (pu)"),
    ("poi_power", "POI Active and Reactive Power",
     [("PMView.Ppoi", r"$P_{POI}$", SBASE),
      ("PMView.Qpoi", r"$Q_{POI}$", SBASE)], "Power (pu)"),
    ("ipoi", "POI Current",
     [("PMView.Ipoi", r"$I_{POI}$", IBASE)], "Current (pu)"),
    ("fpoi", "POI Frequency",
     [("PMView.Fpoi", r"$f_{POI}$", 1.0)], "Frequency (Hz)"),
    ("vinst_pmu_3phase", "PMU Instantaneous Voltage (3-Phase)",
     [("PMView.Vinst_PMU:1", r"$V_{PMU,a}$", VBASE_PK),
      ("PMView.Vinst_PMU:2", r"$V_{PMU,b}$", VBASE_PK),
      ("PMView.Vinst_PMU:3", r"$V_{PMU,c}$", VBASE_PK)],
     "Voltage (pu)"),
    ("vinst_dfr_3phase", "DFR Instantaneous Voltage (3-Phase)",
     [("PMView.Vinst_DFR:1", r"$V_{DFR,a}$", VBASE_PK),
      ("PMView.Vinst_DFR:2", r"$V_{DFR,b}$", VBASE_PK),
      ("PMView.Vinst_DFR:3", r"$V_{DFR,c}$", VBASE_PK)],
     "Voltage (pu)"),
    ("breaker_status", "Breaker Status",
     [("PMView.BRK1A", "BRK1A", 1.0), ("PMView.BRK1B", "BRK1B", 1.0),
      ("PMView.BRK1C", "BRK1C", 1.0)], "Status (0/1)"),
    # machine internals: no GFM analogue, added for the benchmark
    ("machine_internals", "Machine Speed, Torque and Field",
     [("G_32_0_1_DYR.Wpu", r"$\omega$ (pu)", 1.0),
      ("G_32_0_1_DYR.TM", r"$T_m$ (pu)", 1.0),
      ("G_32_0_1_DYR.TE", r"$T_e$ (pu)", 1.0),
      ("G_32_0_1_DYR.Ef", r"$E_f$ (pu)", 1.0)], "per unit"),
]


def plot_test(d):
    m = re.match(r"test_(\d+)_(.+)", d.name)
    tn, tname = int(m.group(1)), m.group(2)
    csvs = sorted(d.glob("data_*.csv"))
    if not csvs:
        print("  %s: no csv, skipped" % d.name)
        return
    df = pd.read_csv(csvs[-1])
    df = df[df["TIME"] >= T_START]
    out = PLOTS / d.name
    out.mkdir(parents=True, exist_ok=True)
    made = 0
    for fname, title, chans, ylabel in PLOT_GROUPS:
        have = [(c, lab, dv) for c, lab, dv in chans
                if c in df.columns]
        if not have:
            continue
        fig, ax = plt.subplots(figsize=(10, 4))
        for k, (c, lab, dv) in enumerate(have):
            ax.plot(df["TIME"], df[c] / dv,
                    color=COLORS[k % len(COLORS)], label=lab)
        ax.set_title("Test %d (%s): %s"
                     % (tn, tname.replace("_", " "), title))
        ax.set_xlabel("Time (s)")
        ax.set_ylabel(ylabel)
        ax.legend(loc="best")
        fig.savefig(out / ("%s.png" % fname))
        plt.close(fig)
        made += 1
    print("  %s: %d figures" % (d.name, made))


def main():
    dirs = sorted(RUNS.glob("test_*"))
    if not dirs:
        sys.exit("no runs/test_* directories; run export_runs.py first")
    for d in dirs:
        plot_test(d)
    print("plots in", PLOTS)


if __name__ == "__main__":
    main()
