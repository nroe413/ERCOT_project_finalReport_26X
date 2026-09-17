"""cct_pebs.py - critical clearing time of the all-GFM IEEE 39-bus system by
the transient-energy-function / PEBS method (Sauer & Pai Ch. 9, Secs 9.6.4-9.7,
Example 9.5), with the synchronous-machine swing replaced by the droop-GFM
swing of Inertia_estimation_3.pdf eq. (20):

    M_i d2(delta_i)/dt2 + D_i d(delta_i)/dt = Pm_i - Pe_i(delta),
    M_i = TPF/(mp_i ws) * (Mb_i/SB),   D_i = 1/(mp_i ws) * (Mb_i/SB)

(equivalently H_eqv = TPF/2mp, D_pu = 1/mp on the unit's own base).  Because
D_i/M_i = 1/TPF is IDENTICAL for every unit (uniform damping), the COI
transformation is exact and the COI damping-correction term vanishes:
sum_j D_j w~_j = (1/TPF) sum_j M_j w~_j = 0.

Three-step procedure (Sauer 9.5/9.6.4):
 1. energy function V = VKE + Vp + Vd for the POSTFAULT reduced system,
    trapezoidal path term (9.51) with the structure-change constant (9.55);
 2. Vcr from the PEBS crossing of the sustained-fault trajectory
    (fT(theta).(theta-theta_s) = 0, also ~ max VPE);
 3. tcr = first time V(theta,w~) = Vcr on the fault-on trajectory.

Internal verification: the classical model's "true" CCT by bisection on the
clearing time (full damped fault-on -> postfault integration), so the PEBS
estimate is checked against the same model before any PSCAD comparison.

Usage:  python cct_pebs.py            (bus-14 PSCAD scenario + sensitivity)
"""
import json
import numpy as np
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import ieee39_data as d39

plt.rcParams.update({
    "font.family": "serif", "font.size": 12, "mathtext.fontset": "cm",
    "figure.dpi": 150, "axes.grid": True, "axes.unicode_minus": True,
})
BLUE, RED, GREEN, ORANGE, GRAY = "#1f77b4", "#c0392b", "#2ca02c", "#e08214", "#7f7f7f"

ROOT = Path(__file__).resolve().parent
PLOTS = ROOT / "plots"
PLOTS.mkdir(exist_ok=True)

NB = 39
GBUS = d39.GEN_BUSES          # [30..39]
M_GFM = len(GBUS)


# ============================= network / power flow ========================

def ybus(branches, nb=NB):
    Y = np.zeros((nb, nb), complex)
    for (f, t, r, x, b, tap) in branches:
        f -= 1; t -= 1
        y = 1.0 / complex(r, x)
        tp = tap if tap else 1.0
        Y[f, f] += (y + 1j * b / 2.0) / tp**2
        Y[t, t] += y + 1j * b / 2.0
        Y[f, t] += -y / tp
        Y[t, f] += -y / tp
    return Y


def power_flow(tol=1e-10, itmax=40):
    """Newton PF, polar, numerical Jacobian.  Returns V (complex, 39)."""
    Y = ybus(d39.BRANCHES)
    Pd = np.zeros(NB); Qd = np.zeros(NB)
    for b, (p, q) in d39.LOADS.items():
        Pd[b - 1] = p; Qd[b - 1] = q
    Pg = np.zeros(NB)
    Vset = {}
    for b, (pg, vs) in d39.GENS.items():
        Vset[b - 1] = vs
        if pg is not None:
            Pg[b - 1] = pg / d39.SBASE
    sl = d39.SLACK_BUS - 1
    pv = [b - 1 for b in GBUS if b - 1 != sl]
    pq = [i for i in range(NB) if i not in pv and i != sl]

    th = np.zeros(NB)
    Vm = np.ones(NB)
    for i, vs in Vset.items():
        Vm[i] = vs

    Psp = Pg - Pd; Qsp = -Qd
    idx_th = [i for i in range(NB) if i != sl]
    idx_vm = pq

    def mism(th, Vm):
        V = Vm * np.exp(1j * th)
        S = V * np.conj(Y @ V)
        dP = S.real - Psp
        dQ = S.imag - Qsp
        return np.concatenate([dP[idx_th], dQ[idx_vm]])

    x = np.concatenate([th[idx_th], Vm[idx_vm]])
    n1 = len(idx_th)
    for it in range(itmax):
        th[idx_th] = x[:n1]; Vm[idx_vm] = x[n1:]
        F = mism(th, Vm)
        if np.max(np.abs(F)) < tol:
            break
        J = np.zeros((len(F), len(x)))
        h = 1e-7
        for k in range(len(x)):
            xp = x.copy(); xp[k] += h
            th2 = th.copy(); Vm2 = Vm.copy()
            th2[idx_th] = xp[:n1]; Vm2[idx_vm] = xp[n1:]
            J[:, k] = (mism(th2, Vm2) - F) / h
        x = x - np.linalg.solve(J, F)
    th[idx_th] = x[:n1]; Vm[idx_vm] = x[n1:]
    V = Vm * np.exp(1j * th)
    S = V * np.conj(ybus(d39.BRANCHES) @ V)
    resid = float(np.max(np.abs(mism(th, Vm))))
    return V, S, resid


