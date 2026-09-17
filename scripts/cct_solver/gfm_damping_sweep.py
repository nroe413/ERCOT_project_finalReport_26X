"""gfm_damping_sweep.py - what the single-inverter energy-method CCT becomes when
the droop damping is scaled down to zero (author's question, 2026-09-12).

Same reduced model and rig as the 1.296 s estimate (analytic_ilimit.py /
make_phase_portrait_fig.py): E = V_s = 1, X_tot = 0.175 (P_max = 5.714 pu),
P* = 0.6 pu, m_p = 0.01, T_Pf = 10 ms, bolted fault (P_e = 0), network intact
after clearing, no current limiter:

    M d2(delta)/dt2 + alpha D d(delta)/dt = P* - P_max sin(delta),
    M = T_Pf/(m_p w_s) = 2.65e-3 pu s^2/rad,   D = 1/(m_p w_s) = 0.265 pu s/rad.

alpha = 1 is the droop device (the report's estimate: overdamped drift,
t_cr = (delta_u - delta_s)/(m_p w_s P*) = 1.296 s); alpha = 0 is the machine
convention applied to the inverter (D = 0, a 0.5 s inertia and nothing else).
The CCT is found by bisection on the RK4 fault-on -> post-fault integration of
the Unit class of make_phase_portrait_fig.py (stable = the angle never passes
the unstable equilibrium after clearing), and for alpha = 0 checked against the
undamped equal-area closed form.

Writes results_gfm_damping_sweep.json and plots/gfm_damping_sweep.png.
Usage: python gfm_damping_sweep.py
"""
import json
import os
import sys
import time

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from make_phase_portrait_fig import Unit, WS   # noqa: E402  (class only; the figure is under __main__)

MP, TPF, PREF, XTOT = 0.01, 0.010, 0.6, 0.175
PMAX = 1.0 / XTOT
DS = float(np.arcsin(PREF * XTOT))
M = TPF / (MP * WS)
D = 1.0 / (MP * WS)
ALPHAS = [0.0, 0.01, 0.03, 0.1, 0.3, 1.0]
EMT_BRACKET = (0.925, 0.931)
DRIFT_TCR = (np.pi - 2.0 * DS) / (MP * WS * PREF)


def undamped_equal_area():
    """Closed form for alpha = 0 with P_e = 0 during the fault: the clearing angle
    delta_cr solves P*(delta_cr - delta_s) = int_{delta_cr}^{delta_u} (P_max sin d - P*) dd,
    and with constant acceleration P*/M, t_cr = sqrt(2 M (delta_cr - delta_s)/P*)."""
    du = np.pi - DS
    lo, hi = DS, du
    for _ in range(200):
        dc = 0.5 * (lo + hi)
        a1 = PREF * (dc - DS)
        a2 = PMAX * (np.cos(dc) - np.cos(du)) - PREF * (du - dc)
        if a1 < a2:
            lo = dc
        else:
            hi = dc
    dc = 0.5 * (lo + hi)
    return dc, float(np.sqrt(2.0 * M * (dc - DS) / PREF))


def main():
    rows = []
    for a in ALPHAS:
        u = Unit("gfm", M, a * D, PREF, PMAX, DS)
        t0 = time.time()
        tcr, d_cl, w_cl = u.t_cr(lo=0.0, hi=3.0, tol=2e-4)
        rows.append(dict(alpha=a, D_pu_s_per_rad=a * D, D_over_M_1_per_s=a * D / M,
                         t_cr_s=round(tcr, 4), delta_cl_deg=round(float(np.degrees(d_cl)), 2),
                         w_cl_rad_s=round(float(w_cl), 3), wall_s=round(time.time() - t0, 1)))
        print("alpha %.2f  D/M %6.1f 1/s  t_cr %.4f s  delta_cl %.1f deg  w_cl %.2f rad/s  (%.0f s)"
              % (a, a * D / M, tcr, np.degrees(d_cl), w_cl, time.time() - t0), flush=True)
    dc, t_ea = undamped_equal_area()
    print("undamped equal-area closed form: delta_cr %.2f deg, t_cr %.4f s" % (np.degrees(dc), t_ea))
    print("overdamped drift closed form (alpha = 1): %.4f s" % DRIFT_TCR)
    out = dict(model=dict(E=1.0, Vs=1.0, Xtot=XTOT, Pmax=PMAX, Pref=PREF, mp=MP, TPf=TPF,
                          M=M, D=D, delta_s_deg=float(np.degrees(DS))),
               sweep=rows, undamped_equal_area=dict(delta_cr_deg=float(np.degrees(dc)), t_cr_s=t_ea),
               drift_closed_form_s=DRIFT_TCR, emt_bracket_s=EMT_BRACKET)
    with open(os.path.join(ROOT, "results_gfm_damping_sweep.json"), "w") as f:
        json.dump(out, f, indent=1)

    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    al = np.array([r["alpha"] for r in rows]); tc = np.array([r["t_cr_s"] for r in rows])
    ax.plot(al[1:], tc[1:], "o-", color="#c62828", lw=1.6, label="reduced droop model, damping scaled by $\\alpha$")
    ax.plot([0.004], [tc[0]], "s", color="#c62828", ms=7, label="$\\alpha=0$ (undamped): %.3f s" % tc[0])
    ax.axhline(DRIFT_TCR, color="#c62828", ls=":", lw=1.0, label="drift closed form, $\\alpha=1$: %.3f s" % DRIFT_TCR)
    ax.axhspan(EMT_BRACKET[0], EMT_BRACKET[1], color="#E8871E", alpha=0.5, label="PSCAD EMT (0.925, 0.931] s")
    ax.set_xscale("log")
    ax.set_xlim(0.003, 1.5)
    ax.set_xlabel("damping scale $\\alpha$  ($D = \\alpha/m_{\\mathrm{p}}$; 0.004 stands for 0)")
    ax.set_ylabel("critical clearing time (s)")
    ax.set_title("Single inverter, infinite bus: energy-method CCT vs droop damping", fontsize=11)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    os.makedirs(os.path.join(ROOT, "plots"), exist_ok=True)
    fig.savefig(os.path.join(ROOT, "plots", "gfm_damping_sweep.png"), dpi=300)
    print("wrote results_gfm_damping_sweep.json and plots/gfm_damping_sweep.png")


if __name__ == "__main__":
    main()
