# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a PSCAD electromagnetic transient (EMT) simulation project for the ERCOT x UT Austin collaboration (SOW Task 2 — PMView 2.4 testing). It validates grid-forming inverter (GFM) interconnection behavior against NERC/ERCOT grid code requirements.

This directory integrates the **National Lab of Rockies (NREL) GFM inverter models** (Kenyon library) into the PMView test harness. The current branch is `gfm_validation_task_2`.

Simulations are built and run through PSCAD 5.0.1, which compiles Fortran via GFortran 4.6 on Windows.

## Key Files

- **`PMView_testing_NREL_GFM.pscx`** — Primary PSCAD project (XML circuit definition)
- **`9_Bus_Zero_Inertia.pscx`** — Supporting 9-bus zero-inertia test system
- **`Kenyon_Library.pslx`** — NREL Kenyon GFM/GFL inverter model library
- **`PMView.pslx`** — PMView test harness library
- **`plot_gfm_tests.py`** — Python plotting script for simulation results
- **`create_pptx.py`** — Assembles plot PNGs into a PowerPoint presentation

## Build and Run

Simulations are normally launched from the PSCAD GUI. Build artifacts live in `PMView_testing_NREL_GFM.gf46/`:

```bash
# Build (compile Fortran, link executable)
PMView_testing_NREL_GFM.gf46/PMView_testing_NREL_GFM_mak.bat

# Run simulation (requires PSCAD runtime connection)
PMView_testing_NREL_GFM.gf46/PMView_testing_NREL_GFM_30000.bat
```

The makefile uses `gfortran -ffree-form -fdefault-real-8 -fdefault-double-8 -O2` and links against PSCAD's `emtdc.lib` and `Solver.lib`.

