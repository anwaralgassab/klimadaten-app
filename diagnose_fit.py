"""
Diagnose-Skript: zeigt, warum einzelne Verteilungen beim Fitten fehlschlagen.
Ausführen mit: python diagnose_fit.py
"""
import sys
import warnings

import numpy as np
import scipy

print("Python:", sys.version)
print("scipy:", scipy.__version__)
print("numpy:", np.__version__)
print("-" * 60)

from scipy import stats

rng = np.random.default_rng(42)
values = rng.normal(loc=9.0, scale=6.5, size=20000)

for name, dist in [
    ("norm", stats.norm),
    ("skewnorm", stats.skewnorm),
    ("weibull_min", stats.weibull_min),
    ("gumbel_r", stats.gumbel_r),
    ("t", stats.t),
]:
    print(f"\n--- {name} ---")
    try:
        params = dist.fit(values)
        print("  params:", params)
        log_likelihood = np.sum(dist.logpdf(values, *params))
        print("  log_likelihood:", log_likelihood)
        ks_stat, ks_p = stats.kstest(values, dist.name, args=params)
        print("  KS:", ks_stat, ks_p)
        print("  OK")
    except Exception as e:
        print(f"  FEHLER: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()