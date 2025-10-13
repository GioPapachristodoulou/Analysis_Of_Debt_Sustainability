from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Optional, Tuple
from .config import THEME

def line_chart(series_dict: Dict[str, pd.Series], title: str, yaxis_title: str, legend: bool = True) -> go.Figure:
    fig = go.Figure()
    colors = ["#2563eb", "#111827", "#f59e0b", "#10b981", "#ef4444", "#6b7280", "#8b5cf6"]
    for i, (label, s) in enumerate(series_dict.items()):
        if s is None or s.empty:
            continue
        x = s.index.to_timestamp()
        fig.add_trace(go.Scatter(
            x=x, y=s.values, mode="lines", name=label, line=dict(color=colors[i % len(colors)], width=2)
        ))
    fig.update_layout(
        title=title,
        showlegend=legend,
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=40),
        xaxis=dict(showgrid=True, gridcolor="#e5e7eb"),
        yaxis=dict(title=yaxis_title, showgrid=True, gridcolor="#e5e7eb"),
        font=dict(family="Inter, Arial, Helvetica, sans-serif")
    )
    return fig

def fan_chart(percentile_series: Dict[str, pd.DataFrame], title: str, yaxis_title: str) -> go.Figure:
    """
    percentile_series keys should be labels; values are DataFrame with columns as percentiles (e.g. 5, 10, 25, 50, 75, 90, 95).
    """
    colors = {
        "p95": "#c7d2fe",
        "p90": "#a5b4fc",
        "p75": "#818cf8",
        "p50": "#6366f1",
        "median": "#1f2937",
    }
    # Use only one label for fan; if multiple labels, overlay bands
    fig = go.Figure()
    for label, dfp in percentile_series.items():
        x = dfp.index.to_timestamp()
        if "5" in dfp.columns and "95" in dfp.columns:
            fig.add_traces([
                go.Scatter(x=x, y=dfp["95"], line=dict(color="rgba(99,102,241,0)"), showlegend=False, hoverinfo="skip"),
                go.Scatter(x=x, y=dfp["5"], fill="tonexty", line=dict(color="rgba(99,102,241,0)"), fillcolor=colors["p95"], name=f"{label} 90% band"),
            ])
        if "10" in dfp.columns and "90" in dfp.columns:
            fig.add_traces([
                go.Scatter(x=x, y=dfp["90"], line=dict(color="rgba(99,102,241,0)"), showlegend=False, hoverinfo="skip"),
                go.Scatter(x=x, y=dfp["10"], fill="tonexty", line=dict(color="rgba(99,102,241,0)"), fillcolor=colors["p90"], name=f"{label} 80% band"),
            ])
        if "25" in dfp.columns and "75" in dfp.columns:
            fig.add_traces([
                go.Scatter(x=x, y=dfp["75"], line=dict(color="rgba(99,102,241,0)"), showlegend=False, hoverinfo="skip"),
                go.Scatter(x=x, y=dfp["25"], fill="tonexty", line=dict(color="rgba(99,102,241,0)"), fillcolor=colors["p75"], name=f"{label} 50% band"),
            ])
        if "50" in dfp.columns:
            fig.add_trace(go.Scatter(x=x, y=dfp["50"], line=dict(color=colors["p50"]), name=f"{label} median"))
    fig.update_layout(
        title=title,
        showlegend=True,
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=40),
        xaxis=dict(showgrid=True, gridcolor="#e5e7eb"),
        yaxis=dict(title=yaxis_title, showgrid=True, gridcolor="#e5e7eb"),
        font=dict(family="Inter, Arial, Helvetica, sans-serif")
    )
    return fig

def waterfall(labels: List[str], values: List[float], title: str, measure: Optional[List[str]] = None) -> go.Figure:
    """
    labels: list of bar labels
    values: list of values
    measure: list with 'relative', 'total' etc. If None, assume all 'relative'
    """
    if measure is None:
        measure = ["relative"] * len(values)
    fig = go.Figure(go.Waterfall(
        name = "Net",
        orientation = "v",
        measure = measure,
        x = labels,
        textposition = "outside",
        text = [f"{v:.2f}" for v in values],
        y = values,
        connector = {"line":{"color":"#e5e7eb"}},
    ))
    fig.update_layout(title=title, showlegend=False, template="plotly_white",
                      margin=dict(l=20, r=20, t=60, b=40),
                      xaxis=dict(showgrid=False),
                      yaxis=dict(showgrid=True, gridcolor="#e5e7eb"))
    return fig