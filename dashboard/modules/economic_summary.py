# ==========================================================
# modules/economic_summary.py
# ASEAN FDI–GDP Econometric Intelligence Dashboard (Interactive Edition)
# ==========================================================

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import statsmodels.api as sm
from statsmodels.tsa.stattools import grangercausalitytests, adfuller
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Optional (Panel FE model)
try:
    from linearmodels import PanelOLS
    HAS_LM = True
except Exception:
    HAS_LM = False

from .utils import apply_global_style, GOLD, TEAL


# ==========================================================
# Helper functions
# ==========================================================
def interpret_corr(r):
    if pd.isna(r):
        return "neutral", "tidak dapat dihitung"
    if r > 0.7: return "strong positive", "FDI sangat berhubungan dengan pertumbuhan GDP"
    if r > 0.4: return "moderate positive", "FDI cukup berkaitan dengan pertumbuhan GDP"
    if r > 0.2: return "weak positive", "FDI mungkin berdampak kecil terhadap GDP"
    if r < -0.2: return "negative", "FDI mungkin bereaksi terhadap kontraksi ekonomi"
    return "neutral", "hubungan lemah / tidak signifikan"


def p_text(p):
    if p < 0.01: return "p < 0.01 (sangat signifikan)"
    if p < 0.05: return "p < 0.05 (signifikan)"
    if p < 0.10: return "p < 0.10 (indikatif)"
    return f"p = {p:.3f} (tidak signifikan)"


def adf_p(series):
    try:
        return round(adfuller(series.dropna(), autolag="AIC")[1], 3)
    except Exception:
        return np.nan


def winsorize(s, q=0.01):
    lo, hi = s.quantile(q), s.quantile(1 - q)
    return s.clip(lo, hi)


