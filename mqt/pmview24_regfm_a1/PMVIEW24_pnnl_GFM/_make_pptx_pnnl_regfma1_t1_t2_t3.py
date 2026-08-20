"""Build results PPTX for PNNL REGFMA1 MQT tests 1-9.

Uses meeting_update_041626_r5.pptx as the base template so the new deck
inherits the UT Austin theme (burnt orange banner, logo, fonts).

Layout: title slide, then per-test: 1 assessment slide + 5 plot slides
(<=2 plots per slide), with verdict per DWG Rev 24 Section 3.1.5.
Pictures are sized with width-only so python-pptx preserves aspect ratio.

Note on run-id mapping: T1-T3 use their original r00001-r00003 plots
(still on disk). A subsequent multi-run sweep wrote T4 (V_Down) to
r00001 and T5 (V_Up) to r00002 of the source .out files, but their
plots were regenerated under r00004_V_Down / r00005_V_Up by
_plot_regfma1_t4_t5.py.
"""
import copy
import datetime
import os

from PIL import Image
from pptx import Presentation
from pptx.util import Emu, Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

HERE = os.path.dirname(os.path.abspath(__file__))
PLOT_DIR = os.path.join(HERE, "plots")
TEMPLATE = os.path.join(HERE, "meeting_update_041626_r5.pptx")

# Font matching meeting_update_041626_r5.pptx
BODY_FONT = "Tw Cen MT"

# Verdict badge colors
PASS_GREEN = RGBColor(0x2C, 0x5F, 0x2D)
COND_AMBER = RGBColor(0xCC, 0x8C, 0x00)
FAIL_RED   = RGBColor(0xB8, 0x00, 0x00)
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
DKGRAY     = RGBColor(0x40, 0x40, 0x40)
MUTED      = RGBColor(0x70, 0x70, 0x70)

SLIDE_W_IN = 10.0
SLIDE_H_IN = 5.625


def load_template():
    prs = Presentation(TEMPLATE)
    # Remove all existing slides while keeping masters/layouts.
    sldIdLst = prs.slides._sldIdLst
    for sldId in list(sldIdLst):
        rId = sldId.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        prs.part.drop_rel(rId)
        sldIdLst.remove(sldId)
    return prs


def layout_by_name(prs, name):
    for m in prs.slide_masters:
        for lyt in m.slide_layouts:
            if lyt.name == name:
                return lyt
    raise KeyError(name)


def force_white_background(slide):
    """Override slide background with a solid white fill.

    The template master uses a blipFill (gray image); setting solidFill on
    the slide's <p:bg> element wins over master background.
    """
    from pptx.oxml.ns import qn
    from lxml import etree
    cSld = slide.element.find(qn('p:cSld'))
    existing = cSld.find(qn('p:bg'))
    if existing is not None:
        cSld.remove(existing)
    bg = etree.SubElement(cSld, qn('p:bg'))
    # ensure bg is first child of cSld (schema requires it)
    cSld.remove(bg)
    cSld.insert(0, bg)
    bgPr = etree.SubElement(bg, qn('p:bgPr'))
    solidFill = etree.SubElement(bgPr, qn('a:solidFill'))
    srgb = etree.SubElement(solidFill, qn('a:srgbClr'))
    srgb.set('val', 'FFFFFF')
    etree.SubElement(bgPr, qn('a:effectLst'))


def set_title(slide, text, size=24):
    for shp in slide.placeholders:
        if shp.placeholder_format.idx == 0:  # title
            shp.text_frame.clear()
            tf = shp.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            r = p.add_run()
            r.text = text
            r.font.size = Pt(size)
            r.font.bold = True
            r.font.name = BODY_FONT
            return


def clear_body(slide):
    """Remove the default body placeholder so we can add custom content."""
    from pptx.oxml.ns import qn
    to_remove = []
    for shp in slide.placeholders:
        if shp.placeholder_format.idx != 0:
            to_remove.append(shp)
    for shp in to_remove:
        sp = shp._element
        sp.getparent().remove(sp)


