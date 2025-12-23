# ==========================================================
# modules/gdp_dashboard.py
# ASEAN GDP Growth Dashboard — Executive Edition (Cleaned)
# ==========================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import streamlit as st
from .utils import apply_global_style, PRIMARY, SLATE, GOLD, TEAL, SILVER


def show():
    """Main GDP Growth Dashboard"""
    apply_global_style()

    # -------------------------------
    # 1) Load & Prepare Data
    # -------------------------------
    file_path = "data/GDP/dataset_gdp.csv"
    raw = pd.read_csv(file_path, skiprows=4)
    raw = raw[raw["Indicator Name"] == "GDP growth (annual %)"]

    ASEAN = [
        "Indonesia", "Malaysia", "Thailand", "Viet Nam", "Vietnam",
        "Philippines", "Singapore", "Brunei Darussalam",
        "Lao PDR", "Myanmar", "Cambodia"
    ]

    dfw = raw[raw["Country Name"].isin(ASEAN)].copy()
    id_cols = [c for c in ["Country Name", "Country Code"] if c in dfw.columns]
    long = dfw.melt(id_vars=id_cols, var_name="Year", value_name="GDP_Growth")

    long["Year"] = pd.to_numeric(long["Year"], errors="coerce")
    long["GDP_Growth"] = pd.to_numeric(long["GDP_Growth"], errors="coerce").round(2)
    long = long.dropna(subset=["Year", "GDP_Growth"])
    years_min, years_max = int(long["Year"].min()), int(long["Year"].max())

    # -------------------------------
    # 2) Banner
    # -------------------------------
    st.markdown(f"""
    <div class="banner">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
        <div>
          <div class="badge">Executive Dashboard</div>
          <h1 style="margin:8px 0 4px 0; color:{GOLD};">ASEAN GDP Growth</h1>
          <div style="opacity:0.9;">Analisis spasial & temporal pertumbuhan ekonomi tahunan (World Bank, {years_min}–{years_max})</div>
        </div>
        <div style="text-align:right; min-width:220px;">
          <div style="font-size:0.9rem;">Data Source: World Development Indicators</div>
          <div style="font-size:0.9rem;">Last updated: 2025</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------
    # 3) Tabs — Interactive
    # -------------------------------
    tab_map, tab_trend, tab_year, tab_event = st.tabs(
        ["🌍 Choropleth Map", "📈 Trends", "🏆 Year Comparison", "⚖️ Event Impact"]
    )

    # === (A) Spatial View (ASEAN-Focused) ===
    with tab_map:
        st.markdown("### 🌍 Spatial View — ASEAN GDP Growth")
        map_col1, map_col2 = st.columns([4, 1.4])

        with map_col2:
            map_mode = st.radio("Display Mode", ["Animated (1960–2024)", "Selected Year"], index=0)
            sel_year_map = st.slider("Select Year", years_min, years_max, 2020)

        custom_scale = [
            [0.0, "#8B1E3F"], [0.25, "#F4A261"], [0.5, "#E9ECEF"],
            [0.75, "#2A9D8F"], [1.0, "#1D3557"]
        ]
        data_map = long if map_mode == "Animated (1960–2024)" else long[long["Year"] == sel_year_map]

        fig_map = px.choropleth(
            data_map,
            locations="Country Code",
            color="GDP_Growth",
            hover_name="Country Name",
            animation_frame="Year" if map_mode == "Animated (1960–2024)" else None,
            color_continuous_scale=custom_scale,
            range_color=(-10, 15),
            projection="mercator"
        )

        fig_map.update_geos(
            showcoastlines=True,
            coastlinecolor="#CBD5E1",
            showland=True,
            landcolor="#F8FAFC",
            showcountries=True,
            fitbounds="locations",
            visible=False,
            center=dict(lat=5, lon=110),
            lataxis_range=[-15, 25],
            lonaxis_range=[90, 135]
        )

        fig_map.update_layout(
            margin=dict(l=10, r=10, t=40, b=10),
            coloraxis_colorbar=dict(
                title="GDP Growth (%)",
                ticksuffix="%",
                len=0.8,
                bgcolor="rgba(255,255,255,0.6)",
                outlinewidth=0,
                titlefont=dict(color="#0B1F3A", size=12),
                tickfont=dict(color="#334155")
            ),
            height=520,
            paper_bgcolor="white",
            plot_bgcolor="white",
        )

        with map_col1:
            st.plotly_chart(fig_map, use_container_width=True)

    # === (B) Trends ===
    with tab_trend:
        st.markdown("### 📈 Long-Run Growth Trends")

        available_countries = sorted(long["Country Name"].unique().tolist())
        default_opts = [c for c in ["Indonesia", "Malaysia", "Thailand", "Viet Nam"] if c in available_countries]

        sel_countries_trend = st.multiselect("Select countries:", available_countries, default=default_opts)

        if sel_countries_trend:
            fig = px.line(
                long[long["Country Name"].isin(sel_countries_trend)],
                x="Year", y="GDP_Growth", color="Country Name",
                markers=True, labels={"GDP_Growth": "GDP Growth (%)"}
            )
            fig.update_layout(height=500, paper_bgcolor="white", hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Please select at least one country.")

    # === (C) Year Comparison ===
    with tab_year:
        st.markdown("### 🏆 Cross-Sectional Comparison")
        latest_year = years_max
        sel_year_comp = st.slider("Select Year:", years_min, years_max, latest_year)
        dfy = long[long["Year"] == sel_year_comp].dropna(subset=["GDP_Growth"]).sort_values("GDP_Growth", ascending=True)

        fig2 = px.bar(
            dfy, x="GDP_Growth", y="Country Name", orientation="h",
            color="GDP_Growth", color_continuous_scale="Blues",
            labels={"GDP_Growth": "GDP Growth (%)"}
        )
        fig2.update_layout(plot_bgcolor="white", height=520, coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    # === (D) Event Impact ===
    with tab_event:
        st.markdown("### ⚖️ Event Impact Analysis")
        event_options = {
            "Asian Financial Crisis (1997–1998)": (1996, 1999),
            "Global Financial Crisis (2008)": (2007, 2009),
            "COVID-19 Pandemic (2020)": (2019, 2021)
        }
        sel_event = st.selectbox("Select Event:", list(event_options.keys()))
        y_before, y_after = event_options[sel_event]
        dfe = long[long["Year"].isin([y_before, y_after])]

        fig3 = px.bar(
            dfe, x="Country Name", y="GDP_Growth", color="Year",
            barmode="group", labels={"GDP_Growth": "GDP Growth (%)"}
        )
        fig3.update_layout(plot_bgcolor="white", height=520)
        st.plotly_chart(fig3, use_container_width=True)

        st.markdown(f"""
        <div style="margin-top:1rem;border-left:4px solid {TEAL};padding-left:1rem;">
            <p>📉 <b>{sel_event}</b> memicu kontraksi tajam di seluruh ASEAN.</p>
            <p>📈 Namun, <b>Vietnam</b> dan <b>Indonesia</b> menunjukkan ketahanan pertumbuhan yang kuat.</p>
        </div>
        """, unsafe_allow_html=True)

    # -------------------------------
    # 4) Executive Notes
    # -------------------------------
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#fff,#f8fafc);
    border:1px solid #E5E7EB;border-radius:16px;padding:20px 24px;
    box-shadow:0 8px 24px rgba(0,0,0,0.04);max-width:900px;margin:auto;">
      <h3 style="color:{PRIMARY};font-weight:800;">💼 Executive Insights</h3>
      <p>🌐 <b>ASEAN GDP growth ({years_max}):</b> tren jangka panjang menunjukkan momentum ekonomi positif.</p>
      <p>⚠️ Krisis besar seperti <b>1998</b>, <b>2008</b>, dan <b>2020</b> menyebabkan kontraksi tajam, 
      namun pola pemulihan semakin cepat setiap dekade.</p>
      <p>🚀 <b>Vietnam</b> dan <b>Philippines</b> menjadi penggerak utama, sementara <b>Singapore</b> menunjukkan stabilitas tinggi.</p>
      <p>🇮🇩 <b>Indonesia</b> konsisten di atas rata-rata ASEAN, menegaskan ketahanan ekonomi makro yang kuat.</p>
    </div>
    """, unsafe_allow_html=True)
