from __future__ import annotations
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR

def calibrate_var(
    df: pd.DataFrame,
    lags: int = 1,
    enforce_positive_definite: bool = True,
) -> Dict:
    """
    Calibrate a VAR(1) on columns, e.g., ['nominal_g', 'effective_r', 'pb_ratio'].
    Returns parameters usable in simulation: A (coef), c (const), Sigma (cov).
    """
    df = df.dropna()
    if len(df) < (lags + 10):
        # Too short to calibrate reliably
        return {}
    try:
        model = VAR(df)
        res = model.fit(lags)
        A = res.coefs[0]  # for VAR(1)
        c = res.intercept
        Sigma = res.sigma_u
        if enforce_positive_definite:
            # Ensure Sigma is PD
            eigvals = np.linalg.eigvals(Sigma)
            if np.min(eigvals) <= 1e-8:
                # add jitter
                Sigma += np.eye(Sigma.shape[0]) * 1e-4
        return {"A": A, "c": c, "Sigma": Sigma, "columns": list(df.columns)}
    except Exception:
        return {}

def compute_effective_r_from_interest_and_debt(interest_bn: pd.Series, psnd_bn: pd.Series) -> pd.Series:
    psnd_y = psnd_bn
    avg_debt = (psnd_y.shift(1) + psnd_y) / 2.0
    r_eff = (interest_bn / avg_debt).rename("effective_r")
    return r_eff

def implied_pb_ratio(psnb_bn: pd.Series, interest_bn: pd.Series, gdp_bn: pd.Series) -> pd.Series:
    """
    Approx primary balance ratio from PSNB and interest:
    PB (bn) = - (PSNB - interest)
    pb_ratio = PB / GDP
    """
    pb_bn = -(psnb_bn - interest_bn)
    pb_ratio = (pb_bn / gdp_bn).rename("pb_ratio")
    return pb_ratio