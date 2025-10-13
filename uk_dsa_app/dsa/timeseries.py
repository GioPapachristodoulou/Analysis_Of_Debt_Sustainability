from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from .config import SUPPORTED_FREQS, FREQ_TO_PANDAS

def _to_period_index(series: pd.Series, freq: str) -> pd.Series:
    target = FREQ_TO_PANDAS[freq]
    if isinstance(series.index, pd.PeriodIndex):
        # If different granularity, convert via timestamp then back to Period with target code
        if series.index.freqstr != target:
            st = series.to_timestamp(how="start")
            if target == "Y":
                return st.resample("YS").mean().to_period("Y")
            if target == "Q":
                return st.resample("QS").mean().to_period("Q")
            if target == "M":
                return st.resample("MS").mean().to_period("M")
        return series
    # If index is int years
    if np.issubdtype(series.index.dtype, np.integer):
        if freq == "yearly":
            s = pd.Series(series.values, index=[pd.Period(year=int(y), freq="Y") for y in series.index])
            return s
        elif freq == "quarterly":
            # Without quarter info, map to period at Q4 of each year to preserve order
            s = pd.Series(series.values, index=[pd.Period(f"{int(y)}Q4", freq="Q") for y in series.index])
            return s
        elif freq == "monthly":
            # Map year-only to December of each year
            s = pd.Series(series.values, index=[pd.Period(f"{int(y)}-12", freq="M") for y in series.index])
            return s
    # If index looks like YYYY or YYYY-MM
    try:
        # Accept strings like YYYY, YYYY-MM, YYYY-MM-DD, or YYYYQx
        if target == "Q":
            # Allow forms like 2020Q1 or 2020-Q1
            idx = [str(x).replace("-Q", "Q") for x in series.index]
            dt = pd.PeriodIndex(idx, freq="Q")
        elif target == "M":
            dt = pd.PeriodIndex(series.index, freq="M")
        else:
            dt = pd.PeriodIndex(series.index, freq="Y")
        return pd.Series(series.values, index=dt)
    except Exception:
        pass
    # Try to parse to DatetimeIndex, then to PeriodIndex
    try:
        dt = pd.to_datetime(series.index, errors="coerce")
        if dt.isna().any():
            raise ValueError("Could not parse index to datetime.")
        p = dt.to_period(target)
        return pd.Series(series.values, index=p)
    except Exception:
        return series

def infer_freq_from_index(idx) -> Optional[str]:
    if isinstance(idx, pd.PeriodIndex):
        inv = {v: k for k, v in FREQ_TO_PANDAS.items()}
        return inv.get(idx.freqstr)
    if isinstance(idx, pd.DatetimeIndex):
        # infer freq
        try:
            f = pd.infer_freq(idx)
            if f and f.startswith("A"):
                return "yearly"
            if f and f.startswith("Q"):
                return "quarterly"
            if f and f.startswith("M"):
                return "monthly"
        except Exception:
            return None
    return None

