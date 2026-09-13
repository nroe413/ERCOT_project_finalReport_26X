"""Report figure fig:dampsweep (narr_cct_damping_sweep.png): energy-method critical
clearing time of the reduced droop-inverter models as the droop damping is scaled
from zero to its full value (author's question, 2026-09-12).

Inputs (shipped in data/report_figure_data/cct_damping_sweep, produced on SOW_task_4 by
cct_smib_sync/gfm_damping_sweep.py and cct_energy_function_multiGFM/cct_pebs_constP.py --dscale):
  experiments/cct_smib_sync/results_gfm_damping_sweep.json      (single inverter, infinite bus)
  experiments/cct_energy_function_multiGFM/results_constP.json  (ten inverters, scale 1)
  experiments/cct_energy_function_multiGFM/results_constP_D{0,0.1,0.3}.json
Both models: M = T_Pf/(m_p w_s), D = alpha / (m_p w_s), constant internal voltage, no
current limiter; the fleet case has the constant-power 39-bus network and the bus-14
self-clearing fault. The EMT brackets are the PSCAD measurements of Figure fig:efcct.

Size 0.85 textwidth x 3.1 in, figstyle contract.
"""
import json
import sys
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_paths as rp  # noqa: E402

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = rp.OUT
sys.path.insert(0, str(Path(__file__).resolve().parent))
import figstyle_26x as st  # noqa: E402

st.apply()

RED, DARK, ORANGE = "#c0392b", "#1f2f5c", "#e8821e"
X0 = 0.003            # where alpha = 0 is drawn on the log axis
EMT_SINGLE, EMT_FLEET = (0.925, 0.931), (1.600, 1.700)


def load():
    s = json.load(open(rp.DATA / "cct_damping_sweep" / "results_gfm_damping_sweep.json"))
    single = [(r["alpha"], r["t_cr_s"]) for r in s["sweep"]]
    mg = rp.DATA / "cct_damping_sweep"      # shipped result files of the two sweeps
    fleet = []
    for a, f in ((0.0, "results_constP_D0.json"), (0.1, "results_constP_D0.1.json"),
                 (0.3, "results_constP_D0.3.json"), (1.0, "results_constP.json")):
        fleet.append((a, json.load(open(mg / f))["bus14_noloss"]["tcr_constP_s"]))
    return single, fleet


def main():
    single, fleet = load()
    fig, ax = plt.subplots(figsize=(0.85 * st.TEXTWIDTH_IN, 3.1))
    for pts, col, mk, lab in ((single, RED, "o", "single inverter, infinite bus"),
                              (fleet, DARK, "s", "ten inverters, 39-bus, bus-14 fault")):
        x = np.array([max(a, X0) for a, _ in pts]); y = np.array([t for _, t in pts])
        ax.plot(x[1:], y[1:], marker=mk, color=col, lw=1.6, ms=5, label=lab)
        ax.plot(x[:2], y[:2], color=col, lw=1.2, ls=":")
        ax.plot(x[0], y[0], marker=mk, color=col, ms=5)
    ax.axhspan(*EMT_SINGLE, color=RED, alpha=0.25, lw=0)
    ax.axhline(0.5 * sum(EMT_SINGLE), color=RED, alpha=0.45, lw=2.2)   # 6 ms bracket: thinner than a line
    ax.axhspan(*EMT_FLEET, color=DARK, alpha=0.25, lw=0)
    ax.text(0.0035, EMT_SINGLE[1] + 0.03, "EMT bracket, single inverter", fontsize=7.5, color=RED, va="bottom")
    ax.text(0.0035, EMT_FLEET[1] + 0.03, "EMT bracket, ten inverters", fontsize=7.5, color=DARK, va="bottom")
    ax.set_xscale("log")
    ax.set_xlim(0.0025, 1.4)
    ax.set_xticks([X0, 0.01, 0.03, 0.1, 0.3, 1.0])
    ax.set_xticklabels(["0", "0.01", "0.03", "0.1", "0.3", "1"])
    ax.set_xlabel(r"damping scale $\alpha$ ($D=\alpha/m_{\mathrm{p}}$; $\alpha=1$ is the droop device)")
    ax.set_ylabel("critical clearing time (s)")
    ax.set_ylim(0, 2.6)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="upper left", fontsize=8, framealpha=0.95)
    fig.savefig(OUT / "narr_cct_damping_sweep.png", dpi=600)
    print("wrote", OUT / "narr_cct_damping_sweep.png")
    print("single:", single)
    print("fleet :", fleet)


if __name__ == "__main__":
    main()
