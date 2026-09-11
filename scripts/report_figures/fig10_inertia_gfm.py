"""Report-format regeneration of fig10_inertia_gfm.png (report fig:hgfm,
0.8\\textwidth = 5.2 in): the same AGS-ESR H = 60*dE measurement applied to
the droop REGFM_A1 grid-forming inverter, reading H = 7.44 s with zero
programmed inertia (VSM off).

Data + math reproduced from
sharp-jackson-1e89b8/experiments/agsesr_inertia_response_GFM/inertia_analysis.py
(panel 5), reusing that experiment's _pscad_io loaders on the original PSCAD
run agsesr_freq_inertia_1Hzps_7s.  No synthesized data.
"""
import sys
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_paths as rp  # noqa: E402

import numpy as np
import matplotlib
matplotlib.use("Agg")

EXP = rp.experiment(r"agsesr_inertia_response_GFM")
OUT = rp.OUT
sys.path.insert(0, str(EXP))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _pscad_io import read_run_to_dataframe, find_inf   # noqa: E402
import figstyle_26x as st                               # noqa: E402

st.apply()
import matplotlib.pyplot as plt                         # noqa: E402

FN = 60.0
WIN = 0.5
ZOOM = (1.7, 3.2)
TRAPZ = np.trapezoid if hasattr(np, "trapezoid") else np.trapz

BLUE = "#1f77b4"; ORANGE = "#e08214"; BANDLINE = "#b85042"


def detect_ramp_start(t, fprof):
    f0 = fprof[0]
    moved = np.abs(fprof - f0) > 5e-3
    return t[np.argmax(moved)] if moved.any() else t[0]


def smooth(y, k):
    """Edge-padded k-sample moving average (verbatim from the original)."""
    if k < 2:
        return y
    pad = k // 2
    return np.convolve(np.pad(y, pad, mode="edge"),
                       np.ones(k) / k, mode="same")[pad:pad + len(y)]


def main():
    inf = find_inf(EXP / "runs" / "agsesr_freq_inertia_1Hzps_7s")
    if inf is None:
        raise SystemExit("no .inf found - run data missing")
    df = read_run_to_dataframe(inf)
    t = df["TIME"].values
    P = df["P (Main)"].values                    # already per-unit (A1 native)
    fprof = df["F_profile"].values

    t0 = detect_ramp_start(t, fprof)
    win = (t >= t0) & (t <= t0 + WIN)
    pre = (t >= t0 - WIN) & (t < t0)
    dt = np.median(np.diff(t))
    ksm = max(1, int(round(0.010 / dt)))          # 10 ms ripple filter
    Pf = smooth(P, ksm)
    P0 = float(np.mean(Pf[pre]))
    dE = float(TRAPZ(Pf[win] - P0, t[win]))
    H = 60.0 * abs(dE)
    assert abs(H - 7.44) < 0.02, "H drifted from the published 7.44 s: %.3f" % H

    fig, ax = plt.subplots(figsize=(0.8 * st.TEXTWIDTH_IN, 3.2))
    ax.grid(alpha=0.3)
    ax.plot(t, P, color="#b4b4b4", lw=0.5, alpha=0.7, zorder=1,
            label="$P$, raw")
    ax.plot(t, Pf, color=BLUE, lw=1.4, zorder=3, label="$P$, 10 ms-smoothed")
    ax.fill_between(t, P0, Pf, where=win, color=ORANGE, alpha=0.35, zorder=2,
                    label=r"$\Delta E=\int_{t_0}^{t_0+0.5}(P-P_0)\,dt$")
    ax.axvline(t0, color=BANDLINE, ls="--", lw=0.8)
    ax.axvline(t0 + WIN, color=BANDLINE, ls="--", lw=0.8)
    ax.set_xlim(*ZOOM)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Active power (pu)")
    box = "\n".join([
        r"$H_{\mathrm{est}} = 60\,\Delta E = %.2f$ s" % H,
        r"filtered-droop $H_{\mathrm{eq}} = T_{\mathrm{Pf}}/2m_{\mathrm{p}} = 0.5$ s",
    ])
    ax.text(0.975, 0.06, box, transform=ax.transAxes, ha="right", va="bottom",
            fontsize=9, color="#222222",
            bbox=dict(boxstyle="round,pad=0.4", fc="#f7f7f7", ec="#bbbbbb"))
    ax.legend(loc="upper left", fontsize=9)
    fig.savefig(OUT / "fig10_inertia_gfm.png", dpi=600)
    print("H = %.3f s  dE = %.5f pu.s  t0 = %.3f s" % (H, dE, t0))
    print("wrote", OUT / "fig10_inertia_gfm.png")


if __name__ == "__main__":
    main()
