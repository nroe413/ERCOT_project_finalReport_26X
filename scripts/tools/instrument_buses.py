#!/usr/bin/env python3
"""instrument_buses.py — Replicate the bus-30 instrumentation cluster on
buses 14, 15, 16, 17, 18, 21 in ieee39_sz/IEEE39_acLine1.pscx.

Each new bus N gets:
  - One master:multimeter (CurI=B<N>IL, VolI=B<N>VLN, P=B<N>P, Q=B<N>Q,
    Vrms=B<N>Vrms, Crms=B<N>Irms) — same params as bus 30, renamed.
  - Six master:datalabel + master:pgb + connecting wire trios.

Layout (visible right next to the bus-30 cluster):
  - New multimeters: one row at y=1098 immediately right of bus 30's
    multimeter (which is at x=486). Each new bus offset by 114 in x.
  - New PGB columns: same x=144 (PGB) / x=108 (datalabel) as bus 30,
    stacked vertically below bus 30's PGB stack starting at y=1548.

Existing GraphFrames are NOT modified — bus 30's curves remain
1-curve-per-graph as the user expects. Add per-bus graphs via PSCAD's
GUI if you want live plotting for the new buses.

The original .pscx is backed up to .PRE_INSTRUMENT_BACKUP. New IDs
allocated above max id (2.14B); new gaddresses above 100.66M.

Run from the worktree root:
    python tools/instrument_buses.py
"""
from __future__ import print_function
import re
import shutil
import sys
from pathlib import Path

WORKTREE_ROOT = Path(__file__).resolve().parent.parent
PSCX = WORKTREE_ROOT / "ieee39_sz" / "IEEE39_acLine1.pscx"
BACKUP = WORKTREE_ROOT / "ieee39_sz" / "IEEE39_acLine1.pscx.PRE_INSTRUMENT_BACKUP"

NEW_BUSES = [14, 15, 16, 17, 18, 21]
SIGNALS = ["VLN", "IL", "P", "Q", "Vrms", "Irms"]   # bus-30 order

# Multimeters: horizontal row at the same y as bus 30's multimeter
# (which sits at x=486, y=1098). Stack new ones to the right.
MM_Y = 1098
MM_X_START = 600                    # first new multimeter (bus 14)
MM_X_PITCH = 114                    # horizontal spacing between buses

# PGB/datalabel column: same x as bus 30 (PGB at x=144, datalabel at
# x=108). Stack new clusters vertically starting just below bus 30's
# bottom PGB (which is at y=1512), with 36-unit row pitch and a small
# gap between clusters.
PGB_X = 144
DL_X = 108
WIRE_X = 108
PGB_X_FOR_WIRE = 144                # wire endpoint x at PGB edge
PGB_COLUMN_TOP_Y = 1548             # first new PGB row (bus 14, VLN)
ROW_PITCH_Y = 36                    # spacing between rows within a cluster
CLUSTER_GAP_Y = 36                  # extra gap between cluster blocks
ROWS_PER_CLUSTER = len(SIGNALS)     # 6
CLUSTER_PITCH_Y = ROWS_PER_CLUSTER * ROW_PITCH_Y + CLUSTER_GAP_Y   # 216

ID_BASE = 2_145_000_000             # safely above max existing id (2.144B)
GADDRESS_BASE = 100_700_000         # safely above max gaddress (100.664M)
Z_BASE = 2000                       # z-order for new components