# ====================== classical model construction =======================

class GFMSystem(object):
    """Reduced internal-node classical model of the 10-GFM 39-bus system."""

    def __init__(self, xg_pu_mbase=None):
        self.xg = d39.XG_PU_MBASE if xg_pu_mbase is None else xg_pu_mbase
        V, S, resid = power_flow()
        self.V0, self.pf_resid = V, resid

        # generator outputs (PF injection + local load) and internal EMFs
        Pd = np.zeros(NB); Qd = np.zeros(NB)
        for b, (p, q) in d39.LOADS.items():
            Pd[b - 1] = p; Qd[b - 1] = q
        self.E = np.zeros(M_GFM); self.d0 = np.zeros(M_GFM)
        self.Pg = np.zeros(M_GFM)
        for k, b in enumerate(GBUS):
            i = b - 1
            Sg = complex(S[i].real + Pd[i], S[i].imag + Qd[i])
            Ii = np.conj(Sg / V[i])
            Eph = V[i] + 1j * d39.gfm_xg_sys(b, self.xg) * Ii
            self.E[k] = abs(Eph)
            self.d0[k] = np.angle(Eph)
            self.Pg[k] = Sg.real

        # swing parameters (system base), uniform damping ratio 1/TPF
        self.M = np.zeros(M_GFM); self.D = np.zeros(M_GFM); self.H = np.zeros(M_GFM)
        for k, b in enumerate(GBUS):
            self.M[k], self.D[k], self.H[k] = d39.gfm_MD(b)
        self.MT = float(np.sum(self.M))

        # load admittances at PF voltages (constant-Z conversion)
        self.yload = np.zeros(NB, complex)
        for b, (p, q) in d39.LOADS.items():
            i = b - 1
            self.yload[i] = np.conj(complex(p, q)) / abs(V[i])**2

        # Pm from prefault reduced network at delta0 (exact equilibrium)
        Gp, Bp = self.reduced_Y(d39.BRANCHES, fault_bus=None)
        self.Pm = self.pe_vec(self.d0, Gp, Bp)
        self.m = M_GFM
        self.buses = list(GBUS)
        self.active = list(range(M_GFM))

    def subsystem(self, active):
        """Shallow view with a subset of the fleet (islanded GFMs removed).
        Pm keeps the prefault dispatch of the surviving units; the resulting
        generation deficit is absorbed by the COI (uniform frequency drift)."""
        import copy
        s = copy.copy(self)
        s.active = list(active)
        s.E = self.E[s.active]; s.d0 = self.d0[s.active]
        s.M = self.M[s.active]; s.D = self.D[s.active]; s.H = self.H[s.active]
        s.Pm = self.Pm[s.active]; s.Pg = self.Pg[s.active]
        s.MT = float(np.sum(s.M))
        s.m = len(s.active)
        s.buses = [GBUS[k] for k in s.active]
        base_reduced = GFMSystem.reduced_Y
        s.reduced_Y = lambda branches, fault_bus=None, dead_buses=(): \
            base_reduced(self, branches, fault_bus=fault_bus,
                         dead_buses=dead_buses, active=s.active)
        return s

    # ---- augmented Y and Kron reduction to the active internal nodes ----
    def _assemble(self, branches, fault_bus=None, dead_buses=(), active=None):
        act = list(range(M_GFM)) if active is None else list(active)
        n = NB + M_GFM
        Y = np.zeros((n, n), complex)
        Y[:NB, :NB] = ybus(branches)
        Y[np.arange(NB), np.arange(NB)] += self.yload
        for k, b in enumerate(GBUS):
            i, g = b - 1, NB + k
            yg = 1.0 / (1j * d39.gfm_xg_sys(b, self.xg))
            Y[i, i] += yg; Y[g, g] += yg
            Y[i, g] -= yg; Y[g, i] -= yg
        drop = set()
        if fault_bus is not None:
            drop.add(fault_bus - 1)          # bolted 3PG: V=0 -> delete row/col
        for b in dead_buses:
            drop.add(b - 1)                  # isolated bus (no load/lines)
        for k in range(M_GFM):               # islanded GFMs leave the model
            if k not in act:
                drop.add(NB + k)
        keep = [i for i in range(n) if i not in drop]
        Y = Y[np.ix_(keep, keep)]
        gi = [keep.index(NB + k) for k in act]
        oi = [i for i in range(len(keep)) if i not in gi]
        return Y, keep, gi, oi

    def reduced_Y(self, branches, fault_bus=None, dead_buses=(), active=None):
        Y, keep, gi, oi = self._assemble(branches, fault_bus, dead_buses, active)
        YII = Y[np.ix_(gi, gi)]; YIO = Y[np.ix_(gi, oi)]
        YOI = Y[np.ix_(oi, gi)]; YOO = Y[np.ix_(oi, oi)]
        Yr = YII - YIO @ np.linalg.solve(YOO, YOI)
        return Yr.real, Yr.imag

    def recon_ops(self, branches, fault_bus=None, dead_buses=(), active=None):
        """Operators to reconstruct the eliminated bus voltages from the
        internal EMFs:  V_other = -YOO^-1 YOI E.  Returns (map_other, R)
        where map_other[j] = original node index of eliminated row j."""
        Y, keep, gi, oi = self._assemble(branches, fault_bus, dead_buses, active)
        YOI = Y[np.ix_(oi, gi)]; YOO = Y[np.ix_(oi, oi)]
        R = -np.linalg.solve(YOO, YOI)
        return [keep[j] for j in oi], R

    # ---- electrical power / accelerating power on given reduced network ----
    def pe_vec(self, delta, G, B):
        E = self.E
        Cm = np.outer(E, E) * B
        Dm = np.outer(E, E) * G
        dd = delta[:, None] - delta[None, :]
        Pe = E**2 * np.diag(G) + np.sum(Cm * np.sin(dd) + Dm * np.cos(dd), axis=1) \
            - np.diag(Cm * np.sin(dd) + Dm * np.cos(dd))
        return Pe

    def f_coi(self, th, G, B):
        """COI accelerating power f_i(theta) incl. the (Mi/MT)Pcoi term."""
        Pe = self.pe_vec(th, G, B)
        Pi = self.Pm - self.E**2 * np.diag(G)
        Dm = np.outer(self.E, self.E) * G
        dd = th[:, None] - th[None, :]
        Pcoi = np.sum(Pi) - np.sum(np.triu(2.0 * Dm * np.cos(dd), 1))
        return self.Pm - Pe - self.M / self.MT * Pcoi

    # ---- COI helpers ----
    def to_coi(self, delta):
        d0 = float(np.sum(self.M * delta) / self.MT)
        return delta - d0

    def sep(self, G, B, th_guess):
        """Postfault COI s.e.p. via Newton on the m-1 free angles."""
        m = self.m
        th = th_guess.copy()

        def full(thm1):
            th_m = -np.sum(self.M[:m - 1] * thm1) / self.M[m - 1]
            return np.concatenate([thm1, [th_m]])

        x = th[:m - 1].copy()
        for it in range(60):
            F = self.f_coi(full(x), G, B)[:m - 1]
            if np.max(np.abs(F)) < 1e-11:
                break
            J = np.zeros((m - 1, m - 1)); h = 1e-7
            for k in range(m - 1):
                xp = x.copy(); xp[k] += h
                J[:, k] = (self.f_coi(full(xp), G, B)[:m - 1] - F) / h
            dx = np.linalg.solve(J, F)
            # damped Newton for robustness
            lam = 1.0
            while lam > 1e-3:
                xn = x - lam * dx
                if np.max(np.abs(self.f_coi(full(xn), G, B)[:m - 1])) < np.max(np.abs(F)):
                    break
                lam *= 0.5
            x = x - lam * dx
        return full(x), float(np.max(np.abs(self.f_coi(full(x), G, B))))

    # ---- energy function on the postfault network ----
    def energy_terms(self, th, w, ths, G, B):
        """VKE and the analytic potential part Vp (path term handled outside)."""
        Pi = self.Pm - self.E**2 * np.diag(G)
        Cm = np.outer(self.E, self.E) * B
        VKE = 0.5 * float(np.sum(self.M * w**2))
        Vp = -float(np.sum(Pi * (th - ths)))
        dd = th[:, None] - th[None, :]
        dds = ths[:, None] - ths[None, :]
        Vp -= float(np.sum(np.triu(Cm * (np.cos(dd) - np.cos(dds)), 1)))
        return VKE, Vp


