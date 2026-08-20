# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Cross-tool validation campaign for the REGFM_A1 grid-forming inverter model: each case folder runs the same disturbance in **PSCAD** (EMT) and **PSSE36** (positive-sequence) against the PNNL black-box model, and (for Case 1) against the NLR open-source benchmark. Reference document is `Validation_REGFM_A1_blackbox_and_PSSE3604.pdf`.

## Runtime requirements (pinned, non-obvious)

- **PSCAD 5.0.1** is pinned in `_pscad_pipeline.py` — 5.0.2 is not installed on the lab machine and `mhi.pscad.launch(version='5.0.2')` will fail. The legacy per-case `PSCAD_REGFMA1.py` scripts in Cases 2–7 still request `5.0.2`; update the version string before running them.
- **Python 3.7** — interpreter is fixed by PSSE36's bundled `psspy` and `dyntools` (`C:\Program Files\PTI\PSSE36\36.4\PSSPY313` / `PSSBIN`). The `__pycache__` artifacts are `cpython-37`.
- **MSYS-shell quirk**: PSCAD's auto-generated makefile contains a Windows `copy` rule that fails under PSCAD's MSYS `sh`. The pipeline pre-stages `PNNL_REGFM_A1_gf46_1.lib` into the build folder so the target already exists. Don't remove that step.
- **`NoDefaultCurrentDirectoryInExePath`** must be unset in the PSCAD child's environment (the pipeline does this on import). If it's set, EMTDC's `<project>_30000.bat` fails to invoke `<project>.exe` by bare name.

## Common commands

