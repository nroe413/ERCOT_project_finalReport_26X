"""Introduction inverter figure from the user's Inkscape drawing
(Desktop/UT/Research/ERCOT/inkscape/26XFinalPresentation/
dcToacInverter.svg): per-phase DC-AC bridge stack, DC-DC stage, and
the microcontroller PWM loop.

The drawing's labels (abc phase marks, dc) are path-outlined sans
glyphs; to blend with the report they are whited out here and re-set
in TeX Gyre Pagella at document scale. The art itself is the user's,
rendered from the CURRENT svg via Inkscape at 2400 px (the png next
to it was a day older than the svg).

Pixel geometry measured on the 2400x1941 render:
  top abc box (37,0)-(392,179), rings a/b/c at x=74/204/329, y=257
  bottom abc box (19,1548)-(373,1703), rings at x=51/181/307, y=1503
  dc box (2168,925)-(2398,1100)
Overwrites fig_inverter_symbol.png so the LaTeX figure block keeps
its name and label.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
            r"\upbeat-jones-67c8d3")
OUT = REPO / "report_26X" / "overleaf" / "figures"
RENDER = Path(r"C:\Users\roena\AppData\Local\Temp\claude"
              r"\C--UT-research-NateRoe-ERCOT-Project--claude-worktrees"
              r"-upbeat-jones-67c8d3"
              r"\30e56d97-153f-4147-9c6f-ea52cf7ef0b9\scratchpad"
              r"\inv_render.png")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import figstyle_26x as st                       # noqa: E402

st.apply()

arr = np.array(Image.open(RENDER).convert("RGBA")).astype(float)
img = (arr[..., :3] * arr[..., 3:] / 255
       + 255 * (1 - arr[..., 3:] / 255)) / 255
H_PX, W_PX = img.shape[:2]

PAD = 6
for x0, y0, x1, y1 in [(37, 0, 392, 179), (2168, 925, 2398, 1100)]:
    img[max(0, y0 - PAD):y1 + PAD, max(0, x0 - PAD):x1 + PAD] = 1.0
# the bottom abc box touches the colored phase rings, so clear only
# neutral (glyph) pixels there and leave saturated ring pixels alone
reg = img[1542:1710, 13:380]
sat = reg.max(axis=2) - reg.min(axis=2)
neutral_dark = (sat < 0.18) & (reg.sum(axis=2) < 2.85)
reg[neutral_dark] = 1.0

W_IN = 3.9                      # placed at 0.6\textwidth
fig = plt.figure(figsize=(W_IN, W_IN * H_PX / W_PX))
ax = fig.add_axes([0, 0, 1, 1])
ax.imshow(img, extent=(0, W_PX, H_PX, 0), interpolation="lanczos")
ax.set_xlim(0, W_PX)
ax.set_ylim(H_PX, 0)
ax.axis("off")

FS = 14
for x, ch in [(74, "a"), (204, "b"), (329, "c")]:
    ax.text(x, 190, ch, ha="center", va="bottom", fontsize=FS)
for x, ch in [(51, "a"), (181, "b"), (307, "c")]:
    ax.text(x, 1575, ch, ha="center", va="top", fontsize=FS)
ax.text(2283, 1012, "dc", ha="center", va="center", fontsize=FS)

dst = OUT / "fig_inverter_symbol.png"
fig.savefig(dst, dpi=600)
plt.close(fig)
print("wrote", dst.name)