@dataclass
class SeriesContainer:
    series: Dict[str, pd.Series] = field(default_factory=dict)
    meta: Dict[str, Dict] = field(default_factory=dict)  # id -> {unit, freq}

    def add(self, metric_id: str, s: pd.Series, unit: str, freq: str):
        if freq not in FREQ_TO_PANDAS:
            raise ValueError(f"Unsupported frequency: {freq}")
        s = _to_period_index(s, freq)
        self.series[metric_id] = s.sort_index()
        self.meta[metric_id] = {"unit": unit, "freq": freq}

    def get(self, metric_id: str) -> pd.Series:
        return self.series.get(metric_id, pd.Series(dtype=float))

    def get_meta(self, metric_id: str) -> Dict:
        return self.meta.get(metric_id, {})

    def available_years(self, metric_id: str) -> Tuple[Optional[int], Optional[int]]:
        s = self.get(metric_id)
        if s.empty:
            return None, None
        idx = s.index
        if isinstance(idx, pd.PeriodIndex):
            try:
                y0 = idx.min().start_time.year
                y1 = idx.max().start_time.year
                return y0, y1
            except Exception:
                return None, None
        return None, None

    def resample(self, metric_id: str, target_freq: str, how: str = "mean") -> pd.Series:
        s = self.get(metric_id)
        if s.empty:
            return s
        src_meta = self.get_meta(metric_id)
        src_freq = src_meta.get("freq", "yearly")
        s = _to_period_index(s, src_freq)
        if src_freq == target_freq:
            return s
        # Upsample or downsample
        if target_freq == "yearly":
            # downsample monthly/quarterly to yearly
            if how == "sum":
                return s.to_timestamp().resample("YS").sum().to_period("Y")
            return s.to_timestamp().resample("YS").mean().to_period("Y")
        elif target_freq == "quarterly":
            if src_freq == "monthly":
                if how == "sum":
                    return s.to_timestamp().resample("QS").sum().to_period("Q")
                return s.to_timestamp().resample("QS").mean().to_period("Q")
            elif src_freq == "yearly":
                # upsample to quarterly: forward fill within year
                t = s.to_timestamp().resample("QS").ffill().to_period("Q")
                return t
        elif target_freq == "monthly":
            if src_freq == "quarterly":
                return s.to_timestamp().resample("MS").ffill().to_period("M")
            elif src_freq == "yearly":
                return s.to_timestamp().resample("MS").ffill().to_period("M")
        return s

    def align(self, metric_ids: List[str], target_freq: str, how: str = "intersection") -> List[pd.Series]:
        rs = [self.resample(mid, target_freq) for mid in metric_ids]
        if not rs:
            return rs
        if how == "intersection":
            idx = rs[0].index
            for s in rs[1:]:
                idx = idx.intersection(s.index)
            rs = [s.reindex(idx) for s in rs]
        elif how == "union":
            idx = rs[0].index
            for s in rs[1:]:
                idx = idx.union(s.index)
            rs = [s.reindex(idx) for s in rs]
        return rs

