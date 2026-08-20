"""PNNL REGFM_A1 voltage step-up case driver.

Defers all PSCAD plumbing to the shared pipeline in the parent folder.
Apples-to-apples timing with the NLR case: 7 s simulation, voltage step
1.0 -> 1.05 pu applied at t = 5 s, plot window 4 -> 7 s. (NLR needs the
extra warmup before its operating point settles; PNNL doesn't, but
matching timing keeps the decks visually aligned.)
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


def main() -> None:
    run_disturbance(
        case_dir=THIS_DIR,
        project_name='REGFM_A1',
        workspace_file='REGFM_A1_PNNL.pswx',
        build_dir_name='REGFM_A1.gf46',
        output_streams=[
            {'prefix': 'REGFM_A1_data', 'csv_basename': 'A1_VoltUp_PSD'},
        ],
        sim_duration=7.0,
        disturbance_time=5.0,
        voltage_step_pu=1.05,
        target_columns=('TIME', 'V_pu', 'I_pu', 'P_pu', 'Q_pu', 'f_drp'),
        project_settings={'time_duration': '7'},
    )


if __name__ == '__main__':
    main()
