"""Shared PSCAD-automation pipeline for the disturbance cases under
``4. PSCAD_PSSE_Validation/``.

A single per-disturbance script imports ``run_disturbance`` and supplies
the case-specific knobs.  The helper handles every quirk we discovered
while wiring the pipeline up:

1. ``mhi.pscad.launch`` is pinned to PSCAD 5.0.1 (5.0.2 isn't installed).
2. Component-parameter writes are made before ``project.save()`` so they
   end up in the .pscx the build reads from.
3. The auto-generated makefile has a ``copy`` rule that fails under
   PSCAD's MSYS sh; we pre-stage the project library inside the build
   folder so the make rule's target file already exists.
4. ``project.run()`` returns before EMTDC finishes, so we poll
   ``project.run_status()`` until idle.
5. ``mpuf.OutFile`` (the docs' suggested reader) flakes on the missing
   .inf race window; we read the .out files directly with numpy and
   parse channel order from the .inf with a small regex.

Channel layout note: PSCAD writes 10 PGB channels per .out file.  We
collect every ``<output_prefix>_NN.out`` in numerical order, concatenate
columns, and trim to the headers requested by ``target_columns``.
"""
from __future__ import annotations

import datetime
import glob
import logging
import os
import re
import shutil
import subprocess
import time
from typing import Dict, Iterable, Optional, Sequence, Tuple

# PSCAD spawns ``cmd /c <project>_30000.bat`` to run EMTDC. That bat does
# ``pushd <build_dir>`` then invokes ``<project>.exe`` by bare name. On
# this machine, ``NoDefaultCurrentDirectoryInExePath=1`` is set in the
# user environment, which disables cmd.exe's default cwd-in-PATH search,
# so the bare exe name fails with "is not recognized as an internal or
# external command". Unsetting it here causes our child PSCAD (and its
# spawned cmd) to inherit the unset value, restoring the lookup.
os.environ.pop('NoDefaultCurrentDirectoryInExePath', None)

import mhi.pscad
import numpy as np
import pandas as pd

LOG = logging.getLogger('pscad_pipeline')

# Default disturbance-component IDs are shared by all disturbance projects in
# this campaign (REGFM_A1 and NLR_comp_to_A1 both inherit them).
DEFAULT_FAULT_TIME_ID = 963051497          # master:tfaultn
DEFAULT_VOLTAGE_COMPARE_ID = 696389395     # master:compare driving Gvolt
DEFAULT_FREQ_COMPARE_ID = 2018508786       # master:compare driving Gfreq

DEFAULT_LIB_SRC = os.path.join('REGFM_A1', 'gf46', 'PNNL_REGFM_A1_gf46.lib')
DEFAULT_LIB_TARGET_NAME = 'PNNL_REGFM_A1_gf46_1.lib'


def parse_inf_columns(inf_path: str) -> list:
    """Return ['TIME', desc1, desc2, ...] in PGB index order from a .inf."""
    cols = ['TIME']
    pattern = re.compile(r'PGB\((\d+)\)\s+Output\s+Desc="([^"]+)"')
    pairs = []
    with open(inf_path, encoding='utf-8') as f:
        for line in f:
            m = pattern.search(line)
            if m:
                pairs.append((int(m.group(1)), m.group(2)))
    pairs.sort()
    cols.extend(name for _, name in pairs)
    return cols


def load_concat_out(build_dir: str, output_prefix: str) -> np.ndarray:
    """Concatenate <prefix>_NN.out chunk files (PSCAD splits at 10 PGBs)."""
    pattern = os.path.join(build_dir, f'{output_prefix}_[0-9][0-9].out')
    paths = sorted(glob.glob(pattern))
    if not paths:
        raise FileNotFoundError(f'No .out files matching {pattern}')

    pieces = []
    time_col = None
    for p in paths:
        chunk = np.loadtxt(p, skiprows=1)
        if chunk.ndim == 1:  # single-row degenerate
            chunk = chunk[None, :]
        # First column of every chunk is time; keep just one copy.
        if time_col is None:
            time_col = chunk[:, 0:1]
        pieces.append(chunk[:, 1:])
    return np.hstack([time_col] + pieces)


def _is_running(exe_name: str) -> bool:
    """True if any process with the given image name is currently alive."""
    try:
        out = subprocess.run(
            ['tasklist', '/FI', f'IMAGENAME eq {exe_name}', '/NH'],
            check=False, capture_output=True, text=True,
        )
    except Exception:
        return False
    return exe_name.lower() in (out.stdout or '').lower()