class DataManager:
    """
    Handles all metric time series storage, frequency management, resampling,
    derived metric computation, dependency-based frequency enforcement, and coverage checks.
    """
    def __init__(self, metrics_def):
        self.metrics_def = metrics_def
        self.sc = SeriesContainer()
        self.user_freq_choices: Dict[str, str] = {}  # user-chosen data entry freq per metric

    def set_user_freq(self, metric_id: str, freq: str):
        if metric_id not in self.metrics_def:
            raise KeyError(metric_id)
        m = self.metrics_def[metric_id]
        if not m.user_selectable_frequency:
            self.user_freq_choices[metric_id] = m.default_freq
            return
        if freq not in m.allowed_freqs:
            raise ValueError(f"Frequency {freq} not allowed for metric {metric_id}")
        self.user_freq_choices[metric_id] = freq

    def get_user_freq(self, metric_id: str) -> str:
        if metric_id in self.user_freq_choices:
            return self.user_freq_choices[metric_id]
        return self.metrics_def[metric_id].default_freq

    def add_series(self, metric_id: str, s: pd.Series, unit: str, freq: Optional[str] = None):
        if metric_id not in self.metrics_def:
            raise KeyError(metric_id)
        if freq is None:
            freq = self.get_user_freq(metric_id)
        self.sc.add(metric_id, s, unit, freq)

    def get_series(self, metric_id: str) -> pd.Series:
        s = self.sc.get(metric_id)
        if s.empty and self.metrics_def[metric_id].derived and self.metrics_def[metric_id].compute_fn:
            # compute derived
            computed = self.metrics_def[metric_id].compute_fn(self)
            # Assume derived series are yearly for simplicity; set meta
            self.sc.add(metric_id, computed, self.metrics_def[metric_id].unit, self.metrics_def[metric_id].default_freq)
            s = self.sc.get(metric_id)
        return s

    def align_series(self, series_list: List[pd.Series], target_freq: str, how: str = "intersection") -> List[pd.Series]:
        # Convert unknown freq to pandas index fallback
        rs = []
        for s in series_list:
            if isinstance(s.index, pd.PeriodIndex):
                # convert via timestamp resample to avoid anchor issues
                st = s.to_timestamp(how="start")
                if target_freq == "yearly":
                    rs.append(st.resample("YS").mean().to_period("Y"))
                elif target_freq == "quarterly":
                    rs.append(st.resample("QS").mean().to_period("Q"))
                else:
                    rs.append(st.resample("MS").mean().to_period("M"))
            else:
                # try convert
                s2 = s.copy()
                try:
                    idx = pd.to_datetime(s2.index.astype(str))
                    p = pd.PeriodIndex(idx, freq=FREQ_TO_PANDAS[target_freq])
                    s2.index = p
                except Exception:
                    pass
                rs.append(s2)
        if not rs:
            return rs
        if how == "intersection":
            idx = rs[0].index
            for s in rs[1:]:
                idx = idx.intersection(s.index)
            return [s.reindex(idx) for s in rs]
        elif how == "union":
            idx = rs[0].index
            for s in rs[1:]:
                idx = idx.union(s.index)
            return [s.reindex(idx) for s in rs]
        return rs

    def resample_series(self, s: pd.Series, target_freq: str, how: str = "mean") -> pd.Series:
        # Use the container's helper by temporarily adding s?
        # Simpler: direct resample by period to timestamp then resample back
        if s.empty:
            return s
        if isinstance(s.index, pd.PeriodIndex) and s.index.freqstr == FREQ_TO_PANDAS[target_freq]:
            return s
        try:
            st = s.to_timestamp()
            if target_freq == "yearly":
                if how == "sum":
                    return st.resample("YS").sum().to_period("Y")
                return st.resample("YS").mean().to_period("Y")
            if target_freq == "quarterly":
                if how == "sum":
                    return st.resample("QS").sum().to_period("Q")
                return st.resample("QS").mean().to_period("Q")
            if target_freq == "monthly":
                if how == "sum":
                    return st.resample("MS").sum().to_period("M")
                return st.resample("MS").mean().to_period("M")
        except Exception:
            return s
        return s

    def coverage_years(self, metric_ids: List[str], target_freq: str) -> Tuple[Optional[int], Optional[int]]:
        series = [self.resample(m, target_freq) for m in metric_ids for _ in [0]]
        series = [self.sc.get(m) for m in metric_ids]
        # compute intersection of coverage
        min_year = None
        max_year = None
        for mid in metric_ids:
            y0, y1 = self.sc.available_years(mid)
            if y0 is None:
                continue
            if min_year is None or y0 > min_year:
                min_year = y0
            if max_year is None or y1 < max_year:
                max_year = y1
        return min_year, max_year

    def enforce_frequency_dependencies(self, rules):
        changes = {}
        for metric_id, chosen in self.user_freq_choices.items():
            for (m, f, forced) in rules:
                if metric_id == m and chosen == f:
                    for dep_m, dep_freq in forced.items():
                        # respect allowed freqs
                        allowed = self.metrics_def[dep_m].allowed_freqs
                        if dep_freq in allowed:
                            # Only upgrade frequency granularity if needed (monthly > quarterly > yearly)
                            # We'll set if currently lower granularity.
                            cur = self.get_user_freq(dep_m)
                            rank = {"monthly": 3, "quarterly": 2, "yearly": 1}
                            if rank[dep_freq] > rank[cur]:
                                self.user_freq_choices[dep_m] = dep_freq
                                changes[dep_m] = dep_freq
        return changes

    def missing_required(self) -> List[str]:
        missing = []
        for mid, m in self.metrics_def.items():
            if m.required and self.sc.get(mid).empty:
                missing.append(mid)
        return missing

    def available_metrics(self) -> List[str]:
        return list(self.sc.series.keys())