def add_textbox(slide, left_in, top_in, width_in, height_in):
    return slide.shapes.add_textbox(Inches(left_in), Inches(top_in),
                                    Inches(width_in), Inches(height_in))


def image_size_at_width(path, width_in):
    im = Image.open(path)
    w_px, h_px = im.size
    return width_in * (h_px / w_px)


def add_picture_aspect(slide, path, left_in, top_in, width_in=None, height_in=None):
    kw = {}
    if width_in is not None:
        kw['width'] = Inches(width_in)
    if height_in is not None:
        kw['height'] = Inches(height_in)
    return slide.shapes.add_picture(path, Inches(left_in), Inches(top_in), **kw)


def add_title_slide(prs, title, subtitle):
    sl = prs.slides.add_slide(layout_by_name(prs, "Title Slide"))
    set_title(sl, title)
    # subtitle placeholder is idx=1
    for shp in sl.placeholders:
        if shp.placeholder_format.idx == 1:
            shp.text_frame.clear()
            p = shp.text_frame.paragraphs[0]
            r = p.add_run()
            r.text = subtitle
            r.font.size = Pt(16)
            break
    return sl


def add_assessment(prs, test_num, test_name, section, config, criteria,
                   assessment, result, rcolor):
    sl = prs.slides.add_slide(layout_by_name(prs, "Title and Content"))
    force_white_background(sl)
    set_title(sl, f"Test {test_num}: {test_name}", size=22)
    clear_body(sl)

    # Verdict badge (top right of content area)
    badge_w, badge_h = 2.2, 0.55
    badge_left = SLIDE_W_IN - badge_w - 0.35
    badge_top = 1.45
    rx = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                             Inches(badge_left), Inches(badge_top),
                             Inches(badge_w), Inches(badge_h))
    rx.fill.solid(); rx.fill.fore_color.rgb = rcolor
    rx.line.fill.background()
    tf = rx.text_frame
    tf.margin_left = Inches(0.05); tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.02); tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = result
    r.font.size = Pt(14); r.font.bold = True; r.font.color.rgb = WHITE
    r.font.name = BODY_FONT

    # Content textbox (left of badge)
    cx = add_textbox(sl, 0.35, 1.40, SLIDE_W_IN - badge_w - 0.90, SLIDE_H_IN - 1.40 - 0.35)
    cf = cx.text_frame
    cf.word_wrap = True
    cf.margin_left = Inches(0); cf.margin_right = Inches(0)

    def add_para(text, *, bold=False, size=10, color=DKGRAY, indent=False, space_before=2):
        p = cf.paragraphs[0] if (len(cf.paragraphs) == 1 and not cf.paragraphs[0].runs) else cf.add_paragraph()
        if indent:
            p.level = 1
        r = p.add_run()
        r.text = text
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color
        r.font.name = BODY_FONT
        p.space_before = Pt(space_before)

    def append_run(text, *, bold=False, size=10, color=DKGRAY):
        r = cf.paragraphs[-1].add_run()
        r.text = text
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color
        r.font.name = BODY_FONT

    add_para("DWG Section: ", bold=True, size=10, space_before=0)
    append_run(section)

    add_para("Configuration: ", bold=True, size=10, space_before=3)
    append_run(config)

    add_para("Criteria (DWG Rev 24):", bold=True, size=10, space_before=6)
    for line in criteria:
        add_para("• " + line, size=9, color=DKGRAY, space_before=1)

    add_para("Assessment:", bold=True, size=10, space_before=8)
    add_para(assessment, size=9, color=DKGRAY, space_before=1)