def wait_for_sim(
    project,
    *,
    sentinel_path: str,
    baseline_mtime: float,
    timeout_s: float = 300.0,
    poll_s: float = 1.0,
    min_wait_s: float = 4.0,
) -> bool:
    """Wait until ``sentinel_path`` (typically the first .out file) has been
    rewritten by EMTDC after ``project.run()`` was called.

    ``project.run_status()`` alone is unreliable: it can read ``(None, None)``
    in the brief window between ``run()`` returning and PSCAD actually
    spawning EMTDC, fooling the caller into thinking the sim already finished.
    The .out mtime sentinel is the authoritative completion signal.
    """
    deadline = time.monotonic() + timeout_s
    last_status = None
    started = False
    grace_until = time.monotonic() + min_wait_s

    while time.monotonic() < deadline:
        # Pull status if available (informational only).
        try:
            st = project.run_status()
        except Exception as exc:
            LOG.warning('run_status() error: %r', exc)
            st = last_status
        if st != last_status:
            LOG.info('run_status: %s', st)
            last_status = st
        if st and st != (None, None):
            started = True

        # Has EMTDC overwritten the sentinel since we called run()?
        try:
            mt = os.path.getmtime(sentinel_path)
        except FileNotFoundError:
            mt = -1.0
        sentinel_fresh = mt > baseline_mtime + 0.1  # 100 ms tolerance

        if sentinel_fresh and st == (None, None) and time.monotonic() > grace_until:
            return True

        time.sleep(poll_s)

    LOG.warning(
        'wait_for_sim timed out after %s s; last status=%s, sentinel_fresh=%s, started_observed=%s',
        timeout_s, last_status,
        os.path.exists(sentinel_path) and os.path.getmtime(sentinel_path) > baseline_mtime,
        started,
    )
    return False


def _apply_overrides(project, overrides: Dict[int, Dict[str, str]]) -> None:
    for cid, params in overrides.items():
        comp = project.component(cid)
        try:
            current = comp.parameters()
        except Exception:
            current = {}
        comp.parameters(**{k: str(v) for k, v in params.items()})
        try:
            now = comp.parameters()
            LOG.info('component %s overrides applied: %s -> %s',
                     cid, {k: current.get(k) for k in params},
                     {k: now.get(k) for k in params})
        except Exception:
            LOG.info('component %s overrides set (could not read back)', cid)


