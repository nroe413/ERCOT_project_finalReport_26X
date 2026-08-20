"""The plain DC->AC inverter block symbol for the introduction,
re-drawn from the deck art (intern presentation slide 4: square split
by a diagonal, DC bar upper-left, AC sine lower-right) as report line
art with TeX Gyre Pagella labels so it blends with the document.
"""
import sys
import numpy as np
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(r"C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees"
            r"\upbeat-jones-67c8d3")
OUT = REPO / "report_26X" / "overleaf" / "figures"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import figstyle_26x as st                       # noqa: E402

st.apply()

INK = "#1a1a1a"
DPI = 600

fig, ax = plt.subplots(figsize=(1.9, 1.55))
ax.set_xlim(-0.32, 1.12)
ax.set_ylim(-0.08, 1.10)
ax.set_aspect("equal")
ax.axis("off")

# the box and its diagonal (lower-left to upper-right, as in the deck)
ax.add_patch(plt.Rectangle((0, 0), 1, 1, fill=False, ec=INK, lw=1.6))
ax.plot([0, 1], [0, 1], color=INK, lw=1.2)

# DC bar, upper-left triangle
ax.plot([0.14, 0.42], [0.80, 0.80], color=INK, lw=2.2)
ax.plot([0.14, 0.24], [0.70, 0.70], color=INK, lw=2.2)
ax.plot([0.32, 0.42], [0.70, 0.70], color=INK, lw=2.2)

# AC sine, lower-right triangle
t = np.linspace(0, 2 * np.pi, 200)
ax.plot(0.56 + 0.30 * t / (2 * np.pi), 0.235 + 0.075 * np.sin(t),
        color=INK, lw=1.6)

# terminal stubs and Pagella labels
ax.plot([-0.26, 0], [0.5, 0.5], color=INK, lw=1.2)
ax.plot([1, 1.26], [0.5, 0.5], color=INK, lw=1.2, clip_on=False)
ax.text(-0.13, 0.565, "DC", ha="center", va="bottom", fontsize=10)
ax.text(1.13, 0.565, "AC", ha="center", va="bottom", fontsize=10,
        clip_on=False)

dst = OUT / "fig_inverter_symbol.png"
fig.savefig(dst, dpi=DPI)
plt.close(fig)
print("wrote", dst.name)