def add_plot_slide(prs, test_num, test_name, plot_title, img1, img2=None):
    sl = prs.slides.add_slide(layout_by_name(prs, "Title and Content"))
    force_white_background(sl)
    set_title(sl, f"Test {test_num}: {test_name} — {plot_title}", size=18)
    clear_body(sl)

    # Available content area below title: y = 1.35 .. 5.3  (h = 3.95)
    content_top = 1.35
    content_h_max = SLIDE_H_IN - content_top - 0.35  # ~3.93

    if img2 and os.path.exists(img2) and os.path.exists(img1):
        w = 4.55
        gap = 0.15
        total_w = 2 * w + gap
        left0 = (SLIDE_W_IN - total_w) / 2
        # Compute heights for centering
        h1 = image_size_at_width(img1, w)
        h2 = image_size_at_width(img2, w)
        top1 = content_top + (content_h_max - h1) / 2
        top2 = content_top + (content_h_max - h2) / 2
        add_picture_aspect(sl, img1, left0, top1, width_in=w)
        add_picture_aspect(sl, img2, left0 + w + gap, top2, width_in=w)
    elif os.path.exists(img1):
        w = 8.5
        h = image_size_at_width(img1, w)
        if h > content_h_max:
            # shrink to fit height
            h = content_h_max
            # width derived from aspect
            add_picture_aspect(sl, img1, (SLIDE_W_IN - w)/2, content_top, height_in=h)
        else:
            left = (SLIDE_W_IN - w) / 2
            top = content_top + (content_h_max - h) / 2
            add_picture_aspect(sl, img1, left, top, width_in=w)


def test_plots(prs, test_num, test_name, dir_name):
    d = os.path.join(PLOT_DIR, dir_name)
    slide_layouts = [
        ("Source Voltage & POI Power",      "vsource.png",          "poi_power.png"),
        ("Power-Voltage Overlay",           "pq_vrms_overlay.png",  None),
        ("POI 3-Phase Voltage & Current",   "vinst_3phase.png",     "ipoi.png"),
        ("POI Frequency & Model/PMU Power", "fpoi.png",             "model_pmu_power.png"),
        ("DFR 3-Phase Voltage & Breaker",   "vinst_dfr_3phase.png", "breaker_status.png"),
    ]
    for title, a, b in slide_layouts:
        img1 = os.path.join(d, a)
        img2 = os.path.join(d, b) if b else None
        add_plot_slide(prs, test_num, test_name, title, img1, img2)


# ============================================================================
prs = load_template()
now = datetime.datetime.now().strftime("%B %d, %Y")
_title_sl = prs.slides.add_slide(layout_by_name(prs, "Title Slide"))
force_white_background(_title_sl)
set_title(_title_sl, "PNNL REGFM_A1 Grid-Forming Inverter — MQT Batch Results — Tests 1–9", size=28)
for shp in _title_sl.placeholders:
    if shp.placeholder_format.idx == 1:
        shp.text_frame.clear()
        p = shp.text_frame.paragraphs[0]
        r = p.add_run()
        r.text = (f"Vbase = 480 V | Sbase = 0.1 MVA | Pref = 0.6 pu\n"
                  f"T1–T3, T6–T9: Qref = 0.2 pu | T4–T5: Qref = 0.0 pu\n{now}")
        r.font.size = Pt(16)
        r.font.name = BODY_FONT
        break

# ---- TEST 1: FLATSTART ----
add_assessment(prs,
    test_num=1,
    test_name="Flat Start",
    section="3.1.5.2 (Flat Start)",
    config="V_grid = 1.000 pu | Pref = 0.6 pu | Qref = 0.2 pu | Sbase = 0.1 MVA | Vbase = 480 V",
    criteria=[
        "\"Flat responses of voltage, MW, MVAR, and frequency — expected to remain "
        "very close to the initial system condition.\"",
        "Minimum 20 seconds of stable simulation required.",
    ],
    assessment=(
        "Clean initialization. After a brief (<0.5 s) transient, all quantities "
        "settle to flat steady state and remain there for the full 30 s run. "
        "Steady-state values (t=5–30 s): P_POI = 0.599 pu (tracks Pref = 0.6), "
        "Q_POI = 0.101 pu, V_source = 1.000 pu, f = 60.00 Hz, I_POI = 0.025 pu. "
        "No oscillations, no drift, no momentary cessation. Note: Q_POI settles "
        "below Qref = 0.2 pu — the PNNL REGFM_A1 AVR/droop trims Q at V = 1.0 pu "
        "(voltage target met). Per DWG §3.1.5.2 this is acceptable; quantities "
        "remain very close to the initial system condition."
    ),
    result="PASS", rcolor=PASS_GREEN,
)
test_plots(prs, 1, "Flat Start", "r00001_Flatstart")

