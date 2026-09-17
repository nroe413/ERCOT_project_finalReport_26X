"""cct_p39_tier3.py - TIER-3 multi-machine theory: CONSTANT-POWER loads
(the EMT model's actual load law - Electranix_Load LoadType=0, found
2026-07-21) + the tier-2 E' flux decay. This is the genuine Bergen-Hill
/ Sauer Ch. 9 structure-preserving regime: constant-P loads cannot be
absorbed into the Y-bus, so the retained-network formulation is not a
representation choice anymore - it is required, and its load terms
change the answer.

Network layer: machines = E' behind x'd (fixed internal-node voltage);
load buses = constant-P/Q injections for |V| >= Vth*V0, impedance
continuation (S ~ V^2) below Vth (EMT converters clamp at deep sags;
Vth = 0.5 default, sensitivity 0.3/0.7). Solve by damped fixed-point
V = A(E) + B I_load(V) with B = Yoo^-1 factorized once per network.

Deliverables (all vs measured EMT CCT (0.237, 0.25] s):
  tier-1P : constant-E', constant-P loads     (load effect alone)
  tier-3  : E' flux decay + constant-P loads  (full correction)
Both as TRUE CCT (bisection, bounded spread). Energy screen: the exact
path-integral V_PE = int sum(Pe-Pm) d(delta) machinery works for ANY
load law; PEBS crossing on the sustained-fault trajectory.

Loads are read from the MODEL ITSELF (Electranix_Load PO/QO/VO in the
pscx), not from case39 tables.

Usage:  python cct_p39_tier3.py
"""
import json
import re
import sys
import time
from pathlib import Path

import numpy as np

_T0 = time.time()
_PROG = Path(__file__).resolve().parent / "progress_tier3.txt"


def prog(msg):
    """Live progress: flushed stdout + an appendable file the user can
    open/refresh (experiments/cct_structpres_39sync/progress_tier3.txt)."""
    line = "[%6.0f s] %s" % (time.time() - _T0, msg)
    print(line, flush=True)
    with open(_PROG, "a") as f:
        f.write(line + "\n")

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import ieee39_data as d39                                  # noqa: E402
import cct_pebs as cp                                      # noqa: E402
from cct_sp39 import build_sync_system, MBASE              # noqa: E402
from cct_e39_tier2 import x_sys, TDO_P, XD_M, XDP_M        # noqa: E402

NB = 39
GBUS = d39.GEN_BUSES
# loads are read from the repository's all-machine PSCAD model (same Electranix_Load set as the study's validation copy)
PSCX = ROOT.parents[1] / "systems" / "ieee39" / "00GFM_all_sync" / "IEEE39_acLine1.pscx"
VTH = 0.5              # const-P holds down to Vth*V0, then S ~ V^2


def read_model_loads():
    s = PSCX.read_text(encoding="utf-8", errors="replace")
    loads = {}
    for m in re.finditer(r'defn="ETRAN:Electranix_Load".*?</User>', s, re.S):
        blk = m.group(0)
        name = re.search(r'<param name="Name" value="E_(\d+)_', blk).group(1)
        po = float(re.search(r'<param name="PO" value="([^"]*)"', blk).group(1))
        qo = float(re.search(r'<param name="QO" value="([^"]*)"', blk).group(1))
        vo = float(re.search(r'<param name="VO" value="([^"]*)"', blk).group(1))
        b = int(name)
        p0, q0 = loads.get(b, (0.0, 0.0, vo))[:2] if b in loads else (0.0, 0.0)
        loads[b] = (p0 + po / d39.SBASE, q0 + qo / d39.SBASE, vo)
    return loads


