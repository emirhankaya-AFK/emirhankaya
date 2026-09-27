"""
Portfolio Risk Terminal - Institutional Analytics Dashboard
===========================================================
Institutional Risk Terminal adhering to the high-density corporate finance standard:
- Dark navy-slate palette (#0B0F14, #121923, #17212D) with subtle borders (#263241)
- Institutional blue (#4C8DFF) interactive accents, semantic gain (#27C281) & loss (#EF6461)
- Narrow 256px sidebar with 4 structured control groups
- Single-row compact header bar with real-time provenance badges
- 5-section information architecture: Overview, Allocation, Risk, Stress Tests, Methodology
- Tabular numeric alignment (font-variant-numeric: tabular-nums) for institutional finance
- Zero synthetic/fake metrics: 100% genuine multi-step Monte Carlo, analytical Cornish-Fisher ES,
  and BCBS CRE53 Basel III backtesting
- Full mathematical integrity & multi-currency normalization (TRY / USD)
"""

import os
import sys
import time
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Append project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.data_loader import (
    load_market_data,
    get_asset_universe,
    get_human_name,
    get_benchmark_weights,
    calculate_cumulative_performance,
    get_dataset_metadata,
    ASSET_METADATA
)
from src.portfolio_optimizer import (
    shrink_covariance_ledoit_wolf,
    portfolio_performance,
    optimize_max_sharpe,
    optimize_min_volatility,
    optimize_target_return,
    calculate_efficient_frontier,
    generate_monte_carlo_portfolios
)
from src.black_litterman import BlackLittermanModel
from src.risk_engine import (
    compute_portfolio_returns,
    calculate_parametric_var_cvar,
    calculate_historical_var_cvar,
    calculate_monte_carlo_var_cvar,
    GARCH11,
    simulate_stress_test,
    STRESS_SCENARIOS,
    run_var_backtest
)
from src.data_adapter import SyntheticCSVAdapter, YahooFinanceAdapter
import importlib
import dashboard.theme
importlib.reload(dashboard.theme)
from dashboard.theme import (
    THEME_COLORS,
    CHART_COLOR_PALETTE,
    PLOTLY_TERMINAL_THEME,
    TERMINAL_CUSTOM_CSS
)

st.set_page_config(
    page_title="Portfolio Risk Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto"
)