# ---- TEST 2: LVRT ERCOT LEGACY ----
add_assessment(prs,
    test_num=2,
    test_name="LVRT ERCOT Legacy",
    section="3.1.5.4 (LVRT — ERCOT Legacy)",
    config="LVRT profile (1.0 → 0.9 pu sustained, dips to 0.1 pu) | Pref = 0.6 pu | Sbase = 0.1 MVA",
    criteria=[
        "No momentary cessation; appropriate dynamic reactive response and AVR response.",
        "At 0.9 pu sustained POI voltage, AVR should drive resource toward nearly full "
        "reactive production (significantly lagging).",
        "Real power recovery should start before POI voltage reaches 0.9 pu and fully "
        "recover within 1.0 s of V recovery to 0.9 pu.",
        "Any oscillations should be well damped.",
    ],
    assessment=(
        "Model rides through all voltage disturbances without tripping or momentary "
        "cessation. At the 0.9 pu sustained segment: P_POI = 0.599 pu (maintained at "
        "Pref), Q_POI = +0.423 pu (reactive injection in correct direction). Real-power "
        "recovery begins before V reaches 0.9 pu and P returns to Pref within ~0.5 s "
        "(meets 1.0 s criterion). Final recovery to 1.0 pu is clean. CONCERNS: "
        "(1) Q_POI = 0.42 pu at V=0.9 pu is moderate — not \"nearly full reactive "
        "production\". (2) During the deep 0.1 pu dip (t=21.5–27 s), P and Q oscillate "
        "(±0.2 pu band) without clear damping; oscillations do not grow but are not "
        "\"well damped\"."
    ),
    result="CONDITIONAL PASS", rcolor=COND_AMBER,
)
test_plots(prs, 2, "LVRT ERCOT Legacy", "r00002_LVRT_ERCOT_Legacy")

# ---- TEST 3: HVRT ERCOT LEGACY ----
add_assessment(prs,
    test_num=3,
    test_name="HVRT ERCOT Legacy",
    section="3.1.5.5 (HVRT — ERCOT Legacy)",
    config="HVRT profile (1.0 → 1.1 pu sustained; later steps) | Pref = 0.6 pu | Sbase = 0.1 MVA",
    criteria=[
        "No momentary cessation; fast reactive absorption during HV transient "
        "(ideally within 0.5 s of transient inception).",
        "At 1.1 pu sustained POI voltage, AVR should drive resource toward nearly full "
        "reactive absorption (significantly leading).",
        "Real power should be sustained during the high-voltage condition (modest ≤5% "
        "reduction acceptable for extra Q absorption).",
        "Full P recovery when V returns to normal range (0.95–1.05 pu).",
    ],
    assessment=(
        "Model rides through the HVRT profile without tripping. Fast Q response: at "
        "the V step to 1.15 pu, Q_POI transitions from +0.10 to −0.45 pu within one "
        "sample window (<<0.5 s). At sustained 1.1 pu: P_POI = 0.600 pu (maintained), "
        "Q_POI = −0.452 pu (absorption in correct direction). At 1.05 pu step: P=0.599, "
        "Q=−0.453 pu (continues absorbing). Post-event: V steps to 2.0 pu (extreme "
        "overvoltage beyond standard HVRT profile); P=0.596 maintained, Q=−3.67 pu heavy "
        "absorption, no trip, no oscillation. CONCERNS: (1) Q absorption of −0.45 pu at "
        "V=1.1 pu is moderate — not \"nearly full reactive absorption\". (2) Model "
        "continues heavy Q absorption at V=1.05 pu rather than relaxing as V returns "
        "toward the normal 0.95–1.05 pu range — minor deviation from recovery criterion."
    ),
    result="CONDITIONAL PASS", rcolor=COND_AMBER,
)
test_plots(prs, 3, "HVRT ERCOT Legacy", "r00003_HVRT_ERCOT_Legacy")

