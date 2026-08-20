"""Report-format regeneration of the first-formulation assembly
(report fig:pdeltacct, file pdelta_to_cct_meeting.png).

Same content as make_meeting_figs.pdelta_to_cct() in the
sharp-jackson cct_smib_sync experiment: the two parent transfer
curves (current-unlimited resistance-tilted sine and the
current-limited arc), their composite (the analytical model's
curve), the MEASURED EMT post-clear arc (runs_gfm boundary pair
T0p925/T0p931, loaded and binned via the ORIGINAL helpers
analytic_eq_rails.load_arc_full / bin_arc -- no math copied), the
unstable-equilibrium angle, and the drift span that becomes the CCT
against the EMT-measured interval. Vendor default (ImaxF = 2 pu,
Emax = 1.15). True print width \\textwidth = 6.5 in.
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
           r"\sharp-jackson-1e89b8\experiments\cct_smib_sync")
OUT = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
           r"\upbeat-jones-67c8d3\report_26X\overleaf\figures")
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import analytic_implemented_law as A                   # noqa: E402
import analytic_eq_rails as AER                        # noqa: E402
import figstyle_26x as st                              # noqa: E402

st.apply()                     # AFTER the SRC imports (rcParams)
matplotlib.rcParams["axes.grid"] = False


def main():
    E, k = 1.15, 2.0
    VS, PREF = 1.0, 0.6
    dd = np.linspace(1e-3, np.pi - 1e-3, 900)
    deg = np.degrees(dd)
    p_u = A.p_unlimited(dd, E)
    p_l = VS * k * np.cos(A.phi_implemented(dd, E, k))
    comp = np.where(A.demand(dd, E) >= k, p_l, p_u)

    dd_, ch = [], {}
    for tag, T in (("T0p925", 0.925), ("T0p931", 0.931)):
        d, cols = AER.load_arc_full("runs_gfm", tag, T)
        dd_.append(d)
        for c, v in cols.items():
            ch.setdefault(c, []).append(v)
    d_all = np.concatenate(dd_)
    cd, cp = AER.bin_arc(d_all, np.concatenate(ch["P_pu"]))

    DS, DU = 4.1, 127.0
    fig, ax = plt.subplots(figsize=(st.TEXTWIDTH_IN, 3.8))
    ax.grid(alpha=0.3)
    ax.plot(deg, p_u, color="0.45", ls="--", lw=1.4,
            label="current-unlimited curve (resistance-tilted "
                  "sine, $E_{\\max}$)")
    ax.plot(deg, p_l, color="tab:red", ls="--", lw=1.2, alpha=0.5,
            label=r"current-limited arc "
                  r"$V_s I_{\max F}\cos\phi(\delta)$")
    ax.plot(deg, comp, color="tab:blue", lw=2.2,
            label="analytical model = the two combined "
                  "(mode switch where the limit binds)")
    ax.plot(cd, cp, color="tab:green", lw=1.8,
            label="PSCAD (EMT): measured post-clear arc, binned "
                  "vs $\\delta$")
    ax.axhline(PREF, color="k", lw=1.0, label=r"$P_{ref}$ = 0.6 pu")
    ax.plot(DS, PREF, "o", ms=5, color="k", zorder=6)
    ax.text(DS + 1.5, 0.40, r"$\delta_s$", fontsize=10)
    ax.plot(DU, PREF, "s", ms=7, color="tab:blue", mec="k",
            zorder=6)
    ax.text(DU, 0.78, r"$\delta_u$", fontsize=10, ha="center",
            color="tab:blue")
    ax.annotate("", xy=(DU, 0.34), xytext=(DS, 0.34),
                arrowprops=dict(arrowstyle="-|>", lw=1.8,
                                color="0.25", mutation_scale=16))
    ax.text(0.5 * (DS + DU), 0.15,
            r"fault-on drift: $(127.0^\circ - 4.1^\circ)\,/\,"
            r"129.6^\circ/\mathrm{s} = t_{cr} = 0.948$ s"
            "   [PSCAD: $(0.925, 0.931]$]",
            fontsize=8.5, ha="center", va="center")
    ax.set_xlabel(r"$\delta$ (deg)")
    ax.set_ylabel("delivered $P$ (pu)")
    ax.set_xlim(0, 180)
    ax.set_xticks(range(0, 181, 30))
    ax.set_ylim(0, 6.0)
    ax.legend(fontsize=8.5, loc="upper right")

    fig.savefig(OUT / "pdelta_to_cct_meeting.png", dpi=600)
    print("wrote", OUT / "pdelta_to_cct_meeting.png")


if __name__ == "__main__":
    main()
