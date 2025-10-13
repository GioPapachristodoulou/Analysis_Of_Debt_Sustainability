from __future__ import annotations
from typing import Dict, List, Optional
import base64
import io
import pandas as pd

def _fig_to_png_bytes(fig) -> bytes:
    try:
        return fig.to_image(format="png", scale=2)
    except Exception:
        # fallback via orca not installed; fallback using static image is not always available
        # If not available, return empty bytes
        return b""

def build_html_report(
    title: str,
    summary: Dict[str, str],
    figures: List[Dict],
    tables: List[pd.DataFrame],
    credits: str,
    logo_svg_path: Optional[str] = None,
) -> str:
    # Build a minimally styled HTML
    styles = """
    <style>
      body { font-family: Inter, Arial, Helvetica, sans-serif; color: #111827; }
      .container { max-width: 960px; margin: 0 auto; padding: 20px; }
      h1,h2,h3 { letter-spacing: 0.2px; }
      .section { margin: 24px 0; }
      .kpi { border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; background: #fff; margin-bottom: 16px; }
      .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
      img.plot { max-width: 100%; height: auto; border: 1px solid #e5e7eb; border-radius: 8px; }
      table { border-collapse: collapse; width: 100%; }
      th, td { border: 1px solid #e5e7eb; padding: 6px 8px; text-align: right; }
      th { background: #f9fafb; text-align: left; }
      .footer { color: #6b7280; font-size: 0.9rem; margin-top: 24px; }
      .logo { height: 48px; }
    </style>
    """
    logo_html = ""
    if logo_svg_path:
        try:
            with open(logo_svg_path, "r", encoding="utf-8") as f:
                svg = f.read()
            logo_html = f'<div><div style="max-width:300px;">{svg}</div></div>'
        except Exception:
            logo_html = ""
    ht = [f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title>{styles}</head><body><div class='container'>"]
    if logo_html:
        ht.append(logo_html)
    ht.append(f"<h1>{title}</h1>")
    ht.append("<div class='section'><div class='grid'>")
    for k, v in summary.items():
        ht.append(f"<div class='kpi'><strong>{k}</strong><div>{v}</div></div>")
    ht.append("</div></div>")
    # Figures
    for fig in figures:
        cap = fig.get("caption", "")
        png = fig.get("png_bytes", b"")
        if png:
            b64 = base64.b64encode(png).decode("utf-8")
            ht.append(f"<div class='section'><img class='plot' src='data:image/png;base64,{b64}' alt='{cap}'/><div class='footer'>{cap}</div></div>")
    # Tables
    for df in tables:
        ht.append("<div class='section'>")
        ht.append(df.to_html(index=True, border=0, justify="center"))
        ht.append("</div>")
    # Credits
    ht.append(f"<div class='footer'>{credits}</div>")
    ht.append("</div></body></html>")
    return "".join(ht)

def html_download_bytes(html_str: str) -> bytes:
    return html_str.encode("utf-8")