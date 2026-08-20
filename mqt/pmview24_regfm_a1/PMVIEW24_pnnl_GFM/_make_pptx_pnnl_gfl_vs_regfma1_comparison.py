"""Build a comparison table PPTX: PNNL GFL (with current limiting) vs PNNL REGFMA1.

Modeled on GFM_MQT_AW_Comparison_Table_20260408_220045.pptx.
"""
import os
from datetime import datetime

from pptx import Presentation
from pptx.util import Emu, Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

NAVY       = RGBColor(0x1E, 0x3A, 0x5F)
ICE        = RGBColor(0xE8, 0xF0, 0xFE)
BAND       = RGBColor(0xD0, 0xD8, 0xE8)
PASS_GREEN = RGBColor(0x22, 0x8B, 0x22)
FAIL_RED   = RGBColor(0xCC, 0x00, 0x00)
COND_AMBER = RGBColor(0xCC, 0x8C, 0x00)
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)

VERDICT_COLORS = {
    'PASS': PASS_GREEN,
    'CONDITIONAL PASS': COND_AMBER,
    'FAIL': FAIL_RED,
    'NOT RUN': RGBColor(0x80, 0x80, 0x80),
}

# Rows: (test#, name, section, config, GFL_verdict, REGFMA1_verdict)
# GFL verdicts: from meeting_update_041626_r5.pptx slide 11, "Current-Limiting ON" column.
# REGFMA1 verdicts: derived from pnnlREGFMA1mQT .out data for tests 1-3; tests 4-9 not yet run.
ROWS = [
    ('1', 'Flat Start',                     '3.1.5.2',  'Vsched = 1.03 | V-Reg ON', 'PASS',             'PASS'),
    ('2', 'LVRT ERCOT Legacy',              '3.1.5.4',  'Vsched = 1.03 | V-Reg ON', 'FAIL',             'CONDITIONAL PASS'),
    ('3', 'HVRT ERCOT Legacy',              '3.1.5.5',  'Vsched = 1.03 | V-Reg ON', 'FAIL',             'CONDITIONAL PASS'),
    ('4', 'Small V Disturbance (Step Down)','3.1.5.3',  'Vsched = 1.01 | V-Reg ON', 'PASS',             'PASS'),
    ('5', 'Small V Disturbance (Step Up)',  '3.1.5.3',  'Vsched = 1.01 | V-Reg ON', 'PASS',             'PASS'),
    ('6', 'LVRT Dips IEEE 2800',            '3.1.5.4',  'Vsched = 1.03 | V-Reg ON', 'CONDITIONAL PASS', 'CONDITIONAL PASS'),
    ('7', 'HVRT Preferred IEEE 2800',       '3.1.5.5',  'Vsched = 1.03 | V-Reg ON', 'FAIL',             'CONDITIONAL PASS'),
    ('8', 'Phase Angle Jump (Down)',        '3.1.5.13', 'Vsched = 1.01 | V-Reg ON', 'PASS',             'CONDITIONAL PASS'),
    ('9', 'Phase Angle Jump (Up)',          '3.1.5.13', 'Vsched = 1.01 | V-Reg ON', 'PASS',             'CONDITIONAL PASS'),
]


def tally(verdicts):
    p = sum(1 for v in verdicts if v == 'PASS')
    c = sum(1 for v in verdicts if v == 'CONDITIONAL PASS')
    f = sum(1 for v in verdicts if v == 'FAIL')
    n = sum(1 for v in verdicts if v == 'NOT RUN')
    return p, c, f, n


def set_cell(cell, text, *, bold=False, size=10, color=None, fill=None, align=PP_ALIGN.LEFT):
    cell.text_frame.clear()
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = cell.text_frame.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.name = 'Calibri'
    r.font.size = Pt(size)
    r.font.bold = bold
    if color is not None:
        r.font.color.rgb = color
    cell.margin_left = Inches(0.06)
    cell.margin_right = Inches(0.06)
    cell.margin_top = Inches(0.02)
    cell.margin_bottom = Inches(0.02)
    if fill is not None:
        cell.fill.solid()
        cell.fill.fore_color.rgb = fill
    else:
        cell.fill.background()


