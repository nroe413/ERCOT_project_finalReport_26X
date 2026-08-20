"""Plot Tests 4 (V_Down) and 5 (V_Up) for REGFMA1.

PSCAD multi-run sweep wrote T4→r00001 and T5→r00002, so we bypass
plot_gfm_tests.plot_test (which assumes r{test_num:05d}) and wire up
explicit run_id mapping here.
"""
import os
import plot_gfm_tests as pgt

RUN_MAP = {
    8: "r00001",  # Angle_Down
    9: "r00002",  # Angle_Up
}


def plot_with_runid(test_num, run_id):
    profile = pgt.TEST_PROFILES[test_num]
    run_prefix = os.path.join(pgt.GF46_DIR, f"{pgt.RUN_PREFIX_NAME}_{run_id}")
    inf_path = run_prefix + ".inf"

    print(f"\nTest {test_num} ({profile}) via {run_id}")
    channels = pgt.parse_inf(inf_path)
    print(f"  {len(channels)} channels")

    time, data = pgt.read_out_files(run_prefix)
    print(f"  {len(time)} samples, {data.shape[1]} cols, "
          f"t=[{time[0]:.3f},{time[-1]:.3f}]s")

    # Plot directory labeled by TEST NUMBER (not run_id) so downstream
    # scripts find plots under r00004_V_Down / r00005_V_Up conventionally.
    out_id = f"r{test_num:05d}"
    out_dir = os.path.join(pgt.PLOT_DIR, f"{out_id}_{profile}")
    os.makedirs(out_dir, exist_ok=True)

    for fname, title, ch_list, ylabel in pgt.PLOT_GROUPS:
        indices = pgt.find_pmview_channels(channels, ch_list)
        save_path = os.path.join(out_dir, f"{fname}.png")
        pgt.plot_group(time, data, indices,
                       f"{title} \u2014 Test {test_num} ({profile})",
                       ylabel, save_path)

    overlay_path = os.path.join(out_dir, "pq_vrms_overlay.png")
    pgt.plot_overlay(time, data, channels,
                     f"POI Power & Grid Voltage \u2014 Test {test_num} ({profile})",
                     overlay_path)


if __name__ == "__main__":
    for tnum, rid in RUN_MAP.items():
        plot_with_runid(tnum, rid)
    print("\nDone.")