# ============================ trajectory machinery ==========================

def integrate(sys, th0, w0, G, B, t_end, dt=2e-4, record_every=5):
    """RK4 of  th' = w,  M w' = f_coi(th) - D w   on network (G,B)."""
    th, w = th0.copy(), w0.copy()
    Minv = 1.0 / sys.M
    ts, THS, WS_ = [0.0], [th.copy()], [w.copy()]

    def rhs(th, w):
        return w, (sys.f_coi(th, G, B) - sys.D * w) * Minv

    n = int(round(t_end / dt))
    for k in range(1, n + 1):
        k1t, k1w = rhs(th, w)
        k2t, k2w = rhs(th + 0.5 * dt * k1t, w + 0.5 * dt * k1w)
        k3t, k3w = rhs(th + 0.5 * dt * k2t, w + 0.5 * dt * k2w)
        k4t, k4w = rhs(th + dt * k3t, w + dt * k3w)
        th = th + dt / 6.0 * (k1t + 2 * k2t + 2 * k3t + k4t)
        w = w + dt / 6.0 * (k1w + 2 * k2w + 2 * k3w + k4w)
        if k % record_every == 0:
            ts.append(k * dt); THS.append(th.copy()); WS_.append(w.copy())
    return np.array(ts), np.array(THS), np.array(WS_)


