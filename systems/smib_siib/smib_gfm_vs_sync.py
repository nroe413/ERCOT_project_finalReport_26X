"""smib_gfm_vs_sync.py — device-only fault ride-through: bus-39 machine vs GFM.

Single-machine-infinite-bus, identical disturbance (bolted 3PG at t = 3.0 s,
5 cycles, RON = 0.001 ohm), identical relative grid strength (SCR = 10,
X/R = 20 on each device's own base). No line is lost, so the post-fault
network is unchanged — what differs is ONLY the device:

  sync : bus-39 Electranix/GENROU + ESST4B + GGOV1 + PSS2B, 2000 MVA / 230 kV
         (IEEE 39 bus TypicalGT.dyr), dispatch 0.50 pu, AVR setpoint 1.03
  GFM  : PNNL REGFM_A1 release SMIB, Mbase 0.1 MVA / 0.48 kV, Preq = 0.60 pu,
         ImaxF = 2.0 (PNNL default — the 39-bus study used 1.5), I_clip = 2.1

PER-UNIT BASES (printed on the figures, per repo convention):
  sync grid meter: pu on 2000 MVA / 230 kV / 5.02 kA (multimeter base scaling)
  GFM channels   : native REGFM pu on its own Mbase/Vbase

Inputs:
  SMIB_SYNC.gf46/             (newest GUI/python run; read directly)
  ../single_machine_infinite_bus_1GFMvalidation/SMIB_1GFM_3PG_PSD.csv

Outputs:
  SMIB_1SYNC_3PG_PSD.csv      (trimmed record CSV, gitignored)
  smib_gfm_vs_sync_VI_<ts>.png, smib_gfm_vs_sync_Pf_<ts>.png

Usage:  python smib_gfm_vs_sync.py
"""
import datetime
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.family": "serif", "font.size": 12, "mathtext.fontset": "cm",
                     "figure.dpi": 150, "axes.grid": True, "axes.unicode_minus": True})

SCRIPT = Path(__file__).resolve().parent
ROOT = SCRIPT.parent.parent
sys.path.insert(0, str(SCRIPT))
from _pscad_io import read_run_to_dataframe, find_inf   # noqa: E402

GFM_CSV = ROOT / "single_machine_infinite_bus_1GFMvalidation" / "SMIB_1GFM_3PG_PSD.csv"
SYNC_GF46 = ROOT / "single_machine_infinite_bus_1syncMachineValidation" / "SMIB_SYNC.gf46"
# Canonical sync record (documented dispatch-0.50 run). Preferred over the live
# .gf46, which currently holds a different (modified .pscx) run.
SYNC_CSV = ROOT / "single_machine_infinite_bus_1syncMachineValidation" / "SMIB_1SYNC_3PG_PSD.csv"
RUN_DIR = SCRIPT / "runs" / "3PG_5cyc_SCR10_10s"
PLOTS = SCRIPT / "plots"
FAULT_T, CLEAR_T = 3.0, 3.0833
BLUE, RED = "#1f77b4", "#c0392b"


def load_sync():
    # Prefer the canonical sync record CSV (documented dispatch-0.50 run); copy it
    # into the run dir for the record. Fall back to the raw .gf46 if it is absent.
    if SYNC_CSV.exists():
        out = pd.read_csv(SYNC_CSV)
        RUN_DIR.mkdir(parents=True, exist_ok=True)
        out.to_csv(RUN_DIR / "SMIB_1SYNC_3PG_PSD.csv", index=False)
        print("read sync from %s %s" % (SYNC_CSV.name, out.shape))
        return out
    df = read_run_to_dataframe(find_inf(SYNC_GF46))
    cols, seen = [], {}
    for c in df.columns:
        seen[c] = seen.get(c, 0)
        cols.append(c if seen[c] == 0 else "%s__dup%d" % (c, seen[c]))
        seen[c] += 1
    df.columns = cols
    out = pd.DataFrame({"TIME": df["TIME"].values})
    keep = {"VRMS2grid": "VRMS2grid", "IRMS2grid": "IRMS2grid", "P2grid": "P2grid",
            "Q2grid": "Q2grid", "Vm": "Vm", "TM": "TM", "TE": "TE", "Ef": "Ef",
            "If": "If", "Wpu": "Wpu", "Wang": "Wang", "thetaMech": "thetaMech",
            "thetaLoad": "thetaLoad",
            # live machine P/Q are the SECOND pair (first pair are dead taps)
            "P__dup1": "P_mach_MW", "Q__dup1": "Q_mach_MVAR"}
    for src, dst in keep.items():
        if src in df.columns:
            out[dst] = df[src].values
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(RUN_DIR / "SMIB_1SYNC_3PG_PSD.csv", index=False)
    print("wrote SMIB_1SYNC_3PG_PSD.csv", out.shape)
    return out


def main():
    sy = load_sync()
    gf = pd.read_csv(GFM_CSV)
    ts_, tg = sy["TIME"].values, gf["TIME"].values
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    sync_disp = float(np.nanmean(sy["P2grid"].values[(ts_ >= 2.8) & (ts_ < 2.99)]))
    base_note = ("Identical SMIB test: bolted 3PG at t = 3.0 s, 5 cycles; SCR = 10, X/R = 20 on each "
                 "device's OWN base; no topology change. Per-unit bases — sync: 2000 MVA / 230 kV / "
                 "5.02 kA (bus-39 machine, TypicalGT.dyr, dispatch %.2f pu); GFM: native REGFM pu on "
                 "Mbase 0.1 MVA / 0.48 kV (PNNL release SMIB, Preq = 0.60 pu, ImaxF = 2.0 — the "
                 "39-bus study used 1.5)." % sync_disp)

    # ---- figure 1: terminal voltage + current (the ride-through picture) ----
    fig, ax = plt.subplots(2, 1, figsize=(11, 7.6))
    for a in ax:
        a.axvspan(FAULT_T, CLEAR_T, color="#fbd0c4", alpha=0.6, zorder=0)
        a.grid(True, alpha=0.3)
        a.set_xlim(2.8, 6.0)
    ax[0].plot(ts_, sy["VRMS2grid"].values, color=BLUE, lw=1.2, label="Synchronous (bus-39 machine)")
    ax[0].plot(tg, gf["V_pu"].values, color=RED, lw=1.2, label="GFM (REGFM_A1)")
    ax[0].axhline(1.0, color="#999999", ls="--", lw=0.7)
    ax[0].set_ylabel("Terminal voltage (pu)")
    ax[0].set_ylim(0, 1.25)
    ax[0].legend(loc="lower right", fontsize=10)
    ax[0].set_title("Voltage ride-through — same fault, same grid strength", fontsize=12.5)
    ax[1].plot(ts_, sy["IRMS2grid"].values, color=BLUE, lw=1.2, label="Synchronous — unlimited")
    ax[1].plot(tg, gf["I_pu"].values, color=RED, lw=1.2, label="GFM — limited")
    ax[1].axhline(2.0, color=RED, ls="--", lw=1.0)
    ax[1].text(5.95, 2.07, "GFM ImaxF = 2.0 pu", color=RED, fontsize=9, ha="right")
    pk_s = float(np.nanmax(sy["IRMS2grid"].values))
    pk_g = float(np.nanmax(gf["I_pu"].values))
    ax[1].set_ylabel("Current (pu of own rating)")
    ax[1].set_ylim(0, max(2.5, 1.12 * pk_s))
    ax[1].set_xlabel("Time (s)")
    ax[1].legend(loc="upper right", fontsize=10)
    ax[1].set_title("Fault current — %.1f pu (machine) vs %.2f pu (GFM): ~%.0f×"
                    % (pk_s, pk_g, pk_s / pk_g), fontsize=12.5)
    fig.suptitle("SMIB device-only fault ride-through: bus-39 synchronous machine vs GFM",
                 fontsize=13.5, fontweight="bold")
    fig.text(0.5, 0.005, base_note, ha="center", va="bottom", fontsize=8.4, color="#404040",
             bbox=dict(boxstyle="round,pad=0.4", fc="#f4f4f4", ec="#bbbbbb"))
    fig.tight_layout(rect=[0, 0.07, 1, 0.95])
    f1 = PLOTS / ("smib_gfm_vs_sync_VI_%s.png" % stamp)
    fig.savefig(f1, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", f1)

    # ---- figure 2: active power + frequency (the recovery picture) ----------
    fig, ax = plt.subplots(2, 1, figsize=(11, 7.6))
    for a in ax:
        a.axvspan(FAULT_T, CLEAR_T, color="#fbd0c4", alpha=0.6, zorder=0)
        a.grid(True, alpha=0.3)
        a.set_xlim(2.5, 10.0)
    ax[0].plot(ts_, sy["P2grid"].values, color=BLUE, lw=1.2,
               label="Synchronous (dispatch 0.50 pu)")
    ax[0].plot(tg, gf["P_pu"].values, color=RED, lw=1.2, label="GFM (Preq = 0.60 pu)")
    ax[0].set_ylabel("Active power (pu of own rating)")
    ax[0].set_xlabel("Time (s)")
    ax[0].legend(loc="lower right", fontsize=10)
    ax[0].set_title("Active-power recovery — the GFM snaps back to its setpoint; the machine's "
                    "governor takes tens of seconds", fontsize=12)
    ax[1].plot(ts_, sy["Wpu"].values * 60.0, color=BLUE, lw=1.2, label="Synchronous (rotor speed)")
    ax[1].plot(tg, gf["f_drp"].values, color=RED, lw=1.2, label="GFM (droop frequency)")
    ax[1].axhline(60.0, color="#999999", ls="--", lw=0.7)
    ax[1].set_ylabel("Frequency (Hz)")
    ax[1].set_xlabel("Time (s)")
    ax[1].legend(loc="lower right", fontsize=10)
    ax[1].set_title("Frequency — both stay tight against the strong grid (the contrast appears "
                    "when the grid is weak or lost)", fontsize=12)
    fig.suptitle("SMIB device-only recovery: bus-39 synchronous machine vs GFM",
                 fontsize=13.5, fontweight="bold")
    fig.text(0.5, 0.005, base_note, ha="center", va="bottom", fontsize=8.4, color="#404040",
             bbox=dict(boxstyle="round,pad=0.4", fc="#f4f4f4", ec="#bbbbbb"))
    fig.tight_layout(rect=[0, 0.07, 1, 0.95])
    f2 = PLOTS / ("smib_gfm_vs_sync_Pf_%s.png" % stamp)
    fig.savefig(f2, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", f2)

    # ---- figure 3: active vs reactive current decomposition -----------------
    def decomp(P, Q, V):
        v = np.asarray(V, float)
        ip = np.asarray(P, float) / v
        iq = np.asarray(Q, float) / v
        bad = v < 0.2                      # P/V, Q/V undefined when V ~ 0 (held fault)
        ip[bad] = np.nan; iq[bad] = np.nan
        return ip, iq
    sIp, sIq = decomp(sy["P2grid"].values, sy["Q2grid"].values, sy["VRMS2grid"].values)
    gIp, gIq = decomp(gf["P_pu"].values, gf["Q_pu"].values, gf["V_pu"].values)

    fig, ax = plt.subplots(2, 1, figsize=(11, 7.6), sharex=True)
    for a in ax:
        a.axvspan(FAULT_T, CLEAR_T, color="#fbd0c4", alpha=0.6, zorder=0)
        a.grid(True, alpha=0.3); a.set_xlim(2.8, 5.5)
    ax[0].plot(ts_, sIp, color=BLUE, lw=1.3, label="Synchronous (bus-39 machine)")
    ax[0].plot(tg, gIp, color=RED, lw=1.3, label="GFM (REGFM_A1)")
    ax[0].axhline(0.0, color="#999999", ls="--", lw=0.7)
    ax[0].set_ylabel(r"Active current  $I_P = P/V$  (pu)")
    ax[0].legend(loc="upper right", fontsize=10)
    ax[0].set_title("Active vs reactive current — why the GFM restores voltage faster with less current",
                    fontsize=12.5)
    ax[0].set_ylim(-0.3, 1.8)
    ax[1].plot(ts_, sIq, color=BLUE, lw=1.3, label="Synchronous (bus-39 machine)")
    ax[1].plot(tg, gIq, color=RED, lw=1.3, label="GFM (REGFM_A1)")
    ax[1].axhline(0.0, color="#999999", ls="--", lw=0.7)
    ax[1].set_ylabel(r"Reactive current  $I_Q = Q/V$  (pu)")
    ax[1].set_xlabel("Time (s)")
    ax[1].set_ylim(-1.2, 1.2)
    ax[1].legend(loc="upper right", fontsize=10)
    note3 = ("Active/reactive split of the terminal current: $I_P=P/V$, $I_Q=Q/V$ (positive = exported); "
             "blanked where V < 0.2 pu (held fault, split undefined). Bases: sync 2000 MVA / 230 kV "
             "(dispatch 0.50 pu); GFM native pu (Preq 0.60). NB the sync's large RMS current in the fault / "
             "early recovery is the decaying subtransient + DC fault transient — it carries ~0 power and is "
             "NOT in this P/Q split; the GFM (converter) has no such transient.")
    fig.suptitle("SMIB device-only: active vs reactive current decomposition",
                 fontsize=13.5, fontweight="bold")
    fig.text(0.5, 0.005, note3, ha="center", va="bottom", fontsize=7.8, color="#404040",
             bbox=dict(boxstyle="round,pad=0.4", fc="#f4f4f4", ec="#bbbbbb"))
    fig.tight_layout(rect=[0, 0.08, 1, 0.95])
    f3 = PLOTS / ("smib_gfm_vs_sync_IPIQ_%s.png" % stamp)
    fig.savefig(f3, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", f3)

    # ---- figure 4: active/reactive as % of the power current, post-fault ----
    def frac(P, Q, V):
        v = np.asarray(V, float)
        ip = np.asarray(P, float) / v
        iq = np.asarray(Q, float) / v
        mag = np.hypot(ip, iq)
        with np.errstate(invalid="ignore", divide="ignore"):
            ap, rp = 100.0 * ip / mag, 100.0 * iq / mag
        bad = (v < 0.2) | (mag < 1e-6)
        ap[bad] = np.nan; rp[bad] = np.nan
        return ap, rp
    sAp, sRp = frac(sy["P2grid"].values, sy["Q2grid"].values, sy["VRMS2grid"].values)
    gAp, gRp = frac(gf["P_pu"].values, gf["Q_pu"].values, gf["V_pu"].values)

    fig, ax = plt.subplots(figsize=(11, 5.7))
    ax.axvspan(FAULT_T, CLEAR_T, color="#fbd0c4", alpha=0.6, zorder=0)
    ax.axhline(0, color="#999999", ls="--", lw=0.7)
    ax.plot(ts_, sRp, color=BLUE, lw=1.5, label="Synchronous (bus-39 machine)")
    ax.plot(tg, gRp, color=RED, lw=1.5, label="GFM (REGFM_A1)")
    ax.set_xlim(3.0, 5.5); ax.set_ylim(-70, 100)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel(r"Reactive fraction  $100\,I_Q/|I|$  (%)")
    ax.set_title(r"Post-fault reactive current fraction  $Q/S = I_Q/\sqrt{I_P^2+I_Q^2}$",
                 fontsize=12.5)
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(True, alpha=0.3)
    note4 = (r"Reactive fraction $100\,I_Q/|I| = 100\,Q/S$ ($=100\sin\varphi$), with $I_Q=Q/V$, "
             r"$|I|=\sqrt{I_P^2+I_Q^2}$ (positive = exported). The active part is the QUADRATURE complement "
             r"$\cos\varphi=\sqrt{1-(I_Q/|I|)^2}$ — NOT 100% minus this (active & reactive are orthogonal). "
             "Blanked where V<0.2 pu (held fault). The GFM settles to ~0% (unity PF); the sync ends ~80% "
             "reactive (over-excited from field forcing, holding its ~1.04 pu overshoot). |I| = power "
             "current, excludes the sync's decaying fault transient.")
    fig.text(0.5, 0.005, note4, ha="center", va="bottom", fontsize=7.9, color="#404040",
             bbox=dict(boxstyle="round,pad=0.4", fc="#f4f4f4", ec="#bbbbbb"))
    fig.tight_layout(rect=[0, 0.09, 1, 1])
    f4 = PLOTS / ("smib_gfm_vs_sync_PCT_%s.png" % stamp)
    fig.savefig(f4, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", f4)


if __name__ == "__main__":
    main()
