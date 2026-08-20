#!/usr/bin/env python3
"""
plot_gfm_tests.py - Plot PSCAD PMView simulation outputs for GFM MQT tests.

Reads text-formatted .out files and .inf channel layouts from PSCAD
simulation runs, generates publication-quality PNG plots per test.

Usage:
    python plot_gfm_tests.py                  # Plot all tests (1-13)
    python plot_gfm_tests.py 1                # Plot test 1 only
    python plot_gfm_tests.py 1 2 3            # Plot tests 1, 2, 3
"""

import sys
import os
import re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── Configuration ──────────────────────────────────────────────────────────

SAMPLE_RATE = 5000  # Hz

GF46_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "pnnlREGFMA1mQT.gf46")
RUN_PREFIX_NAME = "pnnlREGFMA1mQT"
PLOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots")

TEST_PROFILES = {
    1:  "Flatstart",
    2:  "LVRT_ERCOT_Legacy",
    3:  "HVRT_ERCOT_Legacy",
    4:  "V_Down",
    5:  "V_Up",
    6:  "LVRT_Dips_IEEE2800_NOGRR245",
    7:  "HVRT_Preferred_IEEE2800",
    8:  "Angle_Down",
    9:  "Angle_Up",
    10: "Custom_Faults",
    11: "Frequency_Down",
    12: "Frequency_Up",
    13: "V_Up_Down_Impedance",
}

# Plot groups: (filename, title, [(channel_desc, label), ...], ylabel)
# All channel names reference the "PMView" group in the .inf file.
PLOT_GROUPS = [
    ("vinst_3phase",
     "POI Instantaneous Voltage (3-Phase)",
     [("Vinst:1", r"$V_a$"), ("Vinst:2", r"$V_b$"), ("Vinst:3", r"$V_c$")],
     "Voltage (pu)"),

    ("vsource",
     "Source Voltage",
     [("Vsource", r"$V_{source}$")],
     "Voltage (pu)"),

    ("poi_power",
     "POI Active and Reactive Power",
     [("Ppoi", r"$P_{POI}$"), ("Qpoi", r"$Q_{POI}$")],
     "Power (pu)"),

    ("model_pmu_power",
     "Model and PMU Power Comparison",
     [("P_PMU", r"$P_{PMU}$"), ("Q_PMU", r"$Q_{PMU}$"),
      ("Pmodel", r"$P_{model}$"), ("Qmodel", r"$Q_{model}$")],
     "Power (pu)"),

    ("ipoi",
     "POI Current",
     [("Ipoi", r"$I_{POI}$")],
     "Current (pu)"),

    ("fpoi",
     "POI Frequency",
     [("Fpoi", r"$f_{POI}$")],
     "Frequency (Hz)"),

    ("vinst_pmu_3phase",
     "PMU Instantaneous Voltage (3-Phase)",
     [("Vinst_PMU:1", r"$V_{PMU,a}$"), ("Vinst_PMU:2", r"$V_{PMU,b}$"),
      ("Vinst_PMU:3", r"$V_{PMU,c}$")],
     "Voltage (pu)"),

    ("vinst_dfr_3phase",
     "DFR Instantaneous Voltage (3-Phase)",
     [("Vinst_DFR:1", r"$V_{DFR,a}$"), ("Vinst_DFR:2", r"$V_{DFR,b}$"),
      ("Vinst_DFR:3", r"$V_{DFR,c}$")],
     "Voltage (pu)"),

    ("breaker_status",
     "Breaker Status",
     [("BRK1A", "BRK1A"), ("BRK1B", "BRK1B"), ("BRK1C", "BRK1C")],
     "Status (0/1)"),
]

# ── Plotting style ─────────────────────────────────────────────────────────

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

COLORS = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd", "#8c564b"]


# ── Functions ──────────────────────────────────────────────────────────────

