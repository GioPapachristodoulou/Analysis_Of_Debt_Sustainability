from __future__ import annotations
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

def check_missing(s: pd.Series) -> List[int]:
    return list(np.where(s.isna())[0])

def check_outliers_zscore(s: pd.Series, threshold: float = 4.0) -> List[int]:
    if s.empty:
        return []
    x = s.values.astype(float)
    mu = np.nanmean(x)
    sd = np.nanstd(x)
    if sd == 0 or np.isnan(sd):
        return []
    z = (x - mu) / sd
    return list(np.where(np.abs(z) > threshold)[0])

def plausible_bounds_check(s: pd.Series, metric_id: str) -> List[int]:
    """
    Basic sanity checks per metric.
    """
    bad = []
    if metric_id in ("yield_10y",):
        # yields between -5 and 30 pct
        bad_idx = np.where((s < -5) | (s > 30))[0]
        bad.extend(list(bad_idx))
    if metric_id in ("gdp_nominal", "psnd_ex", "psnb_ex", "debt_interest"):
        # must be non-negative
        bad_idx = np.where(s < 0)[0]
        bad.extend(list(bad_idx))
    return bad

def compute_sfa(psnd: pd.Series, psnb: pd.Series) -> pd.Series:
    """
    Stock-flow adjustment residual: SFA = ΔDebt - Deficit (sign conventions vary).
    With PSNB positive = deficit, debt should increase. SFA captures valuation and other adjustments.
    """
    psnd_y = psnd.copy()
    psnb_y = psnb.copy()
    d_debt = psnd_y.diff()
    sfa = d_debt - psnb_y
    sfa.name = "sfa"
    return sfa