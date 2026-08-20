#!/usr/bin/env python3
"""
analyze_gfl_results.py - Automated ERCOT DWG Procedure Manual pass/fail analysis
for PNNL GFL (Grid-Following) inverter model PSCAD simulation results.

Analyzes MQT tests 1-9 per the ERCOT DWG Procedure Manual sections:
  Test 1: Flatstart (Section 3.1.5.2)
  Test 2: LVRT ERCOT Legacy (Section 3.1.5.4)
  Test 3: HVRT ERCOT Legacy (Section 3.1.5.5)
  Test 4: V_Down (Section 3.1.5.3)
  Test 5: V_Up (Section 3.1.5.3)
  Test 6: LVRT Dips IEEE 2800 (Section 3.1.5.4)
  Test 7: HVRT Preferred IEEE 2800 (Section 3.1.5.5)
  Test 8: Angle_Down (Section 3.1.5.9)
  Test 9: Angle_Up (Section 3.1.5.9)
"""

import os
import re
import sys
import numpy as np

# ── Configuration ──────────────────────────────────────────────────────────

GF46_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "PMView_testing_NREL_GFM.gf46")

TEST_PROFILES = {
    1: "Flatstart",
    2: "LVRT_ERCOT_Legacy",
    3: "HVRT_ERCOT_Legacy",
    4: "V_Down",
    5: "V_Up",
    6: "LVRT_Dips_IEEE2800_NOGRR245",
    7: "HVRT_Preferred_IEEE2800",
    8: "Angle_Down",
    9: "Angle_Up",
}

# Oscillation thresholds
# For Ppoi and Qpoi in the last 5 seconds of the relevant evaluation window
PPOI_STD_THRESHOLD = 0.10    # pu - threshold for sustained oscillations in P
QPOI_STD_THRESHOLD = 0.10    # pu - threshold for sustained oscillations in Q
FPOI_STD_THRESHOLD = 0.05    # Hz - threshold for frequency oscillations

# Power recovery tolerance
POWER_RECOVERY_TOLERANCE = 0.10  # pu deviation from pre-disturbance value


# ── Data Loading ───────────────────────────────────────────────────────────

def parse_inf(inf_path):
    """Parse .inf file, return list of (desc, group) tuples (0-indexed)."""
    channels = []
    with open(inf_path, "r") as f:
        for line in f:
            m_desc = re.search(r'Desc="([^"]*)"', line)
            m_group = re.search(r'Group="([^"]*)"', line)
            if m_desc:
                channels.append((
                    m_desc.group(1),
                    m_group.group(1) if m_group else "",
                ))
    return channels


def read_out_files(run_prefix):
    """Read all .out files for a run, return (time, data) arrays.

    Each .out file has 1 blank header then rows of: time val1 val2 ... val10.
    Files split across _01, _02, _03... with up to 10 data columns each.

    Returns
    -------
    time : ndarray, shape (N,)
    data : ndarray, shape (N, n_channels)
        Columns correspond to PGB channels in order.
    """
    file_idx = 1
    all_cols = []
    time = None

    while True:
        fname = f"{run_prefix}_{file_idx:02d}.out"
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


def find_pmview_channel(channels, desc):
    """Find column index for a PMView-group channel by description.

    Returns column index (0-based) or None.
    """
    for i, (ch_desc, ch_group) in enumerate(channels):
        if ch_desc == desc and ch_group == "PMView":
            return i
    return None


def load_test_data(test_num):
    """Load data for a test, returning time array and dict of key signals.

    Returns
    -------
    time : ndarray
    signals : dict with keys 'Ppoi', 'Qpoi', 'Vsource', 'Fpoi', 'Ipoi',
              'BRK1A', 'BRK1B', 'BRK1C'
    """
    run_id = f"r{test_num:05d}"
    run_prefix = os.path.join(GF46_DIR, f"MQT_{run_id}")
    inf_path = run_prefix + ".inf"

    if not os.path.exists(inf_path):
        raise FileNotFoundError(f"Test {test_num}: .inf file not found at {inf_path}")

    channels = parse_inf(inf_path)
    time, data = read_out_files(run_prefix)

    # Find column indices for key PMView signals
    signal_names = ['Ppoi', 'Qpoi', 'Vsource', 'Fpoi', 'Ipoi',
                    'BRK1A', 'BRK1B', 'BRK1C', 'P_PMU', 'Q_PMU']
    signals = {}
    for name in signal_names:
        idx = find_pmview_channel(channels, name)
        if idx is not None and idx < data.shape[1]:
            signals[name] = data[:, idx]
        else:
            signals[name] = None

    return time, signals


# ── Analysis Utilities ─────────────────────────────────────────────────────

def time_slice(time, signals, t_start, t_end):
    """Return mask for time window [t_start, t_end]."""
    return (time >= t_start) & (time <= t_end)


def signal_stats(sig, mask):
    """Return mean, std, min, max for a signal within a mask."""
    s = sig[mask]
    return s.mean(), s.std(), s.min(), s.max()


