# ERCOT x UT Austin Grid-Forming Inverter Testbed

Report source, PSCAD test systems, model-quality-testing harnesses, run
data, and processing scripts accompanying the year-one report *Stability
Assessment of a 100% Grid-Forming (GFM) Inverter Power System* (ERCOT /
The University of Texas at Austin, 2026).

Every directory is a copy of a working setup from the study, stripped of
PSCAD build artifacts (`*.gf46/`) and with raw `.out` chunk files omitted
where a stitched CSV or an export script reproduces them. Library and
project links inside the PSCAD files are relative to this repository, so a
clone opens and builds without re-pointing paths.

## Layout

| Path | Contents |
|---|---|
| `report/` | The report: `main.tex`, `ut26x.sty`, `figures/` (PNGs and editable TikZ schematics), `prism-uploads/`, and the compiled `main.pdf`. See `report/README.md`. |
| `systems/lib` | Shared libraries linked by every PSCAD project: E-TRAN runtime (`ETRAN_GF46.lib`, `ETRAN_IF12.lib`) and the PNNL REGFM_A1 wrapper project with its compiled library |
| `systems/ieee39/00GFM_all_sync` | E-TRAN-converted IEEE 39-bus, 230 kV, all ten units synchronous machines (ERCOT-specified GENROU + ESST4B + GGOV1 + PSS2B) |
| `systems/ieee39/01GFM` ... `10GFM` | The machine-for-inverter replacement ladder: k units replaced by PNNL REGFM_A1 grid-forming inverters (ImaxF = 2.0 pu, the PNNL default) |
| `systems/ieee39/10GFM_Vsched` | All-GFM system at the scheduled-voltage dispatch (the report's bus-14 reference case) |
| `systems/ieee39/10GFM_Vsched_Ilim1p5` | All-GFM system with the practical current limit ImaxF = 1.5 pu (the report's bus-10 fault study) |
| `systems/ieee39/01GFL` | One PNNL grid-following inverter at bus 32, remaining units synchronous |
| `systems/smib_siib` | Single-machine and single-inverter infinite-bus fault harnesses used for the SMIB/SIIB comparison |
| `mqt/pmview24_*` | ERCOT PMView 2.4 model-quality-testing rigs: PNNL REGFM_A1, NLR GFM model, PNNL GFL |
| `mqt/pnnl_nlr_pscad_psse_bench` | PNNL vs NLR PSCAD/PSS-E benchmark cases and per-case CSVs |
| `mqt/pmview35_*` | PMView 3.5 advanced-grid-support (inertia) test rigs: REGFM_A1, REGFM_B1, and the Gen-32 synchronous machine |
| `mqt/typicalgt_dwg_battery` | DWG Procedure Manual Rev. 24 tests 1-9 run as one PSCAD multiple-run battery on the Gen-32 machine (driver, exports, figures) |
| `data/report_figure_data` | The CSV extracts behind the model-quality-testing figures (including the REGFM_A1 legacy LVRT record of Figure 13, re-run 2026-09-18 with `mqt/pmview24_regfm_a1/PMVIEW24_pnnl_GFM/run_lvrt_headless.py`) and the bus-13 current-limit figure (Figure 27: five limits from 15 to 1.1 pu, plus the 1.0 pu run that does not recover), and the result files of the CCT solver |
| `scripts/report_figures` | The report's figure scripts (matplotlib, report style) with repository-relative paths |
| `scripts/log_decrement` | Total damping of the single machine's swing mode from the logarithmic decrement of its fault ring-down (Section 4.6 and the last row of Table 5): zero-phase band-pass, then peaks; runs from the shipped single-machine record; results in `data/report_figure_data/log_decrement` |
| `scripts/cct_solver` | The energy-method critical-clearing-time solver behind Figure 50 (constant-power network, swing-form devices, bisection); see its `README.md` |
| `scripts/tools` | Bus instrumentation and .out-to-CSV stitching utilities |
| `manifest.json` | Machine-readable map of every copied directory to its source and exclusions |

**Setting a fault in the 39-bus cases.** The fault is set by four constants on the main page (`BrkFaultLocation`, `BrkFaultType`, `BrkFaultTime`, `BrkFaultDuration`) and, per line, `InstantTrip` and `RecloseEnabled`; the shipped files carry the bus-14 reference fault. The E-TRAN fault elements (`master:tpflt`) ship with `OpCur = 0`, so each phase of a fault clears at its first current zero after the set duration. For a fault at a synchronous machine's own transmission bus (the bus-39 case of report Figure 29, `BrkFaultLocation = 39` with `InstantTrip = 0` on lines 1-39 and 9-39) the machine's offset fault current has no zero crossing on two phases for about 2.9 s and the fault lingers; the report's all-machine bus-39 record was run with `OpCur = 1` (clearing possible at any current) on the fault elements of `00GFM_all_sync`. The all-GFM records and every other fault location in the report clear within 10 ms of the set time with the stock setting.

## What runs directly from a clone

- **Report.** `cd report && pdflatex main.tex && pdflatex main.tex` (or
  `latexmk -pdf main.tex`) rebuilds the 57-page PDF with standard TeX Live
  or MiKTeX packages; every path in `main.tex` is relative.
- **PSCAD systems.** Open any `.pswx` under `systems/` in PSCAD 5.0.2 with
  GFortran 4.6 and build; the E-TRAN and PNNL libraries are linked from
  `systems/lib` by relative path. The all-machine case
  (`00GFM_all_sync`) and the all-GFM case (`10GFM_Vsched`) were built and
  run from a fresh copy of this repository on 2026-09-11 to confirm this;
  `python scripts/tools/verify_pscad_build.py` repeats that check headlessly
  (PSCAD's own automation package, `mhi.pscad`, is required).
- **CCT solver.** `cd scripts/cct_solver && python cct_pebs_constP.py --scenario bus14_noloss`
  reruns the ten-inverter energy-method clearing time from the shipped PSCAD model's loads
  (`numpy` only; hours per scenario). `smib_cct.py` and `gfm_damping_sweep.py` are the single-device cases.
- **Figure scripts.** `python scripts/report_figures/fig_mqt_042826.py`,
  `python scripts/report_figures/fig3_mqt_split.py` and
  `python scripts/report_figures/fig_mqt_regfma1_lvrt.py` regenerate the
  model-quality-testing figures from the shipped CSVs into
  `report/figures/`. The other scripts read the full PSCAD records, which
  are too large for GitHub (see `DATA.md`); each stops with a message
  naming the input it needs until `ERCOT_EXPERIMENTS` points at a copy of
  the study's `experiments/` directory. Figures that need no data
  (`inertia_timescale.py`, `saturation_block.py`) also run directly.

## Known gaps

- `mqt/pmview35_regfmb1_inertia`: the workspace references the PNNL
  REGFM_B1 wrapper project, which is not bundled pending the provenance
  review in `PROVENANCE.md`; place the PNNL REGFM_B1 release beside the
  repository as `../PNNL_REGFM/REGFM_B1/...` or re-point that entry.
- Three PMView 2.4 rigs reference an E-TRAN placeholder `..\inputfile.dyr`
  that is not part of the release.

## Folder names and the study's working tree

Directory names here are not the names used on the authors' machines: the
NLR PMView rig lives under `mqt/pmview24_nlr_gfm/rig` (its original
100-character folder name exceeded Windows path limits), the E-TRAN and PNNL
libraries are consolidated in `systems/lib` instead of sitting inside each
model folder, and the figure scripts lost their `_prism` suffix. When
comparing against or revising from the study's repository, use the
`origin_branch` / `origin_path` fields in `manifest.json`, which name each
directory's source branch and path in the UT project repository. On
Windows, run `git config --global core.longpaths true` before cloning;
some paths still exceed 200 characters.

## Python dependencies by script

Every script was run with CPython 3.13.9 from an Anaconda environment; the pinned
versions are in `requirements.txt` (`pip install -r requirements.txt`). Two
packages are not on PyPI: `mhi.pscad` (version 3.1.2) comes with PSCAD 5.0.2's
Automation Library installer, and `psspy` / `dyntools` come with PSS/E 36.

| Scripts | Third-party packages | Also needs |
|---|---|---|
| `scripts/report_figures/*.py` (the report's figures) | `numpy`, `pandas`, `matplotlib` | `figstyle_26x.py` and `repo_paths.py` in the same folder; TeX Gyre Pagella from a MiKTeX or TeX Live install (falls back to a serif face) |
| `scripts/report_figures/{fig_mqt_042826, fig3_mqt_split, fig_mqt_regfma1_lvrt, inertia_timescale, saturation_block, damping_vs_freq, hest_scr, ilim_arms_bus13}.py` | `numpy`, `matplotlib` (`pandas` for the three MQT scripts) | nothing else: they run from the shipped CSVs or from constants |
| `scripts/report_figures/{ilimit_sweep_emt, exec_gfm_vs_sync_bus39_pu, peakI_pair}.py` | `numpy`, `pandas`, `matplotlib` | import `analytic_ilimit`, `gfm_vs_sync_bus39_pu`, `make_bus10_sync_deck` from the study's `experiments/` tree (`ERCOT_EXPERIMENTS`), not included here |
| `scripts/report_figures/_pscad_io.py`, `aggregate.py`, `scripts/tools/out_chunks_to_csv_example.py` | `numpy`, `pandas` | the raw PSCAD `.inf` + `.out` chunk files (see `DATA.md`) |
| `scripts/cct_solver/*.py` (the CCT solver) | `numpy` (`pandas`, `matplotlib` for the two single-device scripts) | the shipped `.pscx` and SMIB record under `systems/` |
| `scripts/tools/instrument_buses.py` | none (standard library only) | a `.pscx` to patch |
| `scripts/tools/verify_pscad_build.py`, `systems/ieee39/01GFL/{run_3PG_fault, diag_build, diag_1gfm_control}.py`, `mqt/typicalgt_dwg_battery/run_battery.py`, the `PSCAD_*.py` drivers and `_pscad_pipeline.py` under `mqt/pnnl_nlr_pscad_psse_bench` and `mqt/pmview35_regfmb1_inertia` (PSCAD automation) | `mhi.pscad` 3.1.2; `pandas` and `numpy` where results are exported | PSCAD 5.0.2 with GFortran 4.6 and a licence on the machine; close interactive PSCAD before running |
| `mqt/typicalgt_dwg_battery/{export_runs, plot_battery}.py`, `mqt/*/plot_gfm_tests.py`, `analyze_gfl_results.py`, `_plot_*.py` | `numpy`, `pandas`, `matplotlib` | the run CSVs in the same folder |
| `mqt/**/create_pptx.py`, `_make_pptx*.py`, `_make_standalone.py`, `systems/smib_siib/make_smib_deck.py` (meeting decks) | `python-pptx`, `Pillow`, `lxml` | the PNGs produced by the plotting scripts |
| `mqt/**/PSSE_*.py` (PSS/E side of the PSCAD/PSS-E benchmark) | `psspy`, `dyntools` (PSS/E 36), `pandas` | PSS/E 36 |

## Requirements

- PSCAD 5.0.2 with GFortran 4.6 (systems were built and run on this pair).
- E-TRAN runtime library for PSCAD (bundled in `systems/lib`; also freely
  available from https://www.electranix.com/software/e-tran-runtime-library-for-pscad/).
- PNNL REGFM_A1 model (bundled in `systems/lib/PNNL_REGFM_A1`; published by
  PNNL at https://github.com/pnnl/PSCAD-and-PSSE-Version-of-WECC-Grid-Forming-Inverter-Models).
- LaTeX: TeX Live 2023+ or MiKTeX with `tikz`, `tgpagella`, `booktabs`,
  `geometry`, `fancyhdr`, `placeins`, `listings`, `hyperref`.
- Python 3.10+ with the packages in `requirements.txt` (per-script list in
  the section above). The figure style module registers TeX Gyre Pagella
  from the MiKTeX or TeX Live font tree when present and falls back to a
  serif face otherwise.

## License

The material authored by this study is released under the MIT License
(`LICENSE`): the report source and PDF under `report/`, the PSCAD projects
and workspaces the study authored, the run data under `data/`, and every
script under `scripts/` and in the `mqt/` drivers.

Third-party components are bundled for convenience only and keep their
originators' terms; the MIT License does not cover them:

- PNNL REGFM_A1 grid-forming inverter model and its compiled library
  (`systems/lib/PNNL_REGFM_A1/`, and wherever the model is referenced under
  `systems/` and `mqt/`): BSD 3-Clause License, Copyright (c) 2026 Battelle
  Memorial Institute. The license and disclaimer texts are kept beside the
  model in `systems/lib/PNNL_REGFM_A1/`.
- E-TRAN runtime libraries (`systems/lib/ETRAN_GF46.lib`, `ETRAN_IF12.lib`)
  and the E-TRAN-generated `ETRAN.pslx` files: Electranix Corporation's terms
  for the freely downloadable runtime library.
- ERCOT PMView 2.4 / 3.5 harness components and the ERCOT-supplied machine
  dynamics record (`.dyr`): ERCOT Dynamics Working Group terms.
- NREL (NLR) GFM model under `mqt/pmview24_nlr_gfm/`: NREL release terms.
- IEEE 39-bus benchmark data: public benchmark.

`PROVENANCE.md` lists the origin and review status of each item.

See `PROVENANCE.md` for the origin and redistribution status of every
third-party artifact, and `DATA.md` for what run data is included versus
regenerable.