class ConstPNetwork(object):
    """Retained network with machine EMF sources and constant-P loads.
    Generic over the machine coupling reactances (xdp_vec: sync x'd or
    GFM coupling Xg), the branch set, and dead buses (norecl cases).
    solve() carries convergence diagnostics (the tier-3 0.052-s lesson:
    silent fixed-point failure near the const-P solvability boundary
    masquerades as instability)."""

    def __init__(self, sys_, loads, fault_bus=None, xdp_vec=None,
                 branches=None, dead_buses=()):
        self.sys = sys_
        self.loads = loads
        branches = d39.BRANCHES if branches is None else branches
        # assemble WITHOUT load admittances: loads enter as injections
        yl_save = sys_.yload.copy()
        sys_.yload = np.zeros(NB, complex)
        Y, keep, gi, oi = sys_._assemble(branches, fault_bus, dead_buses,
                                         None)
        sys_.yload = yl_save
        self.keep, self.gi, self.oi = keep, gi, oi
        YOI = Y[np.ix_(oi, gi)]
        YOO = Y[np.ix_(oi, oi)]
        self.A_op = -np.linalg.solve(YOO, YOI)          # V_o = A_op E + ...
        self.B = np.linalg.inv(YOO)
        self.node_of_row = [keep[j] for j in oi]
        self.row_of_node = {n: j for j, n in enumerate(self.node_of_row)}
        self.fault_bus = fault_bus
        self.xdp = (np.array([x_sys(b, XDP_M) for b in GBUS])
                    if xdp_vec is None else np.asarray(xdp_vec, float))
        self.fail_count = 0                 # unconverged solves (diagnostic)
        # load rows
        self.lrows, self.lS0, self.lV0 = [], [], []
        for b, (p, q, vo) in loads.items():
            r = self.row_of_node.get(b - 1)
            if r is not None:
                self.lrows.append(r)
                self.lS0.append(complex(p, q))
                self.lV0.append(vo)
        self.lrows = np.array(self.lrows, int)
        self.lS0 = np.array(self.lS0)
        self.lV0 = np.array(self.lV0)

    def _fixed_point(self, A, V, damp, iters, tol):
        for _ in range(iters):
            Vl = V[self.lrows]
            vm = np.abs(Vl)
            vth = VTH * self.lV0
            S = self.lS0.copy()
            low = vm < vth
            S[low] = self.lS0[low] * (vm[low] / vth[low])**2
            with np.errstate(divide="ignore", invalid="ignore"):
                Il = -np.conj(S / Vl)
            Il[~np.isfinite(Il)] = 0.0
            Iinj = np.zeros(len(self.node_of_row), complex)
            Iinj[self.lrows] = Il
            Vn = A + self.B @ Iinj
            err = float(np.max(np.abs(Vn - V)))
            V = damp * Vn + (1.0 - damp) * V
            if err < tol:
                return V, True
        return V, False

    def solve(self, delta, E, V_prev=None, tol=1e-7):
        """Adaptive-damping fixed point with an explicit convergence
        flag; failures counted in self.fail_count."""
        Eph = E * np.exp(1j * delta)
        A = self.A_op @ Eph
        V0 = A.copy() if V_prev is None else V_prev.copy()
        for damp, iters in ((0.6, 25), (0.3, 60), (0.12, 150)):
            V, ok = self._fixed_point(A, V0.copy(), damp, iters, tol)
            if ok:
                return V
        self.fail_count += 1
        return V

    def pe_id(self, delta, E, V_prev=None):
        V = self.solve(delta, E, V_prev)
        Pe = np.zeros(len(GBUS))
        idv = np.zeros(len(GBUS))
        for k, b in enumerate(GBUS):
            r = self.row_of_node.get(b - 1)
            Vb = V[r] if r is not None else 0.0 + 0j
            Eph = E[k] * np.exp(1j * delta[k])
            Ik = (Eph - Vb) / (1j * self.xdp[k])
            Pe[k] = (Eph * np.conj(Ik)).real
            vq = abs(Vb) * np.cos(delta[k] - np.angle(Vb)) if abs(Vb) > 0 \
                else 0.0
            idv[k] = (E[k] - vq) / self.xdp[k]
        return Pe, idv, V


def f_coi_net(sys_, Pe):
    acc = sys_.Pm - Pe
    return acc - sys_.M / sys_.MT * float(np.sum(acc))


