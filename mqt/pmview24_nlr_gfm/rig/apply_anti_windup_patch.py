#!/usr/bin/env python3
"""
apply_anti_windup_patch.py - Apply anti-windup improvements to PSCAD-generated Fortran.

Run this AFTER PSCAD generates the Fortran code but BEFORE compiling/running.
It patches Voltage_Loop.f and Current_Loop_1.f in the gf46 build directory.

Usage:
    python apply_anti_windup_patch.py
"""

import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GF46_DIR = os.path.join(SCRIPT_DIR, "PMView_testing_NREL_GFM.gf46")


def patch_file(filepath, patches):
    """Apply text replacements to a file. Each patch is (old, new, description)."""
    with open(filepath, "r") as f:
        content = f.read()

    original = content
    for old_text, new_text, desc in patches:
        if old_text not in content:
            print(f"  WARNING: patch target not found for: {desc}")
            print(f"           File may already be patched or PSCAD changed the code.")
            continue
        content = content.replace(old_text, new_text, 1)
        print(f"  Applied: {desc}")

    if content == original:
        print(f"  No changes made to {os.path.basename(filepath)}")
        return False

    with open(filepath, "w") as f:
        f.write(content)
    print(f"  Wrote {os.path.basename(filepath)}")
    return True


def patch_voltage_loop():
    """Replace integrator-freeze anti-windup with back-calculation decay."""
    filepath = os.path.join(GF46_DIR, "Voltage_Loop.f")
    if not os.path.exists(filepath):
        print(f"ERROR: {filepath} not found")
        return False

    print(f"\nPatching Voltage_Loop.f:")

    patches = [
        # Q-axis integrator: freeze -> exponential decay
        (
            "! 230:[select] Two Input Selector \n"
            "      IF (Limiting .EQ. RTCI(NRTCI)) THEN\n"
            "         RT_12 = RT_25\n"
            "      ELSE\n"
            "         RT_12 = RT_22\n"
            "      ENDIF\n"
            "      NRTCI = NRTCI + 1\n"
            "!",

            "! 230:[select] Two Input Selector -- PATCHED: back-calc anti-windup\n"
            "!     Decay q-axis integrator state toward zero (tau=100ms)\n"
            "      IF (Limiting .EQ. RTCI(NRTCI)) THEN\n"
            "         RT_12 = -10.0 * RT_13\n"
            "      ELSE\n"
            "         RT_12 = RT_22\n"
            "      ENDIF\n"
            "      NRTCI = NRTCI + 1\n"
            "!",

            "Q-axis integrator: freeze -> back-calc decay (Kb=10, tau=100ms)"
        ),

        # D-axis integrator: freeze -> exponential decay
        (
            "! 290:[select] Two Input Selector \n"
            "      IF (Limiting .EQ. RTCI(NRTCI)) THEN\n"
            "         RT_14 = RT_24\n"
            "      ELSE\n"
            "         RT_14 = RT_7\n"
            "      ENDIF\n"
            "      NRTCI = NRTCI + 1\n"
            "!",

            "! 290:[select] Two Input Selector -- PATCHED: back-calc anti-windup\n"
            "!     Decay d-axis integrator state toward zero (tau=100ms)\n"
            "      IF (Limiting .EQ. RTCI(NRTCI)) THEN\n"
            "         RT_14 = -10.0 * RT_9\n"
            "      ELSE\n"
            "         RT_14 = RT_7\n"
            "      ENDIF\n"
            "      NRTCI = NRTCI + 1\n"
            "!",

            "D-axis integrator: freeze -> back-calc decay (Kb=10, tau=100ms)"
        ),
    ]

    return patch_file(filepath, patches)


def patch_current_loop():
    """Tighten current loop integrator limits from +/-100M to +/-50."""
    filepath = os.path.join(GF46_DIR, "Current_Loop_1.f")
    if not os.path.exists(filepath):
        print(f"ERROR: {filepath} not found")
        return False

    print(f"\nPatching Current_Loop_1.f:")

    patches = [
        # Q-axis integrator limits
        (
            "      RT_9 = EMTDC_XINT(0, 0, 0, RVD1_1, 1.0, 0.0, -100000000.0, 1000000&\n"
            "     &00.0, RVD2_2, RVD2_1)",

            "! PATCHED: tightened integrator limits from +/-100M to +/-50\n"
            "      RT_9 = EMTDC_XINT(0, 0, 0, RVD1_1, 1.0, 0.0, -50.0, 50.0, RVD2_2,&\n"
            "     & RVD2_1)",

            "Q-axis integrator: limits +/-100M -> +/-50"
        ),

        # D-axis integrator limits
        (
            "      RT_18 = EMTDC_XINT(0, 0, 0, RVD1_1, 1.0, 0.0, -100000000.0, 100000&\n"
            "     &000.0, RVD2_2, RVD2_1)",

            "! PATCHED: tightened integrator limits from +/-100M to +/-50\n"
            "      RT_18 = EMTDC_XINT(0, 0, 0, RVD1_1, 1.0, 0.0, -50.0, 50.0, RVD2_2&\n"
            "     &, RVD2_1)",

            "D-axis integrator: limits +/-100M -> +/-50"
        ),
    ]

    return patch_file(filepath, patches)


def main():
    print("Anti-windup patch for NREL GFM Inverter")
    print("=" * 50)

    v_ok = patch_voltage_loop()
    c_ok = patch_current_loop()

    if v_ok or c_ok:
        print(f"\nPatches applied. Now compile and run from PSCAD.")
        print(f"Or compile manually:")
        print(f"  cd {GF46_DIR}")
        print(f"  PMView_testing_NREL_GFM_mak.bat")
    else:
        print(f"\nNo patches were applied (files may already be patched).")

    return 0 if (v_ok or c_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
