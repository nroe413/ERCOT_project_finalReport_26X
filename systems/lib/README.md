# Shared libraries for the shipped PSCAD projects

- `ETRAN_GF46.lib`, `ETRAN_IF12.lib`: E-TRAN runtime libraries (Electranix, free download;
  https://www.electranix.com/software/e-tran-runtime-library-for-pscad/). GF46 is the
  GFortran 4.6 build used by every project here; IF12 is the Intel Fortran 12 build kept
  for completeness.
- `PNNL_REGFM_A1/`: the PNNL REGFM_A1 grid-forming inverter wrapper project and its compiled
  library (PNNL public release, https://github.com/pnnl/PSCAD-and-PSSE-Version-of-WECC-Grid-Forming-Inverter-Models).
  Redistributed under PNNL's BSD 3-Clause License (Copyright (c) 2026 Battelle Memorial
  Institute); see `PNNL_REGFM_A1/LICENSE-PNNL.txt` and `PNNL_REGFM_A1/DISCLAIMER-PNNL.txt`.

Every `.pscx` and `.pswx` under `systems/` and `mqt/` links these files by relative path,
so a clone builds without re-pointing library paths.
