# NREL Kenyon GFM Inverter Model — Model Quality Test (MQT) Evaluation

**Project:** ERCOT x UT Austin SOW Task 2 — PMView 2.4 Testing
**Model Under Test:** National Lab of Rockies (NREL) Kenyon Grid-Forming Inverter (GFM_Inverter_Dev4)
**Test Harness:** PMView_testing_NREL_GFM.pscx (PSCAD 5.0.1)
**Reference Standard:** DWG Procedure Manual Revision 24 (ROS Approved June 5, 2025)
**Date:** March 11, 2026
**Branch:** gfm_validation_task_2

---

## Executive Summary

Nine of thirteen planned Model Quality Tests were executed on the NREL Kenyon GFM inverter model per the ERCOT DWG Procedure Manual Rev. 24, Sections 3.1.5.2 through 3.1.5.9. Tests 10-13 have not yet been run.

| Test | Name | Result | Section |
|------|------|--------|---------|
| 1 | Flat Start | **PASS** | 3.1.5.2 |
| 2 | LVRT (ERCOT Legacy) | **CONDITIONAL PASS** | 3.1.5.4 |
| 3 | HVRT (ERCOT Legacy) | **FAIL** | 3.1.5.5 |
| 4 | Small Voltage Disturbance (Step Down) | **PASS** | 3.1.5.3 |
| 5 | Small Voltage Disturbance (Step Up) | **PASS** | 3.1.5.3 |
| 6 | LVRT Voltage Dips (IEEE 2800) | **PASS** | 3.1.5.4 |
| 7 | HVRT Preferred (IEEE 2800) | **FAIL** | 3.1.5.5 |
| 8 | Phase Angle Jump (Down) | **FAIL** | 3.1.5.9 |
| 9 | Phase Angle Jump (Up) | **FAIL** | 3.1.5.9 |
| 10 | Custom Faults | NOT RUN | — |
| 11 | Frequency Down | NOT RUN | 3.1.5.7 |
| 12 | Frequency Up | NOT RUN | 3.1.5.7 |
| 13 | V Up/Down Impedance | NOT RUN | 3.1.5.8 |

**Overall: 4 PASS, 1 CONDITIONAL PASS, 4 FAIL, 4 NOT RUN**

The model performs well under small-signal disturbances and flat start conditions but exhibits severe sustained power oscillations under large voltage disturbances (HVRT) and phase angle jumps. The common failure mode is an undamped low-frequency oscillation in active and reactive power that does not damp after the disturbance.

---

## Simulation Setup

Per DWG Procedure Manual Section 3.1.5.1:

- The GFM inverter facility model is connected to a controllable infinite bus.
- The generator is dispatched at full real power output (~0.43 pu at POI).
- POI bus voltage initialized to nominal 1.0 pu.
- Initial reactive power exchange near zero (Qpoi ~ -0.04 pu).
- Simulation time step: 5 microseconds.
- Output sample rate: 5,000 Hz.
- Simulation duration: 40 seconds per run (exceeds the 20-second minimum).
- Breaker B and C are closed; Breaker A remains open throughout all tests.

All tests share identical initialization: the inverter energizes at t ~ 2.5 s and reaches steady state by t ~ 5 s.

---

## Detailed Test Results

### Test 1: Flat Start (Section 3.1.5.2) — PASS

**Criteria:** No-disturbance test for minimum 20 seconds. Flat responses of voltage, MW, MVAR, and frequency expected to remain very close to initial system conditions.

**Results:**

| Signal | Steady-State Value | Std Dev (last 5s) |
|--------|-------------------|-------------------|
| Ppoi | 0.4289 pu | 0.0000 |
| Qpoi | -0.0387 pu | 0.0000 |
| Fpoi | 60.0000 Hz | 0.0000 |
| Vsource | 16.67 kV (1.0 pu) | stable |

**Assessment:** The model initializes cleanly with a well-damped startup transient (oscillations settle within ~2 seconds of energization). After reaching steady state at approximately t = 5 s, all quantities remain perfectly flat for the remaining 35 seconds. Voltage, active power, reactive power, and frequency show zero variation. **Meets all Section 3.1.5.2 criteria.**