def vd_trapezoid(sys, THS, ths, th_o, G, B):
    """Path-dependent transfer-conductance term Vd(t) along a trajectory,
    trapezoidal rule (9.51), initialized with the (9.55) constant using the
    fault-on start th_o and the postfault s.e.p ths."""
    Dm = np.outer(sys.E, sys.E) * G
    m = sys.m
    iu, ju = np.triu_indices(m, 1)
    # (9.55) structure-change constant
    I = 0.5 * Dm[iu, ju] * (np.cos(th_o[iu] - th_o[ju]) + np.cos(ths[iu] - ths[ju])) \
        * ((th_o[iu] + th_o[ju]) - (ths[iu] + ths[ju]))
    out = np.zeros(len(THS))
    out[0] = np.sum(I)
    for k in range(1, len(THS)):
        a, b = THS[k], THS[k - 1]
        I = I + 0.5 * Dm[iu, ju] * (np.cos(a[iu] - a[ju]) + np.cos(b[iu] - b[ju])) \
            * ((a[iu] + a[ju]) - (b[iu] + b[ju]))
        out[k] = np.sum(I)
    return out


# ================================ PEBS run ==================================

def pebs_cct(sys, fault_bus, post_branches, dead_buses=(), t_int=4.0,
              label="", make_plots=True, active=None):
    """Steps 1-3.  Returns dict of results."""
    if active is not None:
        sys = sys.subsystem(active)
    GF, BF = sys.reduced_Y(d39.BRANCHES, fault_bus=fault_bus)
    GP, BP = sys.reduced_Y(post_branches, fault_bus=None, dead_buses=dead_buses)

    th0 = sys.to_coi(sys.d0)
    ths, sep_resid = sys.sep(GP, BP, th0)

    # fault-on trajectory (damped, COI)
    ts, TH, W = integrate(sys, th0, np.zeros(sys.m), GF, BF, t_int)

    # energy on postfault parameters
    VKE = np.zeros(len(ts)); Vp = np.zeros(len(ts)); g = np.zeros(len(ts))
    for k in range(len(ts)):
        VKE[k], Vp[k] = sys.energy_terms(TH[k], W[k], ths, GP, BP)
        g[k] = float(np.sum(sys.f_coi(TH[k], GP, BP) * (TH[k] - ths)))
    Vd = vd_trapezoid(sys, TH, ths, th0, GP, BP)
    VPE = Vp + Vd
    V = VKE + VPE

    # PEBS crossing: g goes - -> + ; also VPE max
    cross = None
    for k in range(1, len(ts)):
        if g[k - 1] < 0.0 <= g[k]:
            cross = k - 1 + (0.0 - g[k - 1]) / (g[k] - g[k - 1])
            break
    kmax = int(np.argmax(VPE))
    if cross is not None:
        kc = int(np.floor(cross)); fr = cross - kc
        Vcr = float((1 - fr) * VPE[kc] + fr * VPE[kc + 1])
        t_pebs = float((1 - fr) * ts[kc] + fr * ts[kc + 1])
    else:
        Vcr = float(VPE[kmax]); t_pebs = float(ts[kmax])

    # tcr: first V(t) = Vcr
    tcr = None
    for k in range(1, len(ts)):
        if V[k - 1] < Vcr <= V[k]:
            fr = (Vcr - V[k - 1]) / (V[k] - V[k - 1])
            tcr = float(ts[k - 1] + fr * (ts[k] - ts[k - 1]))
            break

    pebs_found = cross is not None
    res = {"label": label, "fault_bus": fault_bus, "xg_pu_mbase": sys.xg,
           "pebs_crossing_found": pebs_found,
           "sep_residual": sep_resid, "pf_residual": sys.pf_resid,
           "t_pebs_s": t_pebs, "Vcr_pu": Vcr,
           "tcr_pebs_s": tcr, "VPE_max_pu": float(VPE[kmax]),
           "t_VPEmax_s": float(ts[kmax])}

    if make_plots:
        tag = label or ("bus%d" % fault_bus)
        fig, ax = plt.subplots(figsize=(9.5, 5.4))
        ax.plot(ts, V, color=BLUE, lw=1.8, label=r"$V = V_{KE}+V_{PE}$")
        ax.plot(ts, VPE, color=RED, lw=1.8, label=r"$V_{PE} = V_p + V_d$")
        ax.plot(ts, VKE, color=GRAY, lw=1.2, ls="--", label=r"$V_{KE}$")
        ax.axhline(Vcr, color=GREEN, ls=":", lw=1.5)
        ax.text(0.01, Vcr, r"$V_{cr}$", color=GREEN, va="bottom", fontsize=12)
        if tcr:
            ax.axvline(tcr, color=GREEN, ls="-.", lw=1.4)
            ax.text(tcr, ax.get_ylim()[0], "  $t_{cr}$=%.3f s" % tcr,
                    color=GREEN, va="bottom", fontsize=12)
        ax.axvline(t_pebs, color=ORANGE, ls=":", lw=1.2)
        ax.text(t_pebs, ax.get_ylim()[1] * 0.97, " PEBS", color=ORANGE,
                va="top", fontsize=10)
        ax.set_xlabel("fault-on time (s)"); ax.set_ylabel("energy (pu)")
        ax.set_title("Transient energy along the sustained-fault trajectory (%s)" % tag)
        ax.legend(loc="upper left"); ax.set_xlim(0, min(t_int, t_pebs * 1.6))
        fig.tight_layout()
        fig.savefig(PLOTS / ("energy_%s.png" % tag), bbox_inches="tight",
                    facecolor="white")
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(9.5, 4.6))
        ax.plot(ts, g, color=BLUE, lw=1.6)
        ax.axhline(0, color=GRAY, lw=0.8)
        ax.axvline(t_pebs, color=ORANGE, ls=":", lw=1.4)
        ax.set_xlabel("fault-on time (s)")
        ax.set_ylabel(r"$f^T(\theta)\,(\theta-\theta^s)$")
        ax.set_title("PEBS crossing detector (%s)" % tag)
        ax.set_xlim(0, min(t_int, t_pebs * 1.6))
        fig.tight_layout()
        fig.savefig(PLOTS / ("pebs_dot_%s.png" % tag), bbox_inches="tight",
                    facecolor="white")
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(9.5, 5.2))
        for k, b in enumerate(sys.buses):
            ax.plot(ts, np.degrees(TH[:, k]), lw=1.3, label="GFM %d" % b)
        ax.set_xlabel("fault-on time (s)"); ax.set_ylabel("COI angle (deg)")
        ax.set_title("Sustained-fault COI angles (%s)" % tag)
        ax.legend(ncol=5, fontsize=9); ax.set_xlim(0, min(t_int, t_pebs * 1.6))
        fig.tight_layout()
        fig.savefig(PLOTS / ("angles_%s.png" % tag), bbox_inches="tight",
                    facecolor="white")
        plt.close(fig)

    return res, (ts, TH, W, V, VPE, g, ths, (GF, BF), (GP, BP))


