"""Report figure fig:hestfit: the damping-corrected inertia estimator
against the measured window sweep.

This is the report version of the meeting figure "GFM PMView inertia
estimate with modified T" (meeting_update_062426_r4, slide 7/9), whose
original generator is
presentations/meeting_062426/overlay_mp0p1_Hest.py. That script asked
for "CMU Serif", which is not installed on this machine and silently
fell back; this version uses figstyle_26x so the type matches the rest
of the report.

What it shows. The classical estimator neglects damping and therefore
reports, for a droop device,

    H_est = H + D T / 4 = H + T / (4 m_p),

a straight line in the averaging window T with slope 1/(4 m_p) and
intercept the true equivalent inertia H = T_Pf / (2 m_p). At m_p = 0.1
that is slope 2.5 and intercept 0.05 s. The measured PSCAD sweep is
plotted on the same axes: the point is that the measurement follows the
corrected law, so the metric is reading droop, not stored energy.

Measured data: experiments/agsesr_inertia_mp0p1/plots/
window_sweep_metrics.json in the sharp-jackson-1e89b8 worktree. No
number is recomputed here.
"""
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")

EXPD = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
            r"\sharp-jackson-1e89b8\experiments")
OUT = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
           r"\upbeat-jones-67c8d3\report_26X\overleaf\figures")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import figstyle_26x as st                     # noqa: E402
st.apply()
import matplotlib.pyplot as plt               # noqa: E402

INK = "#2d3338"
MEAS = "#1f4e79"
ANA = "#c0504d"

H_TRUE, MP = 0.05, 0.1
SLOPE = 1.0 / (4.0 * MP)


def h_analytic(T):
    return H_TRUE + SLOPE * np.asarray(T, float)


def main():
    m = json.loads((EXPD / "agsesr_inertia_mp0p1" / "plots"
                    / "window_sweep_metrics.json").read_text())
    T_exp = np.array(m["T_list_s"], float)
    H_exp = np.array(m["H_python_s"], float)

    fig, ax = plt.subplots(figsize=(0.8 * st.TEXTWIDTH_IN, 3.1))

    tt = np.linspace(0, 0.55, 100)
    ax.plot(tt, h_analytic(tt), color=ANA, lw=1.6,
            label=r"corrected law $H+T/(4m_p)$")
    ax.plot(T_exp, h_analytic(T_exp), "s", color=ANA, ms=5,
            mec=INK, mew=0.4, label="corrected law, at the swept windows")
    ax.plot(T_exp, H_exp, "o", color=MEAS, ms=5.5, mec=INK, mew=0.4,
            label="PSCAD measured")

    # "~" is a LaTeX non-breaking space; matplotlib mathtext renders it
    # literally outside math mode, so it printed as a tilde. Plain space.
    # Label sits low-right where the axes are empty; at 0.30 it crossed
    # the fitted line.
    ax.axhline(H_TRUE, color=INK, ls=":", lw=0.9)
    ax.annotate(r"equivalent inertia $H=T_{Pf}/2m_p=0.05$ s",
                xy=(0.075, H_TRUE), xytext=(0.155, 0.155), fontsize=8.5,
                color=INK, ha="left", va="bottom",
                arrowprops=dict(arrowstyle="-", lw=0.7, color=INK))

    ax.set_xlim(0, 0.55)
    ax.set_ylim(0, 1.45)
    ax.set_xlabel(r"averaging window $T$ (s)")
    ax.set_ylabel(r"reported inertia $H_{\rm est}$ (s)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8.5, loc="upper left", framealpha=0.95,
              handlelength=1.7, borderpad=0.35)

    out = OUT / "hest_corrected.png"
    fig.savefig(out, dpi=600)
    print("m_p = %.2f, slope 1/(4 m_p) = %.2f, intercept H = %.3f s"
          % (MP, SLOPE, H_TRUE))
    for t, he, ha in zip(T_exp, H_exp, h_analytic(T_exp)):
        print("  T=%.2f  measured %.3f  corrected law %.3f  err %+.1f%%"
              % (t, he, ha, 100 * (ha - he) / he))
    print("wrote", out)


if __name__ == "__main__":
    main()