---

### Test 2: LVRT — ERCOT Legacy (Section 3.1.5.4) — CONDITIONAL PASS

**Criteria:** The model shall inject reactive current during voltage recovery. Real power should recover to full output within 1.0 s of POI voltage recovering to 0.9 pu. The model shall not exhibit momentary cessation.

**Voltage Profile Applied:**

| Time (s) | Vsource (pu) | Description |
|-----------|-------------|-------------|
| 0–10 | 1.00 | Nominal |
| 10 | 0.00 | Zero-voltage transient |
| 10–11 | 0.00 → 0.90 | Voltage ramp-up |
| 12–20 | 0.90 | Sustained low voltage |
| 20–28 | 0.95 | Sustained slightly low voltage |
| 28+ | 0.10 | Deep sustained low voltage |

**Results during standard LVRT profile (t = 10–28 s):**

- **Zero-voltage transient (t ~ 10 s):** The model rides through the zero-voltage event. During the ramp-up from zero, reactive current injection is observable (Qpoi increases from -0.04 to +0.26 pu). No momentary cessation occurs.
- **0.90 pu sustained (t = 12–20 s):** Ppoi recovers to 0.4305 pu (full output) within ~1 second. Qpoi stabilizes at +0.2362 pu (lagging — appropriate reactive support for depressed voltage). Fpoi remains at 60.000 Hz. Response is well-damped and stable.
- **0.95 pu sustained (t = 20–28 s):** Ppoi stable at 0.4299 pu, Qpoi = +0.1056 pu (reduced reactive support as voltage is closer to nominal). Stable operation.

**Results during deep low-voltage segment (t > 28 s):**

- Vsource drops to ~0.10 pu (1.67 kV). The model enters **sustained, undamped oscillations** in both P and Q.
- Ppoi oscillates between approximately -0.11 and +0.11 pu.
- Qpoi oscillates between approximately -0.11 and +0.11 pu.
- Oscillations persist for the remainder of the simulation with no sign of damping.

**Assessment:** The model meets all standard ERCOT Legacy LVRT criteria for the primary ride-through events (zero-voltage transient, 0.9 pu sustained, and 0.95 pu sustained). Reactive current injection is appropriate and real power recovery is within the 1.0-second requirement. However, during the final extended very-low-voltage condition (0.10 pu), the model exhibits sustained undamped P/Q oscillations, indicating the current limiter and power controls become unstable at very low terminal voltages. This final segment may exceed the legacy LVRT ride-through envelope, but the oscillatory behavior is a concern for robustness.

**Recommendation:** Investigate current limiter behavior and anti-windup logic at very low sustained voltages (< 0.2 pu). The GFM droop control may be fighting the current limiter, causing a limit cycle.

---

### Test 3: HVRT — ERCOT Legacy (Section 3.1.5.5) — FAIL

**Criteria:** During high voltage, the model should provide fast dynamic response to absorb reactive power. For 1.1 pu sustained voltage, the AVR should move toward nearly full reactive absorbing (leading). Real power should be sustained.

**Voltage Profile Applied:**

| Time (s) | Vsource (pu) | Description |
|-----------|-------------|-------------|
| 0–10 | 1.00 | Nominal |
| 10 | 1.15 | Initial high-voltage step |
| 11–20 | 1.10 | Sustained high voltage |
| 20–28 | 1.05 | Sustained slightly high voltage |
| 28+ | 2.00 | Extreme high voltage |

**Results:**

- Immediately upon the voltage step at t = 10 s, the model enters **severe, sustained oscillations** in both active and reactive power.
- During the 1.10 pu sustained period (t = 11–20 s):
  - Ppoi oscillates between approximately -1.25 and +0.10 pu (mean ~ -0.8 pu, deeply negative).
  - Qpoi oscillates between approximately -0.88 and +1.10 pu.
  - Oscillation period is approximately 1.0–1.5 seconds.
  - **No damping is observed** — the oscillations persist indefinitely.