# ====================== classical-model true CCT (bisection) ===============

def stable_after_clearing(sys, t_cl, GF, BF, GP, BP, ths, t_post=6.0):
    th0 = sys.to_coi(sys.d0)
    ts, TH, W = integrate(sys, th0, np.zeros(sys.m), GF, BF, t_cl,
                          record_every=50)
    ts2, TH2, W2 = integrate(sys, TH[-1], W[-1], GP, BP, t_post,
                             record_every=50)
    # unstable if any COI angle diverges far beyond the s.e.p spread
    spread = np.max(np.abs(TH2 - ths[None, :]))
    settled = np.max(np.abs(W2[-1])) < 1e-3 and \
        np.max(np.abs(TH2[-1] - ths)) < 0.8
    return bool(settled and spread < np.pi), float(spread)


def true_cct(sys, GF, BF, GP, BP, ths, lo=0.0, hi=4.0, tol=5e-3):
    """Bisection on clearing time in the classical model itself."""
    ok_lo, _ = stable_after_clearing(sys, max(lo, 1e-3), GF, BF, GP, BP, ths)
    if not ok_lo:
        return 0.0
    ok_hi, _ = stable_after_clearing(sys, hi, GF, BF, GP, BP, ths)
    if ok_hi:
        return float("inf")
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        ok, _ = stable_after_clearing(sys, mid, GF, BF, GP, BP, ths)
        if ok:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ================================== main ====================================

