from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple
from .config import SUPPORTED_FREQS

@dataclass
class Metric:
    id: str
    display_name: str
    description: str
    allowed_freqs: List[str]
    default_freq: str
    unit: str
    required: bool = True
    depends_on: List[str] = field(default_factory=list)
    derived: bool = False
    # If derived, provide a function signature: f(data_manager) -> pandas.Series
    compute_fn: Optional[Callable] = None
    # Whether users can choose frequency for data entry; if False, enforced frequency
    user_selectable_frequency: bool = True
    # If monthly not supported, set allowed_freqs accordingly

def all_metrics_definition() -> Dict[str, Metric]:
    """
    Define raw and derived metrics necessary for UK DSA.
    """
    metrics: Dict[str, Metric] = {}

    metrics["gdp_nominal"] = Metric(
        id="gdp_nominal",
        display_name="Nominal GDP",
        description="Nominal GDP in current prices.",
        allowed_freqs=["quarterly", "yearly"],
        default_freq="yearly",
        unit="bn_gbp",
        required=True,
    )
    metrics["psnd_ex"] = Metric(
        id="psnd_ex",
        display_name="PSND ex BoE (level)",
        description="Public Sector Net Debt excluding Bank of England (level).",
        allowed_freqs=["monthly", "quarterly", "yearly"],
        default_freq="yearly",
        unit="bn_gbp",
        required=True,
    )
    metrics["psnb_ex"] = Metric(
        id="psnb_ex",
        display_name="PSNB ex (net borrowing)",
        description="Public Sector Net Borrowing excluding Bank of England.",
        allowed_freqs=["quarterly", "yearly"],
        default_freq="yearly",
        unit="bn_gbp",
        required=True,
    )
    metrics["debt_interest"] = Metric(
        id="debt_interest",
        display_name="Debt Interest (net)",
        description="Public sector net debt interest payments.",
        allowed_freqs=["quarterly", "yearly"],
        default_freq="yearly",
        unit="bn_gbp",
        required=True,
    )
    metrics["gdp_deflator"] = Metric(
        id="gdp_deflator",
        display_name="GDP Deflator (Index)",
        description="GDP deflator index.",
        allowed_freqs=["quarterly", "yearly"],
        default_freq="yearly",
        unit="index_2019_100",
        required=False,
    )
    metrics["cpi"] = Metric(
        id="cpi",
        display_name="CPI (Index)",
        description="Consumer Price Index (CPI) or CPIH index.",
        allowed_freqs=["monthly", "yearly"],
        default_freq="monthly",
        unit="index_2015_100",
        required=False,
    )
    metrics["yield_10y"] = Metric(
        id="yield_10y",
        display_name="10y Gilt Yield",
        description="Nominal 10-year UK gilt yield.",
        allowed_freqs=["monthly", "quarterly", "yearly"],
        default_freq="yearly",
        unit="pct",
        required=False,
    )
    metrics["avg_maturity_years"] = Metric(
        id="avg_maturity_years",
        display_name="Average Maturity (years)",
        description="Average maturity of public debt.",
        allowed_freqs=["yearly"],
        default_freq="yearly",
        unit="years",
        required=False,
        user_selectable_frequency=False,
    )

    # Derived metric: primary_balance = -(psnb_ex) + debt_interest (sign convention)
    # If PSNB is positive (deficit), primary balance is deficit + interest -> negative primary balance
    # Define pb so that positive pb reduces debt/GDP
    def compute_primary_balance(dm):
        import pandas as pd
        psnb = dm.get_series("psnb_ex")  # bn
        di = dm.get_series("debt_interest")  # bn
        # Primary balance (bn): PB = -PSNB - Interest? Let's carefully define:
        # PSNB = Primary Deficit + Interest + Net Investment adjustments; for consistency we assume:
        # Primary balance approximate = - (PSNB - Interest)
        # Positive PB reduces debt.
        pb = -(psnb - di)
        pb.name = "primary_balance"
        return pb

    metrics["primary_balance"] = Metric(
        id="primary_balance",
        display_name="Primary Balance (derived)",
        description="Primary balance computed as -(PSNB - debt interest). Positive value reduces debt.",
        allowed_freqs=["quarterly", "yearly"],
        default_freq="yearly",
        unit="bn_gbp",
        required=False,
        depends_on=["psnb_ex", "debt_interest"],
        derived=True,
        compute_fn=compute_primary_balance,
        user_selectable_frequency=False,
    )

    # Derived metric: debt ratio b = PSND / GDP
    def compute_debt_ratio(dm):
        psnd = dm.get_series("psnd_ex")
        gdp = dm.get_series("gdp_nominal")
        aligned = dm.align_series([psnd, gdp], target_freq="yearly", how="intersection")
        psnd_al, gdp_al = aligned[0], aligned[1]
        b = (psnd_al / gdp_al).rename("debt_ratio")
        return b

    metrics["debt_ratio"] = Metric(
        id="debt_ratio",
        display_name="Debt-to-GDP Ratio (derived)",
        description="PSND ex BoE as a share of nominal GDP.",
        allowed_freqs=["yearly"],
        default_freq="yearly",
        unit="ratio",
        required=False,
        depends_on=["psnd_ex", "gdp_nominal"],
        derived=True,
        compute_fn=compute_debt_ratio,
        user_selectable_frequency=False,
    )

    # Derived: effective interest rate r = interest / avg debt stock
    def compute_effective_rate(dm):
        import pandas as pd
        psnd = dm.get_series("psnd_ex")
        di = dm.get_series("debt_interest")
        psnd_y, di_y = dm.align_series([psnd, di], target_freq="yearly", how="intersection")
        avg_debt = (psnd_y.shift(1) + psnd_y) / 2.0
        r = (di_y / avg_debt).rename("effective_r")
        return r

    metrics["effective_r"] = Metric(
        id="effective_r",
        display_name="Effective Interest Rate (derived)",
        description="Debt interest divided by average debt stock.",
        allowed_freqs=["yearly"],
        default_freq="yearly",
        unit="ratio",
        required=False,
        depends_on=["psnd_ex", "debt_interest"],
        derived=True,
        compute_fn=compute_effective_rate,
        user_selectable_frequency=False,
    )

    # Derived: nominal GDP growth g
    def compute_nominal_g(dm):
        gdp = dm.get_series("gdp_nominal")
        g_y = dm.resample_series(gdp, target_freq="yearly")
        g = (g_y.pct_change()).rename("nominal_g")
        return g

    metrics["nominal_g"] = Metric(
        id="nominal_g",
        display_name="Nominal GDP Growth (derived)",
        description="Nominal GDP growth rate.",
        allowed_freqs=["yearly"],
        default_freq="yearly",
        unit="ratio",
        required=False,
        depends_on=["gdp_nominal"],
        derived=True,
        compute_fn=compute_nominal_g,
        user_selectable_frequency=False,
    )

    return metrics