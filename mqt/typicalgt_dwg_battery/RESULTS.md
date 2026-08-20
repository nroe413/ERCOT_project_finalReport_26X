# Results: synchronous-machine model-quality battery (DWG tests 1-9)

Machine: Gen-32 of the IEEE 39-bus ETRAN conversion
(`IEEE 39 bus TypicalGT.dyr`: GENROU + ESST4B + GGOV1 + PSS2B,
650 MVA, 230 kV, H = 5.46 s), at its load-flow dispatch in this rig
(essentially no-load: P ~ 0.5 MW, Q ~ 0 pre-disturbance).
All nine runs completed the full 40 s (160,001 samples at 4 kHz);
no run crashed, no breaker action, frequency held at 60.000 Hz
throughout. Figures per test in `plots/test_NN_<name>/`, same channel
groups and style as the GFM campaign's `plot_gfm_tests.py`.

## Per-test outcome

| test | profile | ride-through | returns to pre-disturbance state? |
|---|---|---|---|
| 1 Flat Start | 1.0 pu, 40 s | n/a | **yes** - Vm 1.0000, Ef 1.073, P/Q flat for 40 s |
| 2 LVRT (legacy) | dips to 0.04/0.10 pu | yes | **no** - Ef latches +5.21, Q settles +1.83 pu |
| 3 HVRT (legacy) | overvoltage steps | yes | **no** - Ef latches -4.22, Q settles -1.31 pu |
| 4 V step down | small step | yes | **no** - Ef +4.95, Q +1.70 pu |
| 5 V step up | small step | yes | **no** - Ef -4.06, Q +1.33 pu |
| 6 LVRT (IEEE 2800) | staged dips | yes | **no** - Ef +5.21, Q +1.83 pu |
| 7 HVRT (preferred) | staged swells | yes | **no** - Ef +5.21, Q +1.83 pu |
| 8 angle jump down | phase steps | yes | **no** - Ef -4.22, Q +0.40 pu |
| 9 angle jump up | phase steps | yes | **no** - Ef -4.22, Q +0.41 pu |

Q values on the 650 MVA machine base, final-2-s means.

## The exciter non-recovery finding

In every disturbance test the ESST4B field voltage leaves its
initialized value (+1.073 pu) at the first transient, rails at a
ceiling (about +5.2 or -4.2 pu), and **stays there permanently** -
values are flat to 4 decimal places over the last 5 s, long after the
source voltage has returned to 1.0 pu. The residual field error is
balanced by a large standing reactive exchange with the stiff source
(up to 1.83 pu of machine base) while terminal voltage sits within
0.2% of nominal. The mechanical side is unaffected: speed returns to
1.0000 pu, torques to their pre-disturbance values, and the machine
never loses synchronism.

Read against the DWG intent (disturbance tests should end back at the
pre-disturbance operating point), this is a conditional-pass at best
for tests 2-9: ride-through and mechanical recovery are clean, but
the excitation state does not recover. The latch triggers on *any*
disturbance, including the small voltage steps of tests 4-5, and even
in tests 8-9 where the voltage magnitude never changes - so it looks
like a property of the ETRAN-converted ESST4B wrapper (e.g. a
saturating integrator without anti-windup, or a latched limit state)
as parameterized in this .dyr, not a tuned response to deep dips.
Mirroring the report's PMView framing: the test rig is not "wrong" -
the battery is doing its job by surfacing an excitation-model state
that a 7-s run never shows (the inertia-validation runs ended before
any of this could be observed).

Caveats for comparison with the GFM results:
- the machine is at essentially zero active-power dispatch in this
  rig (the GFM units ran at their dispatch), so P-recovery is trivial
  here;
- the rig source is effectively ideal at the machine bus, which makes
  the standing Q figure a rig-dependent quantity (a weaker grid would
  convert the same field error into a larger voltage offset instead).