All runs must happen from inside the case folder (the pipeline `os.chdir`'s to `case_dir`). Activate the project's Python 3.7 environment first.

```powershell
# Case 1, NLR variant — PSCAD run → plots → PPTX
cd "1. Voltage Step Down_NLR"
python PSCAD_VoltageStepDown.py                          # writes NLR_VoltDwn_PSD_<ts>.csv
python Case_VStepDown_results\_plot_vstepdown.py         # writes plots/*.png + latest_run.txt
python Case_VStepDown_results\_make_pptx_vstepdown.py    # writes Case1_VoltageStepDown_NLR_<ts>.pptx

# Case 1, PNNL variant — same shape, different filenames
cd "..\1. Voltage Step Down_pnnl"
python PSCAD_REGFMA1.py                                  # writes A1_VoltDwn_PSD_<ts>.csv
python Case_VStepDown_results\_plot_vstepdown.py
python Case_VStepDown_results\_make_pptx_vstepdown.py

# Cases 2–7 (legacy, no shared pipeline yet)
python PSCAD_REGFMA1.py                                  # PSCAD driver
python PSSE_REGFMA1.py                                   # PSSE driver
```

The plot step picks up the newest CSV in `CASE_DIR` automatically; pass an explicit path as `argv[1]` to override. The PPTX step reads `plots/latest_run.txt` to find the matching PNG set.

## Architecture

### Two pipeline tiers

**Tier 1 — shared pipeline (Case 1 only, both variants):** `_pscad_pipeline.py` exposes `run_disturbance(...)` and each case driver is a thin caller that supplies case-specific knobs (`case_dir`, `project_name`, `workspace_file`, `build_dir_name`, `output_streams`, `sim_duration`, `disturbance_time`, `voltage_step_pu`, `target_columns`, optional `extra_param_overrides`, `project_settings`). Outputs land as `<csv_basename>_<YYYYMMDD_HHMMSS>.csv` in the case folder.

**Tier 2 — legacy standalone (Cases 2–7):** `PSCAD_REGFMA1.py` and `PSSE_REGFMA1.py` are self-contained per-case scripts modeled on the PNNL examples. They `mhi.pscad.launch` directly, use `mpuf.OutFile(...).toCSV(...)`, and rewrite column headers inline. Reuse the pipeline when extending these — Cases 2–7 should be migrated, not duplicated.

### Why the pipeline exists

`_pscad_pipeline.py`'s docstring is the canonical record of the quirks the rewrite worked around. The five that matter most:

1. `project.run()` returns before EMTDC actually spawns; `run_status()` reads `(None, None)` in the race window. The pipeline uses a one-shot `SimulationSet` (`add_tasks`, not `add_task` — the latter is rejected as Unknown), then polls `tasklist /FI "IMAGENAME eq <project>.exe"` until EMTDC exits and verifies the sentinel `.out` mtime advanced.
2. PSCAD writes **10 PGB channels per `.out` file**; large projects split into `<prefix>_NN.out` chunks. `load_concat_out` concatenates them in numerical order and `parse_inf_columns` recovers the channel layout from `<prefix>.inf` via regex on `PGB(N) Output Desc="..."` lines. The docs' `mpuf.OutFile` reader flakes on the `.inf` race window — don't use it.
3. Component-parameter writes must happen **before** `project.save()` so they end up in the `.pscx` the build reads.
4. Three master components are reset on every run (parked past sim end) before applying the case's disturbance: `tfaultn` (id 963051497), Gvolt-compare (696389395), Gfreq-compare (2018508786). Voltage step is `voltage_compare_id.parameters(OH=<pu>, X=<t>)`.
5. `output_streams` is a list because the NLR `NLR_comp_to_A1` project also exports a PNNL black-box stream in parallel; supply one entry per `.inf` you care about.

### NLR vs PNNL operating-point alignment (Case 1)

`PSCAD_VoltageStepDown.py` in the NLR folder documents the base-conversion gotcha: the NLR project's global `Mbase` / `V_base` / `G_volt` master:var sliders are authored at PNNL bases (0.1 MVA / 0.48 kV) even though the NLR machine is 200 MVA / 13.8 kV. The shared pipeline accepts `extra_param_overrides={component_id: {param: value}}` so the driver can flip these to the NLR machine's bases (200 MVA / 13.8 kV) without editing the `.pscx`. If you add NLR runs for other disturbances, replicate the override dict from `PSCAD_VoltageStepDown.py:87–94`.

### Results / slides convention

Each case has a `Case_<Name>_results/` subfolder containing `_plot_<case>.py` and `_make_pptx_<case>.py`. Plots go to `Case_<Name>_results/plots/` with a shared per-run timestamp; `latest_run.txt` is the contract between plot and pptx steps. The deck inherits theme from `slide_templates/meeting_update_042226_r3.pptx` — `_make_pptx_vstepdown.py:59–68` strips its slides while keeping master layouts, then `force_white_background` overrides the template's dark background per slide.

## Conventions

- Per-run CSV filenames are timestamped (`<basename>_YYYYMMDD_HHMMSS.csv`); the plain `A1_VoltDwn_PSD.csv` / `REGFMA1_VoltDown.csv` at the case-folder root are the original reference outputs and should not be overwritten.
- PNNL uses red solid, NLR uses blue (solid in NLR-only plots, dashed when overlaid). See `_plot_vstepdown.py:61–64`.
- Plot window is `(4.0, 7.0)` s for Case 1 and Case 2 (disturbance at t=5, 1 s pre / 2 s post). Y-limits in the NLR plot script are intentionally wider than the PNNL deck because the NLR machine shows larger transients.
- `target_columns` always begins with `'TIME'`; the rest are picked from the `.inf` channel descriptions (e.g. `V_pu`, `I_pu`, `P_pu`, `Q_pu`, `f_drp`).

## NLR parameter override gotchas

The NLR project (`NLR_comp_to_A1.pscx`) has two distinct namespaces for what looks like the same parameter:

- **Inverter-local** parameter on the GFM_Inverter_Dev4 instance (id `137448792`) — e.g. `cur_limit_time`, `Ki_avr`, `Kp_avr`, `s_base`. Overrides here go through `extra_param_overrides={NLR_GFM_INVERTER_ID: {...}}`.
- **Master-scope** parameter on top-level `master:compare` / `master:datalabel` components — e.g. the `master:compare` at id `1718620349` has `X="cur_limit_time"`, but that string is a **master-scope variable reference**, *not* a forwarded value from the inverter's local `cur_limit_time`. **Overriding the inverter parameter does not change what the master:compare reads.**

To control the limiter-enable timing from Python, override the `master:compare` X parameter directly:
```python
NLR_LIMITER_COMPARE_ID = 1718620349
extra_param_overrides = {
    NLR_LIMITER_COMPARE_ID: {'X': 'cur_limit_time'},  # or a numeric literal like '2'
}
```
If you set `X` to a numeric literal during a test, **the pipeline's `project.save()` persists it into the .pscx** — restoration requires explicitly setting it back to `'cur_limit_time'` on the next run, or hand-patching the .pscx XML.

## NLR signal-name reference (from `NLR_data.inf`, 76 PGB channels)

For diagnosing AVR / current-limiter behavior, the most useful channels are:

| PGB # | Desc                       | Group                  | Meaning |
|-------|----------------------------|------------------------|---------|
| 1–5   | V_pu, I_pu, P_pu, f_drp, Q_pu | Main               | Standard ride-through signals |
| 11    | Limiting_Status            | GFM_Inverter_Dev4      | High-level "limiter active" flag |
| 12–13 | Iref_q_limited / Iref_d_limited | GFM_Inverter_Dev4 | Current refs after the limiter clamp |
| 31    | V_error                    | GFM_Inverter_Dev4      | V_ref − V_measured (AVR input error) |
| 32    | V_ref                      | GFM_Inverter_Dev4      | AVR target |
| 69    | Status                     | Current_Limiter_Scale  | **Activity flag** — high when limiter is *actively clamping*, not when it is "enabled". Confirmed empirically: fires at AVR-engage time (Release_Time + Tavr_release), not at `cur_limit_time`. |
| 70–71 | Idq / Idq_limit            | Current_Limiter_Scale  | Actual vs limit current magnitude |

The 76-channel layout has duplicate `Desc` strings (e.g. `Iref_q` in both GFM_Inverter_Dev4 and Voltage_Loop groups), so name-based filtering with `target_columns` is ambiguous for some signals. To extract by PGB index, read the raw `<prefix>_NN.out` files directly with `parse_inf_columns` + `load_concat_out` from `_pscad_pipeline.py` and index into the resulting dataframe by column position rather than by name.

## Case 2 ride-through behavior (key empirical findings, 2026-05-13)

- **PNNL** has a droop V regulation: 5% source step → terminal V settles at ~1.04 pu, Q at ~−0.44 pu, no oscillation.
- **NLR** has integral AVR (`Ki_avr=10`, `Kp_avr=5`, `VQ_Control=1`, `Vsched=1.0`) — for a 5% step, the required Q to drag V back to 1.0 pu exceeds the limiter capability and the system enters a sustained ~5 Hz limit cycle (V oscillating 1.03↔1.07, Q oscillating −0.6↔+0.85, P inverting to −1.17 pu).
- The limit cycle is **inherent** to the 5% step at Pset=0.6 — tested independent of:
  - `Ki_avr` value (5× reduction to 2 → identical oscillation)
  - `cur_limit_time` master-compare threshold (override didn't propagate via the inverter param, and changing the master compare X showed no qualitative change)
  - Disturbance arrival time (moving disturbance to t=2 → CL_Status fires at t=2.21 = AVR engage time, identical oscillation thereafter)
- At a **2% step**, NLR rides through cleanly (Q saturates at ~−0.85, V settles back at 1.0). The instability boundary sits in `0.02 < ΔV ≤ 0.05`.
- **Reducing grid SCR from 40 → 5 (weak-grid benchmark) eliminates the limit cycle entirely** at the 5% step. SCR slider lives at master:var id `734618996` (same component ID in both PNNL and NLR projects), authored Value=40. With SCR=5: NLR settles at V=0.999, Q=−0.26, P=0.596, I=0.65 — current limiter never activates (`CL_Status` never transitions). This is consistent with GFM-in-stiff-grid theory: in a strong grid the inverter's voltage authority is too small relative to the source, so the AVR demands more Q than the limiter allows; in a weak grid the AVR has authority and finds a stable operating point.
- **PNNL droop is also SCR-sensitive but always stable.** PNNL at SCR=40 settles at V=1.040, Q=−0.44; PNNL at SCR=5 settles at V=1.009, Q=−0.20 (about half the Q for the same step, V much closer to nominal). PNNL handles both stiff and weak grids cleanly — the droop characteristic naturally accommodates whatever line impedance is in front of it. The contrast NLR-vs-PNNL is clearest in a stiff grid where NLR's integral AVR is incompatible with the operating point.
- **Case 1 (V step down 0.95 pu) SCR sensitivity is the mirror image of Case 2** and was confirmed empirically. PNNL @ SCR=5 step down: V settles at 0.999, Q=+0.20 (injecting reactive instead of absorbing). NLR @ SCR=5 step down: completely settled (V=0.998, P=0.599=Pset, Q=+0.24, f=60.000 exact). The SCR=5 weak-grid setting eliminates any oscillation in both cases for the NLR model.