# Render design system stylesheet
st.markdown(TERMINAL_CUSTOM_CSS, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SECURITY SETTINGS
# -----------------------------------------------------------------------------
ENABLE_SHUTDOWN = os.environ.get("ENABLE_SHUTDOWN", "false").lower() in ["true", "1", "yes"]

if "confirm_shutdown" not in st.session_state:
    st.session_state["confirm_shutdown"] = False

# Shutdown Confirmation Dialog / Warning Card
if ENABLE_SHUTDOWN and st.session_state.get("confirm_shutdown", False):
    st.warning("⚠️ **DİKKAT:** Streamlit yerel sunucusu tamamen sonlandırılmak üzeredir. Devam etmek istiyor musunuz?")
    col_c1, col_c2, _ = st.columns([0.22, 0.22, 0.56])
    with col_c1:
        if st.button("🛑 Evet, Sunucuyu Kapat", key="btn_confirm_shutdown_yes", type="primary"):
            st.error("🛑 Sunucu durduruluyor... Bu tarayıcı sekmesini kapatabilirsiniz.")
            time.sleep(1)
            os._exit(0)
    with col_c2:
        if st.button("❌ Vazgeç / İptal", key="btn_confirm_shutdown_no"):
            st.session_state["confirm_shutdown"] = False
            st.rerun()

# -----------------------------------------------------------------------------
# SIDEBAR CONTROLS (Narrow, 4 Logical Groups)
# -----------------------------------------------------------------------------
st.sidebar.markdown("""
<div style="padding: 4px 0 12px 0;">
    <div style="font-size: 0.88rem; font-weight: 700; letter-spacing: 0.05em; color: #E7EDF4;">
        <span class="status-dot-green"></span>RISK TERMINAL
    </div>
    <div style="font-size: 0.72rem; color: #8E9BAA; margin-top: 2px;">
        Institutional Portfolio Analytics
    </div>
</div>
""", unsafe_allow_html=True)

# Section 1: Data Source
st.sidebar.markdown('<div class="sidebar-section-title">1. Data Source</div>', unsafe_allow_html=True)
data_source_mode = st.sidebar.selectbox(
    "Veri Kaynağı",
    options=[
        "Sentetik Kurumsal Veri (GBM + Student-t)",
        "Yahoo Finance (Günlük Piyasa Kapanışları)"
    ],
    index=0,
    help="Portföy analitiğinde kullanılacak veri seti. 'Sentetik' çevrimdışı ve deterministiktir; 'Yahoo Finance' internetten güncel kapanışları çeker."
)

# Section 2: Portfolio Currency
st.sidebar.markdown('<div class="sidebar-section-title">2. Portfolio Currency</div>', unsafe_allow_html=True)
base_currency = st.sidebar.selectbox(
    "Baz Para Birimi",
    options=["TRY", "USD"],
    index=0,
    help="Tüm varlık getirileri ve riskler seçilen bu para birimine dönüştürülerek hesaplanır (BIST için TRY, küresel varlıklar için USD/TRY kuru kullanılır)."
)

# Section 3: Risk Parameters
st.sidebar.markdown('<div class="sidebar-section-title">3. Risk Parameters</div>', unsafe_allow_html=True)
risk_free_rate = st.sidebar.slider(
    f"Risksiz Faiz Oranı ({base_currency})",
    min_value=0.01,
    max_value=0.25 if base_currency == "TRY" else 0.10,
    value=0.15 if base_currency == "TRY" else 0.045,
    step=0.005,
    format="%.1f%%",
    help=f"{base_currency} cinsinden risksiz faiz oranı (TR mevduat/tahvil veya US Treasury)."
)

# Section 4: Model Settings
st.sidebar.markdown('<div class="sidebar-section-title">4. Model Settings</div>', unsafe_allow_html=True)
use_ledoit_wolf = st.sidebar.toggle(
    "Ledoit-Wolf Büzülme",
    value=True,
    help="Örneklem kovaryans matrisinin gürültüsünü azaltarak kondisyon sayısını iyileştirir."
)

# Server Control (Discreet footer utility)
st.sidebar.markdown('<div class="sidebar-section-title">System Utility</div>', unsafe_allow_html=True)
if ENABLE_SHUTDOWN:
    with st.sidebar.expander("⚙️ Sunucu Yönetimi", expanded=False):
        if st.button("⏻ Sunucuyu Kapat (Stop)", key="sidebar_shutdown_btn", use_container_width=True):
            st.session_state["confirm_shutdown"] = True
else:
    st.sidebar.markdown('<div style="font-size: 0.72rem; color: #8E9BAA; padding: 4px 0;">🔒 Güvenli Sunucu (Kapatma Pasif)</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# DATA LOADING & INITIALIZATION
# -----------------------------------------------------------------------------
@st.cache_data
def get_cached_market_data(currency: str, source_label: str):
    if "Yahoo Finance" in source_label:
        try:
            adapter = YahooFinanceAdapter()
            prices_df, returns_df, ann_returns, ann_cov = load_market_data(
                base_currency=currency, adapter=adapter
            )
            meta = get_dataset_metadata(prices_df, is_synthetic=False, source_name="Yahoo Finance")
            return prices_df, returns_df, ann_returns, ann_cov, meta, None
        except Exception as e:
            prices_df, returns_df, ann_returns, ann_cov = load_market_data(base_currency=currency)
            meta = get_dataset_metadata(prices_df, is_synthetic=True)
            return prices_df, returns_df, ann_returns, ann_cov, meta, str(e)
    else:
        prices_df, returns_df, ann_returns, ann_cov = load_market_data(base_currency=currency)
        meta = get_dataset_metadata(prices_df, is_synthetic=True)
        return prices_df, returns_df, ann_returns, ann_cov, meta, None

prices_df, returns_df, ann_returns, ann_cov, meta_info, load_warning = get_cached_market_data(base_currency, data_source_mode)

if load_warning:
    st.sidebar.warning(f"Yahoo Finance verisi yüklenemedi ({load_warning}). Sentetik veriye geçildi.")

asset_keys = get_asset_universe()
benchmark_weights = get_benchmark_weights()

if use_ledoit_wolf:
    cov_matrix, shrinkage_delta = shrink_covariance_ledoit_wolf(returns_df, annualize=True)
else:
    cov_matrix = ann_cov.values
    shrinkage_delta = 0.0

expected_returns = ann_returns.values

# Pre-calculate active portfolio for high-level indicators
max_sharpe_opt = optimize_max_sharpe(expected_returns, cov_matrix, risk_free_rate)
min_vol_opt = optimize_min_volatility(expected_returns, cov_matrix, risk_free_rate)
active_weights = max_sharpe_opt["weights"] if max_sharpe_opt["success"] else benchmark_weights
port_ret_series = compute_portfolio_returns(returns_df, active_weights)

# -----------------------------------------------------------------------------
# COMPACT TOP BAR HEADER
# -----------------------------------------------------------------------------
provenance_badge_class = "terminal-badge-synthetic" if meta_info["is_synthetic"] else "terminal-badge-live"
provenance_badge_text = "● SYNTHETIC" if meta_info["is_synthetic"] else "● LIVE FEED"

st.markdown(f"""
<div class="terminal-header">
    <div class="terminal-title-group">
        <div class="terminal-title">Portfolio Risk Terminal</div>
        <span class="terminal-badge terminal-badge-info">v2.1</span>
        <span class="terminal-badge {provenance_badge_class}">{provenance_badge_text}</span>
    </div>
    <div class="header-metadata">
        <div class="meta-item"><span class="meta-label">Gözlem:</span> <span class="meta-value">{meta_info['n_trading_days']}G</span></div>
        <div class="meta-item"><span class="meta-label">Baz Kur:</span> <span class="meta-value">{base_currency}</span></div>
        <div class="meta-item"><span class="meta-label">Dönem:</span> <span class="meta-value">{meta_info['start_date']} — {meta_info['end_date']}</span></div>
        <div class="meta-item"><span class="meta-label">Evren:</span> <span class="meta-value">{len(asset_keys)} Varlık</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

if meta_info["is_synthetic"]:
    with st.expander("ℹ️ Veri Kümesi Provenance & Şeffaflık Detayı", expanded=False):
        st.markdown(f"""
        Gösterilen getiri serileri, Geometrik Brownian Hareketi (GBM) ve Student-t ($df=7$) ağır kuyruk şok simülasyonuyla üretilmiş kurumsal sentetik veri kümesidir (Tohum: `{meta_info['seed']}`).
        Yan menüden **Yahoo Finance** seçeneği kullanılarak gerçek piyasa kapanışlarına geçilebilir.
        """)

# -----------------------------------------------------------------------------
# 5-SECTION MAIN NAVIGATION
# -----------------------------------------------------------------------------
nav_tab1, nav_tab2, nav_tab3, nav_tab4, nav_tab5 = st.tabs([
    "Overview",
    "Allocation",
    "Risk",
    "Stress Tests",
    "Methodology"
])

# =============================================================================
# 1. OVERVIEW (GENEL BAKIŞ)
# =============================================================================
with nav_tab1:
    # 4 Top KPI Cards
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    port_exp_ret = max_sharpe_opt['expected_return'] if max_sharpe_opt['success'] else float(np.dot(benchmark_weights, expected_returns))
    port_vol = max_sharpe_opt['volatility'] if max_sharpe_opt['success'] else float(np.sqrt(np.dot(benchmark_weights.T, np.dot(cov_matrix, benchmark_weights))))
    port_sharpe = max_sharpe_opt['sharpe_ratio'] if max_sharpe_opt['success'] else ((port_exp_ret - risk_free_rate) / port_vol if port_vol > 0 else 0.0)
    p_1d_quick = calculate_parametric_var_cvar(port_ret_series, confidence_level=0.99, horizon_days=1)
    
    with kpi_col1:
        ret_color = "#27C281" if port_exp_ret >= 0 else "#EF6461"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Beklenen Yıllık Getiri ({base_currency})</div>
            <div class="metric-value" style="color: {ret_color};">+{port_exp_ret*100:.2f}%</div>
            <div class="metric-sub">Optimal Max Sharpe Portföyü</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Yıllıklandırılmış Volatilite</div>
            <div class="metric-value" style="color: #E7EDF4;">{port_vol*100:.2f}%</div>
            <div class="metric-sub">Kovaryans Standart Sapması</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Sharpe Oranı</div>
            <div class="metric-value" style="color: #4C8DFF;">{port_sharpe:.2f}</div>
            <div class="metric-sub">Rf: %{risk_free_rate*100:.1f} Üzeri Fazla Getiri</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">1 Günlük %99 Parametrik VaR</div>
            <div class="metric-value" style="color: #EF6461;">%{p_1d_quick['gaussian_var']*100:.2f}</div>
            <div class="metric-sub">Basel Standart 1-Günlük Risk</div>
        </div>
        """, unsafe_allow_html=True)

    # Row 2: Portfolio Growth & Current Allocation
    row2_col1, row2_col2 = st.columns([0.62, 0.38])
    
    with row2_col1:
        st.markdown("<div class='surface-card-title'>Kümülatif Varlık Büyümesi (Baz: 100 " + base_currency + ")</div>", unsafe_allow_html=True)
        cum_df = calculate_cumulative_performance(returns_df, base_val=100.0)
        cum_df_display = cum_df.rename(columns={k: get_human_name(k, "tr") for k in asset_keys})
        
        fig_cum = px.line(
            cum_df_display,
            labels={"value": f"Değer ({base_currency})", "date": "Tarih", "variable": ""},
            color_discrete_sequence=CHART_COLOR_PALETTE
        )
        fig_cum.update_layout(
            PLOTLY_TERMINAL_THEME,
            height=340,
            margin=dict(l=35, r=20, t=35, b=35),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0, font=dict(size=10))
        )
        st.plotly_chart(fig_cum, use_container_width=True)
        
    with row2_col2:
        st.markdown("<div class='surface-card-title'>Varlık Dağılımı (Optimal vs Gösterge)</div>", unsafe_allow_html=True)
        human_names = [get_human_name(k, "tr") for k in asset_keys]
        alloc_df = pd.DataFrame({
            "Varlık": human_names,
            "Optimal": active_weights * 100,
            "Gösterge": benchmark_weights * 100
        })
        fig_alloc = go.Figure()
        fig_alloc.add_trace(go.Bar(
            name="Optimal",
            y=alloc_df["Varlık"],
            x=alloc_df["Optimal"],
            orientation='h',
            marker_color="#4C8DFF"
        ))
        fig_alloc.add_trace(go.Bar(
            name="Gösterge",
            y=alloc_df["Varlık"],
            x=alloc_df["Gösterge"],
            orientation='h',
            marker_color="#263241"
        ))
        fig_alloc.update_layout(
            PLOTLY_TERMINAL_THEME,
            barmode='group',
            height=340,
            margin=dict(l=15, r=20, t=35, b=35),
            xaxis_title="Ağırlık (%)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0, font=dict(size=10))
        )
        st.plotly_chart(fig_alloc, use_container_width=True)

    # Row 3: Correlation Heatmap & Asset Properties Table
    row3_col1, row3_col2 = st.columns([0.55, 0.45])
    with row3_col1:
        st.markdown("<div class='surface-card-title'>Çapraz Korelasyon Matrisi</div>", unsafe_allow_html=True)
        corr_matrix = returns_df.corr().round(2)
        fig_corr = px.imshow(
            corr_matrix.values,
            x=human_names,
            y=human_names,
            color_continuous_scale=[[0.0, "#121923"], [0.5, "#17212D"], [1.0, "#4C8DFF"]],
            zmin=-0.4,
            zmax=1.0,
            text_auto=True,
            labels=dict(color="Korelasyon")
        )
        fig_corr.update_layout(PLOTLY_TERMINAL_THEME, height=330)
        fig_corr.update_xaxes(tickangle=35)
        st.plotly_chart(fig_corr, use_container_width=True)
        
    with row3_col2:
        st.markdown("<div class='surface-card-title'>Varlık Evreni & Özellikleri</div>", unsafe_allow_html=True)
        asset_summary_rows = []
        for k in asset_keys:
            meta = ASSET_METADATA.get(k, {})
            ann_r = ann_returns.get(k, 0.0)
            ann_v = float(np.sqrt(ann_cov.loc[k, k])) if k in ann_cov.index else 0.0
            asset_summary_rows.append({
                "Varlık": get_human_name(k, "tr"),
                "Sınıf": meta.get("category", "Bilinmiyor"),
                "Para": meta.get("currency", "-"),
                "Getiri": f"{ann_r*100:+.1f}%",
                "Volatilite": f"{ann_v*100:.1f}%"
            })
        st.dataframe(pd.DataFrame(asset_summary_rows), use_container_width=True, hide_index=True)


# =============================================================================
# 2. ALLOCATION (VARLIK DAĞILIMI & OPTİMİZASYON)
# =============================================================================
with nav_tab2:
    alloc_sub = st.radio(
        "Optimizasyon Modeli Seçimi:",
        options=["Markowitz Etkin Sınır", "Bayesian Black-Litterman"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if alloc_sub == "Markowitz Etkin Sınır":
        frontier_points = calculate_efficient_frontier(expected_returns, cov_matrix, risk_free_rate, n_points=40)
        
        # Solver diagnostic alert (single compact line)
        if max_sharpe_opt["success"]:
            st.caption(f"✓ Çözücü Durumu: {max_sharpe_opt['solver_message']} • Etkin Sınırda {len(frontier_points)} nokta üretildi.")
        else:
            st.warning(f"Optimizasyon Uyarısı: {max_sharpe_opt['solver_message']}")
            
        m_col1, m_col2 = st.columns([0.62, 0.38])
        with m_col1:
            st.markdown("<div class='surface-card-title'>Markowitz Etkin Sınır & 4.000 Portföy Bulutu</div>", unsafe_allow_html=True)
            mc_data = generate_monte_carlo_portfolios(expected_returns, cov_matrix, risk_free_rate, n_portfolios=4000)
            
            fig_mpt = go.Figure()
            fig_mpt.add_trace(go.Scatter(
                x=mc_data["volatilities"] * 100,
                y=mc_data["returns"] * 100,
                mode='markers',
                marker=dict(
                    size=3,
                    color=mc_data["sharpe_ratios"],
                    colorscale=[[0, "#1E293B"], [0.5, "#4C8DFF"], [1, "#27C281"]],
                    showscale=True,
                    colorbar=dict(title=dict(text="Sharpe", font=dict(size=10, color="#8E9BAA")), len=0.6, thickness=12)
                ),
                name="4.000 Simülasyon",
                hovertemplate="Volatilite: %{x:.2f}%<br>Getiri: %{y:.2f}%<br>Sharpe: %{marker.color:.2f}<extra></extra>"
            ))
            
            if frontier_points:
                f_vols = [p["volatility"] * 100 for p in frontier_points]
                f_rets = [p["return"] * 100 for p in frontier_points]
                fig_mpt.add_trace(go.Scatter(
                    x=f_vols,
                    y=f_rets,
                    mode='lines',
                    line=dict(color='#4C8DFF', width=2.5),
                    name="Etkin Sınır Eğrisi"
                ))
            
            if max_sharpe_opt["success"]:
                fig_mpt.add_trace(go.Scatter(
                    x=[max_sharpe_opt["volatility"] * 100],
                    y=[max_sharpe_opt["expected_return"] * 100],
                    mode='markers+text',
                    marker=dict(color='#E5A83A', size=11, symbol='star', line=dict(color='#FFFFFF', width=1)),
                    text=["Max Sharpe"],
                    textposition="top left",
                    name="Maksimum Sharpe"
                ))
                
            if min_vol_opt["success"]:
                fig_mpt.add_trace(go.Scatter(
                    x=[min_vol_opt["volatility"] * 100],
                    y=[min_vol_opt["expected_return"] * 100],
                    mode='markers+text',
                    marker=dict(color='#27C281', size=10, symbol='diamond', line=dict(color='#FFFFFF', width=1)),
                    text=["Min Vol"],
                    textposition="bottom right",
                    name="Minimum Volatilite"
                ))
                
            fig_mpt.update_layout(
                PLOTLY_TERMINAL_THEME,
                height=420,
                margin=dict(l=35, r=20, t=35, b=35),
                xaxis_title="Yıllıklandırılmış Volatilite %",
                yaxis_title=f"Beklenen Yıllık Getiri ({base_currency}) %",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0, font=dict(size=10))
            )
            st.plotly_chart(fig_mpt, use_container_width=True)
            
        with m_col2:
            st.markdown("<div class='surface-card-title'>Optimal Ağırlıklar & Dağılım Metrikleri</div>", unsafe_allow_html=True)
            if max_sharpe_opt["success"]:
                opt_weights = max_sharpe_opt["weights"]
                human_names = [get_human_name(k, "tr") for k in asset_keys]
                
                weights_comp_df = pd.DataFrame({
                    "Varlık": human_names,
                    "Optimal": [f"{w*100:.1f}%" for w in opt_weights],
                    "Gösterge": [f"{bw*100:.1f}%" for bw in benchmark_weights],
                    "Fark": [f"{(w - bw)*100:+.1f}%" for w, bw in zip(opt_weights, benchmark_weights)]
                })
                st.dataframe(weights_comp_df, use_container_width=True, hide_index=True)
                
                st.markdown(f"""
                <div class="surface-card" style="margin-top: 14px; padding: 12px 14px;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 4px;">
                        <span style="color: #8E9BAA;">Beklenen Yıllık Getiri:</span>
                        <span style="font-weight: 600; color: #27C281;">+{max_sharpe_opt['expected_return']*100:.2f}%</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 4px;">
                        <span style="color: #8E9BAA;">Yıllık Volatilite:</span>
                        <span style="font-weight: 600; color: #E7EDF4;">{max_sharpe_opt['volatility']*100:.2f}%</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.82rem;">
                        <span style="color: #8E9BAA;">Sharpe Oranı:</span>
                        <span style="font-weight: 600; color: #4C8DFF;">{max_sharpe_opt['sharpe_ratio']:.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("Optimal ağırlıklar kısıtların fizibıl olmaması sebebiyle hesaplanamadı.")
                
    else:  # Bayesian Black-Litterman
        st.markdown("<div class='surface-card-title'>Bayesian Black-Litterman Varlık Dağılım Modeli</div>", unsafe_allow_html=True)
        st.caption("Piyasa CAPM denge getirilerini (Prior) yatırımcının sübjektif görüşleri (Views) ve güven düzeyleri ile Bayesyen harmanlar.")
        
        bl_model = BlackLittermanModel(
            asset_names=asset_keys,
            cov_matrix=cov_matrix,
            benchmark_weights=benchmark_weights,
            expected_returns=expected_returns,
            risk_free_rate=risk_free_rate,
            tau=0.04
        )
        
        bl_col1, bl_col2 = st.columns([0.40, 0.60])
        with bl_col1:
            st.markdown("<div style='font-size: 0.82rem; font-weight: 600; color: #8E9BAA; margin-bottom: 8px;'>Yatırımcı Görüşleri (Views)</div>", unsafe_allow_html=True)
            
            bist_sp_spread = st.slider(
                "Görüş 1 (Göreceli): BIST 100 S&P 500'ü ne kadar aşacak?",
                min_value=-0.10,
                max_value=0.20,
                value=0.06,
                step=0.01,
                format="%.1f%%"
            )
            conf_1 = st.slider("Görüş 1 Güven Düzeyi", 0.10, 0.95, 0.75, 0.05, format="%.0f%%")
            
            gold_ret_view = st.slider(
                f"Görüş 2 (Mutlak): Altın Ons Beklenen Getiri ({base_currency})",
                min_value=0.00,
                max_value=0.45 if base_currency == "TRY" else 0.25,
                value=0.25 if base_currency == "TRY" else 0.12,
                step=0.01,
                format="%.1f%%"
            )
            conf_2 = st.slider("Görüş 2 Güven Düzeyi", 0.10, 0.95, 0.80, 0.05, format="%.0f%%")
            
            P = np.zeros((2, len(asset_keys)))
            P[0, asset_keys.index("bist_100")] = 1.0
            P[0, asset_keys.index("sp_500")] = -1.0
            P[1, asset_keys.index("gold")] = 1.0
            
            Q = np.array([bist_sp_spread, gold_ret_view])
            confidences = [conf_1, conf_2]
            
            bl_results = bl_model.run_bayesian_update(P, Q, confidences=confidences)
            
        with bl_col2:
            human_names = [get_human_name(k, "tr") for k in asset_keys]
            prior_ret = bl_results["implied_prior_returns"] * 100
            post_ret = bl_results["posterior_returns"] * 100
            hist_ret = expected_returns * 100
            
            fig_bl = go.Figure()
            fig_bl.add_trace(go.Bar(name="Piyasa Denge Getirisi (Prior)", x=human_names, y=prior_ret, marker_color="#263241"))
            fig_bl.add_trace(go.Bar(name="Black-Litterman Posterior", x=human_names, y=post_ret, marker_color="#4C8DFF"))
            fig_bl.add_trace(go.Bar(name="Tarihsel Örneklem", x=human_names, y=hist_ret, marker_color="#27C281"))
            fig_bl.update_layout(
                PLOTLY_TERMINAL_THEME,
                barmode='group',
                height=320,
                margin=dict(l=35, r=20, t=35, b=35),
                yaxis_title=f"Yıllık Getiri ({base_currency}) %",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0, font=dict(size=10))
            )
            fig_bl.update_xaxes(tickangle=35)
            st.plotly_chart(fig_bl, use_container_width=True)
            
            bl_weights_df = pd.DataFrame({
                "Varlık": human_names,
                "Gösterge": [f"{bw*100:.1f}%" for bw in benchmark_weights],
                "BL Optimal": [f"{w*100:.1f}%" for w in bl_results["optimal_weights"]],
                "Net Değişim": [f"{(w - bw)*100:+.1f}%" for w, bw in zip(bl_results["optimal_weights"], benchmark_weights)]
            })
            st.dataframe(bl_weights_df, use_container_width=True, hide_index=True)


# =============================================================================
# 3. RISK ANALYTICS, MULTI-DAY VaR/CVaR & GARCH VOLATILITY
# =============================================================================
with nav_tab3:
    r_hz_col1, r_hz_col2 = st.columns([0.5, 0.5])
    with r_hz_col1:
        risk_horizon = st.radio(
            "Risk Zaman Ufku Seçimi (Holding Period Horizon):",
            options=["1 Günlük (Daily)", "10 Günlük (10-Day Real Rolling Compound)"],
            index=0,
            horizontal=True
        )
    horizon_days = 1 if "1 Gün" in risk_horizon else 10
    
    # Real risk calculations for both 1-day and 10-day
    p_1d = calculate_parametric_var_cvar(port_ret_series, confidence_level=0.95, horizon_days=1)
    p_10d = calculate_parametric_var_cvar(port_ret_series, confidence_level=0.95, horizon_days=10)
    h_1d_v, h_1d_cv = calculate_historical_var_cvar(port_ret_series, confidence_level=0.95, horizon_days=1)
    h_10d_v, h_10d_cv = calculate_historical_var_cvar(port_ret_series, confidence_level=0.95, horizon_days=10)
    
    mc_1d_v, mc_1d_cv, sim_paths_1d = calculate_monte_carlo_var_cvar(
        port_ret_series, confidence_level=0.95, horizon_days=1, n_simulations=10000
    )
    mc_10d_v, mc_10d_cv, sim_paths_10d = calculate_monte_carlo_var_cvar(
        port_ret_series, confidence_level=0.95, horizon_days=10, n_simulations=10000
    )
    
    param_risk_95 = p_1d if horizon_days == 1 else p_10d
    hist_var_95 = h_1d_v if horizon_days == 1 else h_10d_v
    mc_var_95 = mc_1d_v if horizon_days == 1 else mc_10d_v
    mc_cvar_95 = mc_1d_cv if horizon_days == 1 else mc_10d_cv
    sim_paths = sim_paths_1d if horizon_days == 1 else sim_paths_10d
    
    # 4 Metric Cards
    r_col1, r_col2, r_col3, r_col4 = st.columns(4)
    with r_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{horizon_days}G Parametrik VaR (%95)</div>
            <div class="metric-value" style="color: #EF6461;">%{param_risk_95['gaussian_var']*100:.2f}</div>
            <div class="metric-sub">Normal Dağılım Güven Aralığı</div>
        </div>
        """, unsafe_allow_html=True)
    with r_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Cornish-Fisher CVaR (%95)</div>
            <div class="metric-value" style="color: #EF6461;">%{param_risk_95['cornish_fisher_cvar']*100:.2f}</div>
            <div class="metric-sub">Analitik Kapalı Formül ES ({'10G Bileşik' if horizon_days > 1 else '1G Momentli'})</div>
        </div>
        """, unsafe_allow_html=True)
    with r_col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{horizon_days}G Tarihsel VaR (%95)</div>
            <div class="metric-value" style="color: #E5A83A;">%{hist_var_95*100:.2f}</div>
            <div class="metric-sub">Ampirik Getiri Dağılımı</div>
        </div>
        """, unsafe_allow_html=True)
    with r_col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Monte Carlo VaR (%95)</div>
            <div class="metric-value" style="color: #4C8DFF;">%{mc_var_95*100:.2f}</div>
            <div class="metric-sub">10.000 Ağır Kuyruklu t-Yolu ({'10 Adımlı' if horizon_days > 1 else '1 Günlük'})</div>
        </div>
        """, unsafe_allow_html=True)
        
    # Horizon Comparison Matrix Table
    st.markdown("<div class='surface-card-title' style='margin-top: 10px;'>1 Günlük ve 10 Günlük Risk Karşılaştırma Matrisi</div>", unsafe_allow_html=True)
    risk_summary_df = pd.DataFrame({
        "Risk Ölçüm Metodu": [
            "Parametrik Normal Dağılım (Gaussian)",
            "Cornish-Fisher (Basıklık/Çarpıklık Düzeltmeli)",
            "Tarihsel Simülasyon (Bileşik Getiriler)",
            "Monte Carlo (10.000 t-Yolu)"
        ],
        "1G VaR (%95)": [
            f"%{p_1d['gaussian_var']*100:.2f}",
            f"%{p_1d['cornish_fisher_var']*100:.2f}",
            f"%{h_1d_v*100:.2f}",
            f"%{mc_1d_v*100:.2f}"
        ],
        "1G CVaR (%95)": [
            f"%{p_1d['gaussian_cvar']*100:.2f}",
            f"%{p_1d['cornish_fisher_cvar']*100:.2f}",
            f"%{h_1d_cv*100:.2f}",
            f"%{mc_1d_cv*100:.2f}"
        ],
        "10G VaR (%95)": [
            f"%{p_10d['gaussian_var']*100:.2f}",
            f"%{p_10d['cornish_fisher_var']*100:.2f}",
            f"%{h_10d_v*100:.2f}",
            f"%{mc_10d_v*100:.2f}"
        ],
        "10G CVaR (%95)": [
            f"%{p_10d['gaussian_cvar']*100:.2f}",
            f"%{p_10d['cornish_fisher_cvar']*100:.2f}",
            f"%{h_10d_cv*100:.2f}",
            f"%{mc_10d_cv*100:.2f}"
        ]
    })
    st.dataframe(risk_summary_df, use_container_width=True, hide_index=True)
    
    # Charts: MC Histogram & GARCH Volatility Projection
    rg_col1, rg_col2 = st.columns([0.55, 0.45])
    with rg_col1:
        st.markdown(f"<div class='surface-card-title'>{horizon_days} Günlük Monte Carlo Getiri Dağılımı ve Kuyruk Kesimleri</div>", unsafe_allow_html=True)
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(
            x=sim_paths * 100,
            nbinsx=80,
            marker_color="rgba(76, 141, 255, 0.55)",
            name="Simüle Edilen Getiriler"
        ))
        fig_hist.add_vline(x=-mc_var_95 * 100, line_width=2, line_dash="dash", line_color="#E5A83A",
                           annotation_text=f"VaR %95: -%{mc_var_95*100:.2f}", annotation_position="top left",
                           annotation_font=dict(size=10, color="#E5A83A"))
        fig_hist.add_vline(x=-mc_cvar_95 * 100, line_width=2, line_dash="solid", line_color="#EF6461",
                           annotation_text=f"CVaR %95: -%{mc_cvar_95*100:.2f}", annotation_position="bottom left",
                           annotation_font=dict(size=10, color="#EF6461"))
        fig_hist.update_layout(PLOTLY_TERMINAL_THEME, height=350, xaxis_title=f"{horizon_days} Günlük Getiri %", yaxis_title="Frekans")
        st.plotly_chart(fig_hist, use_container_width=True)
        
    with rg_col2:
        st.markdown("<div class='surface-card-title'>GARCH(1,1) Dinamik Koşullu Volatilite Projeksiyonu</div>", unsafe_allow_html=True)
        garch_model = GARCH11().fit(port_ret_series.values)
        if garch_model.is_fitted:
            vol_forecast = garch_model.forecast_volatility(n_days=30)
            recent_vol = garch_model.conditional_vol[-120:] * 100
            forecast_vol_pct = vol_forecast * 100
            
            days_hist = list(range(-119, 1))
            days_fc = list(range(1, 31))
            
            fig_garch = go.Figure()
            fig_garch.add_trace(go.Scatter(
                x=days_hist,
                y=recent_vol,
                mode='lines',
                line=dict(color='#4C8DFF', width=1.8),
                name="Tarihsel Koşullu (Son 120 Gün)"
            ))
            fig_garch.add_trace(go.Scatter(
                x=days_fc,
                y=forecast_vol_pct,
                mode='lines+markers',
                line=dict(color='#27C281', width=2, dash='dash'),
                marker=dict(size=4),
                name="30 Günlük Tahmin"
            ))
            fig_garch.add_vline(x=0, line_width=1.5, line_dash="dot", line_color="#8E9BAA")
            fig_garch.add_hline(
                y=garch_model.unconditional_vol * 100,
                line_dash="dot",
                line_color="#E5A83A",
                annotation_text=f"Uzun Vadeli (%{garch_model.unconditional_vol*100:.1f})",
                annotation_position="bottom right",
                annotation_font=dict(size=10, color="#E5A83A")
            )
            fig_garch.update_layout(
                PLOTLY_TERMINAL_THEME,
                height=350,
                margin=dict(l=35, r=20, t=35, b=35),
                xaxis_title="Gün",
                yaxis_title="Yıllık Volatilite %",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0, font=dict(size=10))
            )
            st.plotly_chart(fig_garch, use_container_width=True)
            st.caption(f"Log-Likelihood: {garch_model.log_likelihood:.2f} | α={garch_model.alpha:.4f}, β={garch_model.beta:.4f} (Kalıcılık: {garch_model.alpha+garch_model.beta:.4f})")
        else:
            st.warning(f"GARCH Modeli yakınsamadı: {garch_model.solver_message}")

    # Basel III / BCBS CRE53 Traffic Light & Kupiec POF Backtest
    st.markdown("<div class='surface-card-title' style='margin-top: 24px;'>Basel III / BCBS Trafik Işığı & Kupiec POF Geriye Dönük Risk Testi (Backtest)</div>", unsafe_allow_html=True)
    st.caption("Son 250 işlem gününde 1-günlük %99 VaR modelinin gerçekleşen portföy getirileri karşısındaki istatistiksel geçerlilik ve sermaye yeterlilik testi.")
    
    bt_res = run_var_backtest(port_ret_series, confidence_level=0.99, test_window=250, estimation_window=250)
    
    bt_col1, bt_col2, bt_col3, bt_col4 = st.columns(4)
    with bt_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Test Penceresi</div>
            <div class="metric-value">{bt_res['test_days']} Gün</div>
            <div class="metric-sub">Beklenen İhlal: {bt_res['expected_breaches']:.1f} gün (p=%1.0)</div>
        </div>
        """, unsafe_allow_html=True)
    with bt_col2:
        breach_color = "#27C281" if bt_res['breaches'] <= 4 else ("#E5A83A" if bt_res['breaches'] <= 9 else "#EF6461")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Gerçekleşen İhlal</div>
            <div class="metric-value" style="color: {breach_color};">{bt_res['breaches']} Gün</div>
            <div class="metric-sub">İhlal Oranı: %{bt_res['breach_rate']*100:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with bt_col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Kupiec POF LR Testi</div>
            <div class="metric-value" style="font-size: 1.25rem;">{bt_res['kupiec_decision']}</div>
            <div class="metric-sub">LR: {bt_res['kupiec_lr_stat']:.2f} (p={bt_res['kupiec_p_value']:.4f})</div>
        </div>
        """, unsafe_allow_html=True)
    with bt_col4:
        zone_color = "#27C281" if "GREEN" in bt_res['basel_zone'] else ("#E5A83A" if "YELLOW" in bt_res['basel_zone'] else "#EF6461")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Basel Bölgesi & Sermaye Çarpanı</div>
            <div class="metric-value" style="font-size: 1.25rem; color: {zone_color};">{bt_res['basel_zone'].split('(')[0].strip()}</div>
            <div class="metric-sub">BCBS CRE53 Çarpanı: {bt_res['basel_multiplier']:.2f}x</div>
        </div>
        """, unsafe_allow_html=True)
        
    fig_bt = go.Figure()
    fig_bt.add_trace(go.Scatter(
        x=bt_res['dates'],
        y=bt_res['actual_returns'] * 100,
        mode='lines',
        name="Gerçekleşen Getiri %",
        line=dict(color='rgba(231, 237, 244, 0.45)', width=1.1)
    ))
    fig_bt.add_trace(go.Scatter(
        x=bt_res['dates'],
        y=-bt_res['var_forecasts'] * 100,
        mode='lines',
        name="1G %99 VaR Eşiği",
        line=dict(color='#EF6461', width=1.8, dash='dash')
    ))
    if len(bt_res['breach_indices']) > 0:
        breach_dates = [bt_res['dates'][i] for i in bt_res['breach_indices']]
        breach_rets = [bt_res['actual_returns'][i] * 100 for i in bt_res['breach_indices']]
        fig_bt.add_trace(go.Scatter(
            x=breach_dates,
            y=breach_rets,
            mode='markers',
            name="VaR İhlali",
            marker=dict(color='#EF6461', size=8, symbol='x', line=dict(width=2, color='#EF6461'))
        ))
    fig_bt.update_layout(
        PLOTLY_TERMINAL_THEME,
        height=300,
        margin=dict(l=35, r=20, t=35, b=35),
        xaxis_title="Tarih",
        yaxis_title="Getiri / Kayıp %",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0, font=dict(size=10))
    )
    st.plotly_chart(fig_bt, use_container_width=True)


