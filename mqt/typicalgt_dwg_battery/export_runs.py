"""Split the multiple-run battery output into per-test run folders in
the experiments convention, and stitch each into a CSV.

Input: the newest runs/<stamp>_raw/ from run_battery.py, containing
TypicalGTPMView_rNNNNN_MM.out chunks (run NNNNN = DWG test NNNNN,
because master:run_num drives the PMView test input) plus the shared
TypicalGTPMView.inf channel map.

Output per test:
  runs/test_NN_<name>/TypicalGTPMView_rNNNNN_MM.out   (raw, copied)
  runs/test_NN_<name>/data_<stamp>.csv               (stitched, named
                                                      like the other
                                                      experiments)
  runs/test_NN_<name>/setup.json

The stitcher is the project-standard one: .inf gives the global
channel order; each .out chunk is whitespace-delimited with time in
column 0 and up to 10 channels; chunk k carries channels 10(k-1)+1..
10k. Channel names are made unique as <Group>.<Desc> and column
collisions get numeric suffixes.
"""
import json
import re
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"

TESTS = {
    1: "Flatstart",
    2: "LVRT_ERCOT_Legacy",
    3: "HVRT_ERCOT_Legacy",
    4: "V_Down",
    5: "V_Up",
    6: "LVRT_Dips_IEEE2800_NOGRR245",
    7: "HVRT_Preferred_IEEE2800",
    8: "Angle_Down",
    9: "Angle_Up",
}


def parse_inf(path):
    chans = []
    for ln in path.read_text(encoding="utf8", errors="ignore").splitlines():
        m = re.match(r"PGB\((\d+)\)\s+Output\s+Desc=\"([^\"]*)\"\s+"
                     r"Group=\"([^\"]*)\"", ln)
        if m:
            chans.append((int(m.group(1)), m.group(2), m.group(3)))
    chans.sort()
    names, seen = [], {}
    for _, desc, group in chans:
        base = ("%s.%s" % (group, desc)).strip(".") or "ch"
        base = re.sub(r"\s+", "_", base)
        k = seen.get(base, 0)
        seen[base] = k + 1
        names.append(base if k == 0 else "%s_%d" % (base, k))
    return names


def stitch(run_files, names):
    run_files = sorted(run_files,
                       key=lambda p: int(p.stem.rsplit("_", 1)[1]))
    cols, t = [], None
    for i, p in enumerate(run_files):
        arr = np.loadtxt(p, skiprows=1)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        if t is None:
            t = arr[:, 0]
        n = min(len(t), arr.shape[0])
        cols.append(arr[:n, 1:])
    n = min(c.shape[0] for c in cols)
    data = np.hstack([c[:n] for c in cols])
    t = t[:n]
    got = data.shape[1]
    use = names[:got] if got <= len(names) else (
        names + ["extra_%d" % i for i in range(got - len(names))])
    df = pd.DataFrame(data, columns=use)
    df.insert(0, "TIME", t)
    return df


def main():
    raws = sorted(RUNS.glob("*_raw"))
    if not raws:
        sys.exit("no runs/<stamp>_raw directory")
    raw = raws[-1]
    stamp = raw.name.replace("_raw", "")
    print("exporting from", raw)

    # each run writes its own .inf; the final run of a multiple-run
    # sequence carries extra aggregate channels (observed: 111 vs 29),
    # so the channel map must be per-run, not shared
    by_run = {}
    for p in raw.glob("TypicalGTPMView_r*_*.out"):
        m = re.match(r"TypicalGTPMView_r(\d+)_(\d+)\.out", p.name)
        by_run.setdefault(int(m.group(1)), []).append(p)

    print("runs found:", sorted(by_run))
    for rn in sorted(by_run):
        name = TESTS.get(rn, "unknown_%d" % rn)
        d = RUNS / ("test_%02d_%s" % (rn, name))
        d.mkdir(exist_ok=True)
        inf = raw / ("TypicalGTPMView_r%05d.inf" % rn)
        names = parse_inf(inf)
        for p in by_run[rn]:
            shutil.copy2(p, d / p.name)
        shutil.copy2(inf, d / inf.name)
        df = stitch(by_run[rn], names)
        csv = d / ("data_%s.csv" % stamp)
        df.to_csv(csv, index=False)
        setup = {
            "experiment": "typicalgt_mqt_battery",
            "test_number": rn,
            "test_name": name,
            "dwg_reference": "DWG Procedure Manual Rev. 24",
            "machine": "G_32_0_1_DYR (GENROU+ESST4B+GGOV1+PSS2B, "
                       "650 MVA, 230 kV, H=5.46 s)",
            "rig": "pscad/ copy of TypicalGT_inertia_validation; "
                   "Vrated=230, T0=3 s, multiple-run via master:run_num",
            "duration_s": float(df["TIME"].iloc[-1]),
            "rows": int(len(df)),
            "columns": int(df.shape[1]),
            "source_stamp": stamp,
        }
        (d / "setup.json").write_text(json.dumps(setup, indent=1),
                                      encoding="utf8")
        print("  test %d (%s): %d rows x %d cols, t_end=%.2f s"
              % (rn, name, len(df), df.shape[1],
                 df["TIME"].iloc[-1]))
    print("DONE", time.strftime("%H:%M:%S"))


if __name__ == "__main__":
    main()