def integrate_net(sys_, net, th0, w0, E0, Efd, decay, t_end, dt=2e-4,
                  record_every=10):
    th, w, E = th0.copy(), w0.copy(), E0.copy()
    Minv = 1.0 / sys_.M
    xd_m_xdp = np.array([x_sys(b, XD_M) - x_sys(b, XDP_M) for b in GBUS])
    Vp = [None]

    def rhs(th, w, E):
        Pe, idv, V = net.pe_id(th, E, Vp[0])
        Vp[0] = V
        dE = ((Efd - E - xd_m_xdp * idv) / TDO_P) if decay \
            else np.zeros(len(E))
        return w, (f_coi_net(sys_, Pe) - sys_.D * w) * Minv, dE, Pe

    ts, THS, WS_, ES, PES = [0.0], [th.copy()], [w.copy()], [E.copy()], None
    pe0 = rhs(th, w, E)[3]
    PES = [pe0.copy()]
    n = int(round(t_end / dt))
    for k in range(1, n + 1):
        k1 = rhs(th, w, E)
        k2 = rhs(th + 0.5 * dt * k1[0], w + 0.5 * dt * k1[1],
                 E + 0.5 * dt * k1[2])
        k3 = rhs(th + 0.5 * dt * k2[0], w + 0.5 * dt * k2[1],
                 E + 0.5 * dt * k2[2])
        k4 = rhs(th + dt * k3[0], w + dt * k3[1], E + dt * k3[2])
        th = th + dt / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
        w = w + dt / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
        E = np.maximum(E + dt / 6 * (k1[2] + 2 * k2[2] + 2 * k3[2] + k4[2]),
                       0.05)
        if k % record_every == 0:
            ts.append(k * dt); THS.append(th.copy())
            WS_.append(w.copy()); ES.append(E.copy())
            PES.append(k1[3].copy())
    return (np.array(ts), np.array(THS), np.array(WS_), np.array(ES),
            np.array(PES))


def stable_net(sys_, netF, netP, t_cl, E0, Efd0, decay, t_post=8.0,
               dt=1e-3):
    """Stability verdict. dt = 1 ms is ample for ~1 Hz swing dynamics
    (RK4); the 0.2 ms step is only needed for the energy path integrals.
    main() cross-checks one verdict at both steps before trusting it."""
    th0 = sys_.to_coi(sys_.d0)
    f0 = netF.fail_count + netP.fail_count
    ts, TH, W, ES, _ = integrate_net(sys_, netF, th0, np.zeros(sys_.m), E0,
                                     np.zeros(sys_.m), decay,
                                     max(t_cl, 1e-3), dt=dt, record_every=20)
    ts2, TH2, W2, ES2, _ = integrate_net(sys_, netP, TH[-1], W[-1], ES[-1],
                                         Efd0, decay, t_post, dt=dt,
                                         record_every=20)
    fails = netF.fail_count + netP.fail_count - f0
    if fails:
        prog("  ALGEBRAIC: %d unconverged network solves at t_cl=%.3f "
             "(const-P solvability, NOT a synchronism verdict)"
             % (fails, t_cl))
    spread = float(np.max(TH2, axis=0).max() - np.min(TH2, axis=0).min())
    drift = float(np.max(np.abs(TH2[-1] - TH2[0])))
    return spread < 2 * np.pi and drift < np.pi


def true_cct_net(sys_, netF, netP, E0, Efd0, decay, lo=0.05, hi=0.6,
                 tol=5e-3, label=""):
    t0 = time.time()
    ok = stable_net(sys_, netF, netP, hi, E0, Efd0, decay)
    prog("%s test 1: t_cl=%.3f -> %s  (%.0f s/test)"
         % (label, hi, "STABLE" if ok else "UNSTABLE", time.time() - t0))
    if ok:
        return float("inf")
    k = 1
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        t0 = time.time()
        ok = stable_net(sys_, netF, netP, mid, E0, Efd0, decay)
        k += 1
        if ok:
            lo = mid
        else:
            hi = mid
        prog("%s test %d: t_cl=%.3f -> %s  bracket (%.3f, %.3f]  (%.0f s)"
             % (label, k, mid, "STABLE" if ok else "UNSTABLE", lo, hi,
                time.time() - t0))
    return 0.5 * (lo + hi)


