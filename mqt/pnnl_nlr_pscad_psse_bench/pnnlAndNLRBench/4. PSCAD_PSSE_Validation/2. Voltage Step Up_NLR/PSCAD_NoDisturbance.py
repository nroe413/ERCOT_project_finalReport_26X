"""NLR no-disturbance baseline run.

Same configuration as PSCAD_VoltageStepUp.py but voltage_step_pu=1.0,
i.e. the 'step' is 1.0 -> 1.0 — no event ever fires. Used to determine
whether the post-event limit cycle observed in the voltage-step-up case
is triggered by the disturbance or is an inherent instability that
appears once the AVR engages at t = Release_Time + Tavr_release = 2.2 s.
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

NLR_GFM_INVERTER_ID = 137448792
NLR_VSCHED_CONST_ID = 1275978730
NLR_MULTIMETER_ID   = 819860882
NLR_MBASE_VAR_ID    = 650716798
NLR_VBASE_VAR_ID    = 1616406748
NLR_GVOLT_VAR_ID    = 1060705507


def main() -> None:
    csvs = run_disturbance(
        case_dir=THIS_DIR,
        project_name='NLR_comp_to_A1',
        workspace_file='NLRBenchmark.pswx',
        build_dir_name='NLR_comp_to_A1.gf46',
        output_streams=[
            {'prefix': 'NLR_data', 'csv_basename': 'NLR_Flat_PSD'},
        ],
        sim_duration=7.0,
        disturbance_time=5.0,
        voltage_step_pu=1.0,  # no step — OH=OL=1.0
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
