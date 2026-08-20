"""NLR Voltage Step Up driver.

Runs the NLR_comp_to_A1.pscx project under the same disturbance as the
PNNL test (1.0 -> 1.05 pu at t = 5 s, 7 s simulation, plot window 4 -> 7).
The 7 s duration gives the NLR-side operating point time to settle
before the disturbance lands — Case 2 with a 3 s disturbance showed
clear pre-event drift in P, Q, I.

The NLR voltage regulator is left ENABLED (its authored configuration)
since disabling it caused the NLR model to fail to hold steady state
through the disturbance.

Base-conversion overrides match Case 1 NLR (the project file was copied
directly): NLR machine at 200 MVA / 13.8 kV, global Mbase / V_base /
G_volt flipped to NLR's bases, multimeter sized 200 MVA / 8.367 kA so
plot pu values are on the machine's base, Vsched=1.0 pins the AVR target
at grid nominal.

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

# Component IDs in NLR_comp_to_A1.pscx (same .pscx as Case 1 NLR).
NLR_GFM_INVERTER_ID = 137448792
NLR_PSET_CONST_ID   = 434574259
NLR_VSCHED_CONST_ID = 1275978730
NLR_MULTIMETER_ID   = 819860882
NLR_MBASE_VAR_ID    = 650716798    # global Mbase  master:var
NLR_VBASE_VAR_ID    = 1616406748   # global V_base master:var
NLR_GVOLT_VAR_ID    = 1060705507   # global G_volt master:var


def main() -> None:
    csvs = run_disturbance(
        case_dir=THIS_DIR,
        project_name='NLR_comp_to_A1',
        workspace_file='NLRBenchmark.pswx',
        build_dir_name='NLR_comp_to_A1.gf46',
        output_streams=[
            {'prefix': 'NLR_data', 'csv_basename': 'NLR_VoltUp_PSD'},
        ],
        sim_duration=7.0,
        disturbance_time=5.0,
        voltage_step_pu=1.05,
        target_columns=('TIME', 'V_pu', 'I_pu', 'P_pu', 'Q_pu', 'f_drp'),
        project_settings={'time_duration': '7'},
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
