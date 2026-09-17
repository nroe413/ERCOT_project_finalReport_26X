"""make_phase_portrait_fig.py - phase portraits that MOTIVATE the
critical-clearing-time boundary (user request 2026-09-02), one panel
per device, using the SAME single-unit models behind the deck numbers:

  synchronous machine (SMIB, results_smib_damping.json):
      H = 5.46 s, P_max = 3.03 pu, P_m = 0.5053 pu, delta_s = 9.6 deg,
      conservative (D = 0)  ->  t_cr = 0.4725 s (equal-area check)
  grid-forming inverter (SIIB, droop, analytic_ilimit constants):
      E = V_s = 1, X_tot = 0.175 (P_max = 5.714), P_ref = 0.6,
      m_p = 0.01, T_PF = 10 ms  ->  droop-equivalent swing
      M = T_PF/(m_p w_s), D = 1/(m_p w_s); limit-free
      delta_u = 173.97 deg, fault-on drift 129.6 deg/s -> 1.296 s

Each panel: level sets of the energy function
    V(delta, w) = 1/2 M w^2 - P(delta - delta_s) - P_max(cos delta - cos delta_s)
(S&P (9.31)-(9.32) form), the CRITICAL level V = V_cr = V_PE(delta_u)
through the unstable equilibrium (the boundary), the bolted-fault
trajectory (P_e = 0) up to its crossing at t_cr, and two post-clear
trajectories: cleared just before t_cr (returns) and just after
(escapes).  Machine: the boundary is a genuine energy level -- speed
counts.  GFM: with D/M = 1/T_PF = 100 1/s the kinetic term is
negligible, so the level sets are near-vertical lines and the boundary
collapses onto delta = delta_u -- CCT = distance / drift speed.

Writes plots/phase_portrait_meeting.png (1000 dpi).  Python 3.7.
"""
import os
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib import font_manager as _fm

ROOT = os.path.dirname(os.path.abspath(__file__))

_TG = Path(r"C:\Users\roena\AppData\Local\Programs\MiKTeX\fonts"
           r"\opentype\public\tex-gyre")
for _f in ("texgyrepagella-regular.otf", "texgyrepagella-bold.otf",
           "texgyrepagella-italic.otf",
           "texgyrepagella-bolditalic.otf"):
    if (_TG / _f).exists():
        _fm.fontManager.addfont(str(_TG / _f))

plt.rcParams.update({"font.family": "serif",
                     "font.serif": ["TeX Gyre Pagella",
                                    "Palatino Linotype",
                                    "STIXGeneral", "DejaVu Serif"],
                     "font.size": 14, "mathtext.fontset": "cm",
                     "axes.unicode_minus": True})

WS = 2.0 * np.pi * 60.0
NAVY, ORANGE, RED, GREEN = "#1E2761", "#E8871E", "#c62828", "#2e7d32"


class Unit(object):
    def __init__(self, name, M, D, P, Pmax, ds):
        self.name, self.M, self.D, self.P, self.Pmax = name, M, D, P, Pmax
        self.ds = ds
        self.du = np.pi - ds

    def vpe(self, d):
        return -self.P * (d - self.ds) - self.Pmax * (np.cos(d)
                                                      - np.cos(self.ds))

    def energy(self, d, w):
        return 0.5 * self.M * w**2 + self.vpe(d)

    def rhs(self, d, w, faulted):
        pe = 0.0 if faulted else self.Pmax * np.sin(d)
        return w, (self.P - pe - self.D * w) / self.M

    def integrate(self, d0, w0, t_end, faulted, dt=1e-4, stop_d=None):
        d, w = d0, w0
        ds, ws = [d], [w]
        n = int(round(t_end / dt))
        for _ in range(n):
            k1 = self.rhs(d, w, faulted)
            k2 = self.rhs(d + 0.5 * dt * k1[0], w + 0.5 * dt * k1[1],
                          faulted)
            k3 = self.rhs(d + 0.5 * dt * k2[0], w + 0.5 * dt * k2[1],
                          faulted)
            k4 = self.rhs(d + dt * k3[0], w + dt * k3[1], faulted)
            d += dt / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
            w += dt / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
            ds.append(d)
            ws.append(w)
            if stop_d is not None and d > stop_d:
                break
        return np.array(ds), np.array(ws)

    def stable(self, t_cl, t_post=3.0, dt=1e-4):
        d1, w1 = self.integrate(self.ds, 0.0, t_cl, True, dt=dt)
        d2, _ = self.integrate(d1[-1], w1[-1], t_post, False, dt=dt,
                               stop_d=self.du + 0.1)
        return d2[-1] <= self.du + 0.1

    def t_cr(self, lo=0.0, hi=3.0, tol=2e-4):
        """True critical clearing time of THIS model by bisection
        (stable = the angle never passes the unstable equilibrium
        after clearing).  Conservative machine: identical to the
        V = V_cr energy criterion."""
        while hi - lo > tol:
            mid = 0.5 * (lo + hi)
            if self.stable(mid):
                lo = mid
            else:
                hi = mid
        tcr = 0.5 * (lo + hi)
        d, w = self.integrate(self.ds, 0.0, tcr, True)
        return tcr, d[-1], w[-1]

    def separatrix(self, wlim, dlim, dt=1e-5):
        """Stable manifold of the saddle (delta_u, 0): start on the
        stable eigenvector and integrate BACKWARD in time until the
        window edge.  For D = 0 this is exactly the V = V_cr level."""
        K = -self.Pmax * np.cos(self.du)          # > 0 at the saddle
        a = self.D / self.M
        lam_s = 0.5 * (-a - np.sqrt(a * a + 4.0 * K / self.M))
        eps = 1e-3
        branches = []
        for sgn in (+1.0, -1.0):
            d, w = self.du + sgn * eps, sgn * eps * lam_s
            ds, ws = [d], [w]
            for _ in range(int(2.0 / dt)):
                f = lambda dd, ww: tuple(-x for x in self.rhs(dd, ww,
                                                               False))
                k1 = f(d, w)
                k2 = f(d + 0.5 * dt * k1[0], w + 0.5 * dt * k1[1])
                k3 = f(d + 0.5 * dt * k2[0], w + 0.5 * dt * k2[1])
                k4 = f(d + dt * k3[0], w + dt * k3[1])
                d += dt / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
                w += dt / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
                ds.append(d)
                ws.append(w)
                if abs(w) > 1.05 * wlim or not (dlim[0] - 5 <
                                                np.degrees(d) < dlim[1] + 5):
                    break
            branches.append((np.array(ds), np.array(ws)))
        return branches


