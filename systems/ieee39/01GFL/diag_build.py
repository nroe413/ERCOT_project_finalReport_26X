"""diag_build.py -- rebuild the 1GFL case and dump every PSCAD build message."""
import os
os.environ.pop("NoDefaultCurrentDirectoryInExePath", None)
os.environ["PATH"] = os.pathsep.join(
    p for p in os.environ["PATH"].split(os.pathsep)
    if "\\usr\\bin" not in p.lower() and "/usr/bin" not in p.lower())

import mhi.pscad

CASE = os.path.dirname(os.path.abspath(__file__))
pscad = mhi.pscad.launch(version="5.0.2", x64=True, minimize=True)
try:
    pscad.load(os.path.join(CASE, "test2works1GFL.pswx"))
    prj = pscad.project("IEEE39_acLine1")
    prj.focus()
    try:
        prj.run()
    except Exception as exc:
        print("run() raised: %r" % (exc,))
    msgs = prj.messages()
    print("=== %d messages ===" % len(msgs))
    for m in msgs:
        # Message objects expose scope/name/text/status-ish fields; be defensive
        try:
            print("[%s] %s | %s" % (getattr(m, "status", "?"),
                                    getattr(m, "scope", getattr(m, "component", "?")),
                                    getattr(m, "text", m)))
        except Exception:
            print(repr(m))
finally:
    try:
        pscad.quit()
    except Exception:
        pass