def run_disturbance(
    *,
    case_dir: str,
    project_name: str,
    workspace_file: str,
    build_dir_name: str,
    output_streams: Sequence[Dict[str, str]],
    sim_duration: float,
    disturbance_time: float,
    target_columns: Sequence[str],
    pscad_version: str = '5.0.1',
    voltage_step_pu: float = 0.95,
    fault_time_id: int = DEFAULT_FAULT_TIME_ID,
    voltage_compare_id: int = DEFAULT_VOLTAGE_COMPARE_ID,
    freq_compare_id: int = DEFAULT_FREQ_COMPARE_ID,
    lib_src_relpath: Iterable[str] = ('REGFM_A1', 'gf46', 'PNNL_REGFM_A1_gf46.lib'),
    lib_target_name: str = DEFAULT_LIB_TARGET_NAME,
    extra_param_overrides: Optional[Dict[int, Dict[str, str]]] = None,
    project_settings: Optional[Dict[str, str]] = None,
    timeout_s: float = 1200.0,
) -> Dict[str, str]:
    """Drive PSCAD for one disturbance case and write trimmed CSVs.

    ``output_streams`` is an iterable of ``{'prefix': ..., 'csv_basename': ...}``
    dicts — one per simulation output stream produced by the project. For
    the unified NLR_comp_to_A1 project this is two entries (NLR_data and
    REGFM_A1_data) since the project runs both inverter models in parallel.

    Returns ``{prefix: csv_path}`` for each stream.
    """
    case_dir = os.path.abspath(case_dir)
    os.chdir(case_dir)
    run_ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

    LOG.info('--- launching PSCAD %s ---', pscad_version)
    pscad = mhi.pscad.launch(version=pscad_version, x64=True, minimize=False)
    pscad.load(os.path.join(case_dir, workspace_file))
    project = pscad.project(project_name)
    project.focus()

    # Project-level settings (e.g. time_duration).
    if project_settings:
        try:
            project.parameters(**{k: str(v) for k, v in project_settings.items()})
            LOG.info('project settings applied: %s', project_settings)
        except Exception as exc:
            LOG.warning('project.parameters() failed: %r', exc)

    # Reset disturbance components — park every event past the sim end.
    project.component(fault_time_id).parameters(TF='100', DF='0.1')
    project.component(voltage_compare_id).parameters(OH='1.0', X='100')
    project.component(freq_compare_id).parameters(OH='1.0', X='100')

    # Operating-point / extra component overrides (e.g. Pset, Vsched, VR_enable).
    if extra_param_overrides:
        _apply_overrides(project, extra_param_overrides)

    # Activate the requested voltage step.
    LOG.info('voltage step: 1.0 -> %s pu at t = %s s', voltage_step_pu,
             disturbance_time)
    project.component(voltage_compare_id).parameters(
        OH=str(voltage_step_pu), X=str(disturbance_time))

    # Persist param edits so the rebuild picks them up.
    project.save()

    # Pre-stage the project library inside the build folder so the make
    # rule that uses Windows ``copy`` (broken under MSYS sh) is satisfied
    # without running.
    build_dir = os.path.join(case_dir, build_dir_name)
    os.makedirs(build_dir, exist_ok=True)
    src_lib = os.path.join(case_dir, *lib_src_relpath)
    staged_lib = os.path.join(build_dir, lib_target_name)
    if os.path.exists(src_lib):
        shutil.copyfile(src_lib, staged_lib)
        LOG.info('staged lib -> %s', staged_lib)
    else:
        LOG.warning('source lib missing: %s', src_lib)

    streams = list(output_streams)
    if not streams:
        raise ValueError('output_streams must have at least one entry')
    sentinels = [
        os.path.join(build_dir, f"{s['prefix']}_01.out") for s in streams
    ]
    baseline_mtimes = [
        os.path.getmtime(p) if os.path.exists(p) else -1.0 for p in sentinels
    ]
    exe_name = f'{project_name}.exe'

    # SimulationSet is the documented automation path. start_run() and
    # project.run() both proved unreliable here (no EMTDC spawn observed),
    # while a SimulationSet wraps the build+run with proper supervision and
    # actually fires EMTDC. We create a one-shot set, add this project as a
    # task, run it synchronously (set.run() blocks until EMTDC exits),
    # then remove the set so reruns don't pile them up.
    set_name = '__auto_run_set'
    try:
        pscad.remove_simulation_set(set_name)
    except Exception:
        pass
    sim_set = pscad.create_simulation_set(set_name)
    # remote API rejects ``add_task`` as Unknown — use ``add_tasks`` (varargs)
    # which the proxy routes correctly. Pass the Project object directly.
    sim_set.add_tasks(project)
    LOG.info('SimulationSet "%s" run() — synchronous build+run...', set_name)
    try:
        sim_set.run()
    except Exception as exc:
        LOG.warning('sim_set.run() raised %r — continuing to wait', exc)

    # Wait for EMTDC to appear (build can take a few seconds first).
    proc_appear_deadline = time.monotonic() + 120.0
    while time.monotonic() < proc_appear_deadline:
        if _is_running(exe_name):
            LOG.info('EMTDC (%s) is running', exe_name)
            break
        time.sleep(0.5)
    else:
        LOG.warning('EMTDC %s never appeared in process list', exe_name)

    # Wait for EMTDC to finish.
    sim_deadline = time.monotonic() + timeout_s
    last_size = -1
    while time.monotonic() < sim_deadline:
        if not _is_running(exe_name):
            break
        if os.path.exists(sentinels[0]):
            sz = os.path.getsize(sentinels[0])
            if sz != last_size:
                LOG.info('sentinel %s size: %.2f MB',
                         os.path.basename(sentinels[0]), sz / 1e6)
                last_size = sz
        time.sleep(3.0)
    else:
        LOG.warning('EMTDC still running after %s s — killing', timeout_s)
        subprocess.run(['taskkill', '/F', '/IM', exe_name],
                       check=False, capture_output=True)

    for s_path, s_base in zip(sentinels, baseline_mtimes):
        if not (os.path.exists(s_path) and os.path.getmtime(s_path) > s_base + 0.1):
            raise SystemExit(
                f'EMTDC did not refresh sentinel {s_path}. '
                f'Baseline mtime {s_base}, current '
                f'{os.path.getmtime(s_path) if os.path.exists(s_path) else "missing"}.'
            )
    LOG.info('Simulation Finished')

    # Read every requested output stream into its own trimmed CSV.
    out_csvs: Dict[str, str] = {}
    for stream in streams:
        prefix = stream['prefix']
        csv_basename = stream['csv_basename']

        inf_path = os.path.join(build_dir, f'{prefix}.inf')
        if not os.path.exists(inf_path):
            raise SystemExit(f'Missing .inf: {inf_path}')

        cols = parse_inf_columns(inf_path)
        LOG.info('[%s] parsed channels (%d): %s',
                 prefix, len(cols), cols[:6] + (['...'] if len(cols) > 6 else []))

        raw = load_concat_out(build_dir, prefix)
        if raw.shape[1] != len(cols):
            raise SystemExit(
                f'[{prefix}] column-count mismatch: .out has {raw.shape[1]} cols, '
                f'.inf says {len(cols)}'
            )
        df = pd.DataFrame(raw, columns=cols)

        missing = [c for c in target_columns if c not in df.columns]
        if missing:
            raise SystemExit(
                f'[{prefix}] channels missing: {missing}; available: {list(df.columns)}'
            )
        df = df[list(target_columns)]
        out_csv = os.path.join(case_dir, f'{csv_basename}_{run_ts}.csv')
        df.to_csv(out_csv, index=False)
        LOG.info('[%s] CSV written: %s', prefix, out_csv)
        out_csvs[prefix] = out_csv

    return out_csvs
