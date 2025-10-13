from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class ShockScenario:
    name: str
    desc: str
    r_pp: float = 0.0
    g_pp: float = 0.0
    pb_pp: float = 0.0
    sfa_ratio_pp: float = 0.0

DEFAULT_SCENARIOS = [
    ShockScenario(name="Rate +300bps", desc="Permanent +3pp shock to effective interest rate", r_pp=0.03),
    ShockScenario(name="Growth -1pp", desc="Permanent -1pp shock to nominal GDP growth", g_pp=-0.01),
    ShockScenario(name="Primary -1% GDP", desc="Permanent -1% GDP shock to primary balance", pb_pp=-0.01),
    ShockScenario(name="Inflation surprise (SFA +1% GDP)", desc="Stock-flow adjustment +1% GDP", sfa_ratio_pp=0.01),
    ShockScenario(name="Combined adverse", desc="r +2pp, g -1pp, pb -0.5% GDP", r_pp=0.02, g_pp=-0.01, pb_pp=-0.005),
]