# ==========================================================
# modules/macro_storytelling.py
# ASEAN Macro Storytelling Dashboard — Cloud-safe Stable Version
# ==========================================================

from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px

from .utils import apply_global_style


def _load_csv_or_stop(path: Path, label: str) -> pd.DataFrame:
    """Loader CSV yang aman untuk Streamlit Cloud."""
    if not path.exists():
        st.error(f"❌ File {label} tidak ditemukan.")
        st.code(str(path))
        st.info(
            "Pastikan struktur repo sesuai, misalnya:\n"
            "- dashboard/data/WDIData.csv\n\n"
            "Kalau file kamu ada di lokasi lain, sesuaikan path di kode."
        )
        st.stop()

    try:
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"❌ Gagal membaca {label}: {e}")
        st.stop()


def _to_long_wdi(df: pd.DataFrame, year_min: int, year_max: int) -> pd.DataFrame:
    """Konversi WDI wide -> long, deteksi kolom tahun secara aman."""
    required = {"Country Name", "Indicator Name"}
    missing = required - set(df.columns)
    if missing:
        st.error(f"Dataset tidak punya kolom wajib: {sorted(missing)}")
        st.stop()

    year_cols = [c for c in df.columns if str(c).isdigit()]
    if not year_cols:
        st.error("Tidak menemukan kolom tahun (mis. 2009, 2010, ...). Cek format WDIData.csv.")
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
    df_long = df_long[df_long["Year"].between(year_min, year_max)].copy()
    return df_long


