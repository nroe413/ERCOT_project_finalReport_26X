"""Report figure fig:satblock: why a current limit breaks the classical
energy function.

CORRECTION 2026-08-11. The first version of this figure drew the
limited transfer curve as a flat clip followed by an invented decay.
That is wrong. Once the limiter binds, the device delivers its limited
current at the terminal voltage, so

    P_lim(delta) = I_maxF * V_s * cos(delta/2),

which falls monotonically to zero at 180 deg. It is not flat. The two
branches meet at the binding angle

    delta_I = 2 * arcsin( I_maxF * X / (2 E) ),

and the meeting is exact, not approximate:
    (E V_s / X) sin(delta_I)
      = (E V_s / X) * 2 sin(delta_I/2) cos(delta_I/2)
      = V_s cos(delta_I/2) * [ 2 E sin(delta_I/2) / X ]
      = V_s cos(delta_I/2) * I_maxF .
The script asserts that identity rather than trusting the algebra.

The consequence the figure exists to show: the descending branch of the
limited curve crosses P_ref at

    delta_u,lim = 2 * arccos( P_ref / (I_maxF V_s) ),

well inside the unlimited pi - arcsin(P_ref/P_max), so the basin the
energy function assumes is larger than the one the device has.

Illustrative parameters, chosen so both branches are legible; the study
device's binding angle is nearer 20 deg (Sec. 4.5).
"""
import sys
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_paths as rp  # noqa: E402

import numpy as np
import matplotlib
matplotlib.use("Agg")

OUT = rp.OUT
sys.path.insert(0, str(Path(__file__).resolve().parent))
import figstyle_26x as st                      # noqa: E402
st.apply()
import matplotlib.pyplot as plt                # noqa: E402

INK = "#2d3338"
LIM = "#c0504d"
UNL = "#7f7f7f"

E, VS, X, IMAX, PREF = 1.0, 1.0, 0.5, 1.2, 0.6
PMAX = E * VS / X

d_I = 2 * np.degrees(np.arcsin(IMAX * X / (2 * E)))
d_u_unl = 180 - np.degrees(np.arcsin(PREF / PMAX))
d_u_lim = 2 * np.degrees(np.arccos(PREF / (IMAX * VS)))

# the two branches must agree at the binding angle
_a = PMAX * np.sin(np.radians(d_I))
_b = IMAX * VS * np.cos(np.radians(d_I) / 2)
assert abs(_a - _b) < 1e-9, (_a, _b)


def p_limited(deg):
    """Sine law below the binding angle, current-limited above it."""
    d = np.asarray(deg, float)
    return np.where(d <= d_I,
                    PMAX * np.sin(np.radians(d)),
                    IMAX * VS * np.cos(np.radians(d) / 2))


def main():
    fig, (axB, axP) = plt.subplots(
        1, 2, figsize=(0.9 * st.TEXTWIDTH_IN, 2.35),
        gridspec_kw=dict(width_ratios=[0.85, 1.15], wspace=0.32))

    # ---------------- left: the saturation block -------------------
    axB.set_xlim(-2.05, 2.05)
    axB.set_ylim(-1.5, 1.5)
    axB.axis("off")
    axB.add_patch(plt.Rectangle((-0.62, -0.72), 1.24, 1.44, fill=False,
                                ec=INK, lw=1.0))
    u = np.linspace(-0.5, 0.5, 200)
    axB.plot(u, np.clip(u * 2.2, -0.45, 0.45), color=LIM, lw=1.6)
    axB.plot([-0.5, 0.5], [0, 0], color="#b9c0c4", lw=0.5, zorder=0)
    axB.plot([0, 0], [-0.55, 0.55], color="#b9c0c4", lw=0.5, zorder=0)
    axB.annotate("", xy=(-0.64, 0), xytext=(-1.25, 0),
                 arrowprops=dict(arrowstyle="-|>", lw=0.9, color=INK))
    axB.annotate("", xy=(1.25, 0), xytext=(0.64, 0),
                 arrowprops=dict(arrowstyle="-|>", lw=0.9, color=INK))
    axB.text(-1.45, 0.14, "current\ndemand", fontsize=8.5, color=INK,
             ha="center", va="bottom")
    axB.text(1.45, 0.14, "delivered\ncurrent", fontsize=8.5, color=INK,
             ha="center", va="bottom")
    axB.text(0.52, 0.5, r"$+I_{\max F}$", fontsize=9.5, color=LIM,
             ha="right", va="bottom")
    axB.text(0.52, -0.5, r"$-I_{\max F}$", fontsize=9.5, color=LIM,
             ha="right", va="top")
    axB.text(0, -1.12, "linear until it is not", fontsize=9.5,
             color=INK, ha="center", va="center")

    # ---------------- right: the transfer characteristic ------------
    dd = np.linspace(0, 180, 900)
    axP.plot(dd, PMAX * np.sin(np.radians(dd)), color=UNL, ls="--", lw=1.3,
             label="unlimited")
    axP.plot(dd, p_limited(dd), color=LIM, lw=1.7, label="current limited")
    axP.axhline(PREF, color=INK, lw=0.8, ls=":")
    axP.text(176, PREF + 0.06, r"$P_{\mathrm{ref}}$", fontsize=9.5,
             color=INK, ha="right", va="bottom")

    # Label sits in the gap between the two curves around 60 deg (limited
    # 1.04, unlimited 1.73); at upper right it ran under the legend.
    axP.plot([d_I], [p_limited(d_I)], "o", ms=3.6, color=LIM, zorder=5)
    axP.annotate(r"$\delta_{\mathrm{I}}$: limiter binds", xy=(d_I, p_limited(d_I)),
                 xytext=(62, 1.30), fontsize=9.5, color=INK, ha="left",
                 va="center",
                 arrowprops=dict(arrowstyle="-", lw=0.7, color=INK))

    for d, col in ((d_u_lim, LIM), (d_u_unl, UNL)):
        axP.plot([d], [PREF], "v", ms=5.5, color=col, mec=INK, mew=0.5,
                 zorder=6)
    axP.annotate("", xy=(d_u_lim, 0.24), xytext=(d_u_unl, 0.24),
                 arrowprops=dict(arrowstyle="<->", lw=0.8, color=INK))
    axP.text(0.5 * (d_u_lim + d_u_unl), 0.30, "margin lost", fontsize=9.5,
             color=INK, ha="center", va="bottom")

    axP.set_xlim(0, 180)
    axP.set_ylim(0, PMAX * 1.12)
    axP.set_xticks([0, 45, 90, 135, 180])
    axP.set_xlabel(r"angle $\delta$ (deg)")
    axP.set_ylabel(r"delivered power (pu)")
    axP.grid(alpha=0.25)
    axP.legend(fontsize=9.5, loc="upper left", framealpha=0.95,
               handlelength=1.6, borderpad=0.3)

    out = OUT / "saturation_block.png"
    fig.savefig(out, dpi=600)
    print("delta_I        = %.1f deg" % d_I)
    print("delta_u limited= %.1f deg" % d_u_lim)
    print("delta_u unlim  = %.1f deg" % d_u_unl)
    print("branches agree at delta_I: %.6f == %.6f" % (_a, _b))
    print("wrote", out)


if __name__ == "__main__":
    main()
