"""ieee39_data.py - IEEE 39-bus network data + the 10-GFM (REGFM_A1) fleet.

Network data source: MHI "IEEE 39 Bus System" technical note (resources/
ieee_39_bus_technical_note (3).pdf), Tables 1-3 -- which is the standard
New England case39 (the note's generator terminal voltages reproduce the
case39 setpoints, e.g. 240.925/230 = 1.0475 at bus 30). The note omits the
12 transformer branches; those are taken from the standard case39 data set
(pstca / MATPOWER case39) that the note cites as its reference [1].

GFM fleet: the ieee39_sz10GFM PSCAD model (experiments/fault_3PG_bus14_10GFM
setup.json) -- one PNNL REGFM_A1 per generator bus 30-39, Mbase = PG/0.6,
Preq = 0.6 pu on Mbase, mp = 0.01, power-filter TPF = 10 ms (PNNL default;
gives the droop-emulated H_eqv = TPF/2mp = 0.5 s on Mbase).

All network quantities in per-unit on SBASE = 100 MVA / 230 kV unless noted.
"""

SBASE = 100.0          # MVA system base
FN = 60.0              # Hz
WS = 2.0 * 3.141592653589793 * FN   # rad/s

# ---------------------------------------------------------------------------
# branches: (from, to, R, X, B_total, tap)   tap = 0 -> no transformer (1.0)
# 34 lines from tech-note Table 2 + 12 standard case39 transformers.
# ---------------------------------------------------------------------------
BRANCHES = [
    # ---- lines (tech note Table 2) ----
    (1,  2, 0.0035, 0.0411, 0.6987, 0),
    (1, 39, 0.0010, 0.0250, 0.7500, 0),
    (2,  3, 0.0013, 0.0151, 0.2572, 0),
    (2, 25, 0.0070, 0.0086, 0.1460, 0),
    (3,  4, 0.0013, 0.0213, 0.2214, 0),
    (3, 18, 0.0011, 0.0133, 0.2138, 0),
    (4,  5, 0.0008, 0.0128, 0.1342, 0),
    (4, 14, 0.0008, 0.0129, 0.1382, 0),
    (5,  6, 0.0002, 0.0026, 0.0434, 0),
    (5,  8, 0.0008, 0.0112, 0.1476, 0),
    (6,  7, 0.0006, 0.0092, 0.1130, 0),
    (6, 11, 0.0007, 0.0082, 0.1389, 0),
    (7,  8, 0.0004, 0.0046, 0.0780, 0),
    (8,  9, 0.0023, 0.0363, 0.3804, 0),
    (9, 39, 0.0010, 0.0250, 1.2000, 0),
    (10, 11, 0.0004, 0.0043, 0.0729, 0),
    (10, 13, 0.0004, 0.0043, 0.0729, 0),
    (13, 14, 0.0009, 0.0101, 0.1723, 0),
    (14, 15, 0.0018, 0.0217, 0.3660, 0),
    (15, 16, 0.0009, 0.0094, 0.1710, 0),
    (16, 17, 0.0007, 0.0089, 0.1342, 0),
    (16, 19, 0.0016, 0.0195, 0.3040, 0),
    (16, 21, 0.0008, 0.0135, 0.2548, 0),
    (16, 24, 0.0003, 0.0059, 0.0680, 0),
    (17, 18, 0.0007, 0.0082, 0.1319, 0),
    (17, 27, 0.0013, 0.0173, 0.3216, 0),
    (21, 22, 0.0008, 0.0140, 0.2565, 0),
    (22, 23, 0.0006, 0.0096, 0.1846, 0),
    (23, 24, 0.0022, 0.0350, 0.3610, 0),
    (25, 26, 0.0032, 0.0323, 0.5130, 0),
    (26, 27, 0.0014, 0.0147, 0.2396, 0),
    (26, 28, 0.0043, 0.0474, 0.7802, 0),
    (26, 29, 0.0057, 0.0625, 1.0290, 0),
    (28, 29, 0.0014, 0.0151, 0.0249, 0),
    # ---- transformers (standard case39; note omits them) ----
    (2, 30, 0.0000, 0.0181, 0.0, 1.025),
    (6, 31, 0.0000, 0.0250, 0.0, 1.070),
    (10, 32, 0.0000, 0.0200, 0.0, 1.070),
    (11, 12, 0.0016, 0.0435, 0.0, 1.006),
    (13, 12, 0.0016, 0.0435, 0.0, 1.006),
    (19, 20, 0.0007, 0.0138, 0.0, 1.060),
    (19, 33, 0.0007, 0.0142, 0.0, 1.070),
    (20, 34, 0.0009, 0.0180, 0.0, 1.009),
    (22, 35, 0.0000, 0.0143, 0.0, 1.025),
    (23, 36, 0.0005, 0.0272, 0.0, 1.000),
    (25, 37, 0.0006, 0.0232, 0.0, 1.025),
    (29, 38, 0.0008, 0.0156, 0.0, 1.025),
]

