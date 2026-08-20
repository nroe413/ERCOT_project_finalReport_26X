"""make_smib_deck.py — minimal deck: the SMIB device-only fault comparison.

Three slides on the meeting template: title + the two comparison figures
(V & fault current; P & frequency recovery), picked newest from plots/.

Usage:  python make_smib_deck.py
"""
import datetime
import sys
from pathlib import Path

from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN

SCRIPT = Path(__file__).resolve().parent
ROOT = SCRIPT.parent.parent
sys.path.insert(0, str(ROOT / "experiments" / "fault_3PG_bus39_GFMvsSync"))
import make_pptx as M

M.TEMPLATE_PATH = ROOT / "slide_templates" / "meeting_update_060426_r5.pptx"


def newest(folder, pattern):
    c = sorted(Path(folder).glob(pattern), key=lambda p: p.stat().st_mtime)
    return c[-1] if c else None


def main():
    prs = M.load_template()
    W = prs.slide_width / 914400.0
    H = prs.slide_height / 914400.0

    # title
    sl = prs.slides.add_slide(M.first_layout(prs, "Title Slide", "Title and Content"))
    M.force_white_background(sl)
    M.clear_placeholders(sl)
    tb = sl.shapes.add_textbox(Inches(0.6), Inches(1.7), Inches(W - 1.2), Inches(1.0))
    p = tb.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = "SMIB fault ride-through — bus-39 synchronous machine vs GFM"
    r.font.size = Pt(26); r.font.bold = True
    r.font.color.rgb = M.NAVY; r.font.name = M.BODY_FONT
    tb = sl.shapes.add_textbox(Inches(0.6), Inches(2.8), Inches(W - 1.2), Inches(1.4))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, line in enumerate((
            "Device-only comparison: same bolted 3PG (t = 3.0 s, 5 cycles), same relative grid "
            "strength (SCR = 10, X/R = 20 on each device's own base), no topology change.",
            "Sync: 2000 MVA / 230 kV bus-39 machine (TypicalGT.dyr), dispatch 0.50 pu.   "
            "GFM: PNNL REGFM_A1 SMIB, Preq = 0.60 pu, ImaxF = 2.0 (39-bus study used 1.5).")):
        par = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        par.alignment = PP_ALIGN.CENTER
        if i:
            par.space_before = Pt(8)
        r = par.add_run(); r.text = line
        r.font.size = Pt(12.5); r.font.color.rgb = M.DKGRAY; r.font.name = M.BODY_FONT

    # the two comparison slides
    for title, pat in (
            ("Same fault, same grid strength — voltage & fault current (1/4)",
             "smib_gfm_vs_sync_VI_*.png"),
            ("Recovery — active power & frequency (2/4)",
             "smib_gfm_vs_sync_Pf_*.png"),
            ("Recovery — active vs reactive current decomposition (3/4)",
             "smib_gfm_vs_sync_IPIQ_*.png"),
            ("Post-fault current composition — reactive vs active share (4/4)",
             "smib_gfm_vs_sync_PCT_*.png")):
        img = newest(SCRIPT / "plots", pat)
        sl = prs.slides.add_slide(M.first_layout(prs, "Title and Content", "Title Only"))
        M.force_white_background(sl)
        M.clear_placeholders(sl)
        M.add_centered_title(sl, title, W, top_in=0.20, height_in=0.6, size=19)
        M.add_picture_aspect(sl, img, W, H, top_in=0.92)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = SCRIPT / ("SMIB_GFMvsSync_fault_comparison_%s.pptx" % ts)
    prs.save(str(out))
    print("saved %s (%d slides)" % (out.name, len(prs.slides._sldIdLst)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