def show():
    """Render ASEAN macroeconomic storytelling dashboard"""
    apply_global_style()

    # ======================================================
    # 1️⃣ HEADER
    # ======================================================
    st.markdown("""
    <div style='background:linear-gradient(90deg,#0F766E,#0D9488);
                padding:1.5rem;border-radius:12px;color:white;'>
      <h1 style='margin:0;'>🌏 ASEAN Economic Storytelling Dashboard</h1>
      <p style='margin-top:0.5rem;font-size:1rem;'>
        Menyajikan cerita ekonomi ASEAN melalui data GDP, investasi, perdagangan, dan populasi.
      </p>
      <p style='font-size:0.85rem;opacity:0.85;'>Sumber: World Bank — World Development Indicators (2009–2023)</p>
    </div>
    """, unsafe_allow_html=True)

    # ======================================================
    # 2️⃣ LOAD DATA (PATH FIX)
    # ======================================================
    BASE_DIR = Path(__file__).resolve().parents[1]  # .../dashboard
    data_path = BASE_DIR / "data" / "WDIData.csv"
    df = _load_csv_or_stop(data_path, "WDIData.csv")

    # Normalisasi nama negara
    df["Country Name"] = df["Country Name"].replace({
        "Viet Nam": "Vietnam",
        "Lao PDR": "Laos",
    })

    asean = [
        "Brunei Darussalam", "Cambodia", "Indonesia", "Laos",
        "Malaysia", "Myanmar", "Philippines", "Singapore",
        "Thailand", "Vietnam"
    ]

    indicators = {
        "GDP": "GDP (current US$)",
        "Population": "Population, total",
        "Exports": "Exports of goods and services (% of GDP)",
        "Imports": "Imports of goods and services (% of GDP)",
        "Investment": "Gross capital formation (% of GDP)"
    }

    df = df[df["Country Name"].isin(asean) & df["Indicator Name"].isin(indicators.values())].copy()
    if df.empty:
        st.error("Data kosong setelah filter ASEAN + indikator. Cek `Indicator Name` di WDIData.csv.")
        st.stop()

    # Long format robust
    df_long = _to_long_wdi(df, year_min=2009, year_max=2023)
    if df_long.empty:
        st.error("Tidak ada data valid pada rentang 2009–2023 setelah parsing.")
        st.stop()

    def get_indicator(key: str) -> pd.DataFrame:
        name = indicators[key]
        sub = df_long[df_long["Indicator Name"] == name]
        if sub.empty:
            return pd.DataFrame()
        pivot = sub.pivot_table(index="Year", columns="Country Name", values="Value", aggfunc="mean")
        pivot = pivot.sort_index().interpolate(method="linear", limit_direction="both")
        pivot = pivot.apply(lambda row: row.fillna(row.median()), axis=1)
        return pivot

    GDP = get_indicator("GDP")
    Pop = get_indicator("Population")
    Exports = get_indicator("Exports")
    Imports = get_indicator("Imports")
    Invest = get_indicator("Investment")
    Trade = Exports.add(Imports, fill_value=0) if (not Exports.empty and not Imports.empty) else pd.DataFrame()

    # ======================================================
    # 3️⃣ GDP PER CAPITA — CERITA 1
    # ======================================================
    st.header("💰 Siapa Negara Terkaya di ASEAN?")
    st.write("Pendapatan rata-rata warga di tiap negara ASEAN berdasarkan GDP per kapita (nominal).")

    if not GDP.empty and not Pop.empty:
        latest_year = int(GDP.index.max())
        if latest_year not in Pop.index:
            st.warning("⚠️ Tahun terakhir GDP tidak ada di Populasi. Menggunakan tahun overlap terakhir.")
            latest_year = int(sorted(set(GDP.index).intersection(set(Pop.index)))[-1])

        GDPpc = (GDP.loc[latest_year] / Pop.loc[latest_year]).dropna().sort_values(ascending=True)
        df_gdp = GDPpc.reset_index()
        df_gdp.columns = ["Country", "GDP per Capita"]

        fig1 = px.bar(
            df_gdp,
            x="GDP per Capita",
            y="Country",
            orientation="h",
            color="GDP per Capita",
            color_continuous_scale="Teal",
            text=df_gdp["GDP per Capita"].apply(lambda x: f"${x:,.0f}")
        )
        fig1.update_layout(height=480, title=f"GDP per Kapita di ASEAN Tahun {latest_year}", template="plotly_white")
        st.plotly_chart(fig1, use_container_width=True)

        st.markdown(f"""
        💬 **Cerita Singkat:**  
        - **Singapura** dan **Brunei Darussalam** menempati posisi teratas pendapatan per kapita.  
        - **Vietnam** dan **Indonesia** tumbuh cepat, menandakan peningkatan daya saing industri.  
        - **Kamboja** dan **Laos** masih berproses menuju ekonomi menengah.
        """)
    else:
        st.warning("⚠️ Data GDP atau populasi tidak lengkap.")

    # ======================================================
    # 4️⃣ INVESTASI — CERITA 2 (DONUT + FALLBACK)
    # ======================================================
    st.header("🏗️ Ekonomi yang Semakin Padat Modal")
    st.write("""
    Pembentukan modal bruto menunjukkan seberapa besar porsi investasi terhadap PDB —
    cerminan kegiatan pembangunan dan ekspansi industri.
    """)

    # Jika Invest kosong, fallback ke trade donut
    if Invest.empty:
        st.warning("⚠️ Indikator investasi (Gross capital formation % GDP) tidak tersedia. Fallback: Trade openness.")
        if not Trade.empty:
            latest_year = int(Trade.dropna(how="all").index.max())
            trade_latest = Trade.loc[latest_year].dropna().sort_values(ascending=False)
            top_trade = trade_latest.head(7).reset_index()
            top_trade.columns = ["Country", "Trade (% of GDP)"]

            fig_trade_donut = px.pie(
                top_trade,
                names="Country",
                values="Trade (% of GDP)",
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Blues_r,
                title=f"Distribusi Keterbukaan Perdagangan (% PDB) — Tahun {latest_year}"
            )
            fig_trade_donut.update_traces(
                textposition="inside",
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>%{value:.1f}% dari PDB<extra></extra>"
            )
            fig_trade_donut.update_layout(showlegend=True, height=520, template="plotly_white")
            st.plotly_chart(fig_trade_donut, use_container_width=True)
        else:
            st.warning("⚠️ Data perdagangan juga tidak tersedia.")
    else:
        latest_year = int(Invest.dropna(how="all").index.max())
        invest_latest = Invest.loc[latest_year].dropna().sort_values(ascending=False).head(7).reset_index()
        invest_latest.columns = ["Country", "Investment (% of GDP)"]

        fig_donut = px.pie(
            invest_latest,
            names="Country",
            values="Investment (% of GDP)",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Teal_r,
            title=f"Distribusi Pembentukan Modal Bruto (% PDB) — Tahun {latest_year}"
        )
        fig_donut.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>%{value:.1f}% dari PDB<extra></extra>"
        )
        fig_donut.update_layout(showlegend=True, height=520, template="plotly_white")
        st.plotly_chart(fig_donut, use_container_width=True)

    # ======================================================
    # 5️⃣ PERDAGANGAN — CERITA 3
    # ======================================================
    st.header("🌐 Perdagangan dan Pertumbuhan Ekonomi")
    st.write("Keterbukaan terhadap perdagangan global menjadi motor penting bagi pertumbuhan ASEAN.")

    if not Trade.empty:
        available_countries = sorted(list(Trade.columns))
        default_idx = available_countries.index("Indonesia") if "Indonesia" in available_countries else 0

        sel_country = st.selectbox(
            "Pilih negara untuk melihat keterbukaan perdagangan:",
            available_countries,
            index=default_idx
        )

        df_trade = Trade[[sel_country]].dropna().reset_index()
        df_trade.columns = ["Year", "Trade Openness (% of GDP)"]

        fig_trade = px.line(
            df_trade,
            x="Year",
            y="Trade Openness (% of GDP)",
            markers=True,
            title=f"Keterbukaan Perdagangan — {sel_country}",
            labels={"Trade Openness (% of GDP)": "% dari PDB"}
        )
        fig_trade.update_layout(template="plotly_white", height=480)
        st.plotly_chart(fig_trade, use_container_width=True)
    else:
        st.warning("⚠️ Data perdagangan tidak tersedia.")

    # ======================================================
    # 6️⃣ POPULASI — CERITA 4
    # ======================================================
    st.header("👥 Populasi dan Skala Ekonomi ASEAN")
    st.write("Populasi besar menjadi kekuatan konsumsi dan tenaga kerja di kawasan.")

    if not Pop.empty:
        latest_year = int(Pop.dropna(how="all").index.max())
        df_pop = Pop.loc[latest_year].dropna().sort_values(ascending=True).reset_index()
        df_pop.columns = ["Country", "Population"]
        df_pop["Population (juta)"] = df_pop["Population"] / 1e6

        fig_pop = px.bar(
            df_pop,
            x="Population (juta)",
            y="Country",
            orientation="h",
            color="Population (juta)",
            color_continuous_scale="Blues",
            text=df_pop["Population (juta)"].round(1)
        )
        fig_pop.update_layout(height=480, title=f"Populasi ASEAN Tahun {latest_year} (juta jiwa)", template="plotly_white")
        st.plotly_chart(fig_pop, use_container_width=True)
    else:
        st.warning("⚠️ Data populasi tidak tersedia.")

    # ======================================================
    # 7️⃣ RINGKASAN
    # ======================================================
    st.markdown("""
    ---
    ### 🧭 Ringkasan Akhir
    - 💰 **Pendapatan meningkat** di sebagian besar negara ASEAN.  
    - 🏗️ **Investasi tumbuh** pesat di negara-negara dengan industrialisasi baru.  
    - 🌐 **Perdagangan** tetap menjadi mesin utama kawasan.  
    - 👥 **Populasi besar** menjadikan ASEAN salah satu pusat pertumbuhan dunia.
    """)
