# ==========================================================
# modules/macro_economic.py
# ASEAN Macro Economic Dashboard — World Bank Executive Edition (Static, Cloud-safe)
# ==========================================================

from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

from .utils import apply_global_style, PRIMARY, GOLD


def _load_csv_or_stop(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        st.error(f"❌ File {label} tidak ditemukan.")
        st.code(str(path))
        st.info(
            "Pastikan file ada di repo sesuai path di atas.\n\n"
            "Jika kamu menjalankan dari Streamlit Cloud, gunakan path berbasis `Path(__file__)` seperti di kode ini."
        )
        st.stop()
    try:
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"❌ Gagal membaca {label}: {e}")
        st.stop()


def show():
    """Render static ASEAN macroeconomic dashboard"""
    apply_global_style()

    st.markdown(f"""
    <div class="banner">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
        <div>
          <div class="badge">Executive Dashboard</div>
          <h1 style="margin:8px 0 4px 0; color:{GOLD};">ASEAN Macro Economic Overview</h1>
          <div style="opacity:0.9;">Visualisasi fundamental ekonomi kawasan ASEAN (2009–2018)</div>
        </div>
        <div style="text-align:right; min-width:220px;">
          <div style="font-size:0.9rem;">Source: World Bank (WDI)</div>
          <div style="font-size:0.9rem;">Last updated: 2025</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # -----------------------------
    # 1️⃣ Load Data (PATH FIX)
    # -----------------------------
    # macro_economic.py ada di: dashboard/modules/macro_economic.py
    BASE_DIR = Path(__file__).resolve().parents[1]  # .../dashboard
    data_path = BASE_DIR / "data" / "WDIData.csv"

    df = _load_csv_or_stop(data_path, "WDIData.csv")

    # Validasi kolom wajib
    required_cols = {"Country Name", "Indicator Name"}
    missing = required_cols - set(df.columns)
    if missing:
        st.error(f"Dataset WDIData.csv tidak punya kolom wajib: {sorted(missing)}")
        st.stop()

    asean_countries = [
        "Brunei Darussalam", "Cambodia", "Indonesia", "Lao PDR",
        "Malaysia", "Myanmar", "Philippines", "Singapore",
        "Thailand", "Vietnam"
    ]

    macro_indicators = [
        "GDP (current US$)",
        "GDP growth (annual %)",
        "Consumer price index (2010 = 100)",
        "Exports of goods and services (% of GDP)",
        "Imports of goods and services (% of GDP)",
        "Population, total",
    ]

    df = df[df["Indicator Name"].isin(macro_indicators) & df["Country Name"].isin(asean_countries)].copy()

    if df.empty:
        st.error("Data kosong setelah filtering. Cek nama indikator (Indicator Name) di WDIData.csv.")
        st.stop()

    # -----------------------------
    # 2️⃣ Long format (YEAR COLS SAFE)
    # -----------------------------
    year_cols = [c for c in df.columns if str(c).isdigit()]
    if not year_cols:
        st.error("Tidak menemukan kolom tahun (misal 2009, 2010, ...). Cek format WDIData.csv.")
        st.stop()

    df_long = df.melt(
        id_vars=["Country Name", "Indicator Name"],
        value_vars=year_cols,
        var_name="Year",
        value_name="Value",
    )

    df_long["Year"] = pd.to_numeric(df_long["Year"], errors="coerce")
    df_long["Value"] = pd.to_numeric(df_long["Value"], errors="coerce")
    df_long = df_long.dropna(subset=["Year"]).copy()
    df_long["Year"] = df_long["Year"].astype(int)

    df_long = df_long[df_long["Year"].between(2009, 2018)].copy()
    if df_long.empty:
        st.error("Tidak ada data di rentang 2009–2018 (setelah cleaning).")
        st.stop()

    # -----------------------------
    # 3️⃣ Pivot Helper
    # -----------------------------
    def pivot_indicator(name: str) -> pd.DataFrame:
        sub = df_long[df_long["Indicator Name"] == name].copy()
        if sub.empty:
            return pd.DataFrame()
        pivot = sub.pivot_table(index="Year", columns="Country Name", values="Value", aggfunc="mean")
        # interpolate + fallback median per-year
        pivot = pivot.sort_index().interpolate(method="linear", limit_direction="both")
        pivot = pivot.apply(lambda row: row.fillna(row.median()), axis=1)
        return pivot

    GDP_growth = pivot_indicator("GDP growth (annual %)")
    CPI = pivot_indicator("Consumer price index (2010 = 100)")
    Exports = pivot_indicator("Exports of goods and services (% of GDP)")
    Imports = pivot_indicator("Imports of goods and services (% of GDP)")
    Pop = pivot_indicator("Population, total")

    # Minimal validation biar gak crash pas plot
    if GDP_growth.empty or CPI.empty or Exports.empty or Imports.empty or Pop.empty:
        st.error("Salah satu indikator tidak ada di data. Cek kembali `macro_indicators` vs isi WDIData.csv.")
        st.stop()

    Trade = Exports + Imports

    # -----------------------------
    # 4️⃣ Visualisasi (STYLE SAFE)
    # -----------------------------
    # Hindari plt.style seaborn (sering tidak tersedia di environment cloud)
    plt.rcParams.update({
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
    })

    fig = plt.figure(figsize=(14, 10))
    fig.suptitle(
        "ASEAN Macro Economic Dashboard — (2009–2018)",
        fontsize=16, fontweight="bold", color="#0F172A", y=1.02
    )

    # GDP Growth
    ax1 = plt.subplot(2, 2, 1)
    for c in GDP_growth.columns:
        ax1.plot(GDP_growth.index, GDP_growth[c], linewidth=1.6, alpha=0.8)
    ax1.set_title("GDP Growth (Annual %)")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("%")

    # CPI
    ax2 = plt.subplot(2, 2, 2)
    for c in CPI.columns:
        ax2.plot(CPI.index, CPI[c], linewidth=1.6, alpha=0.8)
    ax2.set_title("Consumer Price Index (2010 = 100)")
    ax2.set_xlabel("Year")
    ax2.set_ylabel("Index")

    # Trade
    ax3 = plt.subplot(2, 2, 3)
    for c in Trade.columns:
        ax3.plot(Trade.index, Trade[c], linewidth=1.6, alpha=0.8)
    ax3.set_title("Trade Openness (Exports + Imports, % of GDP)")
    ax3.set_xlabel("Year")
    ax3.set_ylabel("% of GDP")

    # Population
    ax4 = plt.subplot(2, 2, 4)
    for c in Pop.columns:
        ax4.plot(Pop.index, Pop[c], linewidth=1.6, alpha=0.8)
    ax4.set_yscale("log")
    ax4.set_title("Population (log scale)")
    ax4.set_xlabel("Year")
    ax4.set_ylabel("Population (log)")

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    st.pyplot(fig, use_container_width=True)

    # -----------------------------
    # 5️⃣ Insights
    # -----------------------------
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#fff,#f8fafc);
    border:1px solid #E5E7EB;border-radius:16px;padding:20px 24px;
    box-shadow:0 8px 24px rgba(0,0,0,0.04);max-width:900px;margin:auto;">
      <h3 style="color:{PRIMARY};font-weight:800;">💼 Executive Insights</h3>
      <p>🌐 GDP growth rata-rata stabil di kisaran <b>4–6%</b> per tahun, menandakan ketahanan ekonomi pasca krisis global.</p>
      <p>💸 Inflasi terkendali, menunjukkan keberhasilan kebijakan moneter di sebagian besar negara ASEAN.</p>
      <p>📦 Keterbukaan perdagangan tinggi (>100% GDP di <b>Singapura</b> dan <b>Malaysia</b>), meski menurun pasca-2015.</p>
      <p>👥 Populasi meningkat konsisten, memperkuat basis permintaan domestik dan tenaga kerja produktif.</p>
      <p>🚀 <b>Vietnam</b> dan <b>Filipina</b> tumbuh cepat, sementara <b>Indonesia</b> tetap menjadi jangkar stabilitas regional.</p>
    </div>
    """, unsafe_allow_html=True)