def build_multimeter(mm_id, mm_x, mm_y, mm_z, bus):
    return (
        '        <User classid="UserCmp" defn="master:multimeter" '
        'id="{mm_id}" x="{mm_x}" y="{mm_y}" w="44" h="54" z="{mm_z}" orient="4" '
        'link="-1" q="4" disable="false">\n'
        '          <paramlist link="-1" name="" crc="27440011">\n'
        '            <param name="MeasI" value="1" />\n'
        '            <param name="MeasV" value="1" />\n'
        '            <param name="MeasP" value="1" />\n'
        '            <param name="MeasQ" value="1" />\n'
        '            <param name="RMS" value="1" />\n'
        '            <param name="MeasPh" value="1" />\n'
        '            <param name="S" value="1.0 [MVA]" />\n'
        '            <param name="BaseV" value="1.0 [kV]" />\n'
        '            <param name="TS" value="0.02 [s]" />\n'
        '            <param name="Freq" value="60.0 [Hz]" />\n'
        '            <param name="Dis" value="0" />\n'
        '            <param name="CurI" value="B{bus}IL" />\n'
        '            <param name="VolI" value="B{bus}VLN" />\n'
        '            <param name="P" value="B{bus}P" />\n'
        '            <param name="Q" value="B{bus}Q" />\n'
        '            <param name="Vrms" value="B{bus}Vrms" />\n'
        '            <param name="Ph" value="" />\n'
        '            <param name="hide1" value="0" />\n'
        '            <param name="hide2" value="0" />\n'
        '            <param name="Pd" value="0.0" />\n'
        '            <param name="Qd" value="0.0" />\n'
        '            <param name="Vd" value="0.0" />\n'
        '            <param name="IRMS" value="1" />\n'
        '            <param name="BaseA" value="1.0" />\n'
        '            <param name="Crms" value="B{bus}Irms" />\n'
        '            <param name="Name" value="" />\n'
        '            <param name="VolILL" value="" />\n'
        '          </paramlist>\n'
        '        </User>'
    ).format(mm_id=mm_id, mm_x=mm_x, mm_y=mm_y, mm_z=mm_z, bus=bus)


def build_datalabel(dl_id, dl_y, signal_name):
    return (
        '        <User classid="UserCmp" id="{dl_id}" name="master:datalabel" '
        'x="{dl_x}" y="{dl_y}" w="48" h="23" z="1" orient="0" '
        'defn="master:datalabel" link="-1" q="4" disable="false">\n'
        '          <paramlist name="" link="-1" crc="127230955">\n'
        '            <param name="Name" value="{signal_name}" />\n'
        '          </paramlist>\n'
        '        </User>'
    ).format(dl_id=dl_id, dl_x=DL_X, dl_y=dl_y, signal_name=signal_name)


def build_pgb(pgb_id, pgb_y, pgb_z, gaddress, signal_name):
    return (
        '        <User classid="UserCmp" id="{pgb_id}" name="master:pgb" '
        'x="{pgb_x}" y="{pgb_y}" w="60" h="40" z="{pgb_z}" orient="0" '
        'defn="master:pgb" link="-1" q="4" disable="false">\n'
        '          <paramlist name="" link="-1" crc="65740200">\n'
        '            <param name="Name" value="{signal_name}" />\n'
        '            <param name="Group" value="" />\n'
        '            <param name="UseSignalName" value="1" />\n'
        '            <param name="enab" value="1" />\n'
        '            <param name="Display" value="1" />\n'
        '            <param name="Scale" value="1.0" />\n'
        '            <param name="Units" value="" />\n'
        '            <param name="mrun" value="0" />\n'
        '            <param name="Pol" value="0" />\n'
        '            <param name="Max" value="2.0" />\n'
        '            <param name="Min" value="-2.0" />\n'
        '          </paramlist>\n'
        '          <paramlist name="global_address">\n'
        '            <param name="gaddress" value="{gaddress}" />\n'
        '          </paramlist>\n'
        '        </User>'
    ).format(pgb_id=pgb_id, pgb_x=PGB_X, pgb_y=pgb_y, pgb_z=pgb_z,
             gaddress=gaddress, signal_name=signal_name)


def build_wire(wire_id, wire_y):
    return (
        '        <Wire classid="WireOrthogonal" id="{wire_id}" name="" '
        'x="{wire_x}" y="{wire_y}" w="46" h="10" orient="0" disable="false">\n'
        '          <vertex x="0" y="0" />\n'
        '          <vertex x="36" y="0" />\n'
        '        </Wire>'
    ).format(wire_id=wire_id, wire_x=WIRE_X, wire_y=wire_y)


