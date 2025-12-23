# ==========================================================
# modules/utils.py
# Global Styling & Utility Functions for Streamlit Dashboards
# ==========================================================

import streamlit as st

# -------------------------------
# Global Color Palette
# -------------------------------
PRIMARY = "#0B1F3A"   # dark navy
SLATE   = "#334155"   # muted gray-blue
MUTED   = "#6B7280"   # soft gray text
SILVER  = "#E5E7EB"   # light border
TEAL    = "#0EA5A4"   # accent teal
GOLD    = "#B08D57"   # executive gold


# -------------------------------
# Global Styling Function
# -------------------------------
def apply_global_style():
    """Inject global CSS & typography for consistent executive styling."""
    css = f"""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif !important;
    }}
    .block-container {{
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1100px;
        margin: auto;
    }}
    h1, h2, h3, h4 {{
        color: {PRIMARY};
        font-weight: 700;
        margin-bottom: 0.5rem;
    }}
    .small-muted {{
        color: {MUTED};
        font-size: 0.9rem;
    }}
    .kpi-card {{
        border: 1px solid {SILVER};
        border-radius: 14px;
        padding: 16px;
        background: #ffffff;
        box-shadow: 0 4px 16px rgba(0,0,0,0.04);
        text-align: center;
        transition: transform 0.2s ease-in-out, box-shadow 0.2s;
    }}
    .kpi-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    }}
    .banner {{
        border-radius: 16px;
        padding: 22px 26px;
        background: linear-gradient(135deg, #0B1F3A, #1F3A5A);
        color: #fff;
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
    }}
    .badge {{
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        background: {GOLD};
        color: #fff;
        font-weight: 600;
        font-size: 0.8rem;
    }}
    .section-title {{
        font-weight: 800;
        color: {PRIMARY};
        margin-bottom: 0.2rem;
    }}
    .footer {{
        text-align: center;
        color: {MUTED};
        font-size: 0.85rem;
        margin-top: 2rem;
        opacity: 0.85;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
def apply_global_style():
    """Inject global CSS & typography for consistent executive styling."""
    css = f"""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif !important;
    }}
    .block-container {{
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1100px;
        margin: auto;
    }}
    h1, h2, h3, h4 {{
        color: {PRIMARY};
        font-weight: 700;
        margin-bottom: 0.5rem;
    }}
    .small-muted {{
        color: {MUTED};
        font-size: 0.9rem;
    }}
    .kpi-card {{
        border: 1px solid {SILVER};
        border-radius: 14px;
        padding: 16px;
        background: #ffffff;
        box-shadow: 0 4px 16px rgba(0,0,0,0.04);
        text-align: center;
        transition: transform 0.2s ease-in-out, box-shadow 0.2s;
    }}
    .kpi-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    }}
    .banner {{
        border-radius: 16px;
        padding: 22px 26px;
        background: linear-gradient(135deg, #0B1F3A, #1F3A5A);
        color: #fff;
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
    }}
    .badge {{
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        background: {GOLD};
        color: #fff;
        font-weight: 600;
        font-size: 0.8rem;
    }}
    .section-title {{
        font-weight: 800;
        color: {PRIMARY};
        margin-bottom: 0.2rem;
    }}
    .footer {{
        text-align: center;
        color: {MUTED};
        font-size: 0.85rem;
        margin-top: 2rem;
        opacity: 0.85;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)



