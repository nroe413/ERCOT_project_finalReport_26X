# ERCOT x UT Austin Grid-Forming Inverter Testbed

PSCAD test systems, model-quality-testing harnesses, run data, and
processing scripts accompanying the report *Stability Assessment of a
100% Grid-Forming (GFM) Inverter Power System* (ERCOT / The University
of Texas at Austin, 2026).

This branch is the curated release layer: every directory is a copy of
a working test setup from the study, stripped of PSCAD build artifacts
(`*.gf46/`) and with raw `.out` chunk files omitted where a stitched
CSV or an export script reproduces them.

## Layout

| Path | Contents |
|---|---|
| `systems/ieee39/00GFM_all_sync` | E-TRAN-converted IEEE 39-bus, 230 kV, all ten units synchronous machines (ERCOT-specified GENROU + ESST4B + GGOV1 + PSS2B) |
| `systems/ieee39/01GFM` ... `10GFM` | The machine-for-inverter replacement ladder: k units replaced by PNNL REGFM_A1 grid-forming inverters (ImaxF = 2.0 pu, the PNNL default) |
| `systems/ieee39/10GFM_Vsched` | All-GFM system at the scheduled-voltage dispatch |
| `systems/ieee39/10GFM_Vsched_Ilim1p5` | All-GFM system with the practical current limit ImaxF = 1.5 pu (the report's bus-10 fault study) |
| `systems/ieee39/01GFL` | One PNNL grid-following inverter at bus 32, remaining units synchronous |
| `systems/smib_siib` | Single-machine and single-inverter infinite-bus fault harnesses used for the SMIB/SIIB validation (Sec. 3/4 of the report) |
| `mqt/pmview24_*` | ERCOT PMView 2.4 model-quality-testing rigs: PNNL REGFM_A1, NLR Kenyon GFM, PNNL GFL |
| `mqt/pnnl_nlr_pscad_psse_bench` | PNNL vs NLR PSCAD/PSS-E benchmark cases and per-case CSVs |
| `mqt/pmview35_*` | PMView 3.5 advanced-grid-support (inertia) test rigs: REGFM_A1, REGFM_B1, and the Gen-32 synchronous machine |
| `mqt/typicalgt_dwg_battery` | DWG Procedure Manual Rev. 24 tests 1-9 run as one PSCAD multiple-run battery on the Gen-32 machine (driver, exports, figures) |
| `data/report_figure_data` | The CSV extracts behind the report's data figures |
| `scripts/report_figures` | Figure-regeneration scripts (matplotlib, report style) |
| `scripts/tools` | Bus instrumentation and .out-to-CSV stitching utilities |
| `manifest.json` | Machine-readable map of every copied directory to its source and exclusions |

## Requirements

- PSCAD 5.0.2 with GFortran 4.6 (systems were built and run on this pair)
- E-TRAN runtime library for PSCAD (bundled here; also freely available from
  https://www.electranix.com/software/e-tran-runtime-library-for-pscad/)
- PNNL REGFM_A1 model (wrapper projects bundled; the compiled library
  `PNNL_REGFM_A1_gf46.lib` is bundled and also published by PNNL at
  https://github.com/pnnl/PSCAD-and-PSSE-Version-of-WECC-Grid-Forming-Inverter-Models/releases/download/V1/REGFM_A1.zip )
- Python 3.10+ with numpy, pandas, matplotlib for the scripts

Library paths inside `.pscx` project files are absolute in places and
will need to be re-pointed on first load; PSCAD's project settings
dialog lists the linked libraries per project.

See `PROVENANCE.md` for the origin and redistribution status of every
third-party artifact, and `DATA.md` for what run data is included
versus regenerable.
