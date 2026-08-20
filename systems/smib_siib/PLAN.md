# SMIB device-only ride-through — bus-39 synchronous machine vs REGFM_A1

Isolate the **device** fault ride-through profile from the islanding topology
that dominated the 39-bus comparison: same single-machine-infinite-bus test,
same bolted **3PG at t = 3.0 s for 5 cycles** (RON = 0.001 Ω), same relative
grid strength (**SCR = 10, X/R = 20 on each device's own base**), infinite bus
held flat. No line is lost, so the post-fault network is unchanged.

## Models (branch root — PSCAD cases, run manually or via their harnesses)

- **Sync**: [`single_machine_infinite_bus_1syncMachineValidation/`](../../single_machine_infinite_bus_1syncMachineValidation)
  — `SMIB_SYNC.pscx`: the bus-39 machine module `G_39_0_1_DYR`
  (GENROU + ESST4B + GGOV1 + PSS2B from `IEEE 39 bus TypicalGT.dyr`,
  2000 MVA / 230 kV) transplanted into the GFM SMIB case. Dispatch 0.50 pu
  (VT = 1.03, Pheta ≈ +2.7° — the machine initializes its .dyr models from the
  `VT∠Pheta` flow through the grid impedance only, excluding its own start-up
  XPU). Grid_Parameters: Mbase 2000 / V_base 230 / G_volt 230 / SCR 10 / XR 20.
  POI multimeter scaled 2000 MVA / 230 kV / 5.02 kA → pu outputs.
- **GFM**: [`single_machine_infinite_bus_1GFMvalidation/`](../../single_machine_infinite_bus_1GFMvalidation)
  — PNNL REGFM_A1 release SMIB (Mbase 0.1 MVA / 0.48 kV), Preq = 0.60 pu.
  **ImaxF = 2.0 here (PNNL default) — the 39-bus study used 1.5**; I_clip 2.1.

## Workflow

1. Run the sync case (PSCAD GUI "go", or its `run_3PG_fault.py` for the
   scripted record run) — fault parameters live in the case
   (tfaultn 963051497: TF = 3, DF = 0.0833; tpflt 1556776980: RON = 0.001).
2. `python smib_gfm_vs_sync.py` (here) — reads the newest sync output straight
   from `SMIB_SYNC.gf46`, writes the trimmed record CSV into
   `runs/3PG_5cyc_SCR10_10s/` (gitignored), and regenerates the two comparison
   figures into `plots/` against the GFM reference CSV.
3. The meeting deck picks the newest figures from `plots/` automatically
   (appendix "SMIB device-only" slides).

## Results (10 s, both devices, per-unit on own rating — bases on the figures)

> **Sync source = the canonical `SMIB_1SYNC_3PG_PSD.csv`** (documented dispatch-0.50
> run) in the sync model folder, read directly by `smib_gfm_vs_sync.py`. NOTE: the
> live `SMIB_SYNC.gf46` currently holds a *different* run (modified `.pscx`,
> dispatch 0.39, peak 4.4 pu, POI voltage holds ~0.45) — don't confuse the two.

| | Synchronous (bus-39) | GFM (REGFM_A1) |
|---|---|---|
| Pre-fault dispatch P | 0.50 pu | 0.60 pu (Preq) |
| Fault current peak (RMS) | **7.8 pu** (unlimited) | **2.0 pu** (ImaxF clamp) — **~4×** |
| During-fault **POI** V (`VRMS2grid` / `V_pu`) | **collapses to ~0 (mean 0.12)** | **collapses to ~0.12** |
| During-fault **machine terminal** (`Vm`) | **holds 0.51–0.77** | (no separate terminal node recorded) |
| Voltage recovery (post-clear) | ~1.05 pu | ~1.00 pu |
| Frequency | tight | tight |

**Reading:** at the **POI** (the faulted node, what the V figure plots) the bolted
3PG clamps the voltage to ~0 for **both** devices — equal, despite the ~4× current
contrast, because the near-zero fault impedance sets that node's voltage, not the
source. At the sync machine's **own terminal** (`Vm`, behind its connection
impedance) the large fault current holds the voltage up at ~0.77 (V = I·Z through
the connection reactance) — the GFM has no comparable terminal node recorded here.
So "equal voltage, very different current" is the **POI** view; the sync's
voltage-support advantage shows at its **terminal**. Post-clear both recover to
~1.0 (grid-pinned). Both ride the fault through cleanly against the SCR-10 grid.

## Parity caveats (printed on the figures)

- GFM limiter here is ImaxF = 2.0 (PNNL default), not the 1.5 of the 39-bus
  campaign → the network-study current contrast (5.95 vs 1.5–1.69 pu) is
  starker than this SMIB plot shows.
- Loadings differ slightly: sync 0.50 pu vs GFM 0.60 pu.
- Possible follow-ups: set the SMIB GFM's ImaxF to 1.5 and re-run for exact
  parity; CCT ladder at the device level (sweep DF in both harnesses).
