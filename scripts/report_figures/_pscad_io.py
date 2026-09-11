"""Shared PSCAD I/O helpers for fault-baseline experiments.

Lifted from the canonical pipeline at
SOW_task_2/PMView2.4/pnnlAndNLRBench/4. PSCAD_PSSE_Validation/_pscad_pipeline.py
on the gfm_validation_task_2 branch — just the file-parsing pieces, no
PSCAD-automation. The .inf parser tries the canonical PGB-indexed pattern
first and falls back to plain Desc= for older .inf files.
"""
import glob
import re
from pathlib import Path

import numpy as np
import pandas as pd


def parse_inf_columns(inf_path):
    """Return ['TIME', desc1, desc2, ...] in PGB index order.

    Falls back to description-order parsing if the .inf lacks PGB(N)
    indexing (older formats used Desc="..." Group="..." per line).
    """
    cols = ["TIME"]
    pgb_pattern = re.compile(r'PGB\((\d+)\)\s+Output\s+Desc="([^"]+)"')
    desc_pattern = re.compile(r'Desc="([^"]+)"')
    pgb_pairs = []
    desc_only = []
    with open(inf_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            m_pgb = pgb_pattern.search(line)
            if m_pgb:
                pgb_pairs.append((int(m_pgb.group(1)), m_pgb.group(2)))
                continue
            m_desc = desc_pattern.search(line)
            if m_desc:
                desc_only.append(m_desc.group(1))
    if pgb_pairs:
        pgb_pairs.sort()
        cols.extend(name for _, name in pgb_pairs)
    else:
        cols.extend(desc_only)
    return cols


def load_concat_out(inf_path):
    """Concatenate <prefix>_NN.out chunks paired with the .inf into ndarray.

    PSCAD splits PGB output at 10 channels per file; chunk files share the
    time column, which is kept once at column 0.
    """
    prefix = Path(inf_path).with_suffix("")
    pattern = str(prefix) + "_[0-9][0-9].out"
    paths = sorted(glob.glob(pattern))
    if not paths:
        raise FileNotFoundError(f"No .out chunks matching {pattern}")
    pieces = []
    time_col = None
    for p in paths:
        chunk = np.loadtxt(p, skiprows=1)
        if chunk.ndim == 1:
            chunk = chunk[None, :]
        if time_col is None:
            time_col = chunk[:, 0:1]
        pieces.append(chunk[:, 1:])
    return np.hstack([time_col] + pieces)


def read_run_to_dataframe(inf_path):
    """Load a PSCAD run as a pandas DataFrame with named columns."""
    cols = parse_inf_columns(inf_path)
    arr = load_concat_out(inf_path)
    if arr.shape[1] != len(cols):
        n = min(arr.shape[1], len(cols))
        arr = arr[:, :n]
        cols = cols[:n]
    return pd.DataFrame(arr, columns=cols)


def find_inf(directory):
    """Return the first .inf in a directory (alphabetical), or None."""
    cands = sorted(Path(directory).glob("*.inf"))
    return cands[0] if cands else None


def find_newest_csv(directory, pattern="*.csv"):
    """Return the most recently modified CSV in a directory, or None."""
    cands = sorted(Path(directory).glob(pattern),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    return cands[0] if cands else None
