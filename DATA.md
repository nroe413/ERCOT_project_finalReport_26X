# Data Inclusion Policy

Included:
- Stitched per-run CSVs up to 95 MB per file (GitHub's hard limit is
  100 MB). This covers the DWG battery exports (~66 MB each), the
  SMIB/SIIB runs, the PMView benchmark per-case CSVs, and every CSV
  behind a report figure (`data/report_figure_data`).
- Every run's `setup.json` and PSCAD `.inf` channel map, and rendered
  figure PNGs.

Not included (regenerable):
- Raw PSCAD `.out` chunk files (2-6 GB per 30 s run). Re-run the
  project in PSCAD, or use the archived copies retained by the
  authors. The `.inf` + `scripts/tools/out_chunks_to_csv_example.py`
  pattern reconstructs CSVs from them.
- The 39-bus fleet-wide full-resolution CSVs over 95 MB (e.g. the
  aggregate all-GFM fault runs); their derived, figure-ready extracts
  are in `data/report_figure_data`.
- PSCAD build directories (`*.gf46/`): regenerated on first compile.
