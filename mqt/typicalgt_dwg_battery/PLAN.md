# TypicalGT Synchronous-Machine Model-Quality Battery (DWG tests 1-9)

Run the ERCOT DWG Rev. 24 model-quality battery on the **Gen-32
synchronous machine** (`IEEE 39 bus TypicalGT.dyr`: GENROU + ESST4B +
GGOV1 + PSS2B, 650 MVA, 230 kV, H = 5.46 s), as a benchmark beside the
grid-forming results in the 26X report Sec. 2.3. Sibling to
[`typicalgt_inertia_validation/`](../typicalgt_inertia_validation/):
same machine, same PMView 3.5 harness, extended from the single inertia
profile to the nine-test battery.

## Rig

[`pscad/`](pscad/) is a **copy** of `TypicalGT_inertia_validation/`
(the original is untouched), modified four ways:

| change | from | to | why |
|---|---|---|---|
| PMView `Vrated` | 345 | **230** kV | machine output bus base (user-confirmed 2026-08-13) |
| `time_duration` | 7 s | **40 s** | the LVRT profile alone spans 30 s after the T0 = 3 s init |
| project `Mruns` | 1 | **9** | PSCAD native multiple-run: one invocation, nine runs |
| test selector | `master:consti` = 17 | **`master:run_num`** | the current-run-number component drives the PMView test input, so run N executes DWG test N |

Everything else is the validated inertia rig unchanged: PMView block
`T0 = 3 s` (machine initialisation allowance), `Prated = 650`,
`ibr_type = 0`, solution step 50 us (no switching in the machine model;
this is what the H = 5.20 s baseline used), channels at 4 kHz
(`sample_step` 250 us), `PlotType = 1`.

## Tests (DWG Rev. 24, numbering per the GFM campaign)

| run | test | DWG section |
|---|---|---|
| 1 | Flat Start | 3.1.5.2 |
| 2 | LVRT (ERCOT legacy) | 3.1.5.4 |
| 3 | HVRT (ERCOT legacy) | 3.1.5.5 |
| 4 | Small Voltage Step Down | 3.1.5.3 |
| 5 | Small Voltage Step Up | 3.1.5.3 |
| 6 | LVRT Voltage Dips (IEEE 2800) | 3.1.5.4 |
| 7 | HVRT Preferred (IEEE 2800) | 3.1.5.5 |
| 8 | Phase Angle Jump (Down) | 3.1.5.9 |
| 9 | Phase Angle Jump (Up) | 3.1.5.9 |

Tests 10-13 (custom faults, frequency up/down, V up/down impedance)
are not in this battery, matching the scope of the GFM results the
report shows.

## Pipeline

1. `run_battery.py` - headless mhi.pscad driver. Environment traps per
   project memory (NoDefaultCurrentDirectoryInExePath popped, Git-Bash
   PATH entries stripped, mtime freshness guard on every output,
   quit() in finally). Copies fresh raw outputs to `runs/<stamp>_raw/`
   and writes `collect_manifest.json`.
2. `export_runs.py` (written after the multi-run output naming is
   observed) - splits the nine runs into
   `runs/test_NN_<name>/` each with the raw `.out`/`.inf` and a
   stitched CSV, plus `setup.json` per run.
3. `plot_battery.py` - per-test figures in the SAME style as the GFM
   MQT campaign (`plot_gfm_tests.py` on `origin/gfm_validation_task_2`:
   same channel groups, same layout), so machine and GFM figures are
   one-for-one comparable in the report.

## Rig repairs found on the way (all in the copy only)

- The ETRAN machine library was linked by a relative path
  (`..\..\..\..\..\Program Files (x86)\...`) that resolved from the
  original folder but not from this deeper one; made absolute. The
  failure mode is a silent build abort.
- `master:run_num` puts its output port at its anchor, not at +36 like
  the `consti` it replaced; the component is placed at x=612 so its
  port lands on the existing wire. The failure mode is a
  "port 'profile' is floating" build error.
- Both sampled playback tables (`PMView_profile_PMU_data.txt`,
  `PMView_profile_DFR_data.txt`) carried a stray 11-column EMTDC
  output row appended at t=5.021, and the PMU table ended at
  t=3.03 s. At 40 s the sequential reader hit EOF and EMTDC died
  ("Sequential READ or WRITE not allowed after EOF marker"). This is
  the "~7 s playback bound" remembered from the inertia campaign, now
  explained. Fix: stray rows dropped, tables extended flat to 45 s
  (the PMU/DFR playback tests are not among tests 1-9, so the hold
  affects no scored quantity).

## Status

- 2026-08-13: rig copied and modified; three launch failures diagnosed
  (lib path, floating port, playback EOF) and fixed; battery relaunched.
  Multiple-run confirmed active (outputs named `_r00001_NN.out`).
- 2026-08-13 (later): all 9 runs completed in one multiple-run
  invocation (~19 min). Exported to `runs/test_NN_<name>/` (CSV +
  setup.json + raw), figures in `plots/` in the GFM campaign style.
  Findings in [RESULTS.md](RESULTS.md) — flat start passes cleanly;
  every disturbance test leaves the ESST4B exciter latched at its
  ceiling (non-recovery finding).
