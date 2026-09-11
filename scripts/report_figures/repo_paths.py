"""Repository-relative locations for the figure scripts.

OUT   -- report/figures: the PNGs that report/main.tex includes.
DATA  -- data/report_figure_data: the CSV extracts shipped in this repository.
experiment(rel) -- a file under the full PSCAD experiment records, which are
      NOT shipped (multi-gigabyte; see DATA.md). Point ERCOT_EXPERIMENTS at a
      checkout of the study's experiments/ directory to enable those scripts;
      otherwise the script stops with a message naming the missing input.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "report" / "figures"
DATA = ROOT / "data" / "report_figure_data"
EXPERIMENTS = Path(os.environ.get("ERCOT_EXPERIMENTS", str(ROOT / "data" / "experiments")))


def experiment(rel):
    p = EXPERIMENTS / rel
    if not p.exists():
        raise SystemExit("input not shipped in this repository: %s\n"
                         "set ERCOT_EXPERIMENTS to the study's experiments/ "
                         "directory (see DATA.md)" % rel)
    return p
