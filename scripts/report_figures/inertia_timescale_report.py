r"""Report figure fig:inertiatimescale -- why the energy method that
misreads a grid-forming inverter still works on a synchronous machine:
TIME-SCALE SEPARATION.

This is Figure 2 (page 8) of the inertia-estimation note
(resources/Inertia_estimation_3.pdf, section 3.5, "Why the same method
works for a synchronous generator").

EXPLANATORY FIGURE, NOT A DATA PLOT.  Nothing here is measured or
simulated.  Both curves are drawn directly from the closed-form
response of a first-order droop path to a constant-RoCoF frequency
ramp, and the numbers below are chosen only to make the shapes legible.
The axes therefore carry no numeric ticks: the figure asserts a
separation of time scales, not a magnitude.

The algebra.  During a ramp the frequency deviation is
Df(t) = (df/dt) t, so the power deviation of either device is

    Dp(t) = (2H/f_n) df/dt   +   K [ t - tau (1 - e^{-t/tau}) ] ,
            \_____________/       \___________________________/
             inertia level         droop path through 1/(1+tau s)

with K = (droop gain) (df/dt)/f_n.  The inertia term is constant in t
(the "inertia level", dashed).  The droop term is the ramp response of
the first-order lag, which is what separates the two devices:

  * grid-forming inverter -- the droop path is gated only by the
    power-measurement filter, tau = T_PF, milliseconds.  For t >> tau
    the bracket is just (t - tau), so the curve is a steep straight
    line that is already well above the inertia level inside the
    measurement window.

  * synchronous machine -- governor, actuator, turbine and reheater
    lags, approximated in the note (eq. 51) as G_gov(s) = 1/(1+T_gov s)
    with T_gov of several seconds.  For t << tau the bracket is
    t^2/(2 tau), so the curve leaves the inertia level quadratically
    and has barely moved when the window closes.

The steady-state droop gains are deliberately set EQUAL here (the note
observes 1/R_SG = 20-100 pu against 1/m_p ~ 20 pu, i.e. comparable), so
the only thing that differs between the two curves is tau.  The gap at
the window edge is time-scale separation and nothing else.

Illustrative constants: T_PF = 0.02 s, T_gov = 2 s, window T = 0.5 s,
horizon 2.5 s.
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")

OUT = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
           r"\upbeat-jones-67c8d3\report_26X\overleaf\figures")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import figstyle_26x as st                      # noqa: E402
st.apply()
import matplotlib.pyplot as plt                # noqa: E402

INK = "#2d3338"
GFM = "#c0504d"          # droop / grid-forming
SYNC = "#2a7f7f"         # inertia / synchronous

T_PF = 0.02              # power-measurement filter, milliseconds
T_GOV = 2.0              # governor + prime mover, several seconds
T_WIN = 0.5              # inertia-measurement window
T_END = 2.5              # horizon

P_INERTIA = 0.26         # common inertia level, arbitrary vertical unit
K = 0.275                # common droop gain x RoCoF / f_n


def ramp_response(t, tau):
    """Droop power for a constant-RoCoF ramp through 1/(1 + tau s)."""
    t = np.asarray(t, float)
    return K * (t - tau * (1.0 - np.exp(-t / tau)))


def main():
    fig, ax = plt.subplots(figsize=(5.2, 2.6))

    t = np.linspace(0.0, T_END, 800)
    p_gfm = P_INERTIA + ramp_response(t, T_PF)
    p_syn = P_INERTIA + ramp_response(t, T_GOV)

    # measurement window, shaded at the left
    ax.axvspan(0.0, T_WIN, color=INK, alpha=0.07, lw=0)
    ax.axvline(T_WIN, color=INK, lw=0.6, alpha=0.35)

    # the level the energy method wants to read
    ax.axhline(P_INERTIA, color=INK, ls=(0, (3.5, 2.8)), lw=0.85,
               alpha=0.8)

    ax.plot(t, p_gfm, color=GFM, lw=1.7,
            label=r"grid-forming inverter (fast droop, "
                  r"$\tau = T_{\mathrm{PF}}$)")
    ax.plot(t, p_syn, color=SYNC, lw=1.7,
            label=r"synchronous machine (slow governor, "
                  r"$\tau = T_{\mathrm{gov}}$)")

    ax.text(0.06, 0.55, "measurement\nwindow", fontsize=8.5, color=INK,
            ha="left", va="center", linespacing=1.25)
    ax.text(T_END, P_INERTIA + 0.018, "inertia level", fontsize=8.5,
            color=INK, ha="right", va="bottom")

    ax.set_xlim(0.0, T_END)
    ax.set_ylim(0.0, 1.0)
    ax.set_xticks([0.0, T_WIN])
    ax.set_xticklabels(["0", r"$T$"])
    ax.set_yticks([])
    ax.set_xlabel(r"time after the disturbance", labelpad=2)
    ax.set_ylabel(r"power deviation $\Delta p$", labelpad=2)

    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK)
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=INK, length=3, width=0.8)
    ax.xaxis.label.set_color(INK)
    ax.yaxis.label.set_color(INK)

    ax.legend(fontsize=8.5, loc="upper left", frameon=False,
              handlelength=1.6, borderpad=0.2, labelspacing=0.4,
              borderaxespad=0.4)

    out = OUT / "inertia_timescale.png"
    fig.savefig(out, dpi=600)

    rise_g = ramp_response(T_WIN, T_PF)
    rise_s = ramp_response(T_WIN, T_GOV)
    print("closed-form shapes only, no data")
    print("  at the window edge T = %.2f s: droop rise above the "
          "inertia level" % T_WIN)
    print("    grid-forming  %.4f  (%.0f%% of its own 2.5 s rise)"
          % (rise_g, 100 * rise_g / ramp_response(T_END, T_PF)))
    print("    synchronous   %.4f  (%.0f%% of the inverter's)"
          % (rise_s, 100 * rise_s / rise_g))
    print("wrote", out)


if __name__ == "__main__":
    main()
