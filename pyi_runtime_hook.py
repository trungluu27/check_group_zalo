"""
PyInstaller runtime hook.

Set conservative BLAS/OpenMP thread limits before user code imports NumPy/pandas.
This mitigates macOS ARM crashes like:
  ___chkstk_darwin -> libopenblas64_.0.dylib -> dgetrf_parallel
"""

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
