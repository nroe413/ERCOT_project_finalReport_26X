"""run_3PG_fault.py — build + run the 1-GFL 39-bus case (ieee39_sz1GFL) headlessly
via mhi.pscad, patterned on single_machine_infinite_bus_1syncMachineValidation/
run_3PG_fault.py (the proven SMIB harness).

CASE: IEEE 39-bus, 9 sync machines + PNNL WECC GFL at bus 32 (grafted by
tools/graft_gfl_bus32.py — see README.md). Base disturbance of the GFL
breakpoint sweep: bolted 3PG at bus 14, t = 3.0 s, 5 cycles (0.0833 s),
reclose disabled. 10 s window, 50 us solve step, 200 us plot step.

The fault dials live as master:const(i) components feeding datalabels (values
verified in-model; asserted here anyway because panel sliders don't persist):
    4119 BrkFaultLocation = 14      4098 BrkFaultType     = 7 (3PG)
    4118 BrkFaultTime     = 3       4117 BrkFaultDuration = 0.0833
    4899 RecloseEnabled   = 0       (InstantTrip=1, RecloseDelay=1 as in the
                                     committed GFM-sweep models; gated off by
                                     RecloseEnabled=0)

RUN (from inside ieee39_sz1GFL/):   python run_3PG_fault.py
On success the fresh .inf + _NN.out land in
    ../experiments/fault_3PG_bus14_1GFL/runs/3PG_at_bus14_w_1GFL_at_bus32_t3p0s_5cyc_norecl_10s/
ready for the standard out_to_csv -> plot_fault_traces -> make_pptx pipeline.
"""
import glob
import logging
import os
import shutil
import sys
import time

# --- environment fixes (hard-won; do NOT remove) --------------------------
# 1) NoDefaultCurrentDirectoryInExePath makes every EMTDC launch die and lets
#    exports silently re-read stale .out files.
os.environ.pop("NoDefaultCurrentDirectoryInExePath", None)
# 2) git-bash /usr/bin shadowing breaks the PSCAD make (sh instead of cmd,
#    linked-lib copy rules fail with Error 127).
os.environ["PATH"] = os.pathsep.join(
    p for p in os.environ["PATH"].split(os.pathsep)
    if "\\usr\\bin" not in p.lower() and "/usr/bin" not in p.lower())

import mhi.pscad  # noqa: E402  (import after the env fixes)

logging.basicConfig(level=logging.INFO,
                    format="%(levelname)-8s %(name)-26s %(message)s")
logging.getLogger("mhi.pscad").setLevel(logging.WARNING)
LOG = logging.getLogger("main")

PROJECT_NAME = "IEEE39_acLine1"
CASE_FOLDER = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.join(CASE_FOLDER, "test2works1GFL.pswx")
RUN_DIR = os.path.normpath(os.path.join(
    CASE_FOLDER, "..", "experiments", "fault_3PG_bus14_1GFL", "runs",
    "3PG_at_bus14_w_1GFL_at_bus32_t3p0s_5cyc_norecl_10s"))

# base-case dials (component id -> Value)
DIALS = {
    4119: "14",       # BrkFaultLocation
    4098: "7",        # BrkFaultType = 3PG
    4118: "3",        # BrkFaultTime [s]
    4117: "0.0833",   # BrkFaultDuration [s] = 5 cycles
    4899: "0",        # RecloseEnabled = 0 (no reclose)
}
TIME_DURATION = "10"   # [s]
TIME_STEP = "50"       # [us]  (solution)
SAMPLE_STEP = "200"    # [us]  (5 kHz channel plot)

# optional CLI overrides: `id=value` sets that component's Value param;
# `id:param=value` sets an arbitrary param (e.g. 1939290356:TapI=1.0);
# `--rundir=NAME` redirects the output copy to runs/NAME (diagnostics).
EXTRA = []   # (component id, param name, value)
for arg in sys.argv[1:]:
    if arg.startswith("--rundir="):
        RUN_DIR = os.path.join(os.path.dirname(RUN_DIR), arg.split("=", 1)[1])
        continue
    if arg.startswith("--duration="):
        TIME_DURATION = arg.split("=", 1)[1]
        continue
    lhs, _, val = arg.partition("=")
    if ":" in lhs:
        cid, _, pname = lhs.partition(":")
        EXTRA.append((int(cid), pname, val))
    else:
        DIALS[int(lhs)] = val

t0 = time.time()
pscad = None
try:
    for ver in ("5.0.2", "5.0.1", None):
        try:
            pscad = (mhi.pscad.launch(version=ver, x64=True, minimize=False)
                     if ver else mhi.pscad.launch(minimize=False))
            LOG.info("PSCAD launched (version=%s)", ver or "default")
            break
        except Exception as exc:  # try the next installed version
            LOG.warning("launch(version=%s) failed: %s", ver, exc)
    if pscad is None:
        sys.exit("could not launch PSCAD")

    pscad.load(WORKSPACE)
    project = pscad.project(PROJECT_NAME)
    project.focus()

    for cid, val in DIALS.items():
        project.component(cid).parameters(Value=val)
        LOG.info("dial %d -> %s", cid, val)
    for cid, pname, val in EXTRA:
        project.component(cid).parameters(**{pname: val})
        LOG.info("param %d.%s -> %s", cid, pname, val)
    project.parameters(time_duration=TIME_DURATION, time_step=TIME_STEP,
                       sample_step=SAMPLE_STEP)

    print("1GFL 39-bus: bolted 3PG at bus 14, t=3.0 s, 5 cyc, no reclose, "
          "%s s window" % TIME_DURATION)
    project.run()
    print("Simulation Finished (%.1f min)" % ((time.time() - t0) / 60.0))

finally:
    if pscad is not None:
        try:
            pscad.quit()
        except Exception:
            pass

# ---- collect FRESH outputs (mtime must postdate the launch) ---------------
gf46 = os.path.join(CASE_FOLDER, PROJECT_NAME + ".gf46")
inf = sorted(glob.glob(os.path.join(gf46, "*.inf")), key=os.path.getmtime)
outs = sorted(glob.glob(os.path.join(gf46, "*_[0-9][0-9].out")))
if not inf:
    sys.exit("no .inf produced in %s" % gf46)
stale = [f for f in inf[-1:] + outs if os.path.getmtime(f) < t0]
if stale:
    sys.exit("STALE outputs (predate this run) — refusing to copy:\n  "
             + "\n  ".join(stale))

if not os.path.isdir(RUN_DIR):
    os.makedirs(RUN_DIR)
copied = []
for f in [inf[-1]] + outs:
    shutil.copy2(f, RUN_DIR)
    copied.append(os.path.basename(f))
print("Copied %d files -> %s" % (len(copied), RUN_DIR))
print("  " + ", ".join(copied[:5]) + (" ..." if len(copied) > 5 else ""))
print("Next: cd ../experiments/fault_3PG_bus14_1GFL && python out_to_csv.py "
      "&& python plot_fault_traces.py")