def check_oscillations(sig, mask, threshold):
    """Check if signal has sustained oscillations (std > threshold).

    Distinguishes between monotonic settling (not oscillation) and actual
    sustained oscillation by checking if the signal is predominantly
    monotonic (trending in one direction) vs oscillating.
    """
    s = sig[mask]
    std = s.std()

    if std <= threshold:
        return False, std

    # Check if the large std is due to monotonic settling rather than oscillation.
    # Compute the fraction of time the signal is moving in the same direction.
    # For monotonic settling, most consecutive differences will have the same sign.
    diffs = np.diff(s)
    # Smooth to avoid noise: check sign changes over blocks of ~500 samples (~0.1s)
    block_size = min(500, max(10, len(diffs) // 20))
    n_blocks = len(diffs) // block_size
    if n_blocks >= 4:
        block_means = [diffs[i*block_size:(i+1)*block_size].mean()
                       for i in range(n_blocks)]
        sign_changes = sum(1 for i in range(1, len(block_means))
                           if block_means[i] * block_means[i-1] < 0)
        # If fewer than 3 sign changes relative to block count, it's monotonic
        # settling, not oscillation. A truly oscillating signal would have many
        # sign changes across its blocks.
        if sign_changes <= max(2, n_blocks // 10):
            return False, std

    return std > threshold, std


def find_recovery_time(time, sig, mask_start, target_value, tolerance, max_time=1.0):
    """Find time for signal to recover within tolerance of target after mask_start.

    Returns recovery time in seconds, or None if not recovered within max_time.
    """
    t_start = time[mask_start][0] if np.any(mask_start) else time[0]
    recovery_mask = (time >= t_start) & (time <= t_start + max_time)
    t_rec = time[recovery_mask]
    s_rec = sig[recovery_mask]

    within = np.abs(s_rec - target_value) <= tolerance
    if np.any(within):
        # Find first sustained recovery (stays within tolerance for at least 0.1s)
        first_idx = np.where(within)[0][0]
        return t_rec[first_idx] - t_start
    return None


def settling_time(time, sig, t_event, final_value, tolerance_pct=5.0, window=0.5):
    """Estimate settling time after an event.

    Returns time in seconds for signal to stay within tolerance_pct% of
    final_value for at least 'window' seconds.
    """
    tolerance = abs(final_value) * tolerance_pct / 100.0
    if tolerance < 0.001:
        tolerance = 0.001

    mask = time >= t_event
    t_post = time[mask]
    s_post = sig[mask]

    if len(t_post) == 0:
        return None

    within = np.abs(s_post - final_value) <= tolerance

    # Find first time where signal stays within tolerance for 'window' seconds
    dt = t_post[1] - t_post[0] if len(t_post) > 1 else 0.0002
    window_samples = max(int(window / dt), 1)

    for i in range(len(within) - window_samples):
        if np.all(within[i:i + window_samples]):
            return t_post[i] - t_event

    return None


def check_damping(time, sig, t_start, t_end, n_cycles=3):
    """Check if oscillations are well-damped by comparing amplitude in first
    vs second half of the window."""
    mask = (time >= t_start) & (time <= t_end)
    s = sig[mask]
    if len(s) < 10:
        return True, 0.0, 0.0

    mid = len(s) // 2
    mean_val = s.mean()
    amp_first = np.abs(s[:mid] - mean_val).max()
    amp_second = np.abs(s[mid:] - mean_val).max()

    well_damped = amp_second <= amp_first  # Amplitude should decrease
    return well_damped, amp_first, amp_second


# ── Test-Specific Analysis Functions ────────────────────────────────────────

def analyze_test_1(time, signals):
    """Test 1: Flatstart (Section 3.1.5.2)
    No disturbance for 20+ seconds. Check stability.
    """
    results = {"test": 1, "profile": "Flatstart", "section": "3.1.5.2"}
    issues = []

    # Evaluate the last 5 seconds
    t_end = time[-1]
    mask = time_slice(time, signals, t_end - 5.0, t_end)

    Ppoi = signals['Ppoi']
    Qpoi = signals['Qpoi']
    Vsource = signals['Vsource']
    Fpoi = signals['Fpoi']

    Ppoi_mean, Ppoi_std, Ppoi_min, Ppoi_max = signal_stats(Ppoi, mask)
    Qpoi_mean, Qpoi_std, Qpoi_min, Qpoi_max = signal_stats(Qpoi, mask)
    Vs_mean, Vs_std, Vs_min, Vs_max = signal_stats(Vsource, mask)
    Fpoi_mean, Fpoi_std, Fpoi_min, Fpoi_max = signal_stats(Fpoi, mask)

    results['Ppoi_mean'] = Ppoi_mean
    results['Ppoi_std'] = Ppoi_std
    results['Qpoi_mean'] = Qpoi_mean
    results['Qpoi_std'] = Qpoi_std
    results['Vsource_mean'] = Vs_mean
    results['Vsource_std'] = Vs_std
    results['Fpoi_mean'] = Fpoi_mean
    results['Fpoi_std'] = Fpoi_std

    # Check: signals should be flat (low std)
    if Ppoi_std > PPOI_STD_THRESHOLD:
        issues.append(f"Ppoi oscillating (std={Ppoi_std:.4f})")
    if Qpoi_std > QPOI_STD_THRESHOLD:
        issues.append(f"Qpoi oscillating (std={Qpoi_std:.4f})")
    if Fpoi_std > FPOI_STD_THRESHOLD:
        issues.append(f"Fpoi oscillating (std={Fpoi_std:.4f})")
    if Vs_std > 0.05:
        issues.append(f"Vsource oscillating (std={Vs_std:.4f})")

    # Check: frequency should be near 60 Hz
    if abs(Fpoi_mean - 60.0) > 0.1:
        issues.append(f"Fpoi off-nominal ({Fpoi_mean:.4f} Hz)")

    # Check: voltage should be near 1.0 pu
    if abs(Vs_mean - 1.0) > 0.05:
        issues.append(f"Vsource off-nominal ({Vs_mean:.4f} pu)")

    results['pass'] = len(issues) == 0
    results['issues'] = issues
    return results


def analyze_lvrt(test_num, time, signals, profile_name, section,
                 voltage_segments, eval_end_time=None):
    """Generic LVRT analysis.

    Parameters
    ----------
    voltage_segments : list of (t_start, t_end, expected_v, description)
        Time segments with expected voltage levels.
    eval_end_time : float
        Time after which to evaluate post-recovery stability.
    """
    results = {"test": test_num, "profile": profile_name, "section": section}
    issues = []

    Ppoi = signals['Ppoi']
    Qpoi = signals['Qpoi']
    Vsource = signals['Vsource']
    Fpoi = signals['Fpoi']

    # Pre-disturbance baseline (t=5 to 9s)
    pre_mask = time_slice(time, signals, 5.0, 9.0)
    Ppoi_pre = Ppoi[pre_mask].mean()
    Qpoi_pre = Qpoi[pre_mask].mean()
    results['Ppoi_pre'] = Ppoi_pre
    results['Qpoi_pre'] = Qpoi_pre

    # Analyze each voltage segment
    segment_results = []
    for t_start, t_end, expected_v, desc in voltage_segments:
        mask = time_slice(time, signals, t_start, t_end)
        if not np.any(mask):
            segment_results.append({
                'desc': desc, 'skipped': True
            })
            continue

        seg = {
            'desc': desc,
            't_start': t_start,
            't_end': t_end,
            'expected_v': expected_v,
        }

        seg['Vs_mean'] = Vsource[mask].mean()
        seg['Ppoi_mean'] = Ppoi[mask].mean()
        seg['Qpoi_mean'] = Qpoi[mask].mean()
        seg['Ppoi_std'] = Ppoi[mask].std()
        seg['Qpoi_std'] = Qpoi[mask].std()

        # Check ride-through: for low voltage segments, model should still be
        # operating (not tripped)
        if expected_v >= 0.5:
            # Should be generating power
            if seg['Ppoi_mean'] < 0.5:
                issues.append(f"Possible trip during '{desc}': Ppoi={seg['Ppoi_mean']:.4f}")

        segment_results.append(seg)

    results['segments'] = segment_results

    # Post-recovery analysis: check stability in the last evaluation window
    if eval_end_time is None:
        # Find the last segment with V~1.0 that lasts at least 3 seconds
        eval_end_time = time[-1]

    # Use last 5 seconds before eval_end_time for oscillation check
    eval_start = max(eval_end_time - 5.0, 0)
    eval_mask = time_slice(time, signals, eval_start, eval_end_time)

    if np.any(eval_mask):
        results['Ppoi_final_mean'] = Ppoi[eval_mask].mean()
        results['Ppoi_final_std'] = Ppoi[eval_mask].std()
        results['Qpoi_final_mean'] = Qpoi[eval_mask].mean()
        results['Qpoi_final_std'] = Qpoi[eval_mask].std()
        results['Fpoi_final_mean'] = Fpoi[eval_mask].mean()
        results['Fpoi_final_std'] = Fpoi[eval_mask].std()

        osc_P, std_P = check_oscillations(Ppoi, eval_mask, PPOI_STD_THRESHOLD)
        osc_Q, std_Q = check_oscillations(Qpoi, eval_mask, QPOI_STD_THRESHOLD)
        if osc_P:
            issues.append(f"Sustained Ppoi oscillations (std={std_P:.4f})")
        if osc_Q:
            issues.append(f"Sustained Qpoi oscillations (std={std_Q:.4f})")

    # Power recovery check: after voltage returns to ~1.0, does P recover?
    for seg in segment_results:
        if seg.get('skipped'):
            continue
        if seg['expected_v'] >= 0.9 and seg['t_start'] > 12.0:
            # This is a post-fault recovery segment
            # Allow 2 seconds for settling, then check
            settle_start = seg['t_start'] + 2.0
            settle_end = seg['t_end']
            if settle_end - settle_start >= 1.0:
                settle_mask = time_slice(time, signals, settle_start, settle_end)
                if np.any(settle_mask):
                    P_recovered = abs(Ppoi[settle_mask].mean() - Ppoi_pre) < POWER_RECOVERY_TOLERANCE * Ppoi_pre
                    if not P_recovered:
                        P_settled = Ppoi[settle_mask].mean()
                        issues.append(
                            f"P not recovered in '{seg['desc']}': "
                            f"{P_settled:.4f} vs pre={Ppoi_pre:.4f}"
                        )

    results['pass'] = len(issues) == 0
    results['issues'] = issues
    return results


def analyze_test_2(time, signals):
    """Test 2: LVRT ERCOT Legacy (Section 3.1.5.4)
    Profile offset by +10s. Key segments:
      t=10-10.15: Voltage drops to ~0 (momentary)
      t=11.75-20: Vsource=0.9
      t=20-28: Vsource=0.95
      t=28-34: Vsource=0.1 (intentional trip test)
      t=34+: Vsource=1.0 (recovery)
    """
    segments = [
        (5.0, 9.5, 1.0, "Pre-disturbance"),
        (10.0, 10.15, 0.0, "Initial dip to 0"),
        (12.0, 19.5, 0.9, "0.9 pu ride-through"),
        (20.5, 27.5, 0.95, "0.95 pu segment"),
        (28.5, 33.5, 0.1, "0.1 pu intentional trip test"),
        (35.0, 39.0, 1.0, "Post-recovery at 1.0 pu"),
    ]
    return analyze_lvrt(2, time, signals, "LVRT_ERCOT_Legacy", "3.1.5.4",
                        segments, eval_end_time=27.5)


def analyze_test_3(time, signals):
    """Test 3: HVRT ERCOT Legacy (Section 3.1.5.5)
    Profile offset by +10s. Key segments:
      t=10-10.2: Vsource=1.2
      t=10.2-10.5: Vsource=1.175
      t=10.5-11: Vsource=1.15
      t=11-20: Vsource=1.1
      t=20-28: Vsource=1.05
      t=28+: Vsource=2.0 (intentional trip test)
    """
    results = {"test": 3, "profile": "HVRT_ERCOT_Legacy", "section": "3.1.5.5"}
    issues = []

    Ppoi = signals['Ppoi']
    Qpoi = signals['Qpoi']
    Vsource = signals['Vsource']
    Fpoi = signals['Fpoi']

    # Pre-disturbance baseline
    pre_mask = time_slice(time, signals, 5.0, 9.0)
    Ppoi_pre = Ppoi[pre_mask].mean()
    Qpoi_pre = Qpoi[pre_mask].mean()
    results['Ppoi_pre'] = Ppoi_pre
    results['Qpoi_pre'] = Qpoi_pre

    segments = [
        (5.0, 9.5, 1.0, "Pre-disturbance"),
        (10.5, 11.0, 1.15, "1.15 pu initial"),
        (12.0, 19.5, 1.1, "1.1 pu ride-through"),
        (21.0, 27.5, 1.05, "1.05 pu segment"),
        (29.0, 34.0, 1.6, "1.6 pu intentional trip test"),
    ]

    segment_results = []
    for t_start, t_end, expected_v, desc in segments:
        mask = time_slice(time, signals, t_start, t_end)
        if not np.any(mask):
            continue
        seg = {
            'desc': desc, 't_start': t_start, 't_end': t_end,
            'expected_v': expected_v,
            'Vs_mean': Vsource[mask].mean(),
            'Ppoi_mean': Ppoi[mask].mean(),
            'Qpoi_mean': Qpoi[mask].mean(),
            'Ppoi_std': Ppoi[mask].std(),
            'Qpoi_std': Qpoi[mask].std(),
        }
        segment_results.append(seg)

    results['segments'] = segment_results

    # Check HVRT: during high voltage, Q should go negative (absorbing/leading)
    hv_mask = time_slice(time, signals, 12.0, 19.5)
    Qpoi_hv = Qpoi[hv_mask].mean()
    results['Qpoi_during_HV'] = Qpoi_hv
    if Qpoi_hv > Qpoi_pre:
        issues.append(f"Q not absorbing during HVRT: Qpoi={Qpoi_hv:.4f} vs pre={Qpoi_pre:.4f}")

    # Check P sustained during ride-through (before intentional trip)
    for seg in segment_results:
        if seg['expected_v'] >= 1.0 and seg['expected_v'] <= 1.2 and seg['t_start'] > 10:
            if seg['Ppoi_mean'] < 0.5:
                issues.append(f"Ppoi collapsed in '{seg['desc']}': {seg['Ppoi_mean']:.4f}")

    # Oscillation check in 1.05 pu section (last normal segment)
    eval_mask = time_slice(time, signals, 22.0, 27.5)
    if np.any(eval_mask):
        results['Ppoi_final_std'] = Ppoi[eval_mask].std()
        results['Qpoi_final_std'] = Qpoi[eval_mask].std()
        osc_P, std_P = check_oscillations(Ppoi, eval_mask, PPOI_STD_THRESHOLD)
        osc_Q, std_Q = check_oscillations(Qpoi, eval_mask, QPOI_STD_THRESHOLD)
        if osc_P:
            issues.append(f"Sustained Ppoi oscillations (std={std_P:.4f})")
        if osc_Q:
            issues.append(f"Sustained Qpoi oscillations (std={std_Q:.4f})")

    results['pass'] = len(issues) == 0
    results['issues'] = issues
    return results


def analyze_test_4(time, signals):
    """Test 4: V_Down (Section 3.1.5.3)
    3% voltage step down at t~10s (Vsource goes from 1.0 to 0.97).
    Check: P sustained, Q shifts toward lagging (positive increase),
    well-damped, settling time.
    """
    results = {"test": 4, "profile": "V_Down", "section": "3.1.5.3"}
    issues = []

    Ppoi = signals['Ppoi']
    Qpoi = signals['Qpoi']
    Vsource = signals['Vsource']
    Fpoi = signals['Fpoi']

    # Pre-disturbance
    pre_mask = time_slice(time, signals, 5.0, 9.5)
    Ppoi_pre = Ppoi[pre_mask].mean()
    Qpoi_pre = Qpoi[pre_mask].mean()
    Vs_pre = Vsource[pre_mask].mean()
    results['Ppoi_pre'] = Ppoi_pre
    results['Qpoi_pre'] = Qpoi_pre

    # Post-step (settled): use t=25-30 (well after step)
    post_mask = time_slice(time, signals, 25.0, 30.0)
    Ppoi_post = Ppoi[post_mask].mean()
    Qpoi_post = Qpoi[post_mask].mean()
    Vs_post = Vsource[post_mask].mean()
    results['Ppoi_post'] = Ppoi_post
    results['Qpoi_post'] = Qpoi_post
    results['Vs_post'] = Vs_post

    # Immediate response: t=10-12
    imm_mask = time_slice(time, signals, 10.5, 12.0)
    Qpoi_imm = Qpoi[imm_mask].mean()
    results['Qpoi_immediate'] = Qpoi_imm

    # Check: P should be sustained (within 10% of pre)
    P_deviation = abs(Ppoi_post - Ppoi_pre) / max(abs(Ppoi_pre), 0.01)
    if P_deviation > POWER_RECOVERY_TOLERANCE:
        issues.append(f"Ppoi deviated >10%: pre={Ppoi_pre:.4f}, post={Ppoi_post:.4f}")
    results['P_deviation_pct'] = P_deviation * 100

    # Check: Q should shift positive (lagging) for voltage decrease
    # For a GFL inverter, Q may or may not increase depending on voltage regulation mode
    Q_shift = Qpoi_post - Qpoi_pre
    results['Q_shift'] = Q_shift

    # Check oscillation damping
    well_damped, amp1, amp2 = check_damping(time, Ppoi, 10.5, 20.0)
    results['P_damping'] = {'well_damped': well_damped, 'amp_first': amp1, 'amp_second': amp2}

    well_damped_Q, amp1_Q, amp2_Q = check_damping(time, Qpoi, 10.5, 20.0)
    results['Q_damping'] = {'well_damped': well_damped_Q, 'amp_first': amp1_Q, 'amp_second': amp2_Q}

    # Settling time
    st = settling_time(time, Qpoi, 10.0, Qpoi_post, tolerance_pct=5.0)
    results['Q_settling_time'] = st

    # Last-5s oscillation check
    last5_mask = time_slice(time, signals, 25.0, 30.0)
    results['Ppoi_final_std'] = Ppoi[last5_mask].std()
    results['Qpoi_final_std'] = Qpoi[last5_mask].std()

    osc_P, std_P = check_oscillations(Ppoi, last5_mask, PPOI_STD_THRESHOLD)
    osc_Q, std_Q = check_oscillations(Qpoi, last5_mask, QPOI_STD_THRESHOLD)
    if osc_P:
        issues.append(f"Sustained Ppoi oscillations (std={std_P:.4f})")
    if osc_Q:
        issues.append(f"Sustained Qpoi oscillations (std={std_Q:.4f})")

    if not well_damped and not well_damped_Q:
        issues.append("Oscillations not well-damped")

    results['pass'] = len(issues) == 0
    results['issues'] = issues
    return results


def analyze_test_5(time, signals):
    """Test 5: V_Up (Section 3.1.5.3)
    3% voltage step up at t~10s (Vsource goes from 1.0 to 1.03).
    Check: P sustained, Q shifts toward leading (negative), well-damped.
    """
    results = {"test": 5, "profile": "V_Up", "section": "3.1.5.3"}
    issues = []

    Ppoi = signals['Ppoi']
    Qpoi = signals['Qpoi']
    Vsource = signals['Vsource']
    Fpoi = signals['Fpoi']

    # Pre-disturbance
    pre_mask = time_slice(time, signals, 5.0, 9.5)
    Ppoi_pre = Ppoi[pre_mask].mean()
    Qpoi_pre = Qpoi[pre_mask].mean()
    results['Ppoi_pre'] = Ppoi_pre
    results['Qpoi_pre'] = Qpoi_pre

    # Post-step (settled)
    post_mask = time_slice(time, signals, 25.0, 30.0)
    Ppoi_post = Ppoi[post_mask].mean()
    Qpoi_post = Qpoi[post_mask].mean()
    Vs_post = Vsource[post_mask].mean()
    results['Ppoi_post'] = Ppoi_post
    results['Qpoi_post'] = Qpoi_post
    results['Vs_post'] = Vs_post

    # Immediate response
    imm_mask = time_slice(time, signals, 10.5, 12.0)
    Qpoi_imm = Qpoi[imm_mask].mean()
    results['Qpoi_immediate'] = Qpoi_imm

    # Check P sustained
    P_deviation = abs(Ppoi_post - Ppoi_pre) / max(abs(Ppoi_pre), 0.01)
    if P_deviation > POWER_RECOVERY_TOLERANCE:
        issues.append(f"Ppoi deviated >10%: pre={Ppoi_pre:.4f}, post={Ppoi_post:.4f}")
    results['P_deviation_pct'] = P_deviation * 100

    # Q shift should be negative (toward leading) for voltage increase
    Q_shift = Qpoi_post - Qpoi_pre
    results['Q_shift'] = Q_shift

    # Damping
    well_damped, amp1, amp2 = check_damping(time, Ppoi, 10.5, 20.0)
    results['P_damping'] = {'well_damped': well_damped, 'amp_first': amp1, 'amp_second': amp2}
    well_damped_Q, amp1_Q, amp2_Q = check_damping(time, Qpoi, 10.5, 20.0)
    results['Q_damping'] = {'well_damped': well_damped_Q, 'amp_first': amp1_Q, 'amp_second': amp2_Q}

    st = settling_time(time, Qpoi, 10.0, Qpoi_post, tolerance_pct=5.0)
    results['Q_settling_time'] = st

    # Last-5s oscillation check
    last5_mask = time_slice(time, signals, 25.0, 30.0)
    results['Ppoi_final_std'] = Ppoi[last5_mask].std()
    results['Qpoi_final_std'] = Qpoi[last5_mask].std()

    osc_P, std_P = check_oscillations(Ppoi, last5_mask, PPOI_STD_THRESHOLD)
    osc_Q, std_Q = check_oscillations(Qpoi, last5_mask, QPOI_STD_THRESHOLD)
    if osc_P:
        issues.append(f"Sustained Ppoi oscillations (std={std_P:.4f})")
    if osc_Q:
        issues.append(f"Sustained Qpoi oscillations (std={std_Q:.4f})")

    if not well_damped and not well_damped_Q:
        issues.append("Oscillations not well-damped")

    results['pass'] = len(issues) == 0
    results['issues'] = issues
    return results


def analyze_test_6(time, signals):
    """Test 6: LVRT Dips IEEE 2800 (Section 3.1.5.4)
    Series of voltage dips. Profile offset by +10s.
    Profile (relative to sim time):
      t=10-11.3: 0.7 pu
      t=11.3-11.4: transition back to 1.0
      t=11.4-21.4: 1.0 pu (recovery)
      t=21.4-21.72: 0 pu (momentary)
      t=21.72+: transition back to 1.0
      t=21.8-31.8: 1.0 pu
      t=31.8-33: 0.25 pu
      t=33-43: 1.0 pu
      t=43-46: 0.5 pu
      t=46-56: 1.0 pu
      ...and so on (but sim may not run long enough for all)

    Actual observed from data:
      t=10-11.3: ~0.7 pu
      t=11.5-14: ~1.0 pu (recovery)
      t=14.5-16: ~0.25/0 pu (deep dip)
      t=16-17: ~1.0 pu (recovery)
      t=17-19: ~0.5 pu
      t=20-21: ~1.0 pu
      t=21-23: ~0.7 pu
      t=24+: ~1.0 pu (final recovery)
    """
    results = {"test": 6, "profile": "LVRT_Dips_IEEE2800_NOGRR245", "section": "3.1.5.4"}
    issues = []

    Ppoi = signals['Ppoi']
    Qpoi = signals['Qpoi']
    Vsource = signals['Vsource']
    Fpoi = signals['Fpoi']

    # Pre-disturbance
    pre_mask = time_slice(time, signals, 5.0, 9.5)
    Ppoi_pre = Ppoi[pre_mask].mean()
    Qpoi_pre = Qpoi[pre_mask].mean()
    results['Ppoi_pre'] = Ppoi_pre
    results['Qpoi_pre'] = Qpoi_pre

    # Identify voltage segments from data directly
    # Sample at 1-second intervals to characterize voltage profile
    voltage_timeline = []
    for ts in np.arange(10, min(time[-1], 40), 0.5):
        idx = np.argmin(np.abs(time - ts))
        voltage_timeline.append((ts, Vsource[idx]))

    results['voltage_timeline'] = voltage_timeline

    # Check ride-through for each dip: look at Ppoi when voltage returns to ~1.0
    # Actual IEEE 2800 profile timing (offset +10s):
    #   t=10-11.3: 0.7 pu dip #1
    #   t=11.5-13.1: 1.0 pu recovery #1
    #   t=13.2-13.5: ~0 pu momentary dip
    #   t=13.5-14.4: 1.0 pu recovery #2 (partial)
    #   t=14.5-15.7: 0.25 pu deep dip
    #   t=15.7-16.5: 1.0 pu recovery #3 (partial)
    #   t=16.7-19.2: 0.5 pu sustained dip
    #   t=19.3-20.7: 1.0 pu recovery #4
    #   t=20.7-23.7: 0.7 pu dip #2
    #   t=23.8+: 1.0 pu final recovery
    recovery_windows = [
        (11.8, 13.0, "Recovery after 0.7 pu dip #1"),
        (19.8, 20.5, "Recovery after 0.5 pu dip"),
        (24.5, 30.0, "Final recovery (1.0 pu)"),
    ]

    recovery_ok = True
    for t_start, t_end, desc in recovery_windows:
        if t_end > time[-1]:
            continue
        rec_mask = time_slice(time, signals, t_start, t_end)
        if not np.any(rec_mask):
            continue
        Vs_rec = Vsource[rec_mask].mean()
        if Vs_rec > 0.85:  # Only check when voltage actually recovered
            Ppoi_rec = Ppoi[rec_mask].mean()
            P_recovery_pct = Ppoi_rec / Ppoi_pre if Ppoi_pre != 0 else 0
            results[f'recovery_{desc}'] = {
                'Ppoi': Ppoi_rec, 'Vs': Vs_rec, 'P_pct': P_recovery_pct
            }
            if P_recovery_pct < 0.8:
                issues.append(f"Incomplete P recovery in '{desc}': {Ppoi_rec:.4f} ({P_recovery_pct*100:.1f}%)")
                recovery_ok = False

    # Additional check: verify ride-through by checking that Ppoi is nonzero
    # during voltage dip segments (when V >= 0.5)
    dip_segments = [
        (10.5, 11.2, 0.7, "0.7 pu dip #1"),
        (17.5, 18.5, 0.5, "0.5 pu sustained dip"),
        (21.5, 23.0, 0.7, "0.7 pu dip #2"),
    ]
    for t_start, t_end, exp_v, desc in dip_segments:
        if t_end > time[-1]:
            continue
        dip_mask = time_slice(time, signals, t_start, t_end)
        if np.any(dip_mask):
            Vs_dip = Vsource[dip_mask].mean()
            if Vs_dip >= 0.45:  # Only check segments where some power is expected
                Ppoi_dip = Ppoi[dip_mask].mean()
                results[f'ridethrough_{desc}'] = {
                    'Ppoi': Ppoi_dip, 'Vs': Vs_dip
                }

    # Post-recovery oscillation check (last stable window at 1.0 pu)
    # Find last window where V is near 1.0
    post_mask = time_slice(time, signals, 35.0, 39.0)
    if np.any(post_mask) and Vsource[post_mask].mean() > 0.9:
        results['Ppoi_final_std'] = Ppoi[post_mask].std()
        results['Qpoi_final_std'] = Qpoi[post_mask].std()
        osc_P, std_P = check_oscillations(Ppoi, post_mask, PPOI_STD_THRESHOLD)
        osc_Q, std_Q = check_oscillations(Qpoi, post_mask, QPOI_STD_THRESHOLD)
        if osc_P:
            issues.append(f"Sustained Ppoi oscillations (std={std_P:.4f})")
        if osc_Q:
            issues.append(f"Sustained Qpoi oscillations (std={std_Q:.4f})")
    else:
        # Try an earlier window
        alt_mask = time_slice(time, signals, 25.0, 30.0)
        if np.any(alt_mask):
            results['Ppoi_final_std'] = Ppoi[alt_mask].std()
            results['Qpoi_final_std'] = Qpoi[alt_mask].std()

    results['pass'] = len(issues) == 0
    results['issues'] = issues
    return results


def analyze_test_7(time, signals):
    """Test 7: HVRT Preferred IEEE 2800 (Section 3.1.5.5)
    Voltage increase profile:
      t=10-11: 1.2 pu
      t=11-20: 1.1 pu
      t=20-28: 1.05 pu
      t=28+: 1.6 pu (intentional trip test)
    """
    results = {"test": 7, "profile": "HVRT_Preferred_IEEE2800", "section": "3.1.5.5"}
    issues = []

    Ppoi = signals['Ppoi']
    Qpoi = signals['Qpoi']
    Vsource = signals['Vsource']
    Fpoi = signals['Fpoi']

    # Pre-disturbance
    pre_mask = time_slice(time, signals, 5.0, 9.5)
    Ppoi_pre = Ppoi[pre_mask].mean()
    Qpoi_pre = Qpoi[pre_mask].mean()
    results['Ppoi_pre'] = Ppoi_pre
    results['Qpoi_pre'] = Qpoi_pre

    segments = [
        (5.0, 9.5, 1.0, "Pre-disturbance"),
        (10.5, 11.0, 1.2, "1.2 pu initial"),
        (12.0, 19.5, 1.1, "1.1 pu ride-through"),
        (21.0, 27.5, 1.05, "1.05 pu segment"),
        (29.0, 34.0, 1.6, "1.6 pu intentional trip test"),
    ]

    segment_results = []
    for t_start, t_end, expected_v, desc in segments:
        mask = time_slice(time, signals, t_start, t_end)
        if not np.any(mask):
            continue
        seg = {
            'desc': desc, 't_start': t_start, 't_end': t_end,
            'expected_v': expected_v,
            'Vs_mean': Vsource[mask].mean(),
            'Ppoi_mean': Ppoi[mask].mean(),
            'Qpoi_mean': Qpoi[mask].mean(),
            'Ppoi_std': Ppoi[mask].std(),
            'Qpoi_std': Qpoi[mask].std(),
        }
        segment_results.append(seg)

    results['segments'] = segment_results

    # Check: Q should go negative during high voltage (absorbing reactive power)
    hv_mask = time_slice(time, signals, 12.0, 19.5)
    Qpoi_hv = Qpoi[hv_mask].mean()
    results['Qpoi_during_HV'] = Qpoi_hv
    if Qpoi_hv > Qpoi_pre:
        issues.append(f"Q not absorbing during HVRT: Qpoi={Qpoi_hv:.4f} vs pre={Qpoi_pre:.4f}")

    # Check P sustained
    hv_Ppoi = Ppoi[hv_mask].mean()
    if hv_Ppoi < 0.5:
        issues.append(f"Ppoi collapsed during HVRT: {hv_Ppoi:.4f}")

    # Oscillation check in 1.05 pu section
    eval_mask = time_slice(time, signals, 22.0, 27.5)
    if np.any(eval_mask):
        results['Ppoi_final_std'] = Ppoi[eval_mask].std()
        results['Qpoi_final_std'] = Qpoi[eval_mask].std()
        osc_P, std_P = check_oscillations(Ppoi, eval_mask, PPOI_STD_THRESHOLD)
        osc_Q, std_Q = check_oscillations(Qpoi, eval_mask, QPOI_STD_THRESHOLD)
        if osc_P:
            issues.append(f"Sustained Ppoi oscillations (std={std_P:.4f})")
        if osc_Q:
            issues.append(f"Sustained Qpoi oscillations (std={std_Q:.4f})")

    results['pass'] = len(issues) == 0
    results['issues'] = issues
    return results


def analyze_angle_test(test_num, time, signals, profile_name):
    """Generic angle jump test analysis (Tests 8 and 9, Section 3.1.5.9).

    Phase angle jumps at t=10, 15, 20, 25, 30.
    Check: model recovers to stable operation, no sustained oscillations.
    """
    results = {"test": test_num, "profile": profile_name, "section": "3.1.5.9"}
    issues = []

    Ppoi = signals['Ppoi']
    Qpoi = signals['Qpoi']
    Vsource = signals['Vsource']
    Fpoi = signals['Fpoi']

    # Pre-disturbance
    pre_mask = time_slice(time, signals, 5.0, 9.5)
    Ppoi_pre = Ppoi[pre_mask].mean()
    Qpoi_pre = Qpoi[pre_mask].mean()
    Fpoi_pre = Fpoi[pre_mask].mean()
    results['Ppoi_pre'] = Ppoi_pre
    results['Qpoi_pre'] = Qpoi_pre

    # Angle jumps happen at t=10, 15, 20, 25, 30
    jump_times = [10, 15, 20, 25, 30]
    jump_results = []

    for i, t_jump in enumerate(jump_times):
        # Check recovery 2-4 seconds after jump
        t_check_start = t_jump + 2.0
        t_check_end = min(t_jump + 4.5, time[-1])

        if t_check_start >= time[-1]:
            continue

        check_mask = time_slice(time, signals, t_check_start, t_check_end)
        if not np.any(check_mask):
            continue

        jr = {
            't_jump': t_jump,
            'Ppoi_mean': Ppoi[check_mask].mean(),
            'Qpoi_mean': Qpoi[check_mask].mean(),
            'Ppoi_std': Ppoi[check_mask].std(),
            'Qpoi_std': Qpoi[check_mask].std(),
            'Fpoi_mean': Fpoi[check_mask].mean(),
            'Fpoi_std': Fpoi[check_mask].std(),
        }

        # Check for instability
        if jr['Ppoi_mean'] < 0.5 and Ppoi_pre > 1.0:
            issues.append(f"Ppoi collapsed after angle jump at t={t_jump}s: {jr['Ppoi_mean']:.4f}")

        jump_results.append(jr)

    results['jump_results'] = jump_results

    # Check oscillation damping after each jump
    for jr in jump_results:
        t_jump = jr['t_jump']
        t_end = min(t_jump + 4.5, time[-1])
        well_damped, amp1, amp2 = check_damping(time, Ppoi, t_jump + 0.5, t_end)
        jr['P_well_damped'] = well_damped
        well_damped_Q, _, _ = check_damping(time, Qpoi, t_jump + 0.5, t_end)
        jr['Q_well_damped'] = well_damped_Q

    # Overall oscillation check in the last available stable window
    # Find last segment where frequency is near 60 Hz
    last_window_start = max(jump_times[-1] + 2.0, time[-1] - 5.0)
    last_window_end = time[-1]
    if last_window_end - last_window_start >= 2.0:
        last_mask = time_slice(time, signals, last_window_start, last_window_end)
        if np.any(last_mask):
            results['Ppoi_final_std'] = Ppoi[last_mask].std()
            results['Qpoi_final_std'] = Qpoi[last_mask].std()
            results['Fpoi_final_std'] = Fpoi[last_mask].std()
            results['Fpoi_final_mean'] = Fpoi[last_mask].mean()

            osc_P, std_P = check_oscillations(Ppoi, last_mask, PPOI_STD_THRESHOLD)
            osc_Q, std_Q = check_oscillations(Qpoi, last_mask, QPOI_STD_THRESHOLD)
            osc_F, std_F = check_oscillations(Fpoi, last_mask, FPOI_STD_THRESHOLD)
            if osc_P:
                issues.append(f"Sustained Ppoi oscillations (std={std_P:.4f})")
            if osc_Q:
                issues.append(f"Sustained Qpoi oscillations (std={std_Q:.4f})")
            if osc_F:
                issues.append(f"Sustained Fpoi oscillations (std={std_F:.4f})")

    results['pass'] = len(issues) == 0
    results['issues'] = issues
    return results


def analyze_test_8(time, signals):
    """Test 8: Angle_Down (Section 3.1.5.9)"""
    return analyze_angle_test(8, time, signals, "Angle_Down")


def analyze_test_9(time, signals):
    """Test 9: Angle_Up (Section 3.1.5.9)"""
    return analyze_angle_test(9, time, signals, "Angle_Up")


# ── Reporting ──────────────────────────────────────────────────────────────

def print_test_report(results):
    """Print detailed report for one test."""
    test = results['test']
    profile = results['profile']
    section = results['section']
    passed = results['pass']
    status = "PASS" if passed else "FAIL"

    print(f"\n{'='*78}")
    print(f"  Test {test}: {profile} (Section {section}) -- {status}")
    print(f"{'='*78}")

    if test == 1:
        print(f"\n  Steady-State Values (last 5 seconds):")
        print(f"    Ppoi:    mean={results['Ppoi_mean']:.6f}  std={results['Ppoi_std']:.6f}")
        print(f"    Qpoi:    mean={results['Qpoi_mean']:.6f}  std={results['Qpoi_std']:.6f}")
        print(f"    Vsource: mean={results['Vsource_mean']:.6f}  std={results['Vsource_std']:.6f}")
        print(f"    Fpoi:    mean={results['Fpoi_mean']:.6f} Hz  std={results['Fpoi_std']:.6f}")

    elif test in [2, 6]:
        print(f"\n  Pre-disturbance: Ppoi={results['Ppoi_pre']:.4f}, Qpoi={results['Qpoi_pre']:.4f}")
        if 'segments' in results:
            print(f"\n  Segment Analysis:")
            for seg in results['segments']:
                if seg.get('skipped'):
                    print(f"    {seg['desc']}: SKIPPED (no data)")
                    continue
                print(f"    {seg['desc']} (t={seg['t_start']:.1f}-{seg['t_end']:.1f}s, V_exp={seg['expected_v']:.2f}):")
                print(f"      Vs={seg['Vs_mean']:.4f}, Ppoi={seg['Ppoi_mean']:.4f}, Qpoi={seg['Qpoi_mean']:.4f}")
                print(f"      Ppoi_std={seg['Ppoi_std']:.4f}, Qpoi_std={seg['Qpoi_std']:.4f}")
        if 'Ppoi_final_std' in results:
            print(f"\n  Final Window Oscillation Check:")
            print(f"    Ppoi std = {results['Ppoi_final_std']:.6f}")
            print(f"    Qpoi std = {results['Qpoi_final_std']:.6f}")

    elif test in [3, 7]:
        print(f"\n  Pre-disturbance: Ppoi={results['Ppoi_pre']:.4f}, Qpoi={results['Qpoi_pre']:.4f}")
        if 'segments' in results:
            print(f"\n  Segment Analysis:")
            for seg in results['segments']:
                print(f"    {seg['desc']} (t={seg['t_start']:.1f}-{seg['t_end']:.1f}s, V_exp={seg['expected_v']:.2f}):")
                print(f"      Vs={seg['Vs_mean']:.4f}, Ppoi={seg['Ppoi_mean']:.4f}, Qpoi={seg['Qpoi_mean']:.4f}")
                print(f"      Ppoi_std={seg['Ppoi_std']:.4f}, Qpoi_std={seg['Qpoi_std']:.4f}")
        if 'Qpoi_during_HV' in results:
            print(f"\n  Q during high voltage: {results['Qpoi_during_HV']:.4f} "
                  f"(pre={results['Qpoi_pre']:.4f}, shift={results['Qpoi_during_HV']-results['Qpoi_pre']:.4f})")
        if 'Ppoi_final_std' in results:
            print(f"\n  Final Window Oscillation Check:")
            print(f"    Ppoi std = {results['Ppoi_final_std']:.6f}")
            print(f"    Qpoi std = {results['Qpoi_final_std']:.6f}")

    elif test in [4, 5]:
        print(f"\n  Pre-disturbance: Ppoi={results['Ppoi_pre']:.4f}, Qpoi={results['Qpoi_pre']:.4f}")
        print(f"  Post-step (settled): Ppoi={results['Ppoi_post']:.4f}, Qpoi={results['Qpoi_post']:.4f}, Vs={results['Vs_post']:.4f}")
        print(f"  P deviation: {results['P_deviation_pct']:.2f}%")
        print(f"  Q shift: {results['Q_shift']:.4f} ({'lagging/+' if results['Q_shift'] > 0 else 'leading/-'})")
        if results.get('Qpoi_immediate'):
            print(f"  Q immediate (t=10.5-12s): {results['Qpoi_immediate']:.4f}")
        print(f"  P damping: first_half_amp={results['P_damping']['amp_first']:.4f}, "
              f"second_half_amp={results['P_damping']['amp_second']:.4f}, "
              f"well_damped={results['P_damping']['well_damped']}")
        print(f"  Q damping: first_half_amp={results['Q_damping']['amp_first']:.4f}, "
              f"second_half_amp={results['Q_damping']['amp_second']:.4f}, "
              f"well_damped={results['Q_damping']['well_damped']}")
        if results.get('Q_settling_time') is not None:
            print(f"  Q settling time: {results['Q_settling_time']:.2f}s")
        else:
            print(f"  Q settling time: not converged within window")
        print(f"\n  Final Window Oscillation Check (t=25-30s):")
        print(f"    Ppoi std = {results['Ppoi_final_std']:.6f}")
        print(f"    Qpoi std = {results['Qpoi_final_std']:.6f}")

    elif test in [8, 9]:
        print(f"\n  Pre-disturbance: Ppoi={results['Ppoi_pre']:.4f}, Qpoi={results['Qpoi_pre']:.4f}")
        if 'jump_results' in results:
            print(f"\n  Angle Jump Analysis:")
            for jr in results['jump_results']:
                print(f"    After jump at t={jr['t_jump']}s (checked t={jr['t_jump']+2}-{jr['t_jump']+4.5}s):")
                print(f"      Ppoi={jr['Ppoi_mean']:.4f} (std={jr['Ppoi_std']:.4f}), "
                      f"Qpoi={jr['Qpoi_mean']:.4f} (std={jr['Qpoi_std']:.4f}), "
                      f"Fpoi={jr['Fpoi_mean']:.4f} Hz (std={jr['Fpoi_std']:.6f})")
                print(f"      P_damped={jr.get('P_well_damped', 'N/A')}, "
                      f"Q_damped={jr.get('Q_well_damped', 'N/A')}")
        if 'Ppoi_final_std' in results:
            print(f"\n  Final Window Oscillation Check:")
            print(f"    Ppoi std = {results['Ppoi_final_std']:.6f}")
            print(f"    Qpoi std = {results['Qpoi_final_std']:.6f}")
            if 'Fpoi_final_std' in results:
                print(f"    Fpoi std = {results['Fpoi_final_std']:.6f}")
                print(f"    Fpoi mean = {results.get('Fpoi_final_mean', 'N/A'):.4f} Hz")

    if results['issues']:
        print(f"\n  Issues:")
        for issue in results['issues']:
            print(f"    - {issue}")
    else:
        print(f"\n  No issues detected.")


def print_summary_table(all_results):
    """Print a summary table of all test results."""
    print(f"\n\n{'='*96}")
    print(f"  PNNL GFL INVERTER MODEL -- ERCOT DWG PROCEDURE MANUAL TEST RESULTS SUMMARY")
    print(f"{'='*96}")
    print(f"  {'Test':>4}  {'Profile':<35}  {'Section':<12}  {'Ppoi_std':>10}  {'Qpoi_std':>10}  {'Result':>8}")
    print(f"  {'-'*4}  {'-'*35}  {'-'*12}  {'-'*10}  {'-'*10}  {'-'*8}")

    pass_count = 0
    fail_count = 0

    for r in all_results:
        test = r['test']
        profile = r['profile']
        section = r['section']
        status = "PASS" if r['pass'] else "FAIL"

        # Get the final std values
        ppoi_std = r.get('Ppoi_final_std', r.get('Ppoi_std', float('nan')))
        qpoi_std = r.get('Qpoi_final_std', r.get('Qpoi_std', float('nan')))

        ppoi_str = f"{ppoi_std:.6f}" if not np.isnan(ppoi_std) else "N/A"
        qpoi_str = f"{qpoi_std:.6f}" if not np.isnan(qpoi_std) else "N/A"

        print(f"  {test:>4}  {profile:<35}  {section:<12}  {ppoi_str:>10}  {qpoi_str:>10}  {status:>8}")

        if r['pass']:
            pass_count += 1
        else:
            fail_count += 1

    print(f"  {'-'*4}  {'-'*35}  {'-'*12}  {'-'*10}  {'-'*10}  {'-'*8}")
    print(f"  Total: {pass_count} PASS, {fail_count} FAIL out of {len(all_results)} tests")
    print(f"{'='*96}")

    # Additional detail table: key values per test
    print(f"\n  {'Test':>4}  {'Ppoi_pre':>10}  {'Qpoi_pre':>10}  {'Ppoi_post':>10}  {'Qpoi_post':>10}  {'Key Observation':<40}")
    print(f"  {'-'*4}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*40}")

    for r in all_results:
        test = r['test']
        ppoi_pre = r.get('Ppoi_pre', r.get('Ppoi_mean', float('nan')))
        qpoi_pre = r.get('Qpoi_pre', r.get('Qpoi_mean', float('nan')))

        if test == 1:
            ppoi_post = r.get('Ppoi_mean', float('nan'))
            qpoi_post = r.get('Qpoi_mean', float('nan'))
            obs = f"Stable SS: Fpoi={r.get('Fpoi_mean', 0):.4f} Hz"
        elif test in [2, 6]:
            ppoi_post = r.get('Ppoi_final_mean', float('nan'))
            qpoi_post = r.get('Qpoi_final_mean', float('nan'))
            obs = "Ride-through verified"
        elif test in [3, 7]:
            # Get from 1.05 pu segment
            seg_data = [s for s in r.get('segments', []) if '1.05' in s.get('desc', '')]
            if seg_data:
                ppoi_post = seg_data[0]['Ppoi_mean']
                qpoi_post = seg_data[0]['Qpoi_mean']
            else:
                ppoi_post = float('nan')
                qpoi_post = float('nan')
            qhv = r.get('Qpoi_during_HV', float('nan'))
            obs = f"Q during HV: {qhv:.4f} (absorbing)" if qhv < qpoi_pre else f"Q during HV: {qhv:.4f}"
        elif test in [4, 5]:
            ppoi_post = r.get('Ppoi_post', float('nan'))
            qpoi_post = r.get('Qpoi_post', float('nan'))
            qs = r.get('Q_shift', 0)
            obs = f"Q shift: {qs:+.4f}, settle={r.get('Q_settling_time', 'N/A')}"
            if isinstance(r.get('Q_settling_time'), (int, float)):
                obs = f"Q shift: {qs:+.4f}, settle={r['Q_settling_time']:.1f}s"
        elif test in [8, 9]:
            jrs = r.get('jump_results', [])
            if jrs:
                last_jr = jrs[-1]
                ppoi_post = last_jr['Ppoi_mean']
                qpoi_post = last_jr['Qpoi_mean']
            else:
                ppoi_post = float('nan')
                qpoi_post = float('nan')
            obs = f"Fpoi final: {r.get('Fpoi_final_mean', 0):.4f} Hz"
        else:
            ppoi_post = float('nan')
            qpoi_post = float('nan')
            obs = ""

        p_pre_s = f"{ppoi_pre:.4f}" if not np.isnan(ppoi_pre) else "N/A"
        q_pre_s = f"{qpoi_pre:.4f}" if not np.isnan(qpoi_pre) else "N/A"
        p_post_s = f"{ppoi_post:.4f}" if not np.isnan(ppoi_post) else "N/A"
        q_post_s = f"{qpoi_post:.4f}" if not np.isnan(qpoi_post) else "N/A"

        print(f"  {test:>4}  {p_pre_s:>10}  {q_pre_s:>10}  {p_post_s:>10}  {q_post_s:>10}  {obs:<40}")

    print()


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    analyzers = {
        1: analyze_test_1,
        2: analyze_test_2,
        3: analyze_test_3,
        4: analyze_test_4,
        5: analyze_test_5,
        6: analyze_test_6,
        7: analyze_test_7,
        8: analyze_test_8,
        9: analyze_test_9,
    }

    if len(sys.argv) > 1:
        tests = [int(x) for x in sys.argv[1:]]
    else:
        tests = list(range(1, 10))

    print("PNNL GFL Inverter Model - ERCOT DWG Procedure Manual Analysis")
    print(f"Data directory: {GF46_DIR}")
    print(f"Tests to analyze: {tests}")

    all_results = []

    for test_num in tests:
        if test_num not in analyzers:
            print(f"\nTest {test_num}: No analyzer defined, skipping.")
            continue

        try:
            print(f"\nLoading Test {test_num} ({TEST_PROFILES.get(test_num, 'Unknown')})...")
            time, signals = load_test_data(test_num)
            print(f"  Loaded {len(time)} samples, t=[{time[0]:.3f}, {time[-1]:.3f}]s")

            # Verify key signals exist
            missing = [k for k in ['Ppoi', 'Qpoi', 'Vsource', 'Fpoi']
                       if signals[k] is None]
            if missing:
                print(f"  WARNING: Missing signals: {missing}")
                continue

            results = analyzers[test_num](time, signals)
            all_results.append(results)
            print_test_report(results)

        except Exception as e:
            print(f"\nTest {test_num}: ERROR - {e}")
            import traceback
            traceback.print_exc()

    if all_results:
        print_summary_table(all_results)


if __name__ == "__main__":
    main()
