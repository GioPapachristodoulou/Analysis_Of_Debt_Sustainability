import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from pathlib import Path

APP_NAME = "UK Debt Sustainability Analysis"
APP_VERSION = "0.1.0"
APP_AUTHOR = "Imperial College Business School UROP Team"
DEFAULT_CURRENCY = "GBP"
DEFAULT_UNIT = "bn_gbp"

DEFAULT_START_YEAR = 1970
DEFAULT_END_YEAR = 2035

SUPPORTED_FREQS = ("monthly", "quarterly", "yearly")
# For PeriodIndex operations use Period-compatible codes (M, Q, Y).
# Resampling operations explicitly specify MS/QS/YS where needed.
FREQ_TO_PANDAS = {
    "monthly": "M",
    "quarterly": "Q",
    "yearly": "Y",
}

# Units known by the app
UNITS = {
    "bn_gbp": {"label": "£ billions", "scale": 1.0},
    "pct": {"label": "%", "scale": 1.0},
    "ratio": {"label": "ratio", "scale": 1.0},
    "index_2019_100": {"label": "Index (2019=100)", "scale": 1.0},
    "index_2015_100": {"label": "Index (2015=100)", "scale": 1.0},
    "years": {"label": "years", "scale": 1.0},
}

THEME = {
    "primary_color": "#2563eb",
    "bg_color": "#ffffff",
    "text_color": "#111827",
    "muted_text": "#6b7280",
    "grid_color": "#e5e7eb",
    "accent_color": "#1e40af",
}

@dataclass
class MonteCarloDefaults:
    n_paths: int = 5000
    horizon_years: int = 10
    seed: int = 42
    # Default shocks configuration
    var_rho: float = 0.6
    var_sigma_g: float = 0.02
    var_sigma_r: float = 0.015
    var_sigma_pb: float = 0.01
    corr_rg: float = 0.4
    corr_rpb: float = 0.2
    corr_gpb: float = -0.3

MC_DEFAULTS = MonteCarloDefaults()

# Legal text references
OGL_ATTRIBUTION = "Contains public sector information licensed under the Open Government Licence v3.0."
DISCLAIMER_HEADER = "Important: Research and Educational Use Only"
DISCLAIMER_TEXT = (
    "This application and its outputs are provided for research and educational purposes only. "
    "They do not constitute investment advice, professional advice, or a recommendation. "
    "No warranty of accuracy, completeness, or fitness for a particular purpose is provided. "
    "Use at your own risk."
)
TERMS_TEXT = (
    "By using this application, you agree not to rely on the outputs for investment decisions. "
    "You accept that the authors and affiliated institutions bear no liability for any damages arising from the use of this application."
)
PRIVACY_TEXT = (
    "The app does not collect personal information. Uploaded data remains in your session memory only and is not stored on the server."
)

DEVELOPER_CREDIT = (
    "Developed by: Mr. Giorgos Papachristodoulou (quantitative analysis and software development), "
    "Mrs. Aaisha Keshari (financial analysis), and supervised by Prof. Alex Michaelides. Project completed October 2025."
)

# Frequencies dependencies rules (example)
# If 'psnd_ex' is monthly -> force 'debt_interest' at least quarterly or yearly? We'll enforce min monthly for psnb_ex and debt_interest to keep consistency in flows.
FREQ_DEPENDENCY_RULES = [
    # (metric, chosen_freq, forced_changes)
    # e.g., if CPI monthly -> GDP deflator at least quarterly
    ("cpi", "monthly", {"gdp_deflator": "quarterly"}),
    # if gdp_nominal is quarterly -> psnb_ex and debt_interest must be at least quarterly to compute primary balance consistently
    ("gdp_nominal", "quarterly", {"psnb_ex": "quarterly", "debt_interest": "quarterly"}),
    # if psnd_ex monthly -> allow fine-grained SFA; suggest debt_interest quarterly
    ("psnd_ex", "monthly", {"debt_interest": "quarterly"}),
]

# Resolve project base (uk_dsa_app/) relative to this file (uk_dsa_app/dsa/config.py)
_BASE_DIR = Path(__file__).resolve().parent.parent
# Optional logo: hide via env var or when file missing
_logo_candidate = (_BASE_DIR / "assets" / "imperial_logo_placeholder.svg").resolve()
_hide_logo = os.getenv("DSA_HIDE_LOGO", "").lower() in {"1", "true", "yes", "on"}
IMPERIAL_LOGO_PATH: Optional[str] = None if _hide_logo or not _logo_candidate.exists() else str(_logo_candidate)
STYLE_CSS_PATH = str((_BASE_DIR / "assets" / "styles.css").resolve())

DEFAULT_HORIZON = 2035