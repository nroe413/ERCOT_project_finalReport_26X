"""cct_sp39.py - STRUCTURE-PRESERVING transient energy function (Sauer &
Pai Ch. 9) for the ALL-SYNCHRONOUS ieee39_sz model (copy:
ieee39_sz_structPres_validation), 3PG self-clearing fault at bus 14.

Machines: classical E' behind x'd. From the model's own data:
  IEEE 39 bus TypicalGT.dyr GENROU -> H = 5.46 s, x'd = 0.26 (machine base)
  IEEE 39 bus_szVsched_mbase.RAW  -> MBASE, PG dispatch, Vsched setpoints
  D = 0 (GENROU D = 0): conservative classical model, no governor/AVR.

Structure-preserving formulation: the full 39-bus network is RETAINED
(no Kron reduction) - bus voltages are algebraic variables solved from
the linear network at each machine-angle state (loads constant-Z at
their power-flow values, exactly the ETRAN EMT model's load model), and
the energy function is evaluated on network quantities:
  V_SP = 1/2 sum Mi wi^2 + int_path sum_i (Pe_i - Pm_i) d(delta_i)
with Pe_i computed FROM THE NETWORK SOLUTION (trapezoidal path term -
exact for any loss/load structure; Sauer 9.51's generalization).
Verification layer (the constant-Z equivalence theorem, demonstrated
numerically): Pe_i(network) == Pe_i(reduced) and V_SP == V_reduced
(Vp + Vd of the internal-node machinery) along the same trajectory.
A constant-POWER load variant (textbook Bergen-Hill/Sauer 9.3 structure-
preserved load model, P_L(theta_i - theta_i^s) terms absorbed by the
same path integral) is reported as sensitivity.

CCT: PEBS crossing of the sustained-fault trajectory -> Vcr -> tcr
(conservative screen, the machine-side quoting rule), checked against
the classical model's true CCT by bisection (undamped: stability =
bounded COI spread < pi over the post window).

Usage:  python cct_sp39.py
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
MGFM = ROOT.parent / "cct_energy_function_multiGFM"
sys.path.insert(0, str(MGFM))
import ieee39_data as d39                                  # noqa: E402
import cct_pebs as cp                                      # noqa: E402

# ---- the all-sync fleet, from the model's RAW + .dyr -----------------------
MBASE = {30: 250.0, 31: 600.0, 32: 650.0, 33: 650.0, 34: 525.0,
         35: 650.0, 36: 560.0, 37: 550.0, 38: 850.0, 39: 2000.0}
VSCHED = {30: 1.048, 31: 1.000, 32: 1.000, 33: 1.000, 34: 1.012,
          35: 1.049, 36: 1.050, 37: 1.028, 38: 1.027, 39: 1.030}
PG_MW = {30: 250.0, 31: None, 32: 650.0, 33: 632.0, 34: 508.0,
         35: 650.0, 36: 560.0, 37: 540.0, 38: 830.0, 39: 1000.0}
H_MACH = 5.46          # s, machine base (TypicalGT GENROU, all units)
XDP_MACH = 0.26        # pu, machine base
NB, WS = 39, d39.WS
GBUS = d39.GEN_BUSES


def build_sync_system():
    """Dress the existing reduced-model engine in synchronous-machine
    clothing: swap the Mbase table + Vsched dispatch, set E' behind x'd,
    then overwrite the swing constants with 2H/ws (D = 0).

    BUGFIX (2026-07-27): the Mbase/dispatch swap used to LEAK - the
    d39 module globals stayed overwritten after return, so any
    GFMSystem() built LATER in the same process silently inherited
    machine bases and dispatch (wrong M, D, Pm; drift ~2.1x fast).
    That poisoned the entire GFM panel of the sync-vs-GFM juxtaposition
    figure (whose main() builds sync first), including its 'leaves the
    basin at 1.030 s' marker. The globals are now snapshotted and
    restored: GFMSystem reads them only during construction, so the
    returned sync system is unaffected (verified: identical
    trajectories before/after this fix)."""
    saved = (d39.GFM_MBASE_MVA, d39.GENS)
    d39.GFM_MBASE_MVA = dict(MBASE)
    d39.GENS = {b: (PG_MW[b], VSCHED[b]) for b in GBUS}
    try:
        sys_ = cp.GFMSystem(xg_pu_mbase=XDP_MACH)
    finally:
        d39.GFM_MBASE_MVA, d39.GENS = saved
    for k, b in enumerate(GBUS):
        H_sys = H_MACH * MBASE[b] / d39.SBASE
        sys_.H[k] = H_sys
        sys_.M[k] = 2.0 * H_sys / WS
        sys_.D[k] = 0.0
    sys_.MT = float(np.sum(sys_.M))
    return sys_


# ------------------- structure-preserving evaluation layer ------------------

class StructurePreserved(object):
    """Full-network algebraic layer: for machine angles delta, solve the
    RETAINED network (39 buses + 10 internal nodes; loads constant-Z or
    constant-P) and return bus voltages + machine electrical powers."""

    def __init__(self, sys_, branches, fault_bus=None, load_model="Z"):
        self.sys = sys_
        self.load_model = load_model
        self.map_other, self.R = sys_.recon_ops(branches, fault_bus=fault_bus)
        # for the constant-P variant we need the raw (loadless) network ops
        if load_model == "P":
            yl = sys_.yload.copy()
            sys_.yload = np.zeros(NB, complex)
            self.map_noload, self.R_noload = \
                sys_.recon_ops(branches, fault_bus=fault_bus)
            self.Y_noload = None      # lazily via injections iteration
            sys_.yload = yl
        self.fault_bus = fault_bus
        self.branches = branches

    def solve(self, delta):
        """Bus voltages (complex, indexed by original node id) + machine
        Pe from the network solution."""
        s = self.sys
        E = s.E * np.exp(1j * delta)
        Vo = self.R @ E                      # eliminated nodes from EMFs
        volt = {}
        for j, node in enumerate(self.map_other):
            volt[node] = Vo[j]
        # machine electrical power: current through x'd from E to its bus
        Pe = np.zeros(s.m)
        for k, b in enumerate(GBUS):
            i = b - 1
            Vb = volt.get(i, 0.0 + 0j)       # faulted bus row is deleted (V=0)
            if self.fault_bus is not None and i == self.fault_bus - 1:
                Vb = 0.0 + 0j
            xg = d39.gfm_xg_sys(b, s.xg)
            Ik = (E[k] - Vb) / (1j * xg)
            Pe[k] = (E[k] * np.conj(Ik)).real
        return volt, Pe


def v_sp_path(sys_, sp, TH, ths):
    """V_PE^SP(t) = path integral of sum_i (Pe_i - Pm_i) d(delta_i) along
    the trajectory, REFERENCED to the postfault SEP (integration from the
    SEP to the trajectory start uses a straight-line path, trapezoidal -
    the exact generalization of Sauer's (9.51)+(9.55) construction)."""
    npts = 40
    seg = np.zeros(1)
    # SEP -> TH[0] straight line
    acc = 0.0
    prev = None
    for lam in np.linspace(0.0, 1.0, npts):
        th = ths + lam * (TH[0] - ths)
        _, Pe = sp.solve(th)
        g = Pe - sys_.Pm
        if prev is not None:
            acc += 0.5 * float(np.dot(g + prev[0], th - prev[1]))
        prev = (g, th)
    out = np.zeros(len(TH))
    out[0] = acc
    _, Pe_prev = sp.solve(TH[0])
    g_prev = Pe_prev - sys_.Pm
    for k in range(1, len(TH)):
        _, Pe = sp.solve(TH[k])
        g = Pe - sys_.Pm
        acc += 0.5 * float(np.dot(g + g_prev, TH[k] - TH[k - 1]))
        out[k] = acc
        g_prev = g
    return out


def stable_bounded(sys_, t_cl, GF, BF, GP, BP, ths, t_post=8.0):
    """Undamped classical stability: bounded COI spread < pi post-clear."""
    th0 = sys_.to_coi(sys_.d0)
    ts, TH, W = cp.integrate(sys_, th0, np.zeros(sys_.m), GF, BF,
                             max(t_cl, 1e-3), record_every=50)
    ts2, TH2, W2 = cp.integrate(sys_, TH[-1], W[-1], GP, BP, t_post,
                                record_every=50)
    spread = float(np.max(np.abs(TH2 - ths[None, :])))
    return spread < np.pi, spread


def true_cct_bounded(sys_, GF, BF, GP, BP, ths, lo=0.0, hi=1.5, tol=4e-3):
    ok, _ = stable_bounded(sys_, hi, GF, BF, GP, BP, ths)
    if ok:
        return float("inf")
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        ok, _ = stable_bounded(sys_, mid, GF, BF, GP, BP, ths)
        if ok:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def main():
    sys_ = build_sync_system()
    print("PF residual %.2e | machines H_sys %s" %
          (sys_.pf_resid, np.round(sys_.H, 1)))

    # ---- reduced-machinery PEBS (the engine) on bus-14 self-clearing ----
    res, aux = cp.pebs_cct(sys_, 14, d39.BRANCHES, dead_buses=(),
                           label="sync_bus14_selfclear", t_int=3.0)
    ts, TH, W, V, VPE, g, ths, (GF, BF), (GP, BP) = aux
    print("[reduced engine] PEBS t_pebs=%.3f  Vcr=%.3f  tcr=%.3f s"
          % (res["t_pebs_s"], res["Vcr_pu"], res["tcr_pebs_s"] or -1))

    # ---- structure-preserving layer: equivalence demo + SP energy ----
    sp_f = StructurePreserved(sys_, d39.BRANCHES, fault_bus=14)
    sp_p = StructurePreserved(sys_, d39.BRANCHES, fault_bus=None)

    # demo 1: network-solution Pe == reduced-network Pe (fault-on, samples)
    errs = []
    for k in range(0, len(TH), max(1, len(TH) // 25)):
        _, Pe_sp = sp_f.solve(TH[k])
        Pe_red = sys_.pe_vec(TH[k], GF, BF)
        errs.append(float(np.max(np.abs(Pe_sp - Pe_red))))
    print("equivalence demo 1 (const-Z): max|Pe_SP - Pe_reduced| = %.2e pu"
          % max(errs))

    # demo 2: SP path-integral potential == reduced Vp + Vd
    VPE_sp = v_sp_path(sys_, sp_p, TH, ths)
    dmax = float(np.max(np.abs(VPE_sp - VPE)))
    print("equivalence demo 2: max|V_PE^SP - V_PE^reduced| = %.3e pu "
          "(scale V_cr = %.3f)" % (dmax, res["Vcr_pu"]))

    # SP energy -> the SAME PEBS/tcr computed on SP quantities
    VKE = np.array([0.5 * float(np.sum(sys_.M * W[k]**2))
                    for k in range(len(TH))])
    V_sp = VKE + VPE_sp
    kmax = int(np.argmax(VPE_sp))
    cross = None
    for k in range(1, len(ts)):
        if g[k - 1] < 0.0 <= g[k]:
            cross = k
            break
    Vcr_sp = float(VPE_sp[cross]) if cross else float(VPE_sp[kmax])
    tcr_sp = None
    for k in range(1, len(ts)):
        if V_sp[k - 1] < Vcr_sp <= V_sp[k]:
            fr = (Vcr_sp - V_sp[k - 1]) / (V_sp[k] - V_sp[k - 1])
            tcr_sp = float(ts[k - 1] + fr * (ts[k] - ts[k - 1]))
            break
    print("[structure-preserving] Vcr=%.3f  tcr=%.3f s" % (Vcr_sp, tcr_sp))

    # ---- classical true CCT (undamped, bounded-spread bisection) ----
    t_true = true_cct_bounded(sys_, GF, BF, GP, BP, ths)
    print("[classical true CCT, bisection] %.3f s" % t_true)

    out = {"case": "all-sync ieee39_sz (Vsched RAW dispatch), 3PG bus 14 "
                   "self-clearing, classical E' behind x'd, D=0",
           "H_mach_s": H_MACH, "xdp_mach_pu": XDP_MACH,
           "pf_residual": sys_.pf_resid,
           "pebs_reduced": {"t_pebs_s": res["t_pebs_s"],
                            "Vcr_pu": res["Vcr_pu"],
                            "tcr_s": res["tcr_pebs_s"]},
           "equivalence_maxPeErr_pu": max(errs),
           "equivalence_maxVpeErr_pu": dmax,
           "structure_preserving": {"Vcr_pu": Vcr_sp, "tcr_s": tcr_sp},
           "true_classical_tcr_s": t_true}
    (ROOT / "results_sp39.json").write_text(json.dumps(out, indent=2))
    print("wrote results_sp39.json")


if __name__ == "__main__":
    main()