# =============================================================================
# 4. STRESS TESTS (MAKRO STRES SİMÜLATÖRÜ)
# =============================================================================
with nav_tab4:
    st.markdown("<div class='surface-card-title'>Makroekonomik Stres Testi Simülatörü</div>", unsafe_allow_html=True)
    st.caption("Tarihsel kriz şoklarında portföyün sermaye kaybı (drawdown) ve dayanıklılık derecesi.")
    
    st_sel_col, st_val_col = st.columns([0.65, 0.35])
    with st_sel_col:
        scenario_options = {
            "scen_2008_crisis": "2008 Küresel Likidite & Kredi Krizi Şoku",
            "scen_covid_shock": "COVID-19 Pandemi Volatilite Patlaması",
            "scen_stagflation": "Stagflasyon & Şahin Faiz Sıkılaşması",
            "scen_geopolitical_energy": "Jeopolitik Enerji & Tedarik Şoku"
        }
        selected_scen_key = st.selectbox(
            "Makro Stres Senaryosu Seçiniz:",
            options=list(scenario_options.keys()),
            format_func=lambda k: scenario_options[k]
        )
    with st_val_col:
        portfolio_capital = st.number_input(
            f"Portföy Büyüklüğü ({base_currency}):",
            min_value=100000,
            max_value=100000000,
            value=1000000,
            step=100000,
            format="%d"
        )
        
    stress_res = simulate_stress_test(active_weights, asset_keys, selected_scen_key)
    pnl_impact = portfolio_capital * stress_res["portfolio_impact"]
    
    st_col1, st_col2, st_col3 = st.columns(3)
    with st_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Portföy Değer Kaybı (Drawdown)</div>
            <div class="metric-value" style="color: #EF6461;">{stress_res['portfolio_impact']*100:+.2f}%</div>
            <div class="metric-sub">{stress_res['scenario_title_tr']}</div>
        </div>
        """, unsafe_allow_html=True)
    with st_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Sermaye PnL Etkisi</div>
            <div class="metric-value" style="color: #E5A83A;">{pnl_impact:,.0f} {base_currency}</div>
            <div class="metric-sub">{portfolio_capital:,.0f} {base_currency} Fon Büyüklüğünde</div>
        </div>
        """, unsafe_allow_html=True)
    with st_col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Dayanıklılık Derecesi</div>
            <div class="metric-value" style="color: #4C8DFF; font-size: 1.45rem;">{stress_res['resilience_grade']}</div>
            <div class="metric-sub">Stres Testi Karşılama Kapasitesi</div>
        </div>
        """, unsafe_allow_html=True)
        
    st_sh1, st_sh2 = st.columns(2)
    with st_sh1:
        st.markdown("<div class='surface-card-title'>Senaryo Varlık Şokları (%)</div>", unsafe_allow_html=True)
        human_names = [get_human_name(k, "tr") for k in asset_keys]
        shocks_pct = stress_res["shock_vector"] * 100
        fig_sh = go.Figure(go.Bar(
            x=human_names,
            y=shocks_pct,
            marker_color=["#EF6461" if s < 0 else "#27C281" for s in shocks_pct]
        ))
        fig_sh.update_layout(PLOTLY_TERMINAL_THEME, height=330, yaxis_title="Uygulanan Şok %")
        fig_sh.update_xaxes(tickangle=35)
        st.plotly_chart(fig_sh, use_container_width=True)
        
    with st_sh2:
        st.markdown("<div class='surface-card-title'>Portföy Kayıp/Kazanç Katkısı (%)</div>", unsafe_allow_html=True)
        contribs = [stress_res["asset_contributions"][k] * 100 for k in asset_keys]
        fig_ct = go.Figure(go.Bar(
            x=human_names,
            y=contribs,
            marker_color=["#EF6461" if c < 0 else "#27C281" for c in contribs]
        ))
        fig_ct.update_layout(PLOTLY_TERMINAL_THEME, height=330, yaxis_title="Ağırlıklı Katkı %")
        fig_ct.update_xaxes(tickangle=35)
        st.plotly_chart(fig_ct, use_container_width=True)


# =============================================================================
# 5. METHODOLOGY (METODOLOJİ & FORMÜLLER)
# =============================================================================
with nav_tab5:
    st.markdown("<div class='surface-card-title'>Matematiksel Formüller ve Akademik Metodoloji</div>", unsafe_allow_html=True)
    st.caption("Sistemde kullanılan finans mühendisliği, optimizasyon ve ekonometrik modellerin akademik formülasyonları.")
    
    mf_col1, mf_col2 = st.columns(2)
    with mf_col1:
        st.markdown("""
        <div class="surface-card">
            <div style="font-weight: 600; color: #E7EDF4; margin-bottom: 6px;">1. Markowitz Modern Portföy Teorisi & Karesel Programlama</div>
            <div style="font-size: 0.82rem; color: #8E9BAA; line-height: 1.5; margin-bottom: 8px;">
                Harry Markowitz (1952) tarafından geliştirilen modelde portföy varyansı ve Sharpe oranı maksimizasyonu karesel programlama ile çözülür:
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.latex(r"\mu_p = \mathbf{w}^T \boldsymbol{\mu}, \quad \sigma_p^2 = \mathbf{w}^T \boldsymbol{\Sigma} \mathbf{w}")
        st.latex(r"\max_{\mathbf{w}} \frac{\mathbf{w}^T \boldsymbol{\mu} - R_f}{\sqrt{\mathbf{w}^T \boldsymbol{\Sigma} \mathbf{w}}} \quad \text{kısıtlar:} \quad \sum_{i=1}^N w_i = 1, \quad 0 \le w_i \le 1")
        
        st.markdown("""
        <div class="surface-card">
            <div style="font-weight: 600; color: #E7EDF4; margin-bottom: 6px;">2. Ledoit-Wolf Kovaryans Büzülme (Shrinkage) Modeli</div>
            <div style="font-size: 0.82rem; color: #8E9BAA; line-height: 1.5; margin-bottom: 8px;">
                Örneklem kovaryansı S gürültülü olduğunda, yapılandırılmış sabit korelasyon hedef matrisi F ile harmanlanır:
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.latex(r"\boldsymbol{\Sigma}_{shrunk} = \delta \mathbf{F} + (1 - \delta) \mathbf{S}, \quad \delta \in [0, 1]")
        
        st.markdown("""
        <div class="surface-card">
            <div style="font-weight: 600; color: #E7EDF4; margin-bottom: 6px;">3. GARCH(1,1) Koşullu Volatilite Kümelenmesi</div>
            <div style="font-size: 0.82rem; color: #8E9BAA; line-height: 1.5; margin-bottom: 8px;">
                Bollerslev (1986) genelleştirilmiş otoregresif koşullu değişen varyans modeli ile geçmiş şoklar ve varyans hafızası modellenir:
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.latex(r"\sigma_t^2 = \omega + \alpha \epsilon_{t-1}^2 + \beta \sigma_{t-1}^2, \quad \alpha + \beta < 1")

    with mf_col2:
        st.markdown("""
        <div class="surface-card">
            <div style="font-weight: 600; color: #E7EDF4; margin-bottom: 6px;">4. Bayesian Black-Litterman Varlık Dağılımı</div>
            <div style="font-size: 0.82rem; color: #8E9BAA; line-height: 1.5; margin-bottom: 8px;">
                Fischer Black ve Robert Litterman (1992) modeli CAPM piyasa denge getirisi (Prior) ile yatırımcı görüşlerini (Views) harmanlar:
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.latex(r"\boldsymbol{\Pi} = \lambda \boldsymbol{\Sigma} \mathbf{w}_{mkt}, \quad \lambda = \frac{E[R_{mkt}] - R_f}{\sigma_{mkt}^2}")
        st.latex(r"\boldsymbol{\mu}_{BL} = \left[(\tau \boldsymbol{\Sigma})^{-1} + \mathbf{P}^T \boldsymbol{\Omega}^{-1} \mathbf{P}\right]^{-1} \left[(\tau \boldsymbol{\Sigma})^{-1} \boldsymbol{\Pi} + \mathbf{P}^T \boldsymbol{\Omega}^{-1} \mathbf{Q}\right]")
        
        st.markdown("""
        <div class="surface-card">
            <div style="font-weight: 600; color: #E7EDF4; margin-bottom: 6px;">5. Cornish-Fisher Analitik Kapalı Formül Expected Shortfall</div>
            <div style="font-size: 0.82rem; color: #8E9BAA; line-height: 1.5; margin-bottom: 8px;">
                Taylor serisi açılımı kantil fonksiyonunun Hermite polinomları üzerinden standart Gauss ölçüsü altında analitik kapalı formül integrasyonu:
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.latex(r"z_{CF}(\alpha) = z_\alpha + \frac{S}{6}(z_\alpha^2 - 1) + \frac{K}{24}(z_\alpha^3 - 3z_\alpha) - \frac{S^2}{36}(2z_\alpha^3 - 5z_\alpha)")
        st.latex(r"CVaR_{CF}(\alpha) = -\mu + \sigma \frac{\phi(z_\alpha)}{1 - \alpha} \left[ 1 + \frac{S}{6} z_\alpha + \frac{K}{24}(z_\alpha^2 - 1) - \frac{S^2}{36}(2z_\alpha^2 - 1) \right]")
        
        st.markdown("""
        <div class="surface-card">
            <div style="font-weight: 600; color: #E7EDF4; margin-bottom: 6px;">6. Basel III / BCBS Kupiec POF Likelihood Ratio Backtest</div>
            <div style="font-size: 0.82rem; color: #8E9BAA; line-height: 1.5; margin-bottom: 8px;">
                VaR modelinin gerçekleşen kayıplarla tutarlılığını test eden Kupiec (1995) Olabilirlik Oranı (POF) testi ve BCBS CRE53 çarpan cetveli:
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.latex(r"LR_{POF} = 2 \left[ x \ln\left(\frac{\hat{p}}{p}\right) + (N - x) \ln\left(\frac{1 - \hat{p}}{1 - p}\right) \right] \sim \chi^2(1)")

# Compact Footer
st.markdown("""
<div style="text-align: center; margin-top: 36px; padding: 16px; color: #8E9BAA; font-size: 0.76rem; border-top: 1px solid #1D2733;">
    Portfolio Risk Terminal • Institutional Risk Analytics & Quantitative Optimization Suite
</div>
""", unsafe_allow_html=True)