def parse_inf(inf_path):
    """Parse .inf file, return list of (desc, group, units) tuples (0-indexed)."""
    channels = []
    with open(inf_path, "r") as f:
        for line in f:
            m_desc = re.search(r'Desc="([^"]*)"', line)
            m_group = re.search(r'Group="([^"]*)"', line)
            m_units = re.search(r'Units="([^"]*)"', line)
            if m_desc:
                channels.append((
                    m_desc.group(1),
                    m_group.group(1) if m_group else "",
                    m_units.group(1) if m_units else "",
                ))
    return channels


def read_out_files(run_prefix):
    """Read all .out files for a run, return (time, data) arrays.

    Each .out file is text: 1 blank header line, then rows of
    ``time val1 val2 ... val10`` (up to 10 data columns per file).
    Files are numbered _01, _02, ... and split channels in order.

    Returns
    -------
    time : ndarray, shape (N,)
    data : ndarray, shape (N, n_channels)
    """
    file_idx = 1
    all_cols = []
    time = None

    while True:
        fname = os.path.join(
            os.path.dirname(run_prefix),
            os.path.basename(run_prefix) + f"_{file_idx:02d}.out",
        )
        if not os.path.exists(fname):
            break

        raw = np.loadtxt(fname, skiprows=1)
        if time is None:
            time = raw[:, 0]
        all_cols.append(raw[:, 1:])
        file_idx += 1

    if time is None:
        raise FileNotFoundError(f"No .out files found for {run_prefix}")

    data = np.hstack(all_cols)
    return time, data


def find_pmview_channels(channels, requested):
    """Map requested channel names to column indices in the PMView group.

    Parameters
    ----------
    channels : list of (desc, group, units) from parse_inf
    requested : list of (desc, label) tuples

    Returns
    -------
    list of (col_index_or_None, label)
    """
    result = []
    for desc, label in requested:
        found = None
        for i, (ch_desc, ch_group, _) in enumerate(channels):
            if ch_desc == desc and ch_group == "PMView":
                found = i
                break
        result.append((found, label))
    return result


def find_channel_by_desc(channels, desc):
    """Find a channel column index by description (any group).

    Returns column index or None.
    """
    for i, (ch_desc, ch_group, _) in enumerate(channels):
        if ch_desc == desc:
            return i
    return None


MAX_TIME = 30.0  # seconds — clip plots at this time

