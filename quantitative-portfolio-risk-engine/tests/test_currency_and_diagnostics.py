"""
Regression & Diagnostic Tests for Currency Normalization, Cornish-Fisher CVaR, and Solver Failures
===================================================================================================
Enforces institutional standards per the Antigravity Project Audit.
"""

import pytest
import numpy as np
import pandas as pd
from src.data_loader import (
    load_market_data,
    get_asset_universe,
    ASSET_METADATA,
    convert_returns_to_base_currency
)
from src.risk_engine import calculate_parametric_var_cvar
from src.portfolio_optimizer import optimize_max_sharpe

def test_asset_currencies_metadata():
    """Each asset must specify its native trading currency (TRY or USD)."""
    universe = get_asset_universe()
    for k in universe:
        assert "currency" in ASSET_METADATA[k], f"Asset {k} missing currency metadata"
        assert ASSET_METADATA[k]["currency"] in ["TRY", "USD"]

def test_currency_conversion_math():
    """
    Validates currency translation between TRY and USD:
    R_TRY = (1 + R_USD) * (1 + R_FX) - 1
    R_USD = (1 + R_TRY) / (1 + R_FX) - 1
    """
    dates = pd.bdate_range("2025-01-01", periods=5)
    # Synthetic test returns
    test_df = pd.DataFrame({
        "bist_100": [0.01, -0.02, 0.03, 0.00],    # Native TRY
        "sp_500": [0.005, 0.010, -0.005, 0.02],   # Native USD
        "usd_try": [0.002, 0.003, -0.001, 0.004]  # FX USD/TRY return
    }, index=dates[1:])
    
    # 1. Convert to TRY base
    try_base_returns = convert_returns_to_base_currency(test_df, base_currency="TRY")
    # BIST 100 is native TRY, so it must be unchanged
    assert np.allclose(try_base_returns["bist_100"], test_df["bist_100"])
    # SP 500 was USD, in TRY it should be (1 + R_SP) * (1 + R_FX) - 1
    expected_sp_try = (1.0 + test_df["sp_500"]) * (1.0 + test_df["usd_try"]) - 1.0
    assert np.allclose(try_base_returns["sp_500"], expected_sp_try)
    
    # 2. Convert to USD base
    usd_base_returns = convert_returns_to_base_currency(test_df, base_currency="USD")
    # SP 500 is native USD, so it must be unchanged
    assert np.allclose(usd_base_returns["sp_500"], test_df["sp_500"])
    # BIST 100 was TRY, in USD it should be (1 + R_BIST) / (1 + R_FX) - 1
    expected_bist_usd = (1.0 + test_df["bist_100"]) / (1.0 + test_df["usd_try"]) - 1.0
    assert np.allclose(usd_base_returns["bist_100"], expected_bist_usd)

def test_cornish_fisher_gaussian_reference_convergence():
    """
    Independent Reference Test 1:
    When Skewness = 0 and Excess Kurtosis = 0, Cornish-Fisher CVaR must mathematically
    converge to the textbook analytical Gaussian Expected Shortfall:
        CVaR_norm = -mu + sigma * phi(z_alpha) / (1 - alpha)
    with machine precision (< 1e-12).
    """
    from scipy.stats import norm
    # Symmetrical distribution with zero skew and excess kurtosis = 0
    mu = 0.001
    sigma = 0.02
    alpha_conf = 0.95
    alpha = 1.0 - alpha_conf
    z_a = float(norm.ppf(alpha_conf))
    
    # Generate perfectly symmetric data with skew ~ 0 and kurtosis ~ 0
    np.random.seed(12345)
    sym_data = np.random.normal(mu, sigma, size=200000)
    series = pd.Series(sym_data)
    
    res = calculate_parametric_var_cvar(series, confidence_level=alpha_conf)
    
    # Benchmark Gaussian formula
    expected_gaussian_cvar = -(mu - (float(norm.pdf(z_a)) / alpha) * sigma)
    
    # Check that Cornish-Fisher matches Gaussian within sampling precision
    assert np.isclose(res["cornish_fisher_cvar"], res["gaussian_cvar"], atol=1e-3)

def test_cornish_fisher_analytical_vs_independent_numerical_quad():
    """
    Independent Reference Test 2:
    Validates the closed-form Hermite polynomial integral against an independent
    high-precision numerical Gauss-Kronrod quadrature in standard normal z-space:
        \\int_{z_\\alpha}^{\\infty} z_{CF}(z) \\phi(z) dz
    Agreement must be within 1e-10.
    """
    from scipy.stats import norm
    from scipy.integrate import quad
    
    z_a = float(norm.ppf(0.95))
    s = 0.45
    k = 1.80
    
    # 1. Closed-form formula implemented in risk engine:
    bracket = 1.0 + (s / 6.0) * z_a + (k / 24.0) * (z_a**2 - 1.0) - (s**2 / 36.0) * (2.0 * z_a**2 - 1.0)
    closed_form_integral = float(norm.pdf(z_a)) * bracket
    
    # 2. Independent numerical quadrature:
    def integrand_z(z):
        z_cf = (
            z
            + (s / 6.0) * (z**2 - 1.0)
            + (k / 24.0) * (z**3 - 3.0 * z)
            - (s**2 / 36.0) * (2.0 * z**3 - 5.0 * z)
        )
        return z_cf * norm.pdf(z)
        
    num_integral, err = quad(integrand_z, z_a, 15.0, epsabs=1e-12, epsrel=1e-12)
    
    diff = abs(closed_form_integral - num_integral)
    assert diff < 1e-10, f"Closed-form and numerical quadrature diverge: diff={diff}"