# ---- TEST 4: SMALL V DISTURBANCE (STEP DOWN) ----
add_assessment(prs,
    test_num=4,
    test_name="Small V Disturbance (Step Down)",
    section="3.1.5.3 (Small Voltage Disturbance)",
    config="Vsched = 1.01 pu | V-Reg ON | V steps: 1.00 → 0.97 → 0.95 pu | Pref = 0.6 pu | Qref = 0.0 pu",
    criteria=[
        "Plant remains connected through all voltage steps.",
        "Stable, well-damped response to each step.",
        "Appropriate voltage regulation: reactive injection as V drops below Vsched.",
        "Real power maintained at Pref throughout.",
        "No sustained oscillations or momentary cessation.",
    ],
    assessment=(
        "Model rides through both voltage steps cleanly. V profile: 1.000 pu pre-event, "
        "steps down to 0.970 pu at t≈5 s, then 0.950 pu at t≈23 s. Real-power tracking: "
        "P_POI = 0.599 pu flat across all three V levels (Pref = 0.6 maintained). Reactive "
        "response: Q_POI increases from +0.058 → +0.360 → +0.425 pu as V drops — correct "
        "V-Reg direction (injection to push V back toward Vsched = 1.01). Current I_POI = "
        "0.025 → 0.032 pu (well below any current limit). Frequency f_POI = 60.000 Hz flat. "
        "Each step exhibits a fast, well-damped transition to the new steady state with no "
        "overshoot or ringing visible. No momentary cessation, no trip."
    ),
    result="PASS", rcolor=PASS_GREEN,
)
test_plots(prs, 4, "Small V Disturbance (Step Down)", "r00004_V_Down")

# ---- TEST 5: SMALL V DISTURBANCE (STEP UP) ----
add_assessment(prs,
    test_num=5,
    test_name="Small V Disturbance (Step Up)",
    section="3.1.5.3 (Small Voltage Disturbance)",
    config="Vsched = 1.01 pu | V-Reg ON | V steps: 1.00 → 1.03 → 1.05 pu | Pref = 0.6 pu | Qref = 0.0 pu",
    criteria=[
        "Plant remains connected through all voltage steps.",
        "Stable, well-damped response to each step.",
        "Appropriate voltage regulation: reactive absorption as V rises above Vsched.",
        "Real power maintained at Pref throughout.",
        "No sustained oscillations or momentary cessation.",
    ],
    assessment=(
        "Model rides through both voltage steps cleanly. V profile: 1.000 pu pre-event, "
        "steps up to 1.030 pu at t≈5 s, then 1.050 pu at t≈23 s. Real-power tracking: "
        "P_POI = 0.599 pu flat across all three V levels (Pref = 0.6 maintained). Reactive "
        "response: Q_POI transitions +0.058 → −0.439 → −0.453 pu as V rises — correct "
        "V-Reg direction (absorption to pull V back toward Vsched = 1.01). Current I_POI "
        "stays at 0.025 → 0.030 pu. Frequency f_POI = 60.000 Hz flat. Each step produces "
        "a fast, well-damped transition with no overshoot or ringing. No momentary "
        "cessation, no trip."
    ),
    result="PASS", rcolor=PASS_GREEN,
)
test_plots(prs, 5, "Small V Disturbance (Step Up)", "r00005_V_Up")

