#!/usr/bin/env python3
"""
create_pptx.py - Assemble GFM test plot PNGs into a PowerPoint presentation.

Uses the ERCOT meeting template from slide_template/ for consistent styling.

Usage:
    python create_pptx.py
"""

import os
from datetime import datetime
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FILE = os.path.join(SCRIPT_DIR, "slide_template",
                             "ERCOT_meeting_022626_r1_022626.pptx")
PLOT_DIR = os.path.join(SCRIPT_DIR, "plots")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "GFM_Test_Results.pptx")

FONT_NAME = "Tw Cen MT"

# Tests 1-9 in order
TESTS = [
    (1, "r00001_Flatstart", "Test 1: Flatstart"),
    (2, "r00002_LVRT_ERCOT_Legacy", "Test 2: LVRT ERCOT Legacy"),
    (3, "r00003_HVRT_ERCOT_Legacy", "Test 3: HVRT ERCOT Legacy"),
    (4, "r00004_V_Down", "Test 4: Voltage Down"),
    (5, "r00005_V_Up", "Test 5: Voltage Up"),
    (6, "r00006_LVRT_Dips_IEEE2800_NOGRR245", "Test 6: LVRT Dips IEEE 2800"),
    (7, "r00007_HVRT_Preferred_IEEE2800", "Test 7: HVRT Preferred IEEE 2800"),
    (8, "r00008_Angle_Down", "Test 8: Angle Down"),
    (9, "r00009_Angle_Up", "Test 9: Angle Up"),
]

# Plot grid: 3 columns, 4 rows (last row has overlay centered + breaker)
PLOT_GRID = [
    ["vinst_3phase.png", "vsource.png", "poi_power.png"],
    ["model_pmu_power.png", "ipoi.png", "fpoi.png"],
    ["vinst_pmu_3phase.png", "vinst_dfr_3phase.png", "pq_vrms_overlay.png"],
    [None, "breaker_status.png", None],
]

# Title position/size matching the template (from slide 4 inspection)
TITLE_LEFT = Emu(0)
TITLE_TOP = Emu(438150)       # 0.479 in
TITLE_WIDTH = Emu(8458200)    # 9.25 in
TITLE_HEIGHT = Emu(666750)    # 0.729 in

# Content area below title
CONTENT_TOP = Emu(438150 + 666750)  # just below title
MARGIN_LEFT = Inches(0.25)
MARGIN_RIGHT = Inches(0.25)
MARGIN_BOTTOM = Inches(0.15)
GAP_X = Inches(0.12)
GAP_Y = Inches(0.08)

# Page number position (from template)
PAGENUM_LEFT = Emu(8458200)   # 9.25 in
PAGENUM_TOP = Emu(4706197)    # 5.147 in
PAGENUM_WIDTH = Emu(622797)
PAGENUM_HEIGHT = Emu(296449)

COLS = 3
ROWS = 4


def delete_all_slides(prs):
    """Remove all existing slides from the presentation."""
    while len(prs.slides) > 0:
        rId = prs.slides._sldIdLst[0].get(
            '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
        )
        prs.part.drop_rel(rId)
        prs.slides._sldIdLst.remove(prs.slides._sldIdLst[0])


def get_layout_from_master(prs, master_idx, layout_name):
    """Get a slide layout by name from a specific master."""
    master = prs.slide_masters[master_idx]
    for layout in master.slide_layouts:
        if layout.name == layout_name:
            return layout
    raise ValueError(f"Layout '{layout_name}' not found in master {master_idx}")


def add_page_number(slide, number):
    """Add a page number text box matching the template style."""
    txBox = slide.shapes.add_textbox(PAGENUM_LEFT, PAGENUM_TOP,
                                     PAGENUM_WIDTH, PAGENUM_HEIGHT)
    tf = txBox.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.text = str(number)
    p.alignment = PP_ALIGN.RIGHT
    run = p.runs[0]
    run.font.name = FONT_NAME
    run.font.size = Pt(10)


def add_title_slide(prs):
    layout = get_layout_from_master(prs, 2, "Section Header")
    slide = prs.slides.add_slide(layout)

    now_str = datetime.now().strftime("%m/%d/%Y %I:%M %p")

    # Use the title placeholder (idx 0)
    title_ph = slide.placeholders[0]
    title_ph.text = "NREL GFM Inverter\nPMView MQT Test Results"
    for para in title_ph.text_frame.paragraphs:
        para.alignment = PP_ALIGN.CENTER
        for run in para.runs:
            run.font.name = FONT_NAME
            run.font.size = Pt(24)

    # Use the subtitle/body placeholder (idx 1)
    body_ph = slide.placeholders[1]
    body_ph.text = (f"National Lab of Rockies Kenyon GFM Model\n"
                    f"SOW Task 2 \u2014 PMView 2.4\n{now_str}\n"
                    f"Without anti-windup current limiting")
    for para in body_ph.text_frame.paragraphs:
        para.alignment = PP_ALIGN.CENTER
        for run in para.runs:
            run.font.name = FONT_NAME
            run.font.size = Pt(14)


def add_test_slide(prs, test_dir, title, slide_number):
    layout = get_layout_from_master(prs, 2, "Title and Content")
    slide = prs.slides.add_slide(layout)

    # Set title via placeholder and reposition to match template
    title_ph = slide.placeholders[0]
    title_ph.left = TITLE_LEFT
    title_ph.top = TITLE_TOP
    title_ph.width = TITLE_WIDTH
    title_ph.height = TITLE_HEIGHT
    title_ph.text = title
    for run in title_ph.text_frame.paragraphs[0].runs:
        run.font.name = FONT_NAME
        run.font.size = Pt(18)

    # Remove the content placeholder so images sit cleanly
    content_ph = slide.placeholders[1]
    sp = content_ph._element
    sp.getparent().remove(sp)

    # Calculate image sizes for the 3x3 grid
    slide_w = prs.slide_width
    usable_w = slide_w - MARGIN_LEFT - MARGIN_RIGHT - GAP_X * (COLS - 1)
    usable_h = (prs.slide_height - CONTENT_TOP - MARGIN_BOTTOM
                - GAP_Y * (ROWS - 1))
    img_w = usable_w // COLS
    img_h = usable_h // ROWS

    # Add images in 3x3 grid
    for row_i, row_files in enumerate(PLOT_GRID):
        for col_i, fname in enumerate(row_files):
            if fname is None:
                continue
            img_path = os.path.join(PLOT_DIR, test_dir, fname)
            if not os.path.exists(img_path):
                print(f"  Warning: {img_path} not found, skipping")
                continue

            left = MARGIN_LEFT + col_i * (img_w + GAP_X)
            top = CONTENT_TOP + row_i * (img_h + GAP_Y)
            slide.shapes.add_picture(str(img_path), int(left), int(top),
                                     int(img_w), int(img_h))

    add_page_number(slide, slide_number)


def main():
    prs = Presentation(TEMPLATE_FILE)

    # Remove all existing template slides
    delete_all_slides(prs)

    add_title_slide(prs)

    for i, (test_num, test_dir, title) in enumerate(TESTS):
        test_path = os.path.join(PLOT_DIR, test_dir)
        if not os.path.isdir(test_path):
            print(f"Skipping {title}: directory not found")
            continue
        print(f"Adding {title}")
        add_test_slide(prs, test_dir, title, slide_number=i + 2)

    prs.save(OUTPUT_FILE)
    print(f"\nSaved {OUTPUT_FILE}")
    print(f"Total slides: {len(prs.slides)}")


if __name__ == "__main__":
    main()
