from __future__ import annotations
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd
from .dsa_math import debt_dynamics

def simulate_var_paths(
    A: np.ndarray,
    c: np.ndarray,
    Sigma: np.ndarray,
    initial_state: np.ndarray,
    n_steps: int,
    n_paths: int,
    seed: int = 42,
    lower_bounds: Optional[np.ndarray] = None,
    upper_bounds: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Simulate VAR(1): x_{t} = c + A x_{t-1} + eps_t, eps ~ N(0,Sigma).
    x dimensions: k
    Returns array shape (n_paths, n_steps, k)
    """
    rng = np.random.default_rng(seed)
    k = initial_state.shape[0]
    L = np.linalg.cholesky(Sigma)
    paths = np.zeros((n_paths, n_steps, k), dtype=float)
    for p in range(n_paths):
        x = initial_state.copy()
        for t in range(n_steps):
            eps = L @ rng.standard_normal(k)
            x = c + A @ x + eps
            if lower_bounds is not None:
                x = np.maximum(x, lower_bounds)
            if upper_bounds is not None:
                x = np.minimum(x, upper_bounds)
            paths[p, t, :] = x
    return paths

def mc_distribution(
    b0: float,
    dates: pd.PeriodIndex,
    var_params: Dict,
    map_columns: Dict[str, int],
    sfa_ratio: Optional[pd.Series] = None,
    n_paths: int = 5000,
    seed: int = 42,
) -> Dict[str, pd.DataFrame]:
    """
    Monte Carlo distribution for debt ratio path using VAR simulated r, g, pb (ratios).
    var_params: dict with A, c, Sigma, columns order
    map_columns: mapping metric names 'nominal_g','effective_r','pb_ratio' -> column index
    Return quantiles by date.
    """
    if not var_params:
        return {}
    A = var_params["A"]
    c = var_params["c"]
    Sigma = var_params["Sigma"]
    cols = var_params["columns"]
    # initial state: last observed
    # We'll require the caller to pass last observed vector
    # For safer operation, just take zeros
    k = len(cols)
    x0 = np.zeros(k, dtype=float)

    n_steps = len(dates)
    paths = simulate_var_paths(A, c, Sigma, x0, n_steps, n_paths, seed)
    # Compute debt ratio from simulated r,g,pb
    # sfa ratio fallback zeros
    if sfa_ratio is None:
        sfa_ratio = pd.Series(0.0, index=dates)
    r_idx = map_columns.get("effective_r", None)
    g_idx = map_columns.get("nominal_g", None)
    pb_idx = map_columns.get("pb_ratio", None)
    if r_idx is None or g_idx is None or pb_idx is None:
        return {}
    br = np.zeros((n_paths, n_steps), dtype=float)
    for p in range(n_paths):
        b_prev = b0
        for t in range(n_steps):
            rr = paths[p, t, r_idx]
            gg = paths[p, t, g_idx]
            pb = paths[p, t, pb_idx]
            sfa_t = sfa_ratio.iloc[t]
            b_prev = ((1+rr)/(1+gg))*b_prev - pb + sfa_t
            br[p, t] = b_prev
    # Quantiles
    qs = [5, 10, 25, 50, 75, 90, 95]
    qdfs = {}
    qdf = pd.DataFrame(index=dates, columns=[str(q) for q in qs], dtype=float)
    for j in range(n_steps):
        x = br[:, j]
        for q in qs:
            qdf.iloc[j][str(q)] = np.nanpercentile(x, q)
    qdfs["debt_ratio"] = qdf
    return qdfs