# ==========================================================
# Main Function
# ==========================================================
def show():
    apply_global_style()

    # --- Load Data
    gdp = pd.read_csv("data/GDP/dataset_gdp.csv", skiprows=4)
    fdi = pd.read_csv("data/FDI/fdi_datasets.csv", skiprows=4)

    gdp = gdp[gdp["Indicator Name"] == "GDP growth (annual %)"]
    fdi = fdi[fdi["Indicator Name"].str.contains("Foreign direct investment", case=False, na=False)]

    ASEAN = ["Indonesia", "Malaysia", "Thailand", "Viet Nam", "Vietnam", "Philippines", "Singapore",
             "Brunei Darussalam", "Lao PDR", "Myanmar", "Cambodia"]
    gdp = gdp[gdp["Country Name"].isin(ASEAN)]
    fdi = fdi[fdi["Country Name"].isin(ASEAN)]
    gdp["Country Name"] = gdp["Country Name"].replace({"Viet Nam": "Vietnam"})
    fdi["Country Name"] = fdi["Country Name"].replace({"Viet Nam": "Vietnam"})

    years = [c for c in gdp.columns if c.isdigit()]
    gdp_long = gdp.melt(id_vars=["Country Name"], value_vars=years, var_name="Year", value_name="GDP_Growth")
    fdi_long = fdi.melt(id_vars=["Country Name"], value_vars=years, var_name="Year", value_name="FDI_PctGDP")

    for df_ in [gdp_long, fdi_long]:
        df_["Year"] = pd.to_numeric(df_["Year"], errors="coerce")

    gdp_long["GDP_Growth"] = pd.to_numeric(gdp_long["GDP_Growth"], errors="coerce")
    fdi_long["FDI_PctGDP"] = pd.to_numeric(fdi_long["FDI_PctGDP"], errors="coerce")

    df = pd.merge(gdp_long, fdi_long, on=["Country Name", "Year"], how="inner")
    df = df.dropna(subset=["GDP_Growth", "FDI_PctGDP"])
    df["GDP_Growth"] = df.groupby("Country Name")["GDP_Growth"].transform(lambda s: winsorize(s, 0.01))
    df["FDI_PctGDP"] = df.groupby("Country Name")["FDI_PctGDP"].transform(lambda s: winsorize(s, 0.01))

    # --- Interactive year range
    year_min, year_max = int(df["Year"].min()), int(df["Year"].max())
    sel_years = st.slider(
        "Pilih rentang tahun analisis",
        min_value=year_min,
        max_value=year_max,
        value=(2019, 2024),
        step=1,
        help="Geser untuk menentukan periode analisis FDI–GDP"
    )
    df = df[(df["Year"] >= sel_years[0]) & (df["Year"] <= sel_years[1])]
    years_min, years_max = sel_years
    latest_year = years_max

    # --- Header
    st.markdown(f"""
    <div class="banner">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
            <div>
                <div class="badge">Econometric Intelligence</div>
                <h1 style="margin:8px 0;color:{GOLD};">ASEAN FDI → GDP Growth Dynamics</h1>
                <div style="opacity:0.9;">World Bank WDI · {years_min}–{years_max}</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.9rem;">Updated: 2025</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Summary KPIs
    df_latest = df[df["Year"] == latest_year]
    mean_gdp = df_latest["GDP_Growth"].mean().round(2)
    mean_fdi = df_latest["FDI_PctGDP"].mean().round(2)
    corr_all = df["GDP_Growth"].corr(df["FDI_PctGDP"])
    rel, txt = interpret_corr(corr_all)

    c1, c2, c3 = st.columns(3)
    c1.metric("GDP Growth (avg)", f"{mean_gdp}%")
    c2.metric("FDI (% of GDP, avg)", f"{mean_fdi}%")
    c3.metric("FDI–GDP Correlation", f"{corr_all:.2f}")
    st.info(f"Hubungan keseluruhan bersifat **{rel}** — {txt}")

    # ==========================================================
    # Tabs
    # ==========================================================
    tab_corr, tab_trend, tab_granger, tab_var, tab_panel, tab_policy = st.tabs(
        ["📊 Korelasi", "📈 Tren", "🧠 Granger", "📣 VAR–IRF", "📘 Panel FE", "🎯 Simulasi Kebijakan"]
    )

    # --- Korelasi per negara
    with tab_corr:
        st.markdown("### 📊 Korelasi FDI dan GDP per Negara")
        country = st.selectbox("Pilih negara:", sorted(df["Country Name"].unique()))
        d = df[df["Country Name"] == country]
        r = d["GDP_Growth"].corr(d["FDI_PctGDP"])
        rel, txt = interpret_corr(r)

        fig = px.scatter(
            d, x="FDI_PctGDP", y="GDP_Growth",
            trendline="ols", color_discrete_sequence=["#0EA5A4"],
            title=f"{country}: FDI vs GDP Growth"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Korelasi {r:.2f} → {rel}, {txt}")

        # ASEAN bar chart
        corr_df = df.groupby("Country Name")[["FDI_PctGDP", "GDP_Growth"]].corr().iloc[0::2, -1].reset_index()
        corr_df = corr_df.rename(columns={"GDP_Growth": "Correlation"})
        fig_bar = px.bar(
            corr_df.sort_values("Correlation", ascending=False),
            x="Correlation", y="Country Name", color="Correlation",
            color_continuous_scale="RdBu", range_color=[-1, 1],
            title="ASEAN FDI–GDP Correlation Overview"
        )
        fig_bar.update_layout(height=500, coloraxis_showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- Tren per negara
    with tab_trend:
        st.markdown("### 📈 Perbandingan Tren GDP & FDI")
        country = st.selectbox("Pilih negara untuk tren:", sorted(df["Country Name"].unique()), key="trend")
        d = df[df["Country Name"] == country]
        d_melt = d.melt(id_vars=["Year"], value_vars=["GDP_Growth", "FDI_PctGDP"],
                        var_name="Indicator", value_name="Value")
        fig2 = px.line(
            d_melt, x="Year", y="Value", color="Indicator",
            markers=True, title=f"{country}: GDP Growth vs FDI Trend"
        )
        st.plotly_chart(fig2, use_container_width=True)

    # --- Granger causality
    with tab_granger:
        st.markdown("### 🧠 Uji Granger Causality — Apakah FDI memprediksi GDP?")
        country = st.selectbox("Negara:", sorted(df["Country Name"].unique()), key="granger")
        d = df[df["Country Name"] == country].sort_values("Year")[["GDP_Growth", "FDI_PctGDP"]].dropna()

        if len(d) < 6:
            st.warning("Data terlalu sedikit untuk uji Granger.")
        else:
            res = grangercausalitytests(d, maxlag=3, verbose=False)
            pvals = [res[i][0]["ssr_ftest"][1] for i in range(1, 4)]
            tbl = pd.DataFrame({"Lag": [1, 2, 3], "p-value": pvals})
            st.dataframe(tbl, use_container_width=True)
            if min(pvals) < 0.05:
                st.success("✅ FDI secara statistik memprediksi GDP (Granger causality terdeteksi).")
            else:
                st.warning("⚠️ Tidak ada bukti kuat FDI memprediksi GDP.")

    # --- VAR & Impulse Response
    with tab_var:
        st.markdown("### 📣 Impulse Response Function (IRF) — Dinamika Jangka Pendek")
        country = st.selectbox("Pilih negara:", sorted(df["Country Name"].unique()), key="irf")
        d = df[df["Country Name"] == country][["GDP_Growth", "FDI_PctGDP"]].dropna()
        if len(d) < 8:
            st.warning("Data belum cukup untuk model VAR.")
        else:
            from statsmodels.tsa.api import VAR
            model = VAR(d)
            sel = model.select_order(maxlags=3)
            p = int(sel.selected_orders.get("aic", 1) or 1)
            res = model.fit(p)
            irf = res.irf(5)
            irf_vals = irf.irfs[:, 0, 1]
            horizon = np.arange(len(irf_vals))
            fig_irf = go.Figure(go.Scatter(x=horizon, y=irf_vals, mode="lines+markers"))
            fig_irf.update_layout(title=f"IRF: Shock FDI → GDP Growth ({country})",
                                  xaxis_title="Years after shock",
                                  yaxis_title="Δ GDP Growth (pp)")
            st.plotly_chart(fig_irf, use_container_width=True)

    # --- Panel Regression (Fixed Effects)
    with tab_panel:
        st.markdown("### 📘 Panel Regression (Fixed Effects Model)")
        st.caption("Mengestimasi pengaruh FDI terhadap GDP Growth dengan kontrol FE per negara & tahun.")

        panel = df.set_index(["Country Name", "Year"]).sort_index()
        panel["GDP_Growth_l1"] = panel.groupby(level=0)["GDP_Growth"].shift(1)
        pdata = panel.dropna(subset=["GDP_Growth", "FDI_PctGDP", "GDP_Growth_l1"])

        try:
            if HAS_LM:
                model = PanelOLS.from_formula(
                    "GDP_Growth ~ 1 + FDI_PctGDP + GDP_Growth_l1 + EntityEffects + TimeEffects",
                    data=pdata
                )
                res = model.fit(cov_type="clustered", cluster_entity=True)
                st.text(res.summary.as_text())
                coef = res.params.get("FDI_PctGDP", np.nan)
                pval = res.pvalues.get("FDI_PctGDP", np.nan)
            else:
                pdata_ = pdata.reset_index()
                X = sm.add_constant(pdata_[["FDI_PctGDP", "GDP_Growth_l1"]])
                y = pdata_["GDP_Growth"]
                model = sm.OLS(y, X).fit()
                st.text(model.summary().as_text())
                coef = model.params["FDI_PctGDP"]
                pval = model.pvalues["FDI_PctGDP"]

            if pd.notna(coef):
                st.success(
                    f"Koefisien FDI = {coef:.3f}, {p_text(pval)} ⇒ "
                    f"kenaikan 1 pp FDI/GDP diperkirakan menaikkan GDP growth ~{coef:.2f} pp."
                )
        except Exception as e:
            st.error(f"Gagal estimasi panel FE: {e}")

    # --- Policy Simulation
    with tab_policy:
        st.markdown("### 🎯 Simulasi Kebijakan: Dampak Kenaikan FDI terhadap GDP Growth")
        uplift = st.slider("Kenaikan FDI (% of GDP)", 0.0, 5.0, 1.0, 0.1)
        try:
            model = sm.OLS(pdata["GDP_Growth"], sm.add_constant(pdata[["FDI_PctGDP", "GDP_Growth_l1"]])).fit()
            coef = model.params["FDI_PctGDP"]
            pred = coef * uplift
            st.success(
                f"Jika FDI meningkat **{uplift:.1f}% PDB**, model memprediksi GDP growth naik ≈ **{pred:.2f} pp**."
            )
        except Exception:
            st.warning("Model belum dapat disimulasikan.")
