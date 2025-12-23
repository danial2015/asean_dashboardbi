# ==========================================================
# modules/fdi_dashboard.py
# ASEAN FDI (% of GDP) Dashboard — Final Stable Version
# ==========================================================

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
from .utils import apply_global_style, PRIMARY, SLATE, GOLD, TEAL, SILVER


# -------------------------------
# Helper Function
# -------------------------------
def _to_numeric_safe(series: pd.Series) -> pd.Series:
    """Convert safely to numeric and round to 2 decimals."""
    numeric = pd.to_numeric(
        series.astype(str)
        .str.replace(r"[^\d\.\-eE]", "", regex=True)
        .replace({"": np.nan}),
        errors="coerce"
    )
    return numeric.round(2)


# -------------------------------
# ASEAN Country Names (Normalized)
# -------------------------------
ASEAN = [
    "indonesia", "malaysia", "thailand", "vietnam", "viet nam",
    "philippines", "singapore", "bruneidarussalam", "brunei darussalam",
    "laopdr", "lao pdr", "myanmar", "cambodia"
]


# -------------------------------
# Dashboard Main Function
# -------------------------------
def show():
    apply_global_style()

    # ===============================
    # 1️⃣ Load Dataset
    # ===============================
    file_path = "data/FDI/fdi_datasets.csv"
    df = pd.read_csv(file_path, skiprows=4)

    if "Country Name" not in df.columns:
        st.error("Kolom 'Country Name' tidak ditemukan dalam dataset.")
        return

    # Normalisasi nama negara
    df["Country_clean"] = (
        df["Country Name"].astype(str)
        .str.lower()
        .str.replace(r"\s+", "", regex=True)
    )

    df = df[df["Country_clean"].isin(ASEAN)]

    # Filter indikator FDI (% of GDP)
    if "Indicator Name" in df.columns:
        df = df[df["Indicator Name"].str.contains(
            "Foreign direct investment, net inflows \\(% of GDP\\)",
            case=False, regex=True, na=False
        )]

    # Konversi kolom tahun menjadi numerik
    year_cols = [c for c in df.columns if c.isdigit()]
    for c in year_cols:
        df[c] = _to_numeric_safe(df[c])

    # Reshape ke long format
    df_long = df.melt(
        id_vars=["Country Name", "Country Code"],
        value_vars=year_cols,
        var_name="Year",
        value_name="FDI_PctGDP"
    )
    df_long["Year"] = pd.to_numeric(df_long["Year"], errors="coerce")
    df_long = df_long.dropna(subset=["FDI_PctGDP"])
    df_long["FDI_PctGDP"] = df_long["FDI_PctGDP"].round(2)

    years_min, years_max = int(df_long["Year"].min()), int(df_long["Year"].max())
    latest_year = years_max

    # ===============================
    # 2️⃣ Banner
    # ===============================
    st.markdown(f"""
    <div class="banner">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
            <div>
                <div class="badge">Executive Dashboard</div>
                <h1 style="margin:8px 0;color:{GOLD};">ASEAN FDI (% of GDP)</h1>
                <div style="opacity:0.9;">World Bank · {years_min}–{years_max}</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.9rem;">Source: World Development Indicators</div>
                <div style="font-size:0.9rem;">Updated: 2025</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

        # ===============================
    # 3️⃣ KPI Metrics (INTERACTIVE)
    # ===============================
    st.markdown("### 🎯 Key Investment Indicators")

    sel_year_kpi = st.slider(
        "Select Year for KPI Overview:",
        min_value=years_min,
        max_value=years_max,
        value=latest_year,
        key="fdi_kpi_year"
    )

    df_selected = df_long[df_long["Year"] == sel_year_kpi]

    if df_selected.empty:
        st.warning(f"Tidak ada data FDI untuk tahun {sel_year_kpi}.")
    else:
        asean_mean = round(df_selected["FDI_PctGDP"].mean(), 2)
        top_row = df_selected.loc[df_selected["FDI_PctGDP"].idxmax()]
        top_country, top_val = top_row["Country Name"], round(top_row["FDI_PctGDP"], 2)

        # ΔYoY dibanding tahun sebelumnya (jika ada)
        prev_year = sel_year_kpi - 1
        if prev_year in df_long["Year"].unique():
            prev_mean = df_long[df_long["Year"] == prev_year]["FDI_PctGDP"].mean()
            avg_delta = round(asean_mean - prev_mean, 2)
        else:
            avg_delta = np.nan

        # Layout KPI cards
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"""
        <div class="kpi-card">
            <div class="section-title">ASEAN Mean ({sel_year_kpi})</div>
            <h2 style="color:{TEAL};margin:0;">{asean_mean:.2f}%</h2>
        </div>
        """, unsafe_allow_html=True)

        c2.markdown(f"""
        <div class="kpi-card">
            <div class="section-title">Top Country ({sel_year_kpi})</div>
            <h3 style="color:{GOLD};margin:0;">{top_country}</h3>
            <p style="color:{SLATE};margin:0;">{top_val:.2f}% of GDP</p>
        </div>
        """, unsafe_allow_html=True)

        delta_str = f"{avg_delta:+.2f} pts" if not np.isnan(avg_delta) else "N/A"
        delta_color = PRIMARY if avg_delta >= 0 else "#E11D48"  # merah jika negatif

        c3.markdown(f"""
        <div class="kpi-card">
            <div class="section-title">Δ YoY (ASEAN Mean)</div>
            <h2 style="color:{delta_color};margin:0;">{delta_str}</h2>
        </div>
        """, unsafe_allow_html=True)

    # ===============================
    # 4️⃣ Tabs
    # ===============================
    tab_trend, tab_compare, tab_heatmap, tab_event = st.tabs(
        ["📈 Trend", "🏆 Comparison", "🌡️ Heatmap", "⚖️ Event Impact"]
    )

    # -----------------------------
    # Trend
    # -----------------------------
    with tab_trend:
        st.markdown("### 📈 FDI (% of GDP) Trend")

        available_countries = sorted(df_long["Country Name"].unique().tolist())
        default_opts = [c for c in ["Singapore", "Vietnam", "Viet Nam", "Indonesia"] if c in available_countries]

        sel_countries = st.multiselect(
            "Select countries:",
            options=available_countries,
            default=default_opts
        )

        if not sel_countries:
            st.warning("Please select at least one country to display the trend.")
        else:
            sub = df_long[df_long["Country Name"].isin(sel_countries)]

            fig = px.line(
                sub, x="Year", y="FDI_PctGDP", color="Country Name",
                markers=True, labels={"FDI_PctGDP": "FDI (% of GDP)"}
            )
            fig.update_layout(
                height=480, paper_bgcolor="white", plot_bgcolor="white",
                hovermode="x unified", legend_title_text=""
            )
            st.plotly_chart(fig, use_container_width=True)

    # -----------------------------
    # Comparison
    # -----------------------------
    with tab_compare:
        st.markdown("### 🏆 FDI Ranking by Year")
        sel_year = st.slider("Select Year:", years_min, years_max, latest_year)
        df_y = df_long[df_long["Year"] == sel_year].dropna(subset=["FDI_PctGDP"])
        df_y = df_y.sort_values("FDI_PctGDP", ascending=True)

        fig2 = px.bar(
            df_y, x="FDI_PctGDP", y="Country Name", orientation="h",
            color="FDI_PctGDP", color_continuous_scale="Blues",
            labels={"FDI_PctGDP": "FDI (% of GDP)"}
        )
        fig2.update_layout(plot_bgcolor="white", height=520, coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    # -----------------------------
    # Heatmap
    # -----------------------------
    with tab_heatmap:
        st.markdown("### 🌡️ ASEAN FDI Heatmap (% of GDP)")
        pivot = df_long.pivot(index="Country Name", columns="Year", values="FDI_PctGDP")
        plt.figure(figsize=(10, 5))
        sns.heatmap(pivot, cmap="YlGnBu", linewidths=0.5,
                    cbar_kws={"label": "FDI (% of GDP)"})
        st.pyplot(plt.gcf(), clear_figure=True, use_container_width=True)

    # -----------------------------
    # Event Impact
    # -----------------------------
    with tab_event:
        st.markdown("### ⚖️ Global Event Impact on FDI")
        events = {
            "Asian Financial Crisis (1997–1998)": (1996, 1999),
            "Global Financial Crisis (2008)": (2007, 2009),
            "COVID-19 Pandemic (2020)": (2019, 2021),
        }
        sel_event = st.selectbox("Select Event:", list(events.keys()))
        y_before, y_after = events[sel_event]
        dfe = df_long[df_long["Year"].isin([y_before, y_after])]
        fig4 = px.bar(
            dfe, x="Country Name", y="FDI_PctGDP", color="Year",
            barmode="group", labels={"FDI_PctGDP": "FDI (% of GDP)"}
        )
        fig4.update_layout(plot_bgcolor="white", height=520)
        st.plotly_chart(fig4, use_container_width=True)

        st.markdown(f"""
        <div style="margin-top:1rem;border-left:4px solid {TEAL};padding-left:1rem;">
            <p>📉 <b>{sel_event}</b> menekan arus investasi asing di hampir seluruh negara ASEAN.</p>
            <p>📈 Namun, <b>Vietnam</b> dan <b>Indonesia</b> menunjukkan ketahanan investasi yang kuat 
            dan pemulihan yang lebih cepat dibanding rata-rata kawasan.</p>
        </div>
        """, unsafe_allow_html=True)
