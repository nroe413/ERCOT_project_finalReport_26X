"""Control experiment: headless build of the UNTOUCHED ieee39_sz1GFM (GUI-proven).
Does 'Electranix_Common_Set has no definition' appear there too?"""
import os
os.environ.pop("NoDefaultCurrentDirectoryInExePath", None)
os.environ["PATH"] = os.pathsep.join(
    p for p in os.environ["PATH"].split(os.pathsep)
    if "\\usr\\bin" not in p.lower() and "/usr/bin" not in p.lower())
import mhi.pscad

GFM = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "ieee39_sz1GFM"))
pscad = mhi.pscad.launch(version="5.0.2", x64=True, minimize=True)
try:
    pscad.load(os.path.join(GFM, "test2works1GFM.pswx"))
    prj = pscad.project("IEEE39_acLine1")
    prj.focus()
    try:
        prj.build()          # build only, no run
    except Exception as exc:
        print("build() raised: %r" % (exc,))
    for m in prj.messages():
        s = getattr(m, "status", "?")
        if s in ("error", "warning") or "Build:" in str(getattr(m, "text", "")):
            print("[%s] %s" % (s, getattr(m, "text", m)))
    tail = [m for m in prj.messages() if "Build" in str(getattr(m, "text", ""))
            or "Make" in str(getattr(m, "text", ""))]
    for m in tail:
        print("TAIL: %s" % getattr(m, "text", m))
finally:
    try:
        pscad.quit()
    except Exception:
        pass