def main():
    if _PROG.exists():
        _PROG.unlink()
    # SELF-CONSISTENT baseline: the theory PF must use the MODEL'S OWN
    # load set (parsed from the pscx), not the case39 tables — first run
    # exposed a 0.24-pu prefault Pe-Pm mismatch from the 19-vs-20-entry
    # difference. Patch d39.LOADS BEFORE building the system.
    loads = read_model_loads()
    old = dict(d39.LOADS)
    d39.LOADS = {b: (p, q) for b, (p, q, v) in loads.items()}
    for b in sorted(set(old) | set(d39.LOADS)):
        o, n = old.get(b), d39.LOADS.get(b)
        if o is None or n is None or abs(o[0] - n[0]) > 1e-3 \
                or abs(o[1] - n[1]) > 1e-3:
            prog("load diff bus %d: case39 %s -> model %s" % (b, o, n))
    sys_ = build_sync_system()
    ptot = sum(p for p, q, v in loads.values())
    prog("model loads: %d entries, %.2f pu total P (const-P, Vth=%.1f)"
         % (len(loads), ptot, VTH))

    netF = ConstPNetwork(sys_, loads, fault_bus=14)
    netP = ConstPNetwork(sys_, loads, fault_bus=None)

    # consistency: prefault Pe at (d0, E0) should equal Pm
    Pe0, id0, _ = netP.pe_id(sys_.d0, sys_.E)
    prog("prefault |Pe - Pm| max = %.3e pu" %
         float(np.max(np.abs(Pe0 - sys_.Pm))))
    xd_m_xdp = np.array([x_sys(b, XD_M) - x_sys(b, XDP_M) for b in GBUS])
    Efd0 = sys_.E + xd_m_xdp * id0

    # dt self-check: same verdict at 1 ms and 0.2 ms on one borderline test
    for dt in (1e-3, 2e-4):
        t0 = time.time()
        ok = stable_net(sys_, netF, netP, 0.25, sys_.E.copy(), Efd0,
                        decay=False, dt=dt)
        prog("dt-check t_cl=0.25 dt=%.0e -> %s  (%.0f s)"
             % (dt, "STABLE" if ok else "UNSTABLE", time.time() - t0))

    # ---- tier-1P: constant-E', constant-P loads ----
    t1p = true_cct_net(sys_, netF, netP, sys_.E.copy(), Efd0, decay=False,
                       label="tier-1P")
    prog("[tier-1P  const-E' + const-P loads] t_cr = %.3f s" % t1p)

    # ---- tier-3: E' decay + constant-P loads ----
    t3 = true_cct_net(sys_, netF, netP, sys_.E.copy(), Efd0, decay=True,
                      label="tier-3")
    prog("[tier-3   E' decay  + const-P loads] t_cr = %.3f s" % t3)

    # ---- energy screen on the tier-3 sustained-fault trajectory ----
    th0 = sys_.to_coi(sys_.d0)
    ts, TH, W, ES, PES = integrate_net(sys_, netF, th0, np.zeros(sys_.m),
                                       sys_.E.copy(), np.zeros(sys_.m),
                                       True, 0.8)
    VKE = 0.5 * np.sum(sys_.M[None, :] * W**2, axis=1)
    # exact path integral of sum (Pe - Pm) d(delta) along the trajectory
    VPE = np.zeros(len(ts))
    acc = 0.0
    for k in range(1, len(ts)):
        g1 = PES[k] - sys_.Pm
        g0 = PES[k - 1] - sys_.Pm
        acc += 0.5 * float(np.dot(g1 + g0, TH[k] - TH[k - 1]))
        VPE[k] = acc
    V = VKE + VPE
    kmax = int(np.argmax(VPE))
    Vcr = float(VPE[kmax])
    tcr_screen = None
    for k in range(1, len(ts)):
        if V[k - 1] < Vcr <= V[k]:
            fr = (Vcr - V[k - 1]) / (V[k] - V[k - 1])
            tcr_screen = float(ts[k - 1] + fr * (ts[k] - ts[k - 1]))
            break
    prog("[tier-3 energy screen, VPEmax rim] t_cr ~ %s"
         % ("%.3f s" % tcr_screen if tcr_screen else "none"))

    # ---- Vth sensitivity ----
    sens = {}
    for vth in (0.3, 0.7):
        globals()["VTH"] = vth
        nF = ConstPNetwork(sys_, loads, fault_bus=14)
        nP = ConstPNetwork(sys_, loads, fault_bus=None)
        sens[vth] = true_cct_net(sys_, nF, nP, sys_.E.copy(), Efd0,
                                 decay=True, label="Vth=%.1f" % vth)
        prog("  [Vth=%.1f] tier-3 t_cr = %.3f s" % (vth, sens[vth]))
    globals()["VTH"] = 0.5

    out = {"loads_total_pu": ptot, "vth_default": 0.5,
           "tier1P_constE_constP_s": t1p,
           "tier3_decay_constP_s": t3,
           "tier3_energy_screen_s": tcr_screen,
           "vth_sensitivity": {str(k): v for k, v in sens.items()},
           "measured_bracket_s": [0.237, 0.25],
           "tier0_constZ_s": 0.479, "tier2_decay_constZ_s": 0.430}
    (ROOT / "results_tier3.json").write_text(json.dumps(out, indent=1))
    print("wrote results_tier3.json")


if __name__ == "__main__":
    main()