**Paths:**
- GFortran 4.6: `C:\Program Files (x86)\GFortran\4.6\`
- PSCAD 5.0.1: `C:\Program Files (x86)\PSCAD50\`

## Simulation Parameters

- Time step: 5 microseconds (200,000 steps/sec)
- Output sample rate: 5,000 Hz (every 200 timesteps)
- Simulation duration: 32 seconds per run

## Plotting and Reporting

```bash
python plot_gfm_tests.py              # Plot all tests (1-13)
python plot_gfm_tests.py 1 2 3        # Plot specific tests
python create_pptx.py                 # Assemble plots into GFM_Test_Results.pptx
```

`plot_gfm_tests.py` requires `numpy` and `matplotlib`. Output PNGs go to `plots/r{NNNNN}_{profile}/` (9 plots per test in a standard set: vinst_3phase, vsource, poi_power, model_pmu_power, ipoi, fpoi, vinst_pmu_3phase, vinst_dfr_3phase, breaker_status).

`create_pptx.py` requires `python-pptx`. It arranges the 9 plots per test into a 3x3 grid on widescreen slides, producing `GFM_Test_Results.pptx`.

## Architecture

### PMView_testing_NREL_GFM.pscx (primary model)

Integrates the NREL/Kenyon GFM inverter with the PMView test harness. Key Fortran components in `PMView_testing_NREL_GFM.gf46/`:
- **Main.f** — Top-level simulation orchestrator
- **GFM_Inverter_Dev4.f** — NREL grid-forming inverter (droop-based, with voltage/current loops, PLL, current limiting, AGC). This is the primary model under test.
- **PMView.f** — Test orchestration driver (calls `PMViewDyn` with profile, start time, IBR type, transient enable)
- **V_Test.f / Frequency_Test.f / VoltStep_Impedance.f / SCR.f / Transient_Volt2.f / Fault_block.f** — Test disturbance drivers
- **PhaseLocked_Loop.f / Current_Loop_1.f / Voltage_Loop.f / Current_Limiter_Scale.f** — Inverter sub-components
- **DFR_Injector.f / PMU_Playback3.f** — Data playback from measurement files
- **DS.f** — Data storage

### 9_Bus_Zero_Inertia.pscx (supporting model)
A 9-bus zero-inertia test system using the same Kenyon library. Build output in `Kenyon PSCAD GFL-GFM Models/a9_Bus_Zero_Inertia.gf46/`.

### Known Build Issues
The `.psmx` shows unresolved definition errors for `PSCADView:PMView`, `Voltage_Loop`, `PhaseLocked_Loop`, `Current_Loop_1`, and `Current_Limiter_Scale`. These are NREL-specific subcomponents that need to be defined within the project scope (not imported from the original PMView library).

## Test Framework (PMView Tests 1–13)

Simulation runs are named `MQT_r00001` through `MQT_r00013`. Each run produces one `.inf` channel layout file and multiple `.out` data files. **Tests 1–9 are complete; tests 10–13 have not yet been run.**

| Test | Profile | Description |
|------|---------|-------------|
| 1 | Flatstart | Baseline initialization |
| 2 | LVRT_ERCOT_Legacy | Low Voltage Ride Through (ERCOT) |
| 3 | HVRT_ERCOT_Legacy | High Voltage Ride Through (ERCOT) |
| 4 | V_Down | Voltage step down |
| 5 | V_Up | Voltage step up |
| 6 | LVRT_Dips_IEEE2800_NOGRR245 | IEEE 2800 LVRT dips |
| 7 | HVRT_Preferred_IEEE2800 | IEEE 2800 preferred HVRT |
| 8 | Angle_Down | Phase angle step down |
| 9 | Angle_Up | Phase angle step up |
| 10 | Custom_Faults | Custom fault scenarios |
| 11 | Frequency_Down | Frequency deviation downward |
| 12 | Frequency_Up | Frequency deviation upward |
| 13 | V_Up_Down_Impedance | Voltage step with impedance |

**Profile files** (`profile_*.txt`, `2800_*.txt`) contain time-value pairs with `!` comment lines, terminated by `ENDFILE:`.

## Output Systems

The project has two parallel output systems:

### PGB Outputs (`.inf` + `.out` files) — Primary
21 channels at 5,000 Hz in the "PMView" group, used by `plot_gfm_tests.py`. Each `.inf` file defines the channel layout. Data splits across `_01.out`, `_02.out`, `_03.out` (10 columns per file, plus time). Tests 1–8 produce 3 `.out` files each; test 9 produces 14 (additional channels recorded).

| Channel | Signal | Description |
|---------|--------|-------------|
| 1 | Q_PMU | Reactive power from PMU |
| 2–4 | Vinst:1–3 | Instantaneous 3-phase voltages |
| 5 | Vsource | Source voltage |
| 6–7 | Ppoi, Pmodel | Active power at POI and model |
| 8–9 | Qmodel, Qpoi | Reactive power at model and POI |
| 10 | Ipoi | Current at POI |
| 11 | Fpoi | Frequency at POI |
| 12–14 | Vinst_PMU:1–3 | PMU instantaneous voltages |
| 15–17 | Vinst_DFR:1–3 | DFR instantaneous voltages |
| 18–20 | BRK1C/B/A | Breaker status (phases C, B, A) |
| 21 | P_PMU | Active power from PMU |

### Internal Diagnostic Outputs (`MQT.infx`) — Debug
70+ inverter-internal signals (Theta_Diff, ROCOF, Headroom, d/q currents and voltages, limiter status, etc.) at ~3,846 Hz. Defined in XML format in `MQT.infx`. These are PSCAD analog outputs from `GFM_Inverter_Dev4` and its sub-components.

## Output File Format

The `.out` files are **text-formatted**. Each has 1 blank header line, then rows of whitespace-delimited values in scientific notation: `time val1 val2 ... val10` (up to 10 data columns per file). Read in Python:
```python
import numpy as np
data = np.loadtxt("MQT_r00001_01.out", skiprows=1)
time = data[:, 0]
channels = data[:, 1:]
```

## Data Playback Files

- **`PMU_data.txt`** — PMU playback (tab-delimited: Seconds, Volt, Angle, Freq, Tie_P, Tie_Q)
- **`DFR_data.txt`** — Digital Fault Recorder playback (tab-delimited: Seconds, VA_V, VB_V, VC_V at ~960 Hz)

## File Types

- **`.pscx`** — PSCAD project file (XML circuit definition)
- **`.psmx`** — PSCAD metadata with build messages and output channel definitions
- **`.pswx` / `.pslx`** — PSCAD workspace and library files
- **`.gf46/`** — Build output directory (Fortran source, objects, executable, channel layouts, simulation output)

## Related Directories

- **`../PMVIEW_2.4_working_w_gfm_claude_directory/`** — Original GFM tests with `Generic_GFM_switching.pscx` (uses PVFarm_GFL_GFM_2 inverter model, not NREL Kenyon models). Output uses `gfmMQT_r*` naming.
- **`../PMVIEW_2.4_clean/`** — Baseline (unmodified) test cases
- **`../PMVIEW_2.4_working/`** — Working test version (synchronous machines)
- **`Kenyon PSCAD GFL-GFM Models/`** — Standalone copy of the NREL Kenyon GFL/GFM library and 9-bus test case
