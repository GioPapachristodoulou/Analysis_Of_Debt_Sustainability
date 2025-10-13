from __future__ import annotations
from .config import DISCLAIMER_HEADER, DISCLAIMER_TEXT, TERMS_TEXT, PRIVACY_TEXT, OGL_ATTRIBUTION

def disclaimer_text() -> str:
    return f"{DISCLAIMER_HEADER}\n\n{DISCLAIMER_TEXT}"

def terms_text() -> str:
    return TERMS_TEXT

def privacy_text() -> str:
    return PRIVACY_TEXT

def ogl_attribution_text() -> str:
    return OGL_ATTRIBUTION