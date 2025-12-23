# ==========================================================
# app.py
# ASEAN & Indonesia Economic Dashboard — Executive Edition
# (Fokus pada ASEAN & Indonesia Long-Run)
# ==========================================================

import streamlit as st
from PIL import Image
from modules import (
    gdp_dashboard,
    fdi_dashboard,
    macro_economic,
    macro_storytelling,
    economic_summary
)
from modules.utils import apply_global_style

# ----------------------------------------------------------
# 1️⃣ Page Config
# ----------------------------------------------------------
st.set_page_config(
    page_title="ASEAN & Indonesia Economic Dashboard",
    page_icon="🌏",
    layout="wide"
)

# ----------------------------------------------------------
# 2️⃣ Global Styling
# ----------------------------------------------------------
apply_global_style()

# ----------------------------------------------------------
# 3️⃣ Sidebar Layout
# ----------------------------------------------------------
st.sidebar.markdown(
    "<h2 style='color:#0F172A;'>🌏 ASEAN & Indonesia Economic Dashboard</h2>",
    unsafe_allow_html=True
)

# Logo
try:
    logo = Image.open("assets/asean_logo.png")
    st.sidebar.image(logo, caption="Executive Data Analytics", width=180)
except Exception:
    st.sidebar.markdown("<p style='color:#94A3B8;'>[Logo not found]</p>", unsafe_allow_html=True)

# Sidebar Description
st.sidebar.markdown("""
<p style='color:#475569; font-size:0.9rem;'>
Analisis interaktif yang memadukan <b>ASEAN macroeconomic trends</b> dan
<b>Transformasi Ekonomi Indonesia (1960–2024)</b>.
</p>
""", unsafe_allow_html=True)

# Sidebar Menu
menu = st.sidebar.radio(
    "📊 Pilih Dashboard:",
    [
        "🌍 ASEAN GDP Growth",
        "💼 ASEAN FDI Inflows",
        "📈 ASEAN Macro Economic",
        "📖 ASEAN Macro Storytelling",
        "🔗 GDP–FDI Integration"
    ],
    index=4
)

# Sidebar Footer
st.sidebar.markdown("""
<hr style="margin:1rem 0; opacity:0.3;">
<p style='font-size:0.8rem; color:#94A3B8;'>
📘 <b>Data Sources</b>:<br>
World Bank (WDI), UNCTAD, IMF, BPS<br><br>
© 2025 ASEAN Economic Research Unit
</p>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# 4️⃣ Routing ke Modul
# ----------------------------------------------------------
if menu == "🌍 ASEAN GDP Growth":
    gdp_dashboard.show()

elif menu == "💼 ASEAN FDI Inflows":
    fdi_dashboard.show()

elif menu == "📈 ASEAN Macro Economic":
    macro_economic.show()

elif menu == "📖 ASEAN Macro Storytelling":
    macro_storytelling.show()

elif menu == "🔗 GDP–FDI Integration":
    economic_summary.show()

# ----------------------------------------------------------
# 5️⃣ Footer
# ----------------------------------------------------------
st.markdown("""
<div style="text-align:center; color:#94A3B8; font-size:0.85rem; margin-top:3rem;">
  <hr style="opacity:0.2; margin-bottom:0.5rem;">
  ASEAN & Indonesia Economic Analytics Suite — Executive Edition © 2025
</div>
""", unsafe_allow_html=True)