def plot_group(time, data, channel_indices, title, ylabel, save_path,
               figsize=None):
    """Create and save a plot for a group of channels."""
    valid = [(idx, lbl) for idx, lbl in channel_indices if idx is not None]
    if not valid:
        print(f"  Skipping {os.path.basename(save_path)}: no valid channels")
        return

    # Clip to MAX_TIME
    mask = time <= MAX_TIME
    t = time[mask]
    d = data[mask]

    n_traces = len(valid)
    if figsize is None:
        figsize = (10, 5) if n_traces <= 2 else (10, 6)

    fig, ax = plt.subplots(figsize=figsize)

    for i, (ch_idx, label) in enumerate(valid):
        ax.plot(t, d[:, ch_idx], label=label,
                color=COLORS[i % len(COLORS)],
                linewidth=0.5 if n_traces >= 3 else 0.8)

    ax.set_xlabel("Time (s)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if n_traces > 1:
        ax.legend(loc="best")
    ax.set_xlim(t[0], t[-1])

    fig.savefig(save_path)
    plt.close(fig)
    print(f"  Saved {os.path.basename(save_path)}")


def plot_overlay(time, data, channels, title, save_path):
    """Create a dual-axis overlay plot: Ppoi & Qpoi on left, Vrms on right."""
    idx_ppoi = find_channel_by_desc(channels, "Ppoi")
    idx_qpoi = find_channel_by_desc(channels, "Qpoi")
    idx_vrms = find_channel_by_desc(channels, "Vsource")

    missing = []
    if idx_ppoi is None:
        missing.append("Ppoi")
    if idx_qpoi is None:
        missing.append("Qpoi")
    if idx_vrms is None:
        missing.append("Vsource")
    if missing:
        print(f"  Skipping overlay: missing channels {missing}")
        return

    # Clip to MAX_TIME
    mask = time <= MAX_TIME
    t = time[mask]
    d = data[mask]

    fig, ax1 = plt.subplots(figsize=(10, 5))

    # Primary axis: Ppoi and Qpoi
    l1, = ax1.plot(t, d[:, idx_ppoi], label=r"$P_{POI}$",
                   color=COLORS[0], linewidth=0.8)
    l2, = ax1.plot(t, d[:, idx_qpoi], label=r"$Q_{POI}$",
                   color=COLORS[1], linewidth=0.8)
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Power (pu)")
    ax1.set_xlim(t[0], t[-1])

    # Pad the primary axis top so power traces sit in the lower portion,
    # visually offset from the voltage trace in the upper portion.
    p_min = min(d[:, idx_ppoi].min(), d[:, idx_qpoi].min())
    p_max = max(d[:, idx_ppoi].max(), d[:, idx_qpoi].max())
    p_range = max(p_max - p_min, 0.1)  # avoid zero range
    ax1.set_ylim(p_min - 0.1 * p_range, p_max + 1.0 * p_range)

    # Secondary axis: Vrms_gridSide_LCL (fixed 0.8–1.2 pu)
    ax2 = ax1.twinx()
    l3, = ax2.plot(t, d[:, idx_vrms], label=r"$V_{source}$",
                   color=COLORS[2], linewidth=0.8, linestyle="--")
    ax2.set_ylabel("Voltage (pu)")
    ax2.set_ylim(-0.05, 1.3)

    # Combined legend
    lines = [l1, l2, l3]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="best")

    ax1.set_title(title)
    ax1.grid(True, alpha=0.3)

    fig.savefig(save_path)
    plt.close(fig)
    print(f"  Saved {os.path.basename(save_path)}")


def plot_test(test_num):
    """Generate all plots for a single test run."""
    profile = TEST_PROFILES.get(test_num, f"Unknown_Test_{test_num}")
    run_id = f"r{test_num:05d}"
    run_prefix = os.path.join(GF46_DIR, f"{RUN_PREFIX_NAME}_{run_id}")
    inf_path = run_prefix + ".inf"

    if not os.path.exists(inf_path):
        print(f"Test {test_num} ({profile}): .inf file not found, skipping")
        return

    print(f"\nTest {test_num}: {profile}")
    print(f"  Reading {os.path.basename(inf_path)}")
    channels = parse_inf(inf_path)
    print(f"  Found {len(channels)} channels")

    print("  Reading .out files...")
    time, data = read_out_files(run_prefix)
    print(f"  Loaded {len(time)} samples, {data.shape[1]} channels, "
          f"t=[{time[0]:.3f}, {time[-1]:.3f}]s")

    # Create output directory
    out_dir = os.path.join(PLOT_DIR, f"{run_id}_{profile}")
    os.makedirs(out_dir, exist_ok=True)

    # Generate PMView plots
    for fname, title, ch_list, ylabel in PLOT_GROUPS:
        indices = find_pmview_channels(channels, ch_list)
        save_path = os.path.join(out_dir, f"{fname}.png")
        plot_group(time, data, indices,
                   f"{title} \u2014 Test {test_num} ({profile})",
                   ylabel, save_path)

    # Generate overlay plot (Ppoi, Qpoi on left axis; Vrms_gridSide_LCL on right)
    overlay_path = os.path.join(out_dir, "pq_vrms_overlay.png")
    plot_overlay(time, data, channels,
                 f"POI Power & Grid Voltage \u2014 Test {test_num} ({profile})",
                 overlay_path)


def main():
    if len(sys.argv) > 1:
        tests = [int(x) for x in sys.argv[1:]]
    else:
        tests = list(TEST_PROFILES.keys())

    print(f"Plotting tests: {tests}")
    for t in tests:
        plot_test(t)

    print(f"\nDone. Plots saved to {PLOT_DIR}/")


if __name__ == "__main__":
    main()
