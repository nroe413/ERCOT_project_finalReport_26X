"""verify_pscad_build.py -- headless smoke test of the shipped PSCAD cases.

Loads each workspace with the PSCAD automation library, builds, runs a
0.3 s record, and reports whether fresh EMTDC output appeared.  Use it
after cloning or unzipping to confirm that PSCAD, GFortran 4.6, and the
libraries under systems/lib are found through the relative links in the
project files.  For every linked library it also prints the file the
generated makefile copies, so a link that still points outside the
repository shows up even on a machine where that outside file exists.

    python scripts/tools/verify_pscad_build.py            # all four cases
    python scripts/tools/verify_pscad_build.py 10GFM_Vsched smib_gfm

Requirements: PSCAD 5.0.2 (x64) with GFortran 4.6 and the mhi.pscad
package (installed with PSCAD).  Note: PSCAD loads library projects
asynchronously; the script waits after loading the workspace, otherwise
the build reports missing E-TRAN definitions.  Run it from a copy with a
short path (for example C:\\ercot26x): the build folders add about 60
characters to the longest path.
"""
import glob
import os
import re
import sys
import time

# mhi.pscad launches EMTDC through cmd.exe; these two environment fixes
# avoid two known failures when the script is started from a Git Bash shell.
os.environ.pop("NoDefaultCurrentDirectoryInExePath", None)
os.environ["PATH"] = os.pathsep.join(
    p for p in os.environ.get("PATH", "").split(os.pathsep)
    if not p.rstrip("\\/").lower().endswith((r"\usr\bin", "/usr/bin")))

import mhi.pscad                                        # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# key: (folder, workspace, project)
CASES = {
    "00GFM_all_sync": ("systems\\ieee39\\00GFM_all_sync", "test2works.pswx", "IEEE39_acLine1"),
    "10GFM_Vsched": ("systems\\ieee39\\10GFM_Vsched", "test2works10GFM.pswx", "IEEE39_acLine1"),
    "smib_sync": ("systems\\smib_siib\\sync", "SMIB_SYNC.pswx", "SMIB_SYNC"),
    "smib_gfm": ("systems\\smib_siib\\gfm", "REGFM_A1_PNNL.pswx", "REGFM_A1"),
}
LOAD_SETTLE_S = 25


def log(msg):
    print(time.strftime("%H:%M:%S ") + msg, flush=True)


def linked_library_sources(gf46):
    """The files the generated makefile copies into the build folder (one per linked library)."""
    out = []
    for mak in glob.glob(os.path.join(gf46, "*.mak")):
        with open(mak, errors="replace") as fh:
            for line in fh:
                m = re.search(r'copy\s+"([^"]+\.(?:lib|obj|o))"', line, re.I)
                if m:
                    out.append(os.path.normpath(os.path.join(gf46, m.group(1))))
    return sorted(set(out))


def main():
    wanted = sys.argv[1:] or list(CASES)
    ok = True
    for key in wanted:
        rel, ws, name = CASES[key]
        model = os.path.join(ROOT, rel)
        gf46 = os.path.join(model, name + ".gf46")
        pscad = mhi.pscad.launch(version="5.0.2", x64=True, minimize=False)
        try:
            os.chdir(model)
            pscad.load(os.path.join(model, ws))
            time.sleep(LOAD_SETTLE_S)
            project = pscad.project(name)
            project.focus()
            project.parameters(time_duration="0.3")
            t0 = time.time()
            log("%s: build + run 0.3 s ..." % key)
            project.run()
            fresh = [f for f in glob.glob(os.path.join(gf46, "*.out"))
                     if os.path.getmtime(f) >= t0]
            errs = [m for m in project.messages()
                    if str(getattr(m, "status", "")).lower() in ("error", "fatal")]
            log("  %.0f s wall, %d fresh .out chunks, %d errors" % (time.time() - t0, len(fresh), len(errs)))
            for m in errs[:5]:
                log("    " + str(getattr(m, "text", m))[:160])
            for src in linked_library_sources(gf46):
                inside = os.path.normcase(src).startswith(os.path.normcase(ROOT))
                log("  links %s%s" % (src, "" if inside else "   <-- OUTSIDE the repository"))
                ok = ok and inside
            if not fresh or errs:
                ok = False
        finally:
            try:
                pscad.quit()
            except Exception:                               # noqa: BLE001
                pass
            time.sleep(3)
    log("RESULT: " + ("OK" if ok else "FAILED"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