- During the 1.05 pu period (t = 20–28 s): same oscillatory behavior continues unabated.
- During the extreme 2.0 pu period (t > 28 s): oscillations intensify further, Ppoi reaches -2.35 pu.
- **Frequency oscillates** around 60 Hz with ~ +/-0.004 Hz variations.
- The model never recovers to stable positive power output after the high-voltage event.

**Root Cause Analysis:** The GFM inverter's voltage-source behavior creates a fundamental conflict during HVRT: the inverter tries to maintain its internal voltage reference while the grid voltage is forced higher. This results in reverse power flow (current flows into the inverter). The droop controller and voltage loop appear unable to stabilize under this condition. The lack of damping suggests insufficient gain margin in the outer power/voltage control loops when operating at elevated terminal voltage, or that the current limiter is being engaged in a manner that creates a limit cycle with the droop control.

**Assessment:** **FAIL.** The model does not sustain real power output during high voltage conditions. The severe undamped oscillations in P and Q are clearly unacceptable per Section 3.1.5.5 criteria. The model does not exhibit the expected fast reactive absorption response.

---

### Test 4: Small Voltage Disturbance — Step Down (Section 3.1.5.3) — PASS

**Criteria:** Apply a 3% step decrease of voltage at the POI. The AVR should transition toward lagging power factor. Oscillations should be well-damped. Real power output should be sustained.

**Voltage Profile Applied:**

| Time (s) | Vsource (pu) | Description |
|-----------|-------------|-------------|
| 0–10 | 1.00 | Nominal |
| 10–30 | 0.97 | First 3% step down |
| 30+ | 0.95 | Second 3% step down |

**Results:**

- **First step (t = 10 s):** Vsource steps from 16.67 kV to 16.18 kV (~3% decrease).
  - Ppoi shows a brief transient then settles at 0.4295 pu (essentially unchanged from pre-disturbance).
  - Qpoi shifts from -0.0387 to +0.0495 pu — the AVR correctly increases reactive output (lagging) to support the depressed voltage.
  - Settling time: < 1 second. Well-damped, no overshoot.
  - Fpoi: 60.0000 Hz throughout, zero deviation.
- **Second step (t = 30 s):** Vsource steps to 15.84 kV (~5% below nominal).
  - Ppoi stable at 0.4298 pu. Qpoi increases further to +0.1057 pu.
  - Same well-damped settling behavior.

**Assessment:** **PASS.** Real power is fully sustained. The AVR provides appropriate reactive support, transitioning toward lagging power factor. All transients are well-damped with fast settling. **Meets all Section 3.1.5.3 criteria.**

---

### Test 5: Small Voltage Disturbance — Step Up (Section 3.1.5.3) — PASS

**Criteria:** Apply a 3% step increase of voltage at the POI. The AVR should transition toward leading power factor. Oscillations should be well-damped. Real power output should be sustained.

**Voltage Profile Applied:**

| Time (s) | Vsource (pu) | Description |
|-----------|-------------|-------------|
| 0–10 | 1.00 | Nominal |
| 10–30 | 1.03 | First 3% step up |
| 30+ | 1.05 | Second 3% step up |

**Results:**

- **First step (t = 10 s):** Vsource steps from 16.67 kV to 17.18 kV (~3% increase).
  - Ppoi settles at 0.4282 pu (essentially unchanged).
  - Qpoi shifts from -0.0387 to -0.1318 pu — the AVR correctly absorbs reactive power (leading) to counter the elevated voltage.
  - Settling time: < 1 second. Well-damped, no overshoot.
  - Fpoi: 60.0000 Hz throughout, zero deviation.
- **Second step (t = 30 s):** Vsource steps to 17.51 kV (~5% above nominal).
  - Ppoi stable at 0.4277 pu. Qpoi shifts further to -0.1966 pu (more leading).
  - Same well-damped settling.

**Assessment:** **PASS.** Real power is fully sustained. The AVR absorbs reactive power (leading) appropriately in response to the voltage increase. All transients are well-damped. **Meets all Section 3.1.5.3 criteria.**

