"""Shared matplotlib style for every 26X report figure.

Contract (user directive, 2026-08-07):
- Figures are sized in TRUE PRINT INCHES.  The report is letter paper
  with 1 in margins, so \\textwidth = 6.5 in.  A figure included at
  width=\\textwidth must be created 6.5 in wide; at 0.85\\textwidth,
  5.52 in wide; and so on.  Never rescale a figure in LaTeX by more
  than a few percent -- make the PNG the right size instead.
- Fonts: TeX Gyre Pagella everywhere (axes, ticks, legends,
  annotations) -- the report body face (ut26x.sty loads tgpagella;
  "CMU Serif" is NOT installed on this machine and silently fell back
  to STIXGeneral before 2026-08-07). The Pagella OTFs are registered
  directly from the MiKTeX distribution. Math stays mathtext "cm",
  matching the report, whose math font is Computer Modern.
- Save WITHOUT a tight bounding box so the physical size on disk is
  exactly the configured inches (use constrained_layout for spacing).

Usage:
    import figstyle_26x as st
    st.apply()
    fig, ax = plt.subplots(figsize=st.size(1.0, 0.55))  # full width
    ...
    st.save(fig, "name")          # writes name.png at 600 dpi
"""
from pathlib import Path

import matplotlib
from matplotlib import font_manager as _fm

TEXTWIDTH_IN = 6.5          # \textwidth: letter paper, 1 in margins
BODY_PT = 11                # document body font size (11pt article)

# TeX Gyre Pagella OpenType files: registered from whichever TeX tree is
# present (MiKTeX per-user or system, TeX Live on Windows or Unix); the
# serif fallback stack below applies when none is found.
import glob as _glob
import os as _os
_CANDIDATES = [
    _os.path.join(_os.environ.get("LOCALAPPDATA", ""), "Programs", "MiKTeX", "fonts", "opentype", "public", "tex-gyre"),
    r"C:\Program Files\MiKTeX\fonts\opentype\public\tex-gyre",
    r"C:\texlive\*\texmf-dist\fonts\opentype\public\tex-gyre",
    "/usr/share/texlive/texmf-dist/fonts/opentype/public/tex-gyre",
    "/usr/share/texmf/fonts/opentype/public/tex-gyre",
    "/usr/local/texlive/*/texmf-dist/fonts/opentype/public/tex-gyre",
]
for _pat in _CANDIDATES:
    for _dir in _glob.glob(_pat):
        for _f in ("texgyrepagella-regular.otf", "texgyrepagella-bold.otf",
                   "texgyrepagella-italic.otf", "texgyrepagella-bolditalic.otf"):
            _p = Path(_dir) / _f
            if _p.exists():
                _fm.fontManager.addfont(str(_p))

SERIF_STACK = ["TeX Gyre Pagella", "Palatino Linotype",
               "STIXGeneral", "DejaVu Serif"]


def apply(base=BODY_PT):
    small = base - 1
    matplotlib.rcParams.update({
        "font.family": "serif",
        "font.serif": SERIF_STACK,
        "mathtext.fontset": "cm",
        "text.usetex": False,
        "font.size": base,
        "axes.titlesize": base,
        "axes.labelsize": base,
        "xtick.labelsize": small,
        "ytick.labelsize": small,
        "legend.fontsize": small,
        "figure.titlesize": base,
        "axes.unicode_minus": True,
        "figure.constrained_layout.use": True,
        "savefig.dpi": 600,
        "savefig.facecolor": "white",
        # exact-inch contract: NO tight bbox cropping
        "savefig.bbox": "standard",
    })


def size(width_frac=1.0, aspect=0.6):
    """(width, height) in inches: width as a fraction of \\textwidth,
    height = width * aspect."""
    w = TEXTWIDTH_IN * width_frac
    return (w, w * aspect)


def save(fig, stem, dpi=600):
    fig.savefig(stem + ".png", dpi=dpi)