def main():
    if not PSCX.exists():
        sys.exit("PSCX not found: {}".format(PSCX))

    raw = PSCX.read_bytes()
    text = raw.decode("utf-8")
    if "\r\n" not in text[:2000]:
        sys.exit("expected CRLF line endings in pscx but didn't find any")

    existing_ids = set(int(m) for m in re.findall(r'\bid="(\d+)"', text))
    existing_gas = set(int(m) for m in re.findall(r'gaddress" value="(\d+)"', text))
    if max(existing_ids) >= ID_BASE:
        sys.exit("max id {} collides with ID_BASE; raise base".format(max(existing_ids)))
    if max(existing_gas) >= GADDRESS_BASE:
        sys.exit("max gaddress collides with GADDRESS_BASE; raise base")

    shutil.copy2(str(PSCX), str(BACKUP))
    print("backed up {} -> {}".format(PSCX.name, BACKUP.name))

    state = {"id": ID_BASE, "ga": GADDRESS_BASE}

    def new_id():
        state["id"] += 1
        return state["id"]

    def new_ga():
        state["ga"] += 1
        return state["ga"]

    # Build cluster blocks for each new bus.
    clusters = []
    summary_lines = []
    for i, bus in enumerate(NEW_BUSES):
        mm_x = MM_X_START + i * MM_X_PITCH
        base_z = Z_BASE + i * 100

        blocks = [build_multimeter(new_id(), mm_x, MM_Y, base_z, bus)]

        cluster_top_y = PGB_COLUMN_TOP_Y + i * CLUSTER_PITCH_Y
        for j, sig in enumerate(SIGNALS):
            row_y = cluster_top_y + j * ROW_PITCH_Y
            blocks.append(build_datalabel(new_id(), row_y,
                                          "B{}{}".format(bus, sig)))
            blocks.append(build_pgb(new_id(), row_y, base_z + 10 + j,
                                    new_ga(), "B{}{}".format(bus, sig)))
            blocks.append(build_wire(new_id(), row_y))

        clusters.append("\n".join(blocks))
        summary_lines.append(
            "  bus {bus:2d}: multimeter at ({mm_x}, {mm_y}); "
            "PGBs at x={pgb_x}, y={y_top}..{y_bot}".format(
                bus=bus, mm_x=mm_x, mm_y=MM_Y, pgb_x=PGB_X,
                y_top=cluster_top_y,
                y_bot=cluster_top_y + (len(SIGNALS) - 1) * ROW_PITCH_Y))

    cluster_text = "\n".join(clusters)

    # Insert immediately after bus 30's multimeter </User> close. That
    # multimeter (id=603240613) lives inside <Definition name="P1"> ->
    # <schematic>...</schematic></Definition>, which is the network
    # sub-module the user actually navigates into. Using the first
    # <Frame classid="GraphFrame"> in the file as the anchor (the
    # previous approach) put the new components in some other
    # Definition entirely, where they were invisible from P1.
    BUS30_MM_ID = "603240613"
    mm_open = text.find('id="{}"'.format(BUS30_MM_ID))
    if mm_open < 0:
        sys.exit("couldn't find bus-30 multimeter id={} as insertion anchor"
                 .format(BUS30_MM_ID))
    close_tag = "</User>"
    mm_close = text.find(close_tag, mm_open) + len(close_tag)
    # Step past the line ending so we insert at the start of the next line.
    if text[mm_close:mm_close + 2] == "\r\n":
        insert_at = mm_close + 2
    else:
        insert_at = mm_close + 1
    text = text[:insert_at] + cluster_text + "\n" + text[insert_at:]

    # Normalize line endings back to CRLF.
    text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    PSCX.write_bytes(text.encode("utf-8"))

    fresh = PSCX.read_bytes().decode("utf-8")
    added_signals = sum(
        fresh.count('value="B{}{}"'.format(bus, sig))
        for bus in NEW_BUSES for sig in SIGNALS
    )
    expected = len(NEW_BUSES) * len(SIGNALS) * 3  # mm + datalabel + pgb
    print("wrote {} bytes; B<N>* signal references: {} (expected {})".format(
        len(text.encode("utf-8")), added_signals, expected))

    new_pgbs = sum(1 for ga in re.findall(r'gaddress" value="(\d+)"', fresh)
                   if int(ga) >= GADDRESS_BASE)
    print("new PGBs (by gaddress): {} (expected {})".format(
        new_pgbs, len(NEW_BUSES) * len(SIGNALS)))

    print("\nnew component locations:")
    for line in summary_lines:
        print(line)
    print("\n(GraphFrames left untouched — bus 30's curves remain 1-per-graph)")


if __name__ == "__main__":
    main()