def build():
    prs = Presentation()
    prs.slide_width = Emu(9144000)
    prs.slide_height = Emu(5143500)
    blank = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank)

    # Title
    title_tx = slide.shapes.add_textbox(Inches(0.35), Inches(0.25), Inches(9.3), Inches(0.55))
    tf = title_tx.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = 'MQT Results Summary — PNNL GFL (w/ Current Limiting) vs. PNNL REGFMA1'
    r.font.name = 'Calibri'
    r.font.size = Pt(18)
    r.font.bold = True
    r.font.color.rgb = NAVY

    # Subtitle
    sub_tx = slide.shapes.add_textbox(Inches(0.35), Inches(0.75), Inches(9.3), Inches(0.30))
    sp = sub_tx.text_frame.paragraphs[0]
    sr = sp.add_run()
    sr.text = 'Per ERCOT DWG Procedure Manual Rev. 24, Section 3.1.5 (Dynamic Model Quality Tests)'
    sr.font.name = 'Calibri'
    sr.font.size = Pt(11)
    sr.font.italic = True
    sr.font.color.rgb = NAVY

    # Table geometry (EMU)
    n_rows = 1 + len(ROWS) + 1  # header + data rows + overall
    n_cols = 6
    tbl_left = Emu(320040)
    tbl_top = Emu(1150000)
    tbl_w = Emu(8595360)
    tbl_h = Emu(3950000)

    tbl_shape = slide.shapes.add_table(n_rows, n_cols, tbl_left, tbl_top, tbl_w, tbl_h)
    tbl = tbl_shape.table

    # Column widths (EMU)
    col_w = [
        Emu(457200),   # Test
        Emu(1600000),  # Name
        Emu(640000),   # Section
        Emu(2100000),  # Configuration (narrow label)
        Emu(1900080),  # PNNL GFL (w/ CL)
        Emu(1898000),  # PNNL REGFMA1
    ]
    for i, w in enumerate(col_w):
        tbl.columns[i].width = w

    # Row heights
    for row in tbl.rows:
        row.height = Emu(280000)

    # Header row
    headers = ['Test', 'Name', 'Section', 'Configuration', 'PNNL GFL (w/ CL)', 'PNNL REGFMA1']
    for j, h in enumerate(headers):
        set_cell(tbl.cell(0, j), h, bold=True, size=11, color=WHITE, fill=NAVY, align=PP_ALIGN.CENTER)

    # Data rows
    gfl_verdicts, rfm_verdicts = [], []
    for i, (tnum, name, section, cfg, gfl_v, rfm_v) in enumerate(ROWS):
        row_idx = i + 1
        zebra = ICE if (i % 2 == 0) else None
        set_cell(tbl.cell(row_idx, 0), tnum, fill=zebra, align=PP_ALIGN.CENTER)
        set_cell(tbl.cell(row_idx, 1), name, fill=zebra)
        set_cell(tbl.cell(row_idx, 2), section, fill=zebra, align=PP_ALIGN.CENTER)
        set_cell(tbl.cell(row_idx, 3), cfg, fill=zebra, size=9)
        set_cell(tbl.cell(row_idx, 4), gfl_v,
                 bold=True, size=10, color=VERDICT_COLORS[gfl_v],
                 fill=zebra, align=PP_ALIGN.CENTER)
        set_cell(tbl.cell(row_idx, 5), rfm_v,
                 bold=True, size=10, color=VERDICT_COLORS[rfm_v],
                 fill=zebra, align=PP_ALIGN.CENTER)
        gfl_verdicts.append(gfl_v)
        rfm_verdicts.append(rfm_v)

    # Overall row
    overall_row = n_rows - 1
    for j in range(3):
        set_cell(tbl.cell(overall_row, j), '', fill=BAND)
    set_cell(tbl.cell(overall_row, 3), 'Overall:', bold=True, size=10, fill=BAND, align=PP_ALIGN.RIGHT)
    gp, gc, gf, gn = tally(gfl_verdicts)
    rp, rc, rf, rn = tally(rfm_verdicts)
    set_cell(tbl.cell(overall_row, 4),
             f'{gp}P / {gc}C / {gf}F ({gn} N/R)',
             bold=True, size=10, color=NAVY, fill=BAND, align=PP_ALIGN.CENTER)
    set_cell(tbl.cell(overall_row, 5),
             f'{rp}P / {rc}C / {rf}F ({rn} N/R)',
             bold=True, size=10, color=NAVY, fill=BAND, align=PP_ALIGN.CENTER)

    # Footnote
    fn_tx = slide.shapes.add_textbox(Inches(0.35), Inches(5.20), Inches(9.3), Inches(0.30))
    fn_p = fn_tx.text_frame.paragraphs[0]
    fn_p.alignment = PP_ALIGN.LEFT
    fn_r = fn_p.add_run()
    fn_r.text = ('GFL verdicts from meeting_update_041626_r5 (Current-Limiting ON). '
                 'REGFMA1 tests 1–3, 6–9 at Pref=0.6/Qref=0.2 pu; tests 4–5 at Pref=0.6/Qref=0.0 pu; 0.1 MVA / 480 V base. '
                 'P=PASS  C=CONDITIONAL PASS  F=FAIL')
    fn_r.font.name = 'Calibri'
    fn_r.font.size = Pt(8)
    fn_r.font.italic = True
    fn_r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)


    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       f'PNNL_GFL_vs_REGFMA1_Comparison_Table_{ts}.pptx')
    prs.save(out)
    print('Saved:', out)
    return out


if __name__ == '__main__':
    build()
