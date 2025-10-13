from __future__ import annotations
import io
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from .timeseries import DataManager
from .config import FREQ_TO_PANDAS

def parse_pasted_two_column(text: str) -> pd.Series:
    """
    Parse two-column data pasted from Excel (year or date, value).
    Supports YYYY or YYYY-MM (or dd/mm/YYYY) as first column.
    """
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    rows = []
    for ln in lines:
        # split on tabs or commas or spaces
        parts = [p for p in ln.replace(",", " ").split() if p]
        if len(parts) == 1:
            # Possibly the user pasted a single column of values, not acceptable here.
            # We'll interpret index as a running counter; leave to caller to handle.
            rows.append((None, float(parts[0])))
        else:
            idx = parts[0]
            val = parts[1]
            try:
                v = float(val)
            except Exception:
                # Try second column that might be separated differently
                try:
                    v = float(parts[-1])
                except Exception:
                    continue
            rows.append((idx, v))
    # Build Series
    if not rows:
        return pd.Series(dtype=float)
    idx_raw = [r[0] for r in rows]
    vals = [r[1] for r in rows]
    s = pd.Series(vals, index=idx_raw, dtype=float)
    return s

def parse_one_column_values(text: str, index: List) -> pd.Series:
    """
    Parse a single column pasted values and use provided index to align.
    """
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    vals = []
    for ln in lines:
        # Accept comma separated
        parts = [p for p in ln.replace(",", " ").split() if p]
        for p in parts:
            try:
                vals.append(float(p))
            except:
                pass
    if len(vals) != len(index):
        raise ValueError(f"Expected {len(index)} values, got {len(vals)}.")
    s = pd.Series(vals, index=index, dtype=float)
    return s

def guess_frequency_from_series(s: pd.Series) -> Optional[str]:
    if s.empty:
        return None
    # try to parse as dates
    try:
        # Accept YYYY or YYYY-MM or dates
        idx_try = pd.to_datetime(s.index, errors="coerce", format="%Y-%m")
        if idx_try.notna().sum() >= max(1, int(0.7 * len(s))):
            return "monthly"
    except Exception:
        pass
    try:
        idx_try = pd.to_datetime(s.index, errors="coerce", format="%Y")
        if idx_try.notna().sum() >= max(1, int(0.7 * len(s))):
            return "yearly"
    except Exception:
        pass
    # Fallback: infer by length
    if len(s) > 80:
        return "monthly"
    if len(s) > 20:
        return "quarterly"
    return "yearly"

def read_csv_uploaded(file_bytes, index_col: int = 0, value_col: int = 1) -> pd.Series:
    df = pd.read_csv(io.BytesIO(file_bytes))
    idx = df.iloc[:, index_col]
    vals = df.iloc[:, value_col]
    s = pd.Series(vals.values, index=idx.values, dtype=float)
    return s

def read_excel_uploaded(file_bytes, sheet_name=0, index_col=0, value_col=1) -> pd.Series:
    df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name)
    idx = df.iloc[:, index_col]
    vals = df.iloc[:, value_col]
    s = pd.Series(vals.values, index=idx.values, dtype=float)
    return s

def normalize_index_to_freq(s: pd.Series, target_freq: str) -> pd.Series:
    """
    Convert free-form index to PeriodIndex of target frequency.
    """
    if s.empty:
        return s
    try:
        dt = pd.to_datetime(s.index.astype(str), errors="coerce")
        p = dt.to_period(FREQ_TO_PANDAS[target_freq])
        s.index = p
        return s
    except Exception:
        # Try parse year-only ints/strings
        try:
            years = [int(str(x)[:4]) for x in s.index]
            p = pd.PeriodIndex([pd.Period(str(y), freq="Y") for y in years])
            s.index = p
            if target_freq != "yearly":
                # upsample with ffill
                s = s.to_timestamp().resample({"monthly": "MS", "quarterly": "QS"}[target_freq]).ffill().to_period({"monthly": "M", "quarterly": "Q"}[target_freq])
            return s
        except Exception:
            return s

def load_obr_csv(file_bytes) -> pd.DataFrame:
    """
    Load an OBR mapping CSV the user provides and return a tidy DataFrame.
    The expected format can vary; we accept wide format and melt if needed.
    """
    df = pd.read_csv(io.BytesIO(file_bytes))
    # If appears tidy, return
    return df

def paste_matrix_to_series(paste: str, index_labels: List[str]) -> pd.Series:
    """
    Allow Excel-like pasting of a column into a pre-defined index labels list.
    """
    # Flatten values in row-major from paste
    tokens = []
    for ln in paste.splitlines():
        parts = [p for p in ln.split("\t") if p != ""]
        if not parts:
            parts = [p for p in ln.replace(",", " ").split() if p]
        for p in parts:
            try:
                tokens.append(float(p))
            except:
                pass
    if len(tokens) != len(index_labels):
        raise ValueError(f"Expected {len(index_labels)} numbers, got {len(tokens)}")
    return pd.Series(tokens, index=index_labels, dtype=float)