# ---------------------------------------------------------------------------
# loads: bus -> (P, Q) pu   (tech note Table 3 = case39)
# ---------------------------------------------------------------------------
LOADS = {
    3: (3.220, 0.024), 4: (5.000, 1.840), 7: (2.338, 0.840),
    8: (5.220, 1.760), 12: (0.075, 0.880), 15: (3.200, 1.530),
    16: (3.294, 0.323), 18: (1.580, 0.300), 20: (6.800, 1.030),
    21: (2.740, 1.150), 23: (2.475, 0.846), 24: (3.086, -0.922),
    25: (2.240, 0.472), 26: (1.390, 0.170), 27: (2.810, 0.755),
    28: (2.060, 0.276), 29: (2.835, 0.269), 31: (0.092, 0.046),
    39: (11.040, 2.500),
}

# ---------------------------------------------------------------------------
# generators (all replaced by REGFM_A1 GFMs in the target model)
# bus -> (Pg_MW, Vset_pu)   Pg per case39 dispatch; bus 31 = slack.
# ---------------------------------------------------------------------------
GENS = {
    30: (250.0, 1.0475), 31: (None, 0.9820),   # slack (case39: ~572.9 MW)
    32: (650.0, 0.9831), 33: (632.0, 0.9972), 34: (508.0, 1.0123),
    35: (650.0, 1.0493), 36: (560.0, 1.0635), 37: (540.0, 1.0278),
    38: (830.0, 1.0265), 39: (1000.0, 1.0300),
}
SLACK_BUS = 31
GEN_BUSES = sorted(GENS.keys())      # 30..39, index order of the GFM fleet

# ---------------------------------------------------------------------------
# GFM fleet (from experiments/fault_3PG_bus14_10GFM setup.json)
# ---------------------------------------------------------------------------
GFM_MBASE_MVA = {30: 417.0, 31: 997.0, 32: 1083.0, 33: 1053.0, 34: 847.0,
                 35: 1083.0, 36: 933.0, 37: 900.0, 38: 1383.0, 39: 1667.0}
MP = 0.01          # droop, pu-freq / pu-power on own Mbase (all GFMs)
TPF = 0.010        # power-measurement filter time constant, s (all GFMs)
# coupling reactance internal EMF -> generator bus (filter + 230:10 kV GSU),
# pu on the GFM's OWN Mbase.  Not stated in setup.json; default 0.15
# (X_tr ~ 0.10 + X_filter ~ 0.05) -- swept in the sensitivity study.
XG_PU_MBASE = 0.15

# per-GFM swing parameters on the SYSTEM base (Sauer eq. 9.13 form with
# delta in rad, t in s:   M_i * dd2(delta) + D_i * dd(delta) = Pm - Pe):
#   H_i  = (TPF / 2 mp) * (Mbase_i / SBASE)          [s]
#   M_i  = 2 H_i / WS                                 [pu s^2/rad]
#   D_i  = (1 / mp) * (Mbase_i / SBASE) / WS          [pu s/rad]
# note D_i / M_i = 1/TPF  identical for every unit -> uniform damping.


def gfm_MD(bus):
    sb = GFM_MBASE_MVA[bus] / SBASE
    H = (TPF / (2.0 * MP)) * sb
    M = 2.0 * H / WS
    D = (1.0 / MP) * sb / WS
    return M, D, H


def gfm_xg_sys(bus, xg_pu_mbase=None):
    x = XG_PU_MBASE if xg_pu_mbase is None else xg_pu_mbase
    return x * SBASE / GFM_MBASE_MVA[bus]
