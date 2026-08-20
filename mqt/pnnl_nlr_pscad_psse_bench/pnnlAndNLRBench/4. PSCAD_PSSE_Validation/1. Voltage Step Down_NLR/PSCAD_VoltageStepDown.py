"""NLR Voltage Step Down driver.

Runs the NLR_comp_to_A1.pscx project under the same disturbance as the
PNNL test (1.0 -> 0.95 pu at t = 5 s, 7 s simulation), with NLR-side
operating-point parameters aligned to the PNNL test so steady-state
quantities pre-event are comparable:

- ``Pset`` const  (id=434574259):  0.40 -> 0.60 pu
- ``Vsched`` const (id=1275978730): 1.03 -> 1.00 pu

The NLR voltage regulator is left ENABLED (its authored configuration)
since disabling it caused the NLR model to fail to hold steady state
through the disturbance. So this run compares:

  - PNNL: open-loop V (V passively follows source voltage step)
  - NLR:  V-regulated (active AVR pulls V back toward Vsched = 1.0 pu)

The 7 s duration gives NLR's ``Release_Time = 2 s`` plus internal
setpoint delays room to settle before the disturbance lands.

Note on per-unit base: NLR uses ``s_base = 200000 kVA = 200 MVA`` at
``v_base = 13.8 kV``; PNNL uses ``Sbase = 100 kVA`` at ``Vbase = 480 V``.
Comparison is meaningful in pu so long as the grid impedance is also
in pu on each model's own base.

NLR_comp_to_A1 also writes a ``REGFM_A1_data`` stream from its embedded
PNNL black box, but this script reads only the NLR stream — the
``1. Voltage Step Down_pnnl`` folder runs PNNL independently.
"""
import logging
import os
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(THIS_DIR, os.pardir))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from _pscad_pipeline import run_disturbance  # noqa: E402

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)-8s %(name)-26s %(message)s')
logging.getLogger('mhi.pscad').setLevel(logging.WARNING)

# Component IDs in NLR_comp_to_A1.pscx
NLR_GFM_INVERTER_ID = 137448792
NLR_PSET_CONST_ID   = 434574259
NLR_VSCHED_CONST_ID = 1275978730
NLR_MULTIMETER_ID   = 819860882
# The project also has GLOBAL Mbase / V_base / G_volt master:var sliders
# whose authored values are PNNL's (0.1 MVA / 0.48 kV / 0.48 kV). They
# propagate via datalabels and drive grid-side per-unit math + the
# voltage-source magnitude. With the NLR (200 MVA, 13.8 kV) machine
# active, leaving them at PNNL values makes the network behave as if
# serving a 0.1 MVA / 480 V machine — the NLR machine then crashes.
NLR_MBASE_VAR_ID    = 650716798    # global Mbase  master:var  (Value=0.1)
NLR_VBASE_VAR_ID    = 1616406748   # global V_base master:var  (Value=0.48)
NLR_GVOLT_VAR_ID    = 1060705507   # global G_volt master:var  (Value=0.48)


def main() -> None:
    csvs = run_disturbance(
        case_dir=THIS_DIR,
        project_name='NLR_comp_to_A1',
        workspace_file='NLRBenchmark.pswx',
        build_dir_name='NLR_comp_to_A1.gf46',
        output_streams=[
            {'prefix': 'NLR_data', 'csv_basename': 'NLR_VoltDwn_PSD'},
        ],
        # Matches PNNL run: 7 s sim, V step at t = 5 s, plot window 4 -> 7.
        # The NLR-side reaches steady state by ~t=3 with the corrected
        # project (transformer removed, global bases on NLR's 200 MVA /
        # 13.8 kV), so 5 s is plenty of warmup before the disturbance.
        sim_duration=7.0,
        disturbance_time=5.0,
        voltage_step_pu=0.95,
        target_columns=('TIME', 'V_pu', 'I_pu', 'P_pu', 'Q_pu', 'f_drp'),
        project_settings={'time_duration': '7'},
        # NLR machine at its authored 200 MVA / 13.8 kV rating. (The
        # 100-MVA-match-source experiment didn't change the oscillation
        # behavior, so we're back to the original sizing.) Global Mbase /
        # V_base / G_volt are flipped to NLR's bases so the grid-side
        # per-unit math + source magnitude align with the active machine,
        # multimeter sized 200 MVA / 8.367 kA so plot pu values are on
        # the machine's base, Vsched=1.0 pins the AVR target at grid
        # nominal.
        extra_param_overrides={
            NLR_GFM_INVERTER_ID: {'s_base': '200000'},
            NLR_MBASE_VAR_ID:    {'Max': '500',  'Value': '200'},
            NLR_VBASE_VAR_ID:    {'Max': '500',  'Value': '13.8'},
            NLR_GVOLT_VAR_ID:    {'Max': '500',  'Value': '13.8'},
            NLR_VSCHED_CONST_ID: {'Value': '1.0'},
            NLR_MULTIMETER_ID:   {'S': '200.0 [MVA]', 'BaseA': '8.367'},
        },
    )
    print('CSVs:', csvs)


if __name__ == '__main__':
    main()