def panel(ax, u, wlim, t_post, title, dlim=(-20.0, 260.0)):
    dd = np.radians(np.linspace(dlim[0], dlim[1], 500))
    ww = np.linspace(-wlim, wlim, 400)
    DD, WW = np.meshgrid(dd, ww)
    V = u.energy(DD, WW)
    vcr = u.vpe(u.du)
    lv = np.linspace(V.min(), vcr + 0.6 * (V.max() - vcr), 26)
    ax.contour(np.degrees(DD), WW, V, levels=sorted(set(lv)),
               colors="0.72", linewidths=0.7)
    for ds, ws in u.separatrix(wlim, dlim):
        ax.plot(np.degrees(ds), ws, color=RED, lw=2.6, zorder=3)

    tcr, dc, wc = u.t_cr()
    # fault-on trajectory up to the boundary crossing
    df, wf = u.integrate(u.ds, 0.0, tcr, True)
    ax.plot(np.degrees(df), wf, color=ORANGE, lw=3.0, zorder=5)
    ax.plot(np.degrees(dc), wc, marker="o", ms=9, color=ORANGE,
            mec="k", zorder=7)
    # cleared just before / just after
    for frac, col in ((0.96, GREEN), (1.04, "#7a1f1f")):
        d1, w1 = u.integrate(u.ds, 0.0, frac * tcr, True)
        d2, w2 = u.integrate(d1[-1], w1[-1], t_post, False,
                             stop_d=np.radians(dlim[1]) + 0.2)
        ax.plot(np.degrees(d2), w2, color=col, lw=1.8, zorder=4,
                ls="-" if frac < 1 else "--")
    ax.plot(np.degrees(u.ds), 0, marker="o", ms=9, color=NAVY, mec="k",
            zorder=8)
    ax.plot(np.degrees(u.du), 0, marker="s", ms=9, color=RED, mec="k",
            zorder=8)
    ax.axhline(0, color="0.5", lw=0.6)
    ax.set_xlim(*dlim)
    ax.set_ylim(-wlim, wlim)
    ax.set_xlabel(r"angle $\delta$ (deg)")
    ax.set_ylabel(r"speed deviation $\dot{\delta}$ (rad/s)")
    ax.set_title("%s:  $t_{cr}$ = %.3f s" % (title, tcr), fontsize=14)
    ax.grid(alpha=0.25)
    return tcr


def main():
    # synchronous machine (SMIB), conservative
    M_m = 2.0 * 5.46 / WS
    mach = Unit("machine", M_m, 0.0, 0.5053, 3.03, np.radians(9.6))
    # grid-forming inverter (SIIB), droop-equivalent swing
    mp, tpf = 0.01, 0.010
    gfm = Unit("gfm", tpf / (mp * WS), 1.0 / (mp * WS), 0.6,
               1.0 / 0.175, np.arcsin(0.6 * 0.175))

    fig, (axa, axb) = plt.subplots(1, 2, figsize=(13.0, 5.4))
    ta = panel(axa, mach, 12.0, 3.0, "synchronous machine (SMIB)")
    tb = panel(axb, gfm, 25.0, 3.0, "grid-forming inverter (SIIB)")
    print("t_cr machine %.4f s   gfm %.4f s" % (ta, tb))

    handles = [
        Line2D([], [], color="0.72", lw=0.9,
               label="energy function $V(\\delta,\\dot\\delta)$ level sets"),
        Line2D([], [], color=RED, lw=2.6,
               label="stability boundary (separatrix)"),
        Line2D([], [], color=ORANGE, lw=3.0, label="fault on"),
        Line2D([], [], color=ORANGE, marker="o", ls="none", ms=9,
               mec="k", label="boundary crossing at $t_{cr}$"),
        Line2D([], [], color=GREEN, lw=1.8, label="cleared before $t_{cr}$"),
        Line2D([], [], color="#7a1f1f", lw=1.8, ls="--",
               label="cleared after $t_{cr}$"),
        Line2D([], [], color=NAVY, marker="o", ls="none", ms=9, mec="k",
               label="stable equilibrium"),
        Line2D([], [], color=RED, marker="s", ls="none", ms=9, mec="k",
               label="unstable equilibrium"),
    ]
    fig.legend(handles=handles, fontsize=11.5, ncol=4,
               loc="upper center", bbox_to_anchor=(0.5, 0.02),
               frameon=False)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    out = os.path.join(ROOT, "plots", "phase_portrait_meeting.png")
    fig.savefig(out, dpi=1000, bbox_inches="tight")
    print("wrote", out)


if __name__ == "__main__":
    main()
