# Provenance and Redistribution Status

Review this file before making this branch public. Each third-party
artifact bundled here is listed with its source and the basis on which
it is included. Items marked REVIEW should be confirmed with the
originating organization before public release.

| Artifact | Where | Origin | Status |
|---|---|---|---|
| IEEE 39-bus case (RAW, line data) | `systems/ieee39/*` | Public benchmark (converted via E-TRAN from PSS/E) | OK - public benchmark |
| ERCOT-specified machine dynamics (`.dyr`, GENROU/ESST4B/GGOV1/PSS2B) | `systems/ieee39/*`, `mqt/pmview35_typicalgt_*` | ERCOT (representative, non-confidential per the study) | REVIEW - confirm ERCOT is comfortable with the .dyr record public |
| E-TRAN runtime libraries (`ETRAN_GF46.lib`, `ETRAN_IF12.lib`) and E-TRAN-generated `ETRAN.pslx` | every converted system | Electranix (free download; generated conversion output) | INCLUDED per project-lead assessment (free academic download); source: electranix.com |
| PNNL REGFM_A1 model + `PNNL_REGFM_A1_gf46.lib` | GFM systems, `mqt/*` | PNNL public GitHub release (PNNL-32278) | OK - public release; cite Du et al. |
| PNNL REGFM_B1 model | `mqt/pmview35_regfmb1_inertia` | PNNL | REVIEW - confirm the B1 release is public like A1 |
| PNNL grid-following model | `systems/ieee39/01GFL`, `mqt/pmview24_pnnl_gfl` | PNNL (WECC-approved GFL) | REVIEW - same check as B1 |
| NLR (NREL) Kenyon GFM model | `mqt/pmview24_nlr_gfm` | NREL / Kenyon PSCAD GFL-GFM models | REVIEW - NREL release terms |
| PMView 2.4 / 3.5 harness (PSCADView library, profiles) | `mqt/*` | ERCOT Dynamics Working Group | REVIEW - ERCOT distributes to market participants; confirm public redistribution |
| PSCAD project files authored by this study | throughout | UT Austin / this project | OK - ours |
| Run data (CSVs) and scripts | `data/`, `runs/`, `scripts/` | This project | OK - ours |
