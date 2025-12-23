# ==========================================================
# modules/fdi_dashboard.py
# ASEAN FDI (% of GDP) Dashboard — Cloud-safe Stable Version
# ==========================================================

from pathlib import Path

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from .utils import apply_global_style, PRIMARY, SLATE, GOLD, TEAL, SILVER


# -------------------------------
# Helper Functions
# -------------------------------
def _load_csv_or_stop(path: Path, label: str, skiprows: int = 4) -> pd.DataFrame:
    """Loader CSV yang aman untuk Streamlit Cloud."""
    if not path.exists():
        st.error(f"❌ File {label} tidak ditemukan.")
        st.code(str(path))
        st.info(
            "Pastikan file ada di repo sesuai struktur:\n"
            "- dashboard/data/FDI/fdi_datasets.csv\n\n"
            "Kalau berbeda, sesuaikan path-nya."
        )
        st.stop()

    try:
        return pd.read_csv(path, skiprows=skiprows)
    except Exception as e:
        st.error(f"❌ Gagal membaca {label}: {e}")
        st.stop()


def _to_numeric_safe(series: pd.Series) -> pd.Series:
    """Convert safely to numeric and round to 2 decimals."""
    numeric = pd.to_numeric(
        series.astype(str)
        .str.replace(r"[^\d\.\-eE]", "", regex=True)
        .replace({"": np.nan}),
        errors="coerce",
    )
    return numeric.round(2)


def _normalize_country(s: pd.Series) -> pd.Series:
    return (
        s.astype(str)
        .str.lower()
        .str.replace(r"\s+", "", regex=True)
        .str.replace(r"[^\w]", "", regex=True)
    )


ASEAN_NORM = {
    "indonesia", "malaysia", "thailand", "vietnam", "vietnam",
    "philippines", "singapore", "bruneidarussalam", "bruneidarussalam",
    "laopdr", "laopdr", "myanmar", "cambodia"
}