**Note on Tests 4 & 5:** The contrast between the excellent small-signal HVRT/LVRT behavior (3–5% voltage changes) and the catastrophic large-signal HVRT behavior (Tests 3 and 7) suggests the instability is a large-signal phenomenon, likely related to current limiter engagement or control saturation that does not occur at small voltage deviations.

---

### Test 6: LVRT Voltage Dips — IEEE 2800 (Section 3.1.5.4) — PASS

**Criteria:** The model shall ride through a series of separate piecewise voltage dips with voltage returning to 1.0 pu between each dip. Active current shall be injected for dips of 0.5 pu and higher. Reactive current injection shall be observable immediately after a non-zero voltage dip. Real power should recover within 1.0 s of voltage recovery.

**Voltage Profile Applied (series of dips):**

| Time (s) | Vsource (pu) | Description |
|-----------|-------------|-------------|
| 0–10 | 1.00 | Nominal |
| ~10–11 | 0.70 | Dip 1: 70% retained |
| ~11–12 | 1.00 | Recovery |
| ~12–13 | 0.00 | Dip 2: Zero voltage (4 cycles) |
| ~13–14 | 1.00 | Recovery |
| ~14–15 | 0.25 | Dip 3: 25% retained |
| ~15–16 | 1.00 | Recovery |
| ~17–19 | 0.50 | Dip 4: 50% retained |
| ~20 | 1.00 | Recovery |
| ~21–23 | 0.70 | Dip 5: 70% retained |
| ~24+ | 1.00 | Final recovery |

**Results:**

- **Dip 1 (0.70 pu):** Model maintains active power output. Qpoi increases to +0.62 pu (strong reactive injection). Recovers cleanly.
- **Dip 2 (0.00 pu, zero voltage):** Model rides through. Brief frequency excursion to 54.1 Hz during the transient (attributable to PLL/droop dynamics during zero-voltage condition). Recovers to full power within ~1 second.
- **Dip 3 (0.25 pu):** Model rides through with reactive injection. Power recovery clean.
- **Dip 4 (0.50 pu):** Active current maintained (~0.43 pu Ppoi). Reactive injection present (Qpoi ~ +0.36 pu). Stable.
- **Dip 5 (0.70 pu):** Same successful ride-through with reactive support (Qpoi ~ +0.62 pu).
- **Final recovery (t > 24 s):** Ppoi = 0.4292 pu, Qpoi = -0.0388 pu, Fpoi = 60.0000 Hz. Completely recovered and stable through the end of simulation.

**Observations:**
- The transient frequency excursion to 54.1 Hz during the zero-voltage dip is large but extremely brief (< 0.1 s). This is a characteristic of the GFM droop control responding to a sudden loss and recovery of terminal voltage. The frequency quickly returns to 60 Hz.
- Active current injection is maintained for all dips >= 0.25 pu as required.
- Reactive current injection is observable immediately upon each dip application.

**Assessment:** **PASS.** The model rides through all five voltage dips successfully, recovers to full output after each event, and returns to nominal steady state. Reactive and active current injection criteria are met. **Meets Section 3.1.5.4 voltage dip criteria.** The brief frequency excursion during zero-voltage should be noted but does not constitute a failure.

---

### Test 7: HVRT — Preferred IEEE 2800 (Section 3.1.5.5) — FAIL

**Criteria:** Same as Test 3 (HVRT). The "preferred" HVRT curve has more stringent requirements than the "legacy" curve.

**Voltage Profile Applied:**

| Time (s) | Vsource (pu) | Description |
|-----------|-------------|-------------|
| 0–10 | 1.00 | Nominal |
| 10 | 1.20 | Initial high-voltage step |
| 11–20 | 1.10 | Sustained high voltage |
| 20–28 | 1.05 | Sustained slightly high voltage |
| 28+ | 1.60 | Extreme high voltage |

**Results:**

- Identical failure mode to Test 3. Upon the voltage step to 1.20 pu at t = 10 s, the model immediately enters severe, sustained oscillations.
- During 1.10 pu sustained (t = 11–20 s):
  - Ppoi oscillates between -1.25 and +0.03 pu (mean ~ -0.9 pu).
  - Qpoi oscillates between -0.82 and +1.12 pu.
  - No damping observed.