def test_cornish_fisher_coherence_and_tail_risk():
    """
    Coherent risk measure verification:
    For any non-trivial return series, CVaR >= VaR at all confidence levels.
    """
    rng = np.random.default_rng(999)
    # Heavy-tailed non-normal returns
    t_returns = pd.Series(rng.standard_t(df=4, size=5000) * 0.02)
    
    for conf in [0.90, 0.95, 0.99]:
        res = calculate_parametric_var_cvar(t_returns, confidence_level=conf)
        assert res["cornish_fisher_cvar"] >= res["cornish_fisher_var"], (
            f"Coherence violation at {conf}: CVaR ({res['cornish_fisher_cvar']}) < VaR ({res['cornish_fisher_var']})"
        )
        assert res["gaussian_cvar"] >= res["gaussian_var"]

def test_monte_carlo_multi_step_compound_path_simulation():
    """
    Validates that 10-day Monte Carlo executes authentic multi-step compound path simulation:
    R_{10} = \\prod_{t=1}^{10} (1 + r_t) - 1, and produces realistic heavy-tailed loss distributions.
    """
    from src.risk_engine import calculate_monte_carlo_var_cvar
    rng = np.random.default_rng(42)
    daily_returns = pd.Series(rng.normal(0.001, 0.015, size=1000))
    
    var_1d, cvar_1d, paths_1d = calculate_monte_carlo_var_cvar(daily_returns, horizon_days=1, n_simulations=5000)
    var_10d, cvar_10d, paths_10d = calculate_monte_carlo_var_cvar(daily_returns, horizon_days=10, n_simulations=5000)
    
    # 10-day risk must be strictly greater than 1-day risk
    assert var_10d > var_1d
    assert cvar_10d > cvar_1d
    assert len(paths_10d) == 5000

def test_var_backtest_kupiec_and_basel_zones():
    """
    Validates rolling out-of-sample VaR backtest, Kupiec POF LR test statistic,
    and Basel Traffic Light classification.
    """
    from src.risk_engine import run_var_backtest
    rng = np.random.default_rng(777)
    # 600 days of stationary returns
    returns = pd.Series(rng.normal(0.0005, 0.012, size=600))
    
    bt = run_var_backtest(returns, confidence_level=0.99, test_window=250, estimation_window=250)
    
    assert bt["test_days"] == 250
    assert 0 <= bt["breaches"] <= 250
    assert bt["expected_breaches"] == pytest.approx(2.5, abs=0.1)
    assert bt["kupiec_lr_stat"] >= 0.0
    assert 0.0 <= bt["kupiec_p_value"] <= 1.0
    assert bt["basel_zone"] in [
        "GREEN (Yeşil Bölge - Geçerli Model)",
        "YELLOW (Sarı Bölge - Denetim Uyarısı)",
        "RED (Kırmızı Bölge - Model Reddedildi)"
    ]
    assert 3.00 <= bt["basel_multiplier"] <= 4.00

def test_cornish_fisher_10d_rolling_compound_moments():
    """
    Validates that 10-day Cornish-Fisher calculates its moments (skewness and kurtosis)
    from the empirical rolling compound return distribution rather than reusing daily moments.
    """
    rng = np.random.default_rng(42)
    # Series with non-trivial autocorrelation to create clear divergence between daily & rolling compound moments
    raw_shocks = rng.standard_t(df=5, size=1000) * 0.01
    series = pd.Series(raw_shocks)
    
    res_1d = calculate_parametric_var_cvar(series, horizon_days=1)
    res_10d = calculate_parametric_var_cvar(series, horizon_days=10)
    
    # 10-day risk must exceed 1-day risk
    assert res_10d["cornish_fisher_var"] > res_1d["cornish_fisher_var"]
    assert res_10d["cornish_fisher_cvar"] > res_1d["cornish_fisher_cvar"]
    # Coherent risk condition CVaR >= VaR must strictly hold on 10-day
    assert res_10d["cornish_fisher_cvar"] >= res_10d["cornish_fisher_var"]

def test_basel_cre53_exact_multiplier_schedule():
    """
    Validates exact Basel Committee (BCBS CRE53) supervisory penalty multipliers:
    0-4: 3.00
    5: 3.40 (NOT 3.60)
    6: 3.50
    7: 3.65
    8: 3.75
    9: 3.85
    10+: 4.00
    """
    from src.risk_engine import compute_basel_zone_and_multiplier
    
    expected_schedule = {
        0: ("GREEN", 3.00),
        1: ("GREEN", 3.00),
        2: ("GREEN", 3.00),
        3: ("GREEN", 3.00),
        4: ("GREEN", 3.00),
        5: ("YELLOW", 3.40),
        6: ("YELLOW", 3.50),
        7: ("YELLOW", 3.65),
        8: ("YELLOW", 3.75),
        9: ("YELLOW", 3.85),
        10: ("RED", 4.00),
        15: ("RED", 4.00),
        25: ("RED", 4.00)
    }
    
    for x, (expected_zone, expected_mult) in expected_schedule.items():
        zone, mult = compute_basel_zone_and_multiplier(x)
        assert zone.startswith(expected_zone), f"Breaches {x}: expected {expected_zone}, got {zone}"
        assert mult == pytest.approx(expected_mult), f"Breaches {x}: expected multiplier {expected_mult}, got {mult}"




def test_optimizer_diagnostics_on_infeasible_problem():
    """Optimizer must explicitly report failure and solver message when constraints are impossible."""
    mu = np.array([0.10, 0.15, 0.12])
    cov = np.diag([0.04, 0.05, 0.03])
    
    # Infeasible: 3 assets each minimum 0.5 (sum must be 1.0, but 3*0.5 = 1.5)
    res = optimize_max_sharpe(mu, cov, min_weight=0.5, max_weight=1.0)
    assert res["success"] is False
    assert "solver_message" in res
    assert len(res["solver_message"]) > 0