# ---- TEST 6: LVRT DIPS IEEE 2800 ----
add_assessment(prs,
    test_num=6,
    test_name="LVRT Dips IEEE 2800",
    section="3.1.5.4 (LVRT — IEEE 2800 Dips)",
    config="Vsched = 1.03 pu | V-Reg ON | Dips to 0.5 / 0.7 pu | Pref = 0.6 pu | Qref = 0.2 pu",
    criteria=[
        "No momentary cessation; appropriate dynamic reactive response during dips.",
        "Reactive injection (lagging) at depressed POI voltage.",
        "Real power recovery before POI voltage reaches nominal, fully recovered "
        "within 1.0 s of V returning to ≥0.9 pu.",
        "Any oscillations should be well damped.",
    ],
    assessment=(
        "Model rides through all IEEE 2800 dips without tripping or momentary "
        "cessation. Pre-event (t<10 s): P_POI = 0.60 pu, Q_POI ≈ +0.10 pu, "
        "V = 1.00 pu. Dip 1 (t≈11 s, V = 0.50 pu): P = 0.598 pu maintained, "
        "Q = +0.389 pu (correct-direction reactive injection). Dip 2 (t≈15 s, "
        "V = 0.70 pu): P = 0.599 pu, Q = +0.413 pu. Between dips P returns to "
        "0.60 pu promptly. Current I_POI ≤ 0.084 pu (well inside capability). "
        "Frequency f_POI = 60.000 Hz flat. CONCERNS: (1) P transient peak of "
        "~1.63 pu observed during one recovery event — 2.7× Pref. (2) Q swings "
        "bounded ±0.75 pu with no sustained growth, but damping during deep "
        "dips is modest rather than tight. (3) Reactive output at V = 0.5–0.7 pu "
        "is moderate (~0.4 pu), not \"nearly full reactive production\"."
    ),
    result="CONDITIONAL PASS", rcolor=COND_AMBER,
)
test_plots(prs, 6, "LVRT Dips IEEE 2800", "r00006_LVRT_Dips_IEEE2800_NOGRR245")

# ---- TEST 7: HVRT PREFERRED IEEE 2800 ----
add_assessment(prs,
    test_num=7,
    test_name="HVRT Preferred IEEE 2800",
    section="3.1.5.5 (HVRT — IEEE 2800 Preferred)",
    config="Vsched = 1.03 pu | V-Reg ON | Swells to 1.1 / 1.05 / 1.6 pu | Pref = 0.6 pu | Qref = 0.2 pu",
    criteria=[
        "No momentary cessation; fast reactive absorption during HV transient "
        "(ideally within 0.5 s of inception).",
        "Reactive absorption (leading) at elevated POI voltage.",
        "Real power sustained during HV condition (modest ≤5% reduction acceptable).",
        "Full P recovery when V returns to 0.95–1.05 pu range.",
    ],
    assessment=(
        "Model rides through the full IEEE 2800 preferred HVRT envelope without "
        "tripping. Fast Q response: Q_POI drops from +0.10 to −0.45 pu within "
        "one sample when V first steps to 1.1 pu (<<0.5 s). Segment 1 (t≈5–13 s, "
        "V = 1.10 pu sustained): P = 0.599 pu, Q = −0.452 pu. Segment 2 "
        "(t≈15–21 s, V = 1.05 pu): P = 0.599 pu, Q = −0.453 pu. Extreme "
        "segment (t≈23–29 s, V = 1.60 pu — beyond standard HVRT envelope): "
        "P = 0.596 pu (−0.6% reduction, well within ≤5%), Q = −2.96 pu (extreme "
        "absorption), I_POI = 0.079 pu. No trip. Frequency f_POI = 60.000 Hz. "
        "CONCERNS: (1) Q absorption of −0.45 pu at V = 1.10 pu is moderate, "
        "not \"nearly full absorption\". (2) At V = 1.05 pu (top of the normal "
        "range) model continues heavy Q absorption instead of relaxing toward "
        "nominal — minor deviation from P/V recovery expectation."
    ),
    result="CONDITIONAL PASS", rcolor=COND_AMBER,
)
test_plots(prs, 7, "HVRT Preferred IEEE 2800", "r00007_HVRT_Preferred_IEEE2800")

# ---- TEST 8: PHASE ANGLE JUMP (DOWN) ----
add_assessment(prs,
    test_num=8,
    test_name="Phase Angle Jump (Down)",
    section="3.1.5.13 (Phase Angle Jump — Down)",
    config="Vsched = 1.01 pu | V-Reg ON | Negative phase-angle steps | Pref = 0.6 pu | Qref = 0.2 pu",
    criteria=[
        "Plant remains connected through each angle step.",
        "No momentary cessation.",
        "Bounded transient response; model returns to steady state between events.",
        "Stable behavior without divergent oscillations.",
    ],
    assessment=(
        "Model rides through all negative phase-angle jumps without tripping. "
        "Between events and post-disturbance (t ≥ 23.5 s): P_POI = 0.60 pu, "
        "Q_POI ≈ +0.10 pu, V ≈ 1.00 pu, f = 60.000 Hz — steady state restored. "
        "Transient excursions during each angle step span t ≈ 3–23 s and are "
        "substantial: peak |P| = 1.63 pu (including brief negative P indicating "
        "momentary real-power absorption), peak |Q| = 1.61 pu, peak frequency "
        "deviation |Δf| = 10.8 Hz, peak I = 0.079 pu. Each transient settles "
        "fully before the next event, and the final steady state is clean. "
        "CONCERNS: (1) Magnitudes of P / Q / Δf transients are large and could "
        "stress a physical plant. (2) Momentary reverse P (absorbing) is "
        "unusual for an inverter-based resource. Behavior is stable and "
        "bounded, but transient severity warrants further tuning review."
    ),
    result="CONDITIONAL PASS", rcolor=COND_AMBER,
)
test_plots(prs, 8, "Phase Angle Jump (Down)", "r00008_Angle_Down")

# ---- TEST 9: PHASE ANGLE JUMP (UP) ----
add_assessment(prs,
    test_num=9,
    test_name="Phase Angle Jump (Up)",
    section="3.1.5.13 (Phase Angle Jump — Up)",
    config="Vsched = 1.01 pu | V-Reg ON | Positive phase-angle steps | Pref = 0.6 pu | Qref = 0.2 pu",
    criteria=[
        "Plant remains connected through each angle step.",
        "No momentary cessation.",
        "Bounded transient response; model returns to steady state between events.",
        "Stable behavior without divergent oscillations.",
    ],
    assessment=(
        "Model rides through all positive phase-angle jumps without tripping. "
        "Between events and post-disturbance (t ≥ 23.5 s): P_POI = 0.60 pu, "
        "Q_POI ≈ +0.10 pu, V ≈ 1.00 pu, f = 60.000 Hz — steady state restored. "
        "Transient excursions during each angle step span t ≈ 3–23 s: peak |P| "
        "= 1.59 pu (with brief negative P during events), peak |Q| = 1.61 pu, "
        "peak frequency deviation |Δf| = 17.0 Hz, peak I = 0.079 pu. "
        "Phase-profile reference Ph_profile oscillates in a bounded 83–98° "
        "band. Each transient settles fully before the next event, and the "
        "final steady state is clean. CONCERNS: (1) |Δf| ≈ 17 Hz is larger "
        "than the step-down case (10.8 Hz) and would be significant for a "
        "physical plant. (2) Momentary reverse P observed during transients. "
        "Stable and bounded overall, but transient severity warrants tuning "
        "review."
    ),
    result="CONDITIONAL PASS", rcolor=COND_AMBER,
)
test_plots(prs, 9, "Phase Angle Jump (Up)", "r00009_Angle_Up")

# ============================================================================
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
fname = os.path.join(HERE, f"PNNL_REGFMA1_MQT_Tests1-9_{ts}.pptx")
prs.save(fname)
print(f"Saved: {fname} ({len(prs.slides)} slides)")