def show():
    apply_global_style()

    # ===============================
    # 1️⃣ Load Dataset (PATH FIX)
    # ===============================
    BASE_DIR = Path(__file__).resolve().parents[1]  # .../dashboard
    file_path = BASE_DIR / "data" / "FDI" / "fdi_datasets.csv"
    df = _load_csv_or_stop(file_path, "FDI dataset", skiprows=4)

    # Validasi kolom
    required_cols = {"Country Name", "Indicator Name"}
    missing = required_cols - set(df.columns)
    if missing:
        st.error(f"Kolom wajib tidak ada: {sorted(missing)}")
        st.stop()

    # Normalisasi nama negara
    df["Country_clean"] = _normalize_country(df["Country Name"])
    df = df[df["Country_clean"].isin(ASEAN_NORM)].copy()

    if df.empty:
        st.error("Data kosong setelah filter ASEAN. Cek nama negara di dataset.")
        st.stop()

    # ===============================
    # 2️⃣ Filter indikator FDI (% of GDP) (lebih fleksibel)
    # ===============================
    # WDI biasanya: "Foreign direct investment, net inflows (% of GDP)"
    df = df[df["Indicator Name"].str.contains(
        r"foreign direct investment.*% of gdp",
        case=False, regex=True, na=False
    )].copy()

    if df.empty:
        st.error("Indikator FDI (% of GDP) tidak ditemukan. Cek 'Indicator Name' di dataset.")
        st.stop()

    # ===============================
    # 3️⃣ Parse Year Columns (aman)
    # ===============================
    year_cols = [c for c in df.columns if str(c).isdigit()]
    if not year_cols:
        st.error("Tidak menemukan kolom tahun (mis. 1990, 2000, 2020, ...).")
        st.stop()

    for c in year_cols:
        df[c] = _to_numeric_safe(df[c])

    id_cols = [c for c in ["Country Name", "Country Code"] if c in df.columns]
    if not id_cols:
        id_cols = ["Country Name"]

    df_long = df.melt(
        id_vars=id_cols,
        value_vars=year_cols,
        var_name="Year",
        value_name="FDI_PctGDP"
    )
    df_long["Year"] = pd.to_numeric(df_long["Year"], errors="coerce")
    df_long["FDI_PctGDP"] = pd.to_numeric(df_long["FDI_PctGDP"], errors="coerce")
    df_long = df_long.dropna(subset=["Year", "FDI_PctGDP"]).copy()
    df_long["Year"] = df_long["Year"].astype(int)

    if df_long.empty:
        st.error("Data long kosong setelah parsing. Cek isi angka di kolom tahun.")
        st.stop()

    years_min, years_max = int(df_long["Year"].min()), int(df_long["Year"].max())
    latest_year = years_max

    # ===============================
    # 4️⃣ Banner
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
    # 5️⃣ KPI Metrics
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
        asean_mean = float(df_selected["FDI_PctGDP"].mean().round(2))
        top_row = df_selected.loc[df_selected["FDI_PctGDP"].idxmax()]
        top_country = top_row["Country Name"]
        top_val = float(round(top_row["FDI_PctGDP"], 2))

        prev_year = sel_year_kpi - 1
        if prev_year in set(df_long["Year"].unique()):
            prev_mean = float(df_long[df_long["Year"] == prev_year]["FDI_PctGDP"].mean())
            avg_delta = float(round(asean_mean - prev_mean, 2))
        else:
            avg_delta = np.nan

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
        delta_color = PRIMARY if (not np.isnan(avg_delta) and avg_delta >= 0) else "#E11D48"

        c3.markdown(f"""
        <div class="kpi-card">
            <div class="section-title">Δ YoY (ASEAN Mean)</div>
            <h2 style="color:{delta_color};margin:0;">{delta_str}</h2>
        </div>
        """, unsafe_allow_html=True)

    # ===============================
    # 6️⃣ Tabs
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
        default_opts = [c for c in ["Singapore", "Vietnam", "Indonesia"] if c in available_countries]

        sel_countries = st.multiselect(
            "Select countries:",
            options=available_countries,
            default=default_opts
        )

        if not sel_countries:
            st.warning("Please select at least one country to display the trend.")
        else:
            sub = df_long[df_long["Country Name"].isin(sel_countries)].copy()
            sub = sub.sort_values(["Country Name", "Year"])

            fig = px.line(
                sub,
                x="Year", y="FDI_PctGDP", color="Country Name",
                markers=True, labels={"FDI_PctGDP": "FDI (% of GDP)"}
            )
            fig.update_layout(
                height=480,
                paper_bgcolor="white",
                plot_bgcolor="white",
                hovermode="x unified",
                legend_title_text="",
            )
            st.plotly_chart(fig, use_container_width=True)

    # -----------------------------
    # Comparison
    # -----------------------------
    with tab_compare:
        st.markdown("### 🏆 FDI Ranking by Year")
        sel_year = st.slider("Select Year:", years_min, years_max, latest_year, key="fdi_rank_year")

        df_y = df_long[df_long["Year"] == sel_year].dropna(subset=["FDI_PctGDP"]).copy()
        df_y = df_y.sort_values("FDI_PctGDP", ascending=True)

        fig2 = px.bar(
            df_y, x="FDI_PctGDP", y="Country Name", orientation="h",
            color="FDI_PctGDP", color_continuous_scale="Blues",
            labels={"FDI_PctGDP": "FDI (% of GDP)"}
        )
        fig2.update_layout(plot_bgcolor="white", height=520, coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    # -----------------------------
    # Heatmap (NO SEABORN)
    # -----------------------------
    with tab_heatmap:
        st.markdown("### 🌡️ ASEAN FDI Heatmap (% of GDP)")

        pivot = df_long.pivot_table(index="Country Name", columns="Year", values="FDI_PctGDP", aggfunc="mean")
        pivot = pivot.sort_index(axis=0).sort_index(axis=1)

        fig_hm = px.imshow(
            pivot,
            labels=dict(x="Year", y="Country", color="FDI (% of GDP)"),
            aspect="auto"
        )
        fig_hm.update_layout(height=520, template="plotly_white")
        st.plotly_chart(fig_hm, use_container_width=True)

    # -----------------------------
    # Event Impact (safe years)
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

        years_available = set(df_long["Year"].unique())
        yy = [y for y in [y_before, y_after] if y in years_available]

        if len(yy) < 2:
            st.warning("Tahun event tidak lengkap di dataset kamu. Menampilkan tahun yang tersedia saja.")
        dfe = df_long[df_long["Year"].isin(yy)].copy()

        fig4 = px.bar(
            dfe, x="Country Name", y="FDI_PctGDP", color="Year",
            barmode="group", labels={"FDI_PctGDP": "FDI (% of GDP)"}
        )
        fig4.update_layout(plot_bgcolor="white", height=520)
        st.plotly_chart(fig4, use_container_width=True)

        st.markdown(f"""
        <div style="margin-top:1rem;border-left:4px solid {TEAL};padding-left:1rem;">
            <p>📉 <b>{sel_event}</b> menekan arus investasi asing di hampir seluruh negara ASEAN.</p>
            <p>📈 Namun, <b>Vietnam</b> dan <b>Indonesia</b> sering menunjukkan pemulihan lebih cepat dibanding rata-rata kawasan.</p>
        </div>
        """, unsafe_allow_html=True)
