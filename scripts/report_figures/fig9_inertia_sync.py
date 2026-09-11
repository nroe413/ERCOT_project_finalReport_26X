"""Report-format regeneration of fig9_inertia_sync.png (report fig:hsync,
0.8\\textwidth = 5.2 in): AGS-ESR inertia measurement H = 60*dE on the
TypicalGT synchronous machine (H = 5.20 s vs 5.46 s nameplate).

Data + math reproduced from
sharp-jackson-1e89b8/experiments/typicalgt_inertia_validation/inertia_analysis.py
(panel 5, the "money plot"), reusing that experiment's _pscad_io loaders on the
original PSCAD run typicalgt_freq_inertia_1Hzps_7s.  No synthesized data.
"""
import sys
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_paths as rp  # noqa: E402

import numpy as np
import matplotlib
matplotlib.use("Agg")

EXP = rp.experiment(r"typicalgt_inertia_validation")
OUT = rp.OUT
sys.path.insert(0, str(EXP))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _pscad_io import read_run_to_dataframe, find_inf   # noqa: E402
import figstyle_26x as st                               # noqa: E402

st.apply()
import matplotlib.pyplot as plt                         # noqa: E402

# constants verbatim from the original generator
FN = 60.0
WIN = 0.5              # spec measurement window, s
H_DYR = 5.46           # nameplate H, IEEE39 TypicalGT.dyr (GENROU, Gen 32)
PRATED = 650.0         # Gen-32 rating, MVA (ETRAN channels are MW)
ZOOM = (2.7, 4.2)
TRAPZ = np.trapezoid if hasattr(np, "trapezoid") else np.trapz

BLUE = "#1f77b4"; ORANGE = "#e08214"; BANDLINE = "#b85042"


def detect_ramp_start(t, fprof):
    f0 = fprof[0]
    moved = np.abs(fprof - f0) > 5e-3
    return t[np.argmax(moved)] if moved.any() else t[0]


def main():
    inf = find_inf(EXP / "runs" / "typicalgt_freq_inertia_1Hzps_7s")
    if inf is None:
        raise SystemExit("no .inf found - run data missing")
    df = read_run_to_dataframe(inf)
    t = df["TIME"].values
    P = df["P (Main)"].values / PRATED          # MW -> pu on machine rating
    fprof = df["F_profile"].values

    t0 = detect_ramp_start(t, fprof)
    win = (t >= t0) & (t <= t0 + WIN)
    pre = (t >= t0 - WIN) & (t < t0)
    P0 = float(np.mean(P[pre]))
    dE = float(TRAPZ(P[win] - P0, t[win]))
    H = 60.0 * abs(dE)
    assert abs(H - 5.20) < 0.02, "H drifted from the published 5.20 s: %.3f" % H

    fig, ax = plt.subplots(figsize=(0.8 * st.TEXTWIDTH_IN, 3.2))
    ax.grid(alpha=0.3)
    ax.plot(t, P, color=BLUE, lw=1.4, label="$P$ (POI), machine per-unit")
    ax.fill_between(t, P0, P, where=win, color=ORANGE, alpha=0.35,
                    label=r"$\Delta E=\int_{t_0}^{t_0+0.5}(P-P_0)\,dt$")
    ax.axvline(t0, color=BANDLINE, ls="--", lw=0.8)
    ax.axvline(t0 + WIN, color=BANDLINE, ls="--", lw=0.8)
    ax.set_xlim(*ZOOM)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Active power (pu)")
    box = "\n".join([
        r"$H_{\mathrm{est}} = 60\,\Delta E = %.2f$ s" % H,
        r"configured $H = %.2f$ s  (%+.1f%%)" % (H_DYR, 100 * (H - H_DYR) / H_DYR),
    ])
    ax.text(0.975, 0.06, box, transform=ax.transAxes, ha="right", va="bottom",
            fontsize=9, color="#222222",
            bbox=dict(boxstyle="round,pad=0.4", fc="#f7f7f7", ec="#bbbbbb"))
    ax.legend(loc="upper left", fontsize=9)
    fig.savefig(OUT / "fig9_inertia_sync.png", dpi=600)
    print("H = %.3f s  dE = %.5f pu.s  t0 = %.3f s" % (H, dE, t0))
    print("wrote", OUT / "fig9_inertia_sync.png")


if __name__ == "__main__":
    main()
