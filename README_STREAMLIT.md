# UK Debt Sustainability Analysis - Deployment Guide

## Current Issue with Streamlit Cloud
Streamlit Cloud is persisting an old cached version despite:
- Multiple reboots and cache clears
- Deleting and recreating the app
- Forcing fresh commits with config changes

## Recommended Solution: Hugging Face Spaces

Hugging Face Spaces is more reliable and always deploys from the latest commit.

### Quick Deploy to Hugging Face Spaces

1. Go to https://huggingface.co/new-space
2. Fill in:
   - **Space name**: `debt-sustainability-analysis`
   - **SDK**: Streamlit
   - **Visibility**: Public
3. Click "Create Space"
4. In the Space's "Files" tab, create these files:

#### app.py (root)
```python
import sys
sys.path.insert(0, 'uk_dsa_app')
from uk_dsa_app.app import main
if __name__ == "__main__":
    main()
```

#### requirements.txt (root)
```
streamlit>=1.38,<2
numpy>=2.1,<3
pandas>=2.2.3,<3
scipy>=1.14.1,<2
statsmodels>=0.14.3,<0.15
plotly>=5.22,<6
kaleido>=0.2,<0.3
pydantic>=2.8,<3
pydantic-settings>=2.4,<3
PyYAML>=6.0,<7
jinja2>=3.1,<4
openpyxl>=3.1,<4
xlrd>=2.0,<3
python-dateutil>=2.8,<3
pillow>=10.3,<11
```

#### .streamlit/config.toml
```toml
[server]
headless = true
enableCORS = false

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#2563eb"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f3f4f6"
textColor = "#111827"
```

5. Upload your entire `uk_dsa_app/` folder to the Space
6. The Space will auto-build and give you a public URL like:
   `https://huggingface.co/spaces/YOUR_USERNAME/debt-sustainability-analysis`

### Or: Link Your GitHub Repo Directly

Even easier—in the Space settings:
1. Enable "Connect to GitHub"
2. Link to: `GioPapachristodoulou/Analysis_Of_Debt_Sustainability`
3. Set entry point to: `uk_dsa_app/app.py`

HF Spaces will automatically pull the latest commit and rebuild on every push.

## Alternative: Deploy with Docker

If you prefer full control, I can create a Dockerfile that bundles everything.

## Current Deployment Status

- **Streamlit Cloud**: Stuck on old version (commit unknown)
- **Latest Commit**: b3450b4
- **Recommended**: Migrate to Hugging Face Spaces

Contact: Issues or questions? Open a GitHub issue on the repo.
