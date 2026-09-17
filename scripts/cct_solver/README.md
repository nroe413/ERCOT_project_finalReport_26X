# Critical-clearing-time (CCT) solver

The energy-method critical clearing times quoted in the report (Section 5.1, Figure 50) are computed
by the scripts in this folder. They are copied from the study's experiment folders with only the
input paths changed to repository-relative ones; the study's result files are in `data/report_figure_data/cct_solver/`
(`results_constP.json`: ten-inverter scenarios; `results_firstslip.json`; `results_gfm_damping_sweep.json`;
`results_sp39/tier2/tier3.json`: all-machine classical, flux-decay and constant-power tiers; `smib_cct_metrics.json`).

| File | Role |
|---|---|
| `ieee39_data.py` | network and fleet data |
| `cct_pebs.py` | classical (constant-impedance) machinery and the GFM system class |
| `cct_sp39.py` | all-machine classical system builder |
| `cct_e39_tier2.py` | machine reactances and field time constant |
| `cct_p39_tier3.py` | constant-power network solver, integrator, classifier, bisection |
| `cct_pebs_constP.py` | ten-inverter 39-bus CCT (report: 2.338 s) |
| `cct_firstslip_constP.py` | same with the EMT ladder's slip rule |
| `make_phase_portrait_fig.py` | single-device reduced model class used by the sweep |
| `gfm_damping_sweep.py` | single-inverter CCT vs droop damping (report: 1.297 s at full damping) |
| `smib_cct.py` | single-machine equal-area CCT (report: 0.474 s) |

## What the solver does

Each device is a constant internal voltage behind a reactance obeying the swing form
`M dw/dt = Pm - Pe - D w` (machines: transient reactance, `D = 0`, optional field-flux decay;
inverters: coupling reactance, `M = 2 H_eq` with `H_eq = T_Pf / (2 m_p)`, `D = 1/m_p`). Loads are
constant P and Q injections read from the PSCAD model's own load blocks, so the network voltages are
solved at every step by a damped fixed-point iteration (`ConstPNetwork.solve`, with a count of
unconverged solves). The trajectory is integrated with fourth-order Runge-Kutta at 1 ms, fault-on
for the trial clearing time and then post-fault, and judged stable or unstable; bisection on the
clearing time to 5 ms gives the CCT (`true_cct_net`).

## Entry points

```
cd scripts/cct_solver
python cct_pebs_constP.py                  # ten-inverter 39-bus fleet, four fault scenarios (hours)
python cct_pebs_constP.py --scenario bus14_noloss --dscale 0.3   # one scenario, damping scaled
python cct_firstslip_constP.py             # same fleet, EMT-ladder slip rule
python gfm_damping_sweep.py                # single inverter on the infinite bus, damping sweep
python smib_cct.py                         # single machine, equal-area and swing integration
```

The ten-inverter bisection is slow (each stability test integrates 39-bus constant-power dynamics
for the clearing time plus 8 s); expect hours per scenario. Results are written as JSON next to the
scripts. Requirements: `numpy`; `pandas` and `matplotlib` for `smib_cct.py` and `gfm_damping_sweep.py`.
`cct_p39_tier3.py` reads the loads from `systems/ieee39/00GFM_all_sync/IEEE39_acLine1.pscx` and
`smib_cct.py` reads its operating point from `systems/smib_siib/runs/3PG_5cyc_SCR10_10s/`.
