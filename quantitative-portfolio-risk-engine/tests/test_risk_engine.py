"""
Unit tests for Risk Analytics, VaR/CVaR, GARCH(1,1), and Macro Stress Testing
"""

import pytest
import numpy as np
import pandas as pd
from src.data_loader import load_market_data, get_asset_universe, get_benchmark_weights
from src.risk_engine import (
    compute_portfolio_returns,
    calculate_parametric_var_cvar,
    calculate_historical_var_cvar,
    calculate_monte_carlo_var_cvar,
    GARCH11,
    simulate_stress_test,
    STRESS_SCENARIOS
)

@pytest.fixture(scope="module")
def risk_setup():
    prices, returns, ann_returns, ann_cov = load_market_data()
    assets = get_asset_universe()
    weights = get_benchmark_weights()
    port_returns = compute_portfolio_returns(returns, weights)
    return {
        "returns_df": returns,
        "assets": assets,
        "weights": weights,
        "port_returns": port_returns
    }

def test_portfolio_returns_calculation(risk_setup):
    port_ret = risk_setup["port_returns"]
    assert len(port_ret) == len(risk_setup["returns_df"])
    assert not port_ret.isnull().any()
    assert -0.20 < port_ret.mean() < 0.20

def test_parametric_var_cvar(risk_setup):
    ret = risk_setup["port_returns"]
    
    # 95% confidence
    risk_95 = calculate_parametric_var_cvar(ret, confidence_level=0.95)
    # 99% confidence
    risk_99 = calculate_parametric_var_cvar(ret, confidence_level=0.99)
    
    # 1. 99% VaR must exceed 95% VaR
    assert risk_99["gaussian_var"] > risk_95["gaussian_var"]
    
    # 2. CVaR must always be greater than or equal to VaR (Expected Shortfall >= VaR)
    assert risk_95["gaussian_cvar"] >= risk_95["gaussian_var"]
    assert risk_99["gaussian_cvar"] >= risk_99["gaussian_var"]
    assert risk_95["cornish_fisher_cvar"] >= risk_95["cornish_fisher_var"]

def test_historical_and_monte_carlo_var(risk_setup):
    ret = risk_setup["port_returns"]
    
    hist_var, hist_cvar = calculate_historical_var_cvar(ret, confidence_level=0.95)
    assert hist_var > 0.0
    assert hist_cvar >= hist_var
    
    mc_var, mc_cvar, sim_paths = calculate_monte_carlo_var_cvar(ret, confidence_level=0.95, n_simulations=5000)
    assert mc_var > 0.0
    assert mc_cvar >= mc_var
    assert len(sim_paths) == 5000

def test_garch_model_fitting_and_stationarity(risk_setup):
    ret = risk_setup["port_returns"].values
    garch = GARCH11().fit(ret)
    
    assert garch.is_fitted
    assert garch.omega > 0.0
    assert garch.alpha > 0.0
    assert garch.beta > 0.0
    
    # Fundamental GARCH(1,1) Stationarity condition: alpha + beta < 1.0
    persistence = garch.alpha + garch.beta
    assert persistence < 1.0, f"GARCH non-stationary: alpha + beta = {persistence}"
    
    # Conditional volatility series
    assert len(garch.conditional_vol) == len(ret)
    assert np.all(garch.conditional_vol > 0.0)
    assert garch.unconditional_vol > 0.0
    
    # Multi-step 30-day forecast
    forecasts = garch.forecast_volatility(n_days=30)
    assert len(forecasts) == 30
    assert np.all(forecasts > 0.0)

def test_macro_stress_testing(risk_setup):
    assets = risk_setup["assets"]
    weights = risk_setup["weights"]
    
    for scen_key in STRESS_SCENARIOS.keys():
        res = simulate_stress_test(weights, assets, scen_key)
        assert "portfolio_impact" in res
        assert "resilience_grade" in res
        assert -1.0 <= res["portfolio_impact"] <= 1.0
        assert len(res["asset_contributions"]) == 8
