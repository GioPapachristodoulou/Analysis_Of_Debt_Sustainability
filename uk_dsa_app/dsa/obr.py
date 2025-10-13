from __future__ import annotations
from typing import Dict, List, Optional
import pandas as pd

def tidy_obr_projection(df: pd.DataFrame, year_col: Optional[str] = None) -> pd.DataFrame:
    """
    Try to coerce an OBR-like projection DataFrame into tidy form with columns:
    metric_id, year, value
    """
    df = df.copy()
    if year_col and year_col in df.columns:
        # assume wide columns with metric names
        metrics = [c for c in df.columns if c != year_col]
        rows = []
        for _, row in df.iterrows():
            y = row[year_col]
            for m in metrics:
                try:
                    val = float(row[m])
                except Exception:
                    continue
                rows.append({"metric_id": m, "year": int(y), "value": val})
        return pd.DataFrame(rows)
    # else if tidy already
    # Expect columns: obr_series_name, app_metric_id, year, value
    return df