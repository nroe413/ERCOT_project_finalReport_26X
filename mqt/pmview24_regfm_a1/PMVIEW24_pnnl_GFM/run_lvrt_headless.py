"""run_lvrt_headless.py -- re-run of PMView 2.4 Test 2 (LVRT_ERCOT_Legacy) on the PNNL REGFM_A1
rig, the record behind report Figure 13 (2026-09-18).

The report's Figure 13 was an archived PNG (plots/r00002_LVRT_ERCOT_Legacy/pq_vrms_overlay.png,
gfm_validation_task_2 commit a4b8e3a, 2026-04-21) whose .out files no longer exist: the rig writes
every multiple-run batch to run slots r00001, r00002, ... and later batches (tests 4-5, then 8-9)
overwrote the slots tests 1-3 had used.

Repository copy: the harness sits in the rig folder (no pscad/ subfolder; MODEL = ROOT below).

Rig: pnnlREGFMA1mQT.pscx, byte-identical to the file on gfm_validation_task_2 (commit 85c5558,
the state behind the "MQT Tests 1-9" results of 2026-04-22 and the copy in the public repository), and
pscad/PMView.pslx of the same commit.  REGFM_A1: 0.1 MVA at 0.48 kV, Preq 0.6, Qreq 0.2, ImaxF 2,
mP 0.01, mQ 0.05, behind an ideal 0.48/13.8 kV transformer; the PMView source records SCR = 10
(SCMVA 1.0) on its own channels.  The test is selected by the master:mrun component (sequential
integer fed to the PMView block: 1 Flatstart, 2 LVRT_ERCOT_Legacy, ...); the only change made here, in
session, is its range, 8..9 -> 2..2.

Qreq: the project file of commit a4b8e3a (the commit that carries the archived PNG) has Qreq = 0, but
a run at Qreq = 0 gives Q = -0.03 pu before the dip where the archived figure shows +0.10; Qreq = 0.2
reproduces it, so the archived run predates the change to 0 (tests 4-5) that a4b8e3a captured.  Both
records are kept: runs/test_02_LVRT_ERCOT_Legacy (Qreq 0.2, the figure) and ..._Qreq0.

Session pattern: fault_3PG_bus13_10GFM_ilim_arms/run_bus13_arms_headless.py (env-var pop, PATH
sanitize, readback asserts, freshness gate, .inf + .out export, setup.json, messages dump,
pscad.quit() in finally, zombie reap).

Usage:  python -u run_lvrt_headless.py            (test 2)
        python -u run_lvrt_headless.py --test 3   (any other PMView test number)
Then:   python out_to_csv.py
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import time

os.environ.pop("NoDefaultCurrentDirectoryInExePath", None)
os.environ["PATH"] = os.pathsep.join(
    p for p in os.environ.get("PATH", "").split(os.pathsep)
    if not p.rstrip("\\/").lower().endswith((r"\usr\bin", "/usr/bin")))

import mhi.pscad                                        # noqa: E402

PSCAD_VERSION = "5.0.2"
PROJECT_NAME = "pnnlREGFMA1mQT"
ROOT = os.path.dirname(os.path.abspath(__file__))
MODEL = ROOT                     # in this repository the harness sits next to the rig files
GF46 = os.path.join(MODEL, PROJECT_NAME + ".gf46")
RUNS = os.path.join(ROOT, "runs")
MRUN_ID = 1080513901
REGFM_ID = 1052800472
# master:var sliders of the Grid_Parameters module: (component id, value stored in the a4b8e3a file)
GRID_VARS = {"SCR": (103853445, "40"), "XR": (1586243618, "20"), "Mbase": (1156710850, "0.1"),
             "V_base": (1790464980, "0.48"), "G_volt": (1976727411, "0.48"), "G_freq": (1204809474, "60"),
             "G_phase": (1126729124, "0")}
TESTS = {1: "Flatstart", 2: "LVRT_ERCOT_Legacy", 3: "HVRT_ERCOT_Legacy", 4: "V_Down", 5: "V_Up",
         6: "LVRT_Dips_IEEE2800_NOGRR245", 7: "HVRT_Preferred_IEEE2800", 8: "Angle_Down", 9: "Angle_Up"}
EXPECT = {"Preq": "0.6", "ImaxF": "2", "mP": "0.01", "mQ": "0.05", "Vreq": "0.999", "TPf": "0.01"}


def log(msg):
    print(time.strftime("%H:%M:%S ") + msg, flush=True)


def pscad_pids():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Pscad.exe", "/FO", "CSV", "/NH"],
                             capture_output=True, text=True).stdout
    except Exception:                                       # noqa: BLE001
        return set()
    pids = set()
    for line in out.splitlines():
        parts = [x.strip('"') for x in line.split('","')]
        if len(parts) >= 2 and parts[0].lower() == "pscad.exe":
            try:
                pids.add(int(parts[1]))
            except ValueError:
                pass
    return pids


def same(back, val):
    b = str(back).split(" ")[0]
    try:
        return abs(float(b) - float(val)) <= 1e-9 * max(1.0, abs(float(val)))
    except ValueError:
        return b == val


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", type=int, default=2, choices=sorted(TESTS))
    ap.add_argument("--qreq", default="0.2", help="REGFM_A1 reactive-power setpoint (file value 0.2)")
    a = ap.parse_args()
    name = "test_%02d_%s" % (a.test, TESTS[a.test]) + ("" if same(a.qreq, "0.2") else "_Qreq%s" % a.qreq.replace(".", "p"))
    run_dir = os.path.join(RUNS, name)
    log("=== PMView 2.4 test %d (%s) on the REGFM_A1 rig ===" % (a.test, TESTS[a.test]))
    before = pscad_pids()
    if before:
        log("WARNING: Pscad.exe already running (pids %s); a GUI session would block the license" % sorted(before))
    pscad = mhi.pscad.launch(version=PSCAD_VERSION, x64=True, minimize=False)
    try:
        os.chdir(MODEL)
        pscad.load(os.path.join(MODEL, "PMView.pslx"), os.path.join(MODEL, PROJECT_NAME + ".pscx"))
        project = pscad.project(PROJECT_NAME)
        project.focus()
        time.sleep(15)
        mrun = project.component(MRUN_ID)
        mrun.parameters(Min1I=str(a.test), Max1I=str(a.test))
        back = mrun.parameters()
        if not (same(back.get("Min1I"), str(a.test)) and same(back.get("Max1I"), str(a.test))):
            raise RuntimeError("mrun range did not take: %r..%r" % (back.get("Min1I"), back.get("Max1I")))
        log("mrun: variation %s, type %s, range %s..%s step %s, enabled %s, repeat-optimal %s"
            % (back.get("VType1"), back.get("IType1"), back.get("Min1I"), back.get("Max1I"), back.get("Inc1I"),
               back.get("ENAB"), back.get("Repeat")))
        # slider positions do not survive a reload; re-assert the values stored in the file
        for label, (cid, val) in GRID_VARS.items():
            project.component(cid).parameters(Value=val)
            rb = project.component(cid).parameters().get("Value")
            if not same(rb, val):
                raise RuntimeError("grid variable %s did not take (%r, wanted %s)" % (label, rb, val))
        log("grid variables asserted: " + ", ".join("%s %s" % (k, v[1]) for k, v in GRID_VARS.items()))
        project.component(REGFM_ID).parameters(Qreq=a.qreq)
        reg = project.component(REGFM_ID).parameters()
        if not same(reg.get("Qreq"), a.qreq):
            raise RuntimeError("Qreq did not take: %r" % reg.get("Qreq"))
        for k, v in EXPECT.items():
            if not same(reg.get(k), v):
                raise RuntimeError("REGFM_A1 %s = %r, expected %s" % (k, reg.get(k), v))
        log("REGFM_A1: Qreq %s, " % reg.get("Qreq") + ", ".join("%s %s" % (k, reg.get(k)) for k in EXPECT))
        pp = project.parameters()
        log("project: duration %s s, step %s us, plot step %s us" % (pp.get("time_duration"), pp.get("time_step"), pp.get("sample_step")))
        t0 = time.time()
        try:
            project.run()
        finally:
            try:
                msgs = [str(m) for m in project.messages()]
                errs = [m for m in msgs if "error" in m.lower()]
                for m in msgs[-6:]:
                    log("  msg: " + m[:160])
                if errs:
                    log("BUILD/RUN ERRORS: " + " | ".join(e[:200] for e in errs[:5]))
            except Exception as e:                          # noqa: BLE001
                log("messages() failed: %s" % e)
        wall = time.time() - t0
        fresh = [f for f in glob.glob(os.path.join(GF46, PROJECT_NAME + "*.out")) + glob.glob(os.path.join(GF46, PROJECT_NAME + "*.inf"))
                 if os.path.getmtime(f) >= t0 - 1]
        if not [f for f in fresh if f.endswith(".out")]:
            raise RuntimeError("STALE OUTPUT - the simulation did not run")
        os.makedirs(run_dir, exist_ok=True)
        for f in fresh:
            shutil.copy2(f, run_dir)
        log("copied %d fresh files -> %s: %s" % (len(fresh), run_dir, sorted(os.path.basename(f) for f in fresh)))
        setup = {
            "title": "PMView 2.4 test %d (%s) - PNNL REGFM_A1 - re-run of the record behind report Figure 13" % (a.test, TESTS[a.test]),
            "rig": "pscad/pnnlREGFMA1mQT.pscx + pscad/PMView.pslx, byte-identical to gfm_validation_task_2 commit 85c5558 "
                   "(SOW_task_2/PMView2.4/PMVIEW24_pnnl_GFM); in session: mrun range 8..9 -> %d..%d, Qreq asserted" % (a.test, a.test),
            "test_selection": {"mrun_id": MRUN_ID, "Min1I": a.test, "Max1I": a.test},
            "pmview": {"T0_s": 3, "ibr_type": 0, "transient_enable": 0},
            "regfm_a1": {k: reg.get(k) for k in ("Sbase", "Vbase", "Preq", "Qreq", "Vreq", "mP", "mQ", "TPf", "TQf", "ImaxF", "Imax",
                                                  "I_clip", "XL_pu", "Qmax", "Qmin", "Pmax", "Pmin")},
            "grid": "PMView source: SCR 10, SCMVA 1.0 (recorded on the harness channels SCR, SCMVA, R, L); project Grid_Parameters "
                    "sliders asserted at their stored values (SCR 40, X/R 20); 0.48/13.8 kV 100 MVA ideal transformer Xl 0.0586 pu",
            "sim": {"duration_s": pp.get("time_duration"), "step_us": pp.get("time_step"), "plot_step_us": pp.get("sample_step")},
            "pscad": PSCAD_VERSION, "wall_s": round(wall, 1), "run_date": time.strftime("%Y-%m-%d %H:%M"),
        }
        with open(os.path.join(run_dir, "setup.json"), "w") as f:
            json.dump(setup, f, indent=1)
        log("done: %s  %.0f s wall" % (name, wall))
    finally:
        try:
            pscad.quit()
        except Exception:                                   # noqa: BLE001
            pass
        time.sleep(8)
        zombies = pscad_pids() - before
        for pid in zombies:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
        if zombies:
            log("reaped Pscad.exe pids %s" % sorted(zombies))


if __name__ == "__main__":
    main()
