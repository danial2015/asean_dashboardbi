# ==========================================================
# modules/macro_storytelling.py
# ASEAN Macro Storytelling Dashboard — Fixed Stable Version
# ==========================================================

import pandas as pd
import streamlit as st
import plotly.express as px
from .utils import apply_global_style


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
    # 2️⃣ LOAD DATA
    # ======================================================
    try:
        df = pd.read_csv("data/WDIData.csv")
    except FileNotFoundError:
        st.error("❌ File 'data/WDIData.csv' tidak ditemukan.")
        return

    # Normalisasi nama negara
    df["Country Name"] = df["Country Name"].replace({
        "Viet Nam": "Vietnam",
        "Lao PDR": "Laos"
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

    df = df[df["Country Name"].isin(asean) & df["Indicator Name"].isin(indicators.values())]

    # Bentuk long format
    df_long = df.melt(id_vars=["Country Name", "Indicator Name"],
                      var_name="Year", value_name="Value")
    df_long = df_long[df_long["Year"].str.isnumeric()]
    df_long["Year"] = df_long["Year"].astype(int)
    df_long["Value"] = pd.to_numeric(df_long["Value"], errors="coerce")
    df_long = df_long[df_long["Year"].between(2009, 2023)]

    def get_indicator(name):
        ind = df_long[df_long["Indicator Name"] == indicators[name]]
        if ind.empty:
            return pd.DataFrame()
        return ind.pivot_table(index="Year", columns="Country Name", values="Value")

    GDP = get_indicator("GDP")
    Pop = get_indicator("Population")
    Exports = get_indicator("Exports")
    Imports = get_indicator("Imports")
    Invest = get_indicator("Investment")
    Trade = Exports.add(Imports, fill_value=0)

    # ======================================================
    # 3️⃣ GDP PER CAPITA — CERITA 1
    # ======================================================
    st.header("💰 Siapa Negara Terkaya di ASEAN?")
    st.write("Pendapatan rata-rata warga di tiap negara ASEAN berdasarkan GDP per kapita (nominal).")

    if not GDP.empty and not Pop.empty:
        latest_year = GDP.index.max()
        GDPpc = (GDP.loc[latest_year] / Pop.loc[latest_year]).dropna().sort_values(ascending=True)
        df_gdp = GDPpc.reset_index()
        df_gdp.columns = ["Country", "GDP per Capita"]

        fig1 = px.bar(
            df_gdp,
            x="GDP per Capita",
            y="Country",
            orientation="h",
            color="GDP per Capita",
            color_continuous_scale="teal",
            text=df_gdp["GDP per Capita"].apply(lambda x: f"${x:,.0f}")
        )
        fig1.update_layout(height=480, title=f"GDP per Kapita di ASEAN Tahun {latest_year}")
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
    # 4️⃣ INVESTASI — EKONOMI PADAT MODAL (DONUT, DENGAN FALLBACK)
    # ======================================================
    st.header("🏗️ Ekonomi yang Semakin Padat Modal")
    st.write("""
    Pembentukan modal bruto menunjukkan seberapa besar porsi investasi terhadap PDB — 
    cerminan kegiatan pembangunan dan ekspansi industri.
    """)

    # --- Pastikan indikator investasi ada ---
    alt_names = [
        "Gross capital formation (% of GDP)",
        "Gross capital formation (current US$)",
        "Gross capital formation (constant 2015 US$)"
    ]

    invest_df = df[df["Indicator Name"].isin(alt_names)]
    if invest_df.empty:
        st.warning("⚠️ Indikator pembentukan modal tidak tersedia dalam file ini.")
        st.write("""
        📊 Sebagai alternatif, berikut visualisasi **keterbukaan ekonomi (ekspor + impor)** 
        yang sering menjadi pengganti indikator padat modal untuk membaca *aktivitas ekonomi produktif*.
        """)
        # --- fallback visualisasi: trade openness donut ---
        if not Trade.empty:
            valid_years = Trade.dropna(how="all").index.tolist()
            if len(valid_years) > 0:
                latest_year = max(valid_years)
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

                st.markdown(f"""
                💬 **Cerita Alternatif:**  
                - Tahun **{latest_year}**, keterbukaan ekonomi tertinggi terdapat di **{top_trade.iloc[0,0]}**, 
                  menandakan ketergantungan kuat pada perdagangan internasional.  
                - Negara seperti **Vietnam** dan **Malaysia** menjadi contoh *ekonomi ekspor-driven* yang berperan penting di rantai nilai global.  
                """)
        else:
            st.warning("⚠️ Data perdagangan juga tidak ditemukan.")
    else:
        # --- gunakan data investasi yang ditemukan ---
        invest_df_long = invest_df.melt(id_vars=["Country Name", "Indicator Name"],
                                        var_name="Year", value_name="Value")
        invest_df_long = invest_df_long[invest_df_long["Year"].str.isnumeric()]
        invest_df_long["Year"] = invest_df_long["Year"].astype(int)
        invest_df_long["Value"] = pd.to_numeric(invest_df_long["Value"], errors="coerce")
        invest_df_long = invest_df_long[invest_df_long["Year"].between(2009, 2023)]

        latest_year = invest_df_long["Year"].max()
        invest_latest = (invest_df_long[invest_df_long["Year"] == latest_year]
                         .dropna(subset=["Value"])
                         .groupby("Country Name")["Value"]
                         .mean()
                         .sort_values(ascending=False)
                         .reset_index())

        if not invest_latest.empty:
            invest_latest = invest_latest.head(7)
            fig_donut = px.pie(
                invest_latest,
                names="Country Name",
                values="Value",
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Teal_r,
                title=f"Distribusi Pembentukan Modal Bruto — Tahun {latest_year}"
            )
            fig_donut.update_traces(
                textposition="inside",
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>%{value:.1f} dari PDB<extra></extra>"
            )
            fig_donut.update_layout(showlegend=True, height=520, template="plotly_white")
            st.plotly_chart(fig_donut, use_container_width=True)

            st.markdown(f"""
            💬 **Cerita Singkat:**  
            - Pada **{latest_year}**, negara dengan porsi investasi terbesar terhadap PDB adalah **{invest_latest.iloc[0,0]}** 
              dengan nilai sekitar **{invest_latest.iloc[0,1]:.1f}**.  
            - Negara dengan porsi tinggi menunjukkan **pembangunan infrastruktur dan industrialisasi** yang kuat.  
            - Negara lain dengan proporsi lebih rendah cenderung berfokus pada konsumsi domestik dan sektor jasa.
            """)
        else:
            st.warning("⚠️ Tidak ada data investasi valid untuk tahun terakhir.")

    # ======================================================
    # 5️⃣ PERDAGANGAN — CERITA 3
    # ======================================================
    st.header("🌐 Perdagangan dan Pertumbuhan Ekonomi")
    st.write("""
    Keterbukaan terhadap perdagangan global menjadi motor penting bagi pertumbuhan ASEAN.
    """)

    if not Trade.empty:
        available_countries = sorted(list(Trade.columns))
        sel_country = st.selectbox(
            "Pilih negara untuk melihat keterbukaan perdagangan:",
            available_countries,
            index=available_countries.index("Indonesia") if "Indonesia" in available_countries else 0
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
        fig_trade.update_traces(mode="lines+markers", marker=dict(size=7))
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
        latest_year = Pop.index.max()
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
        fig_pop.update_layout(height=480, title=f"Populasi ASEAN Tahun {latest_year} (juta jiwa)")
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
