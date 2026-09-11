# Year-one report: LaTeX source

Source of the report *Stability Assessment of a 100% Grid-Forming (GFM)
Inverter Power System*, year-one EMT testbed and analysis
(ERCOT / The University of Texas at Austin, 2026). `main.pdf` is the
compiled report; everything needed to rebuild it is in this directory.

## Files

- `main.tex` — report text, tables, and bibliography (the bibliography is
  embedded; no BibTeX run is needed).
- `ut26x.sty` — typography, colors, cover page, and running headers.
- `figures/` — every raster figure (PNG, 600 dpi at print size) and the
  editable TikZ schematics (`tikz_*.tex`, `energy_surface_*.tex`) that
  `main.tex` inputs.
- `prism-uploads/` — the three energy-surface renderings used by the
  energy-method figures.

All paths inside `main.tex` are relative to this directory
(`\graphicspath{{figures/}}`).

## Build

From this directory, run pdfLaTeX twice so cross-references and the table
of contents settle:

```sh
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

or, equivalently, `latexmk -pdf main.tex`. Verified on MiKTeX (Windows) and
requires only standard packages: `geometry`, `fancyhdr`, `tgpagella`
(TeX Gyre Pagella), `amsmath`, `booktabs`, `array`, `graphicx`, `tikz`
with the `arrows.meta` and `positioning` libraries, `placeins`,
`listings`, `hyperref`, and `xcolor`. TeX Live 2023 or newer ships all of
them.

## Regenerating figures

The raster figures were produced with matplotlib under a fixed style
(TeX Gyre Pagella text, Computer Modern math, true print inches, 600 dpi).
The scripts whose input data is small enough to ship live in
`../scripts/report_figures/` together with that style module; their data is
in `../data/report_figure_data/`. The remaining figures are derived from
multi-gigabyte PSCAD records held by the authors (see `../DATA.md`) and are
included here as the finished PNGs.

## Overleaf

Upload `main.tex`, `ut26x.sty`, `figures/`, and `prism-uploads/` as they
are, keeping the relative paths, and set `main.tex` as the main document.
