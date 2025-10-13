from __future__ import annotations
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd

def debt_dynamics(
    b0: float,
    r: pd.Series,
    g: pd.Series,
    pb: pd.Series,
    sfa: Optional[pd.Series] = None,
    start_year: Optional[int] = None,
) -> pd.Series:
    """
    Core debt dynamics in ratios:
    b_t = (1 + r_t) / (1 + g_t) * b_{t-1} - pb_t + sfa_t_ratio
    pb_t is primary balance in ratio (positive reduces debt).
    sfa_t_ratio is stock-flow adjustment as ratio of GDP (optional).
    r and g are nominal rates (ratios), aligned yearly.
    """
    idx = r.index.intersection(g.index)
    idx = idx.intersection(pb.index)
    if sfa is not None:
        idx = idx.intersection(sfa.index)
    r = r.reindex(idx).fillna(method="ffill")
    g = g.reindex(idx).fillna(method="ffill")
    pb = pb.reindex(idx).fillna(0.0)
    if sfa is not None:
        sfa = sfa.reindex(idx).fillna(0.0)
    else:
        sfa = pd.Series(0.0, index=idx)
    b = pd.Series(np.nan, index=idx, dtype=float)
    prev = b0
    for t in idx:
        rr = r.loc[t]
        gg = g.loc[t]
        pb_t = pb.loc[t]
        sfa_t = sfa.loc[t]
        prev = ((1.0 + rr) / (1.0 + gg)) * prev - pb_t + sfa_t
        b.loc[t] = prev
    b.name = "debt_ratio"
    return b

def stabilize_primary_balance(b: pd.Series, r: pd.Series, g: pd.Series) -> pd.Series:
    """
    Debt-stabilizing primary balance (ratio):
    pb* = ((r - g) / (1 + g)) * b
    """
    idx = b.index.intersection(r.index).intersection(g.index)
    b = b.reindex(idx)
    r = r.reindex(idx)
    g = g.reindex(idx)
    pb_star = ((r - g) / (1.0 + g)) * b
    pb_star.name = "pb_stabilizing"
    return pb_star

def fiscal_gap(pb: pd.Series, pb_star: pd.Series) -> pd.Series:
    """
    Fiscal gap = pb - pb_star (positive implies overperformance relative to stabilization requirement).
    """
    idx = pb.index.intersection(pb_star.index)
    gap = (pb.reindex(idx) - pb_star.reindex(idx)).rename("fiscal_gap")
    return gap

def gfn_from_deficit_and_maturity(
    b: pd.Series, gdp: pd.Series, deficit: pd.Series, avg_maturity_years: Optional[pd.Series] = None
) -> pd.Series:
    """
    Gross Financing Needs (bn) approx = deficit (bn) + amortization (bn).
    Amortization approximated by debt stock / avg maturity (years).
    If avg_maturity_years missing, assume 10 years.
    """
    idx = b.index.intersection(gdp.index).intersection(deficit.index)
    b = b.reindex(idx)
    gdp = gdp.reindex(idx)
    deficit = deficit.reindex(idx)
    if avg_maturity_years is not None and not avg_maturity_years.empty:
        m = avg_maturity_years.reindex(idx).fillna(method="ffill").fillna(10.0)
    else:
        m = pd.Series(10.0, index=idx)
    debt_bn = b * gdp
    amort_bn = debt_bn / m
    gfn = (deficit + amort_bn).rename("gfn_bn")
    return gfn

def interest_to_gdp(debt_interest_bn: pd.Series, gdp_bn: pd.Series) -> pd.Series:
    idx = debt_interest_bn.index.intersection(gdp_bn.index)
    itg = (debt_interest_bn.reindex(idx) / gdp_bn.reindex(idx)).rename("interest_to_gdp")
    return itg

def stock_flow_adjustment_ratio(psnd: pd.Series, psnb: pd.Series, gdp: pd.Series) -> pd.Series:
    """
    SFA ratio = (ΔDebt - Deficit) / GDP
    """
    idx = psnd.index.intersection(psnb.index).intersection(gdp.index)
    d_debt = psnd.reindex(idx).diff()
    sfa_bn = d_debt - psnb.reindex(idx)
    sfa_ratio = (sfa_bn / gdp.reindex(idx)).rename("sfa_ratio")
    return sfa_ratio

def present_value_of_surpluses(pb_ratio: pd.Series, r: pd.Series, g: pd.Series, horizon: int = 50) -> float:
    """
    Compute present value sum of expected future primary surpluses in ratio terms under expected r,g.
    PV = sum_{t=1..H} [ pb_t / Prod_{s=1..t} (1 + r_s) / (1 + g_s) ]
    For parsimony assume stationary expected r,g at last available values.
    """
    if pb_ratio.empty or r.empty or g.empty:
        return np.nan
    rr = r.iloc[-1]
    gg = g.iloc[-1]
    pb_last = pb_ratio.iloc[-1]
    pv = 0.0
    df = 1.0
    for t in range(1, horizon + 1):
        df *= (1.0 + rr) / (1.0 + gg)
        pv += pb_last / df
    return pv

def debt_stress_response(
    b0: float, r: pd.Series, g: pd.Series, pb: pd.Series, sfa: Optional[pd.Series], shocks: Dict[str, float]
) -> pd.Series:
    """
    Apply deterministic shocks: shocks dict may include:
    - 'r_pp': + in percentage points to r
    - 'g_pp': + to nominal g
    - 'pb_pp': + to primary balance ratio
    - 'sfa_ratio_pp': + to sfa ratio
    """
    r2 = r.copy() + shocks.get("r_pp", 0.0)
    g2 = g.copy() + shocks.get("g_pp", 0.0)
    pb2 = pb.copy() + shocks.get("pb_pp", 0.0)
    sfa2 = None
    if sfa is not None:
        sfa2 = sfa.copy() + shocks.get("sfa_ratio_pp", 0.0)
    return debt_dynamics(b0=b0, r=r2, g=g2, pb=pb2, sfa=sfa2)