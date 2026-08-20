"""DWG model-quality battery (tests 1-9) on the TypicalGT synchronous
machine, driven through PSCAD's native multiple-run feature.

The rig is a COPY (pscad/) of TypicalGT_inertia_validation, modified
four ways and only in the copy:
  Vrated 345 -> 230 kV (machine bus base; user-confirmed),
  time_duration 7 -> 40 s (LVRT profile alone spans 30 s + T0 = 3 s),
  Mruns 1 -> 9 (project multiple-run),
  the test-select integer const -> master:run_num, so run N IS test N.

One project.run() therefore executes all nine tests. Test names follow
the DWG Rev. 24 numbering used by the GFM campaign
(origin/gfm_validation_task_2, plot_gfm_tests.py TEST_PROFILES).

Environment traps handled per project memory:
  - NoDefaultCurrentDirectoryInExePath popped before launch, or every
    simulation dies at startup and exports silently re-read stale .out;
  - Git-Bash \\usr\\bin entries stripped from PATH, or linked-lib copy
    rules die under sh (make Error 127);
  - output freshness is proven by mtime: anything already in the build
    dir is recorded before the run and only files newer than run start
    are accepted;
  - pscad.quit() in finally, then any surviving Pscad.exe that we
    launched is reported (never blindly killed: the user may run their
    own instance).
"""
import json
import os
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PSCAD_DIR = HERE / "pscad"
RUNS = HERE / "runs"
WORKSPACE = PSCAD_DIR / "typicalGT_inertia_validation_battery.pswx"
PROJECT = "TypicalGTPMView"
GF46 = PSCAD_DIR / (PROJECT + ".gf46")
PSCAD_VERSION = "5.0.2"

TESTS = {
    1: "Flatstart",
    2: "LVRT_ERCOT_Legacy",
    3: "HVRT_ERCOT_Legacy",
    4: "V_Down",
    5: "V_Up",
    6: "LVRT_Dips_IEEE2800_NOGRR245",
    7: "HVRT_Preferred_IEEE2800",
    8: "Angle_Down",
    9: "Angle_Up",
}


def log(msg):
    line = "%s  %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line, flush=True)
    with open(HERE / "battery_log.txt", "a", encoding="utf8") as f:
        f.write(line + "\n")


def clean_env():
    os.environ.pop("NoDefaultCurrentDirectoryInExePath", None)
    parts = os.environ.get("PATH", "").split(os.pathsep)
    keep = [p for p in parts if "\\usr\\bin" not in p.lower()]
    os.environ["PATH"] = os.pathsep.join(keep)
    log("env cleaned: PATH entries %d -> %d" % (len(parts), len(keep)))


def main():
    clean_env()
    import mhi.pscad                                   # noqa: E402

    RUNS.mkdir(exist_ok=True)
    pre = {p.name: p.stat().st_mtime for p in GF46.glob("*.out")} \
        if GF46.exists() else {}
    log("pre-existing .out files in build dir: %d" % len(pre))

    t_start = time.time()
    pscad = None
    try:
        log("launching PSCAD %s" % PSCAD_VERSION)
        pscad = mhi.pscad.launch(version=PSCAD_VERSION, x64=True,
                                 minimize=True)
        os.chdir(PSCAD_DIR)
        log("loading workspace %s" % WORKSPACE.name)
        pscad.load(str(WORKSPACE))
        project = pscad.project(PROJECT)
        project.focus()

        # verify the copy's settings took (never trust the file alone)
        ps = project.parameters()
        for k in ("time_duration", "Mruns", "MrunType", "time_step",
                  "sample_step", "PlotType"):
            log("  project %s = %s" % (k, ps.get(k)))
        assert str(ps.get("time_duration")).startswith("40"), \
            "duration is not 40 s in the loaded project"
        assert str(ps.get("Mruns")) == "9", "Mruns is not 9"

        log("running the battery (one multiple-run invocation, 9 runs "
            "x 40 s at %s us)" % ps.get("time_step"))
        try:
            project.run()
        finally:
            # A 9 x 40 s battery cannot finish in seconds, so a fast
            # return means a build/run failure: log every project
            # message so the failure names itself (first attempt died
            # silently on the ETRAN lib's relative path breaking in
            # the copied location).
            try:
                for m in project.messages():
                    log("  msg [%s] %s" % (getattr(m, 'scope', '?'),
                                           getattr(m, 'text', m)))
            except Exception as e:
                log("  could not read messages: %s" % e)
        log("run() returned after %.1f min" % ((time.time() - t_start) / 60))
    finally:
        if pscad is not None:
            try:
                pscad.quit()
                log("pscad.quit() ok")
            except Exception as e:
                log("pscad.quit() failed: %s" % e)

    # ---- collect fresh outputs -----------------------------------
    fresh = [p for p in GF46.glob("*.out")
             if p.stat().st_mtime >= t_start - 1]
    infs = [p for p in GF46.glob("*.inf")
            if p.stat().st_mtime >= t_start - 1]
    log("fresh .out files: %d, fresh .inf: %d" % (len(fresh), len(infs)))
    for p in sorted(fresh):
        log("   %s  (%d bytes)" % (p.name, p.stat().st_size))
    if not fresh:
        log("FATAL: no fresh output; the freshness guard refuses stale "
            "files. Nothing exported.")
        sys.exit(2)

    # Group multi-run outputs. PSCAD names run sets either
    # <name>_r#[_NN].out or <name>[_NN].out inside per-run subdirs;
    # discover rather than assume.
    import re
    groups = {}
    for p in fresh:
        m = re.match(r".*_(\d{2})\.out$", p.name)
        stem = re.sub(r"_\d{2}\.out$", "", p.name)
        groups.setdefault(stem, []).append(p)
    # also catch per-run folders
    run_dirs = [d for d in GF46.glob("*") if d.is_dir()
                and d.stat().st_mtime >= t_start - 1]
    log("output stems: %s; fresh run dirs: %s"
        % (sorted(groups), [d.name for d in run_dirs]))

    stamp = time.strftime("%Y%m%d_%H%M%S")
    manifest = {"stamp": stamp, "stems": sorted(groups),
                "run_dirs": [d.name for d in run_dirs],
                "wall_min": round((time.time() - t_start) / 60, 1)}
    (HERE / "collect_manifest.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf8")

    # copy everything fresh into runs/<stamp>_raw for the export step
    raw = RUNS / ("%s_raw" % stamp)
    raw.mkdir(parents=True, exist_ok=True)
    for p in fresh + infs:
        shutil.copy2(p, raw / p.name)
    for d in run_dirs:
        shutil.copytree(d, raw / d.name, dirs_exist_ok=True)
    log("raw outputs copied to %s" % raw)
    log("DONE")


if __name__ == "__main__":
    main()
