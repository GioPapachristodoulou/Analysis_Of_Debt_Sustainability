import numpy as np
import pandas as pd
from dsa.engine.dsa_math import debt_dynamics, stabilize_primary_balance

def test_debt_dynamics_increasing_when_r_gt_g_and_pb_zero():
    idx = pd.period_range(start="2025", periods=5, freq="Y")
    r = pd.Series(0.05, index=idx)
    g = pd.Series(0.02, index=idx)
    pb = pd.Series(0.0, index=idx)
    b = debt_dynamics(b0=1.0, r=r, g=g, pb=pb)
    assert b.iloc[-1] > 1.0

def test_pb_stabilizing_signs():
    idx = pd.period_range(start="2025", periods=3, freq="Y")
    b = pd.Series([0.8, 0.82, 0.83], index=idx)
    r = pd.Series([0.03, 0.03, 0.03], index=idx)
    g = pd.Series([0.02, 0.02, 0.02], index=idx)
    pb_star = stabilize_primary_balance(b, r, g)
    assert (pb_star > 0).all()