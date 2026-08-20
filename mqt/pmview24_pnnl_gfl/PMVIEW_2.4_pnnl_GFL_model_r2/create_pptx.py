#!/usr/bin/env python3
"""
create_pptx.py - Assemble PNNL GFL test plot PNGs into a PowerPoint presentation.

Uses the ERCOT meeting template from slide_template/ for consistent styling.

Usage:
    python create_pptx.py
"""

import os
from datetime import datetime
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FILE = os.path.join(SCRIPT_DIR, "slide_template",
                             "ERCOT_meeting_022626_r1_022626.pptx")
PLOT_DIR = os.path.join(SCRIPT_DIR, "plots")
OUTPUT_FILE = os.path.join(
    SCRIPT_DIR,
    f"GFL_Test_Results_PNNL_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pptx"
)

FONT_NAME = "Tw Cen MT"

# Tests 1-9 in order
TESTS = [
    (1, "r00001_Flatstart", "Test 1: Flatstart"),
    (2, "r00002_LVRT_ERCOT_Legacy", "Test 2: LVRT ERCOT Legacy"),
    (3, "r00003_HVRT_ERCOT_Legacy", "Test 3: HVRT ERCOT Legacy"),
]

# Each slide pairs vsource (left) with one other plot (right)
PLOT_GRID = [
    ["vsource.png", "vinst_3phase.png"],
    ["vsource.png", "poi_power.png"],
    ["vsource.png", "model_pmu_power.png"],
    ["vsource.png", "ipoi.png"],
    ["vsource.png", "fpoi.png"],
    ["vsource.png", "vinst_pmu_3phase.png"],
    ["vsource.png", "vinst_dfr_3phase.png"],
    ["vsource.png", "pq_vrms_overlay.png"],
    ["vsource.png", "breaker_status.png"],
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

COLS = 2
ROWS = 1


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
    title_ph.text = "PNNL GFL Inverter\nPMView MQT Test Results"
    for para in title_ph.text_frame.paragraphs:
        para.alignment = PP_ALIGN.CENTER
        for run in para.runs:
            run.font.name = FONT_NAME
            run.font.size = Pt(24)

    # Use the subtitle/body placeholder (idx 1)
    body_ph = slide.placeholders[1]
    body_ph.text = (f"PNNL GFL Model\n"
                    f"SOW Task 2 \u2014 PMView 2.4\n{now_str}")
    for para in body_ph.text_frame.paragraphs:
        para.alignment = PP_ALIGN.CENTER
        for run in para.runs:
            run.font.name = FONT_NAME
            run.font.size = Pt(14)


def add_test_slide(prs, test_dir, title, slide_number, row_files):
    """Add one slide with two side-by-side plots (vsource + one other)."""
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

    # Calculate image sizes for 2-column, 1-row layout
    slide_w = prs.slide_width
    usable_w = slide_w - MARGIN_LEFT - MARGIN_RIGHT - GAP_X * (COLS - 1)
    usable_h = (prs.slide_height - CONTENT_TOP - MARGIN_BOTTOM)
    img_w = usable_w // COLS
    img_h = usable_h // ROWS

    for col_i, fname in enumerate(row_files):
        if fname is None:
            continue
        img_path = os.path.join(PLOT_DIR, test_dir, fname)
        if not os.path.exists(img_path):
            print(f"  Warning: {img_path} not found, skipping")
            continue

        # Fit image within cell while preserving aspect ratio
        with Image.open(img_path) as im:
            native_w, native_h = im.size
        native_ratio = native_w / native_h
        cell_ratio = img_w / img_h

        if native_ratio > cell_ratio:
            fit_w = img_w
            fit_h = int(img_w / native_ratio)
        else:
            fit_h = img_h
            fit_w = int(img_h * native_ratio)

        # Center within the cell
        left = MARGIN_LEFT + col_i * (img_w + GAP_X) + (img_w - fit_w) // 2
        top = CONTENT_TOP + (img_h - fit_h) // 2
        slide.shapes.add_picture(str(img_path), int(left), int(top),
                                 int(fit_w), int(fit_h))

    add_page_number(slide, slide_number)


def main():
    prs = Presentation(TEMPLATE_FILE)

    # Remove all existing template slides
    delete_all_slides(prs)

    add_title_slide(prs)

    slide_num = 2
    for test_num, test_dir, title in TESTS:
        test_path = os.path.join(PLOT_DIR, test_dir)
        if not os.path.isdir(test_path):
            print(f"Skipping {title}: directory not found")
            continue
        print(f"Adding {title}")
        for row_files in PLOT_GRID:
            # Build subtitle from the non-vsource plot name
            other = [f for f in row_files if f and f != "vsource.png"]
            subtitle = other[0].replace(".png", "").replace("_", " ") if other else ""
            slide_title = f"{title} — {subtitle}"
            add_test_slide(prs, test_dir, slide_title, slide_num, row_files)
            slide_num += 1

    prs.save(OUTPUT_FILE)
    print(f"\nSaved {OUTPUT_FILE}")
    print(f"Total slides: {len(prs.slides)}")


if __name__ == "__main__":
    main()
