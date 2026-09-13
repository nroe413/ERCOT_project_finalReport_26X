"""Report figure fig:trip (narr_trip_bus14.png): the bus-14 reference fault on the
all-GFM fleet at ImaxF = 1.2 pu with and without a hardware overcurrent trip
(experiment fault_trip_gfm on SOW_task_4, 2026-09-12).

Inputs: compact extracts of the three PSCAD records, shipped in
data/report_figure_data/fault_trip_gfm/extract_{notrip,k1p5,k1p2}.csv: TIME,
bus-16 RMS voltage (kV, 230 kV side), fleet active power (sum of the ten
generator-bus channels B<N>P, 230 kV side of the step-up transformers), and
for the trip records the unit-32 breaker phase currents IB32A/B/C (kA, 10 kV
branch) and the latch BRK32.

Panels (textwidth x 5.2 in, three rows):
  (a) bus-16 voltage in pu of 230 kV, 2.5-10 s;
  (b) fleet active power in GW;
  (c) unit-32 phase currents in pu of rated peak current
      (rated peak = sqrt(2) x 1083 MVA / (sqrt(3) x 10 kV) = 88.43 kA) over
      the first 6 ms of the fault, k = 1.5 record, with the two thresholds
      and the trip instant.
"""
import sys
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_paths as rp  # noqa: E402

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = rp.OUT
sys.path.insert(0, str(Path(__file__).resolve().parent))
import figstyle_26x as st  # noqa: E402

st.apply()
plt.rcParams["figure.constrained_layout.use"] = False   # manual spacing below

EXTRACT = rp.DATA / "fault_trip_gfm"      # shipped CSV extracts of the three records
FAULT_T, CLEAR_T = 3.0, 3.0833
PEAK_KA_PER_PU_32 = np.sqrt(2.0) * 1083.0 / (np.sqrt(3.0) * 10.0)   # 88.43 kA per pu of rated peak
BLUE, RED, DARK = "#1f77b4", "#c0392b", "#7f1d1d"
BAND = "#fbd0c4"

RECORDS = [("notrip", "no trip", BLUE, "-"),
           ("k1p5", "trip at 1.5 pu of rated peak, 1 ms", RED, "-"),
           ("k1p2", "trip at 1.2 pu of rated peak, 1 ms", DARK, "--")]


def main():
    data = {k: pd.read_csv(EXTRACT / ("extract_%s.csv" % k)) for k, _, _, _ in RECORDS}
    fig, ax = plt.subplots(3, 1, figsize=(st.TEXTWIDTH_IN, 5.2),
                           gridspec_kw=dict(height_ratios=[1.0, 1.0, 1.15], hspace=0.62))

    for k, lab, col, ls in RECORDS:
        d = data[k]
        ax[0].plot(d.TIME, d.V16_kV / 230.0, color=col, ls=ls, lw=1.1, label=lab)
        ax[1].plot(d.TIME, d.P_fleet_MW / 1e3, color=col, ls=ls, lw=1.1, label=lab)
    for a in ax[:2]:
        a.axvspan(FAULT_T, CLEAR_T, color=BAND, alpha=0.6, zorder=0)
        a.set_xlim(2.5, 10.0)
        a.grid(True, alpha=0.3)
    ax[0].set_ylabel("bus-16 voltage (pu)")
    ax[0].set_ylim(0.4, 1.1)
    ax[0].set_yticks([0.4, 0.6, 0.8, 1.0])
    ax[0].legend(loc="lower center", fontsize=8, framealpha=0.95, bbox_to_anchor=(0.58, 0.0))
    ax[1].set_ylabel("fleet active power (GW)")
    ax[1].set_ylim(2.0, 7.0)
    ax[1].set_xlabel("time (s)")
    ax[0].set_title("(a) bus-16 RMS voltage", fontsize=9, loc="left")
    ax[1].set_title("(b) active power of the ten units, 230 kV side", fontsize=9, loc="left")

    d = data["k1p5"]
    z = (d.TIME >= 2.999) & (d.TIME <= 3.006)
    tms = (d.TIME[z] - FAULT_T) * 1e3
    for ph, c in zip("ABC", ("#1f77b4", "#2ca02c", "#9467bd")):
        ax[2].plot(tms, np.abs(d["IB32" + ph][z]) / PEAK_KA_PER_PU_32, color=c, lw=1.0, label="phase " + ph.lower())
    for thr, lab, col in ((1.5, "1.5 pu threshold", RED), (1.2, "1.2 pu threshold", DARK)):
        ax[2].axhline(thr, color=col, lw=0.9, ls=":")
        ax[2].text(5.9, thr + 0.04, lab, ha="right", va="bottom", fontsize=7.5, color=col)
    trip = d.TIME[z][d.BRK32[z] > 0.5]
    if len(trip):
        tt = (trip.iloc[0] - FAULT_T) * 1e3
        ax[2].axvline(tt, color="k", lw=0.9)
        ax[2].text(tt + 0.08, 2.1, "trip at %.1f ms" % tt, fontsize=7.5, va="top")
    ax[2].set_xlim(-1.0, 6.0)
    ax[2].set_ylim(0, 2.2)
    ax[2].set_xlabel("time after fault inception (ms)")
    ax[2].set_ylabel("unit-32 current\n(pu of rated peak)")
    ax[2].grid(True, alpha=0.3)
    ax[2].legend(loc="upper left", fontsize=7.5, ncol=1, framealpha=0.95)
    ax[2].set_title("(c) unit-32 phase currents in the 10 kV branch, 1.5 pu record", fontsize=9, loc="left")

    fig.subplots_adjust(left=0.13, right=0.98, top=0.95, bottom=0.10)
    fig.savefig(OUT / "narr_trip_bus14.png", dpi=600)
    print("wrote", OUT / "narr_trip_bus14.png")
    for k, lab, _, _ in RECORDS:
        dd = data[k]; post = dd.TIME > 6.0
        print("  %-38s V16 post %.3f pu, fleet P post %.2f GW" % (lab, (dd.V16_kV[post] / 230.0).mean(), dd.P_fleet_MW[post].mean() / 1e3))


if __name__ == "__main__":
    main()
