# ieee39_sz1GFL — step 1 of the GFL breakpoint sweep (GFL grafted — verify in PSCAD)

IEEE 39-bus, **9 synchronous machines + 1 PNNL grid-following IBR at the Gen-32 bus**.
The GFL is already integrated: `tools/graft_gfl_bus32.py` removed the REGFM_A1 (GFM)
that this dir was seeded with and transplanted PNNL's WECC GFL plant
(**REGC_A + REEC_A + REPC_A + IBR_AVM + CurrentLimit**) from
[`../PNNL_GFL/IBR_DM.pscx`](../PNNL_GFL/GFL_MODEL_SOURCES.md) — the same island PNNL used
to replace *their* Gen 30 in the same 39-bus system. Electrical path:

```
N32 (230 kV) ── E-Tran boundary xfmr ── multimeter (B32* channels)
   ── GSU 230/10 kV (Tmva3=100, Xl=0.02, TapI=1.0 — see note)
   ── secondary (1800,792) ──[N32LV nodelabel pair]── GFL island (multimeter P32/Q32/V32 → AVM)
```

> **`TapI` MUST stay 1.0.** The GFM build's 1.07 tap boosts the POI voltage; the GFL's
> V-loop (Vref = 1.0) then absorbs deep Q and the **PLL loses synchronism at the t≈1 s
> machine release** (delivered P collapses to ~0.1 pu while commands stay healthy —
> found the hard way, runs 2–5). With TapI = 1.0 the unit delivers 650 MW at 60.000 Hz.

The island (converter + plant controller + setpoint/flag logic + tuning panels) sits in
the canvas region around (770–2660, 2100–3300) on page P1, tied in by the `N32LV` labels.

## Parameterization (PNNL values, re-based Gen 30 → Gen 32)

| Quantity | PNNL (Gen 30) | Here (Gen 32) |
|---|---|---|
| Plant base `Sbase` (MVA consts ×2) | 480 | **1248** |
| `Pdm` (P setpoint, pu of Sbase) | 0.5208333 (→250 MW) | 0.5208333 (→**650 MW**) |
| `Vdm` (V setpoint at POI) | 1.0475 | **1.000** (Gen-32 schedule) |
| `Qdm` / `pfdm` | 0 / 1 | 0 / 1 |
| POI voltage base | 22 kV | **10 kV** (our GSU LV; island + AVM-internal meters re-based) |
| Current limit `Imax` (REEC) | 1.0 pu | 1.0 pu (same loading fraction ⇒ same headroom ≈1.9×) |
| `iqrmax` (REGC Iq rate limit) | 1.5 pu/s | **1.5 pu/s (stock)** — briefly raised to 25 during diagnosis, reverted after the parameter-isolation matrix showed it isn't needed for ride-through (FINDINGS §9; 25 pu/s is also unphysical for real bridge hardware). Trade-off on record: no meaningful fault-window Iq support at 1.5 pu/s |
| PLL freq limits (tvekta) | 0.8–1.2 pu (48–72 Hz) | **0.99–1.01 pu** — unclamped, the PLL runs away during deep sags (mis-phased injection, measured Iq ≈ 0/negative while ordered 1.0); clamped, it holds near-sync (id 318584670). At dead-bus voltage it still parks at the floor — a GFL cannot re-synchronize to a collapsed pocket |
| PLL | Kp=100, Ki=1000 | unchanged |
| AVM DC bus | `src_ccin_1` constant-current source (PV-at-MPPT, no chopper) | **`source_1` voltage source** (internal mode, Vm = 60.36 kV = PNNL's 132.79/22 ratio at our 10 kV base) — PNNL's own predecessor design (6 of 7 AVM variants); the shipped current source latch-locks at fault clearing (`tools/swap_gfl_dc_source.py`, FINDINGS §§5–7) |
| Mode flags | Vflag=1 Qflag=1 PQflag=0 (Q-priority), FreqFlag=0, Lvplsw=1 | unchanged |
| Deblock / Start timers | t > 0.15 s / 0.2 s | unchanged |

Setpoints + flags are on **ControlFrames** (slider/switch panels) next to the island —
tune `Pdm/Qdm/Vdm/pfdm` and the WECC flags there. `P32/Q32/V32` pgb channels record the
POI measurements (extra columns alongside the `B32*` bus channels).

## First-open checklist (PSCAD 5.0.1 / GFortran 4.6)

1. **Open + let PSCAD settle** the imported defs (`REPC_A_1`, `REGC_A_1_2_1_1`,
   `REEC_A_1_2_1_1`, `CurrentLimit_1_2_1_1`, `IBR_AVM_2_1_1`); the project tree
   (`<call>` list) regenerates on save. `.psmx` is stale (GFM-era) — regenerates at build.
2. **Build.** The WECC defs are pure schematics (no Fortran of their own, no new libs —
   the existing `ETRAN_GF46.lib` link is untouched).
3. **Inspect bus 32**: the island connects via the two `N32LV` node labels; confirm the
   GSU secondary → island continuity (no floating node warnings).
4. **No-fault run**: check steady state — bus-32 230 kV voltage near 1.00 pu and
   P ≈ 650 MW. If V is off-schedule, the GSU tap (`TapI` = 1.07, tuned for the GFM at this
   dispatch) vs. `Vdm` = 1.000 is the dial pair to reconcile.
5. Watch the first 0.5 s: GFL deblocks at t = 0.15/0.2 s during the E-Tran init — if it
   fights the init, push the `DBlk`/`Start` compare thresholds later (island logic blocks).
6. Then the base fault case (3PG bus 14, 5-cycle, no reclose) → `.inf`/`.out` into
   [`../experiments/fault_3PG_bus14_1GFL/runs/`](../experiments/fault_3PG_bus14_1GFL/README.md).

`IEEE 39 bus TypicalGT.dyr` is byte-identical to the baseline — the 9 remaining machines
keep their original dynamics. Sweep design + breakpoint criterion:
[`../GFL_BREAKPOINT_PLAN.md`](../GFL_BREAKPOINT_PLAN.md).