def branches_without(pairs):
    gone = {tuple(sorted(p)) for p in pairs}
    return [b for b in d39.BRANCHES if tuple(sorted((b[0], b[1]))) not in gone]


def main():
    out = {"cases": [], "sensitivity": []}

    # ---- the PSCAD-validated scenario: 3PG at bus 14, lines stay tripped ----
    sys = GFMSystem()
    post = branches_without([(4, 14), (13, 14), (14, 15)])
    res, aux = pebs_cct(sys, 14, post, dead_buses=(14,),
                        label="bus14_norecl", t_int=4.0)
    ts, TH, W, V, VPE, g, ths, (GF, BF), (GP, BP) = aux
    t_true = true_cct(sys, GF, BF, GP, BP, ths)
    res["tcr_true_classical_s"] = t_true
    out["cases"].append(res)
    print("[bus14 norecl xg=%.2f]  PEBS tcr=%.3f s | Vcr=%.3f | true(classical)=%.3f s"
          % (sys.xg, res["tcr_pebs_s"] or -1, res["Vcr_pu"], t_true))

    # ---- the bus-10 PSCAD scenario: 3PG at bus 10, lines 10-11/10-13 out,
    #      bus 10 + GFM-32 islanded -> 9-GFM postfault system ----
    act9 = [k for k in range(M_GFM) if GBUS[k] != 32]
    post10 = branches_without([(10, 11), (10, 13)])
    res10, aux10 = pebs_cct(sys, 10, post10, dead_buses=(10,),
                            label="bus10_island", t_int=4.0, active=act9)
    _, _, _, _, _, _, ths10, (GF10, BF10), (GP10, BP10) = aux10
    sub9 = sys.subsystem(act9)
    res10["tcr_true_classical_s"] = true_cct(sub9, GF10, BF10, GP10, BP10, ths10)
    out["cases"].append(res10)
    print("[bus10 island xg=%.2f]  PEBS tcr=%.3f s | Vcr=%.3f | true=%.3f s"
          % (sys.xg, res10["tcr_pebs_s"] or -1, res10["Vcr_pu"],
             res10["tcr_true_classical_s"]))

    # ---- same fault, self-clearing (no line loss) for reference ----
    res2, aux2 = pebs_cct(sys, 14, d39.BRANCHES, dead_buses=(),
                          label="bus14_noloss", t_int=4.0)
    ts2, TH2, W2, V2, VPE2, g2, ths2, (GF2, BF2), (GP2, BP2) = aux2
    t_true2 = true_cct(sys, GF2, BF2, GP2, BP2, ths2)
    res2["tcr_true_classical_s"] = t_true2
    out["cases"].append(res2)
    print("[bus14 noloss xg=%.2f]  PEBS tcr=%.3f s | Vcr=%.3f | true=%.3f s"
          % (sys.xg, res2["tcr_pebs_s"] or -1, res2["Vcr_pu"], t_true2))

    # ---- a few other fault buses (self-clearing) ----
    for fb in (16, 4, 26):
        r, aux3 = pebs_cct(sys, fb, d39.BRANCHES, label="bus%d_noloss" % fb,
                           t_int=4.0, make_plots=False)
        _, _, _, _, _, _, ths3, (GF3, BF3), (GP3, BP3) = aux3
        r["tcr_true_classical_s"] = true_cct(sys, GF3, BF3, GP3, BP3, ths3)
        out["cases"].append(r)
        print("[bus%d noloss]  PEBS tcr=%.3f s | true=%.3f s"
              % (fb, r["tcr_pebs_s"] or -1, r["tcr_true_classical_s"]))

    # ---- Xg sensitivity on the PSCAD scenario ----
    for xg in (0.05, 0.10, 0.15, 0.20, 0.25):
        s2 = GFMSystem(xg_pu_mbase=xg)
        r, aux4 = pebs_cct(s2, 14, post, dead_buses=(14,),
                           label="xg%02d" % int(xg * 100), t_int=4.0,
                           make_plots=False)
        _, _, _, _, _, _, ths4, (GF4, BF4), (GP4, BP4) = aux4
        r["tcr_true_classical_s"] = true_cct(s2, GF4, BF4, GP4, BP4, ths4)
        out["sensitivity"].append(r)
        print("[xg=%.2f]  PEBS tcr=%.3f s | true=%.3f s"
              % (xg, r["tcr_pebs_s"] or -1, r["tcr_true_classical_s"]))

    # sensitivity figure
    xs = [r["xg_pu_mbase"] for r in out["sensitivity"]]
    tp = [r["tcr_pebs_s"] for r in out["sensitivity"]]
    tt = [r["tcr_true_classical_s"] for r in out["sensitivity"]]
    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    ax.plot(xs, tp, "o-", color=BLUE, lw=1.8, ms=7, label="PEBS estimate")
    ax.plot(xs, tt, "s--", color=RED, lw=1.6, ms=7, label="classical model (bisection)")
    ax.set_xlabel(r"GFM coupling reactance $X_g$ (pu on own Mbase)")
    ax.set_ylabel(r"critical clearing time $t_{cr}$ (s)")
    ax.set_title("CCT vs GFM coupling reactance - 3PG at bus 14 (lines 4-14/13-14/14-15 out)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS / "cct_vs_xg.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)

    (ROOT / "results.json").write_text(json.dumps(out, indent=2))
    print("wrote results.json + plots/")


if __name__ == "__main__":
    main()