- During the 1.60 pu period (t > 28 s): Ppoi reaches -1.84 pu with continued oscillations.
- The model never recovers to stable positive power output.

**Assessment:** **FAIL.** Same failure mechanism as Test 3. The model cannot handle sustained high-voltage conditions. The oscillatory behavior is unacceptable per Section 3.1.5.5. Since the model also fails the legacy HVRT (Test 3), both profiles must be reported as failures.

---

### Test 8: Phase Angle Jump — Down (Section 3.1.5.9) — FAIL

**Criteria:** The model should withstand a sudden voltage phase angle decrease and recover to normal stable operation.

**Disturbance Profile:** Four progressively larger negative phase angle jumps applied at approximately t = 10, 15, 20, and 25 seconds.

**Results:**

- Upon the first phase angle jump at t = 10 s, the model enters **sustained undamped oscillations** in both P and Q.
  - Ppoi oscillates between approximately -1.14 and +0.32 pu.
  - Qpoi oscillates between approximately -0.88 and +1.10 pu.
- Frequency exhibits sharp transient excursions down to 49.2 Hz at each angle jump, recovering between jumps to ~60 Hz.
- The oscillations **never damp**. They persist continuously from t = 10 s through the end of the simulation (t = 40 s).
- Subsequent angle jumps at t = 15, 20, 25 s produce additional frequency spikes (progressively deeper: 54.1 Hz, 52.3 Hz, 49.2 Hz) but the oscillation amplitude does not increase significantly — the model is already in a sustained limit cycle.

**Root Cause Analysis:** The phase angle jump creates an instantaneous mismatch between the GFM inverter's internal voltage angle reference and the grid voltage angle. The droop-based power control attempts to correct this by adjusting its frequency/angle, but the dynamics of the correction appear to overshoot and create a sustained oscillation. The inverter alternates between injecting and absorbing significant power as its internal angle swings back and forth relative to the grid. This is a classic stability issue for droop-controlled GFM inverters under sudden angle disturbances and points to insufficient damping in the power-angle droop loop.

**Assessment:** **FAIL.** The model cannot ride through even the smallest phase angle jump and recover to stable operation. This is a fundamental stability limitation of the current control tuning. **Does not meet Section 3.1.5.9 criteria.**

---

### Test 9: Phase Angle Jump — Up (Section 3.1.5.9) — FAIL

**Criteria:** The model should withstand a sudden voltage phase angle increase and recover to normal stable operation.

**Disturbance Profile:** Four progressively larger positive phase angle jumps at approximately t = 10, 15, 20, and 25 seconds.

**Results:**

- Same failure mode as Test 8 (mirror image). Upon the first phase angle jump at t = 10 s, the model enters sustained undamped P/Q oscillations.
  - Ppoi oscillates between approximately -1.14 and +0.32 pu.
  - Qpoi oscillates between approximately -0.88 and +1.11 pu.
- Frequency spikes upward to 64.9 Hz, 67.5 Hz, 70.5 Hz, and 77.1 Hz at each successive angle jump.
- The progressively larger frequency excursions indicate the angle jumps are increasing in magnitude, but the model is already in an oscillatory state from the first jump.
- Oscillations persist for the entire remaining simulation duration with no sign of damping.

**Assessment:** **FAIL.** Same fundamental instability as Test 8. The model cannot recover from phase angle jumps in either direction. **Does not meet Section 3.1.5.9 criteria.**

---

## Common Failure Mode Analysis

Tests 3, 7, 8, and 9 share a common failure pattern: **sustained, undamped low-frequency power oscillations** once the disturbance pushes the inverter beyond its small-signal stability boundary. The oscillation characteristics are:

- **Period:** ~1.0–1.5 seconds (frequency ~0.7–1.0 Hz)
- **Active power amplitude:** swings of 1.0–2.5 pu peak-to-peak
- **Reactive power amplitude:** swings of 1.5–2.0 pu peak-to-peak
- **Damping:** zero — oscillations persist indefinitely

This is consistent with a **limit cycle** in the GFM droop control, likely caused by:

1. **Insufficient damping in the power-angle (P-f) droop loop.** The droop gain and virtual inertia settings may need to be retuned for larger disturbances, or an explicit damping term (virtual friction/resistance) may be needed.

2. **Current limiter interaction.** When large disturbances drive the inverter current to its limits, the current limiter engages and disengages cyclically, creating a nonlinear limit cycle. The anti-windup mechanisms in the voltage and current loops may not be properly coordinated with the droop controller.

3. **Lack of power reference limiting/rate limiting.** The droop controller may generate power references that change too rapidly for the inner control loops to track, leading to oscillatory interaction.

The fact that small-signal tests (Tests 4, 5) and moderate LVRT events (Tests 2, 6) pass cleanly confirms that the inner voltage and current loops are properly tuned for normal operation. The instability is a **large-signal phenomenon** that only manifests when the operating point moves far from nominal.

---

## Recommendations

1. **HVRT (Tests 3, 7):** The model requires fundamental improvements to its reactive power absorption capability under high-voltage conditions. Consider:
   - Adding or retuning a fast reactive current injection/absorption pathway that engages during large voltage deviations.
   - Implementing a high-voltage current limiting strategy that avoids limit cycling.
   - Reviewing the virtual impedance settings and voltage loop saturation limits.

2. **Phase Angle Jump (Tests 8, 9):** The droop controller needs additional damping for large angle disturbances. Consider:
   - Increasing the virtual inertia constant (H) to slow the angle response.
   - Adding explicit damping (virtual friction/damper winding equivalent) to the power-angle loop.
   - Implementing rate limiters on the power reference from the droop controller.
   - Reviewing the PLL bandwidth relative to the droop loop bandwidth to avoid adverse interaction.

3. **LVRT Current Limiter (Test 2, final segment):** While not a strict failure, the sustained oscillations at 0.10 pu voltage indicate the current limiter/anti-windup logic needs attention at extreme low-voltage conditions. Consider tightening the anti-windup and adding hysteresis to the current limiting logic.

4. **Frequency Transient (Test 6):** The brief 54.1 Hz excursion during zero-voltage ride-through should be monitored. While acceptable per current criteria, large instantaneous frequency excursions may interact poorly with protection systems in a full network simulation.

5. **Tests 10–13:** These tests (Custom Faults, Frequency Down/Up, V Up/Down Impedance/SCR) should be executed to complete the MQT suite. Given the failures in large-disturbance tests, the System Strength test (Test 13, Section 3.1.5.8) may reveal additional stability concerns at lower SCR values.

---

## Summary Table

| Test | Profile | DWG Section | Key Metric | Result |
|------|---------|-------------|------------|--------|
| 1 | Flat Start | 3.1.5.2 | Ppoi = 0.43 pu (flat), Fpoi = 60.00 Hz | **PASS** |
| 2 | LVRT Legacy | 3.1.5.4 | Rides through, recovers; oscillates at 0.1 pu | **COND. PASS** |
| 3 | HVRT Legacy | 3.1.5.5 | Sustained P/Q oscillation, Ppoi to -2.3 pu | **FAIL** |
| 4 | V Step Down | 3.1.5.3 | Ppoi sustained, Qpoi +0.05/+0.11 pu (lagging) | **PASS** |
| 5 | V Step Up | 3.1.5.3 | Ppoi sustained, Qpoi -0.13/-0.20 pu (leading) | **PASS** |
| 6 | LVRT Dips IEEE 2800 | 3.1.5.4 | All 5 dips ridden through, full recovery | **PASS** |
| 7 | HVRT Preferred IEEE 2800 | 3.1.5.5 | Sustained P/Q oscillation, Ppoi to -1.8 pu | **FAIL** |
| 8 | Angle Jump Down | 3.1.5.9 | Sustained oscillation, Fpoi to 49.2 Hz | **FAIL** |
| 9 | Angle Jump Up | 3.1.5.9 | Sustained oscillation, Fpoi to 77.1 Hz | **FAIL** |
| 10–13 | (various) | — | — | **NOT RUN** |
