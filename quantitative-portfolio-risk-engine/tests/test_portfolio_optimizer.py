"""
Unit tests for Markowitz Modern Portfolio Theory & Optimization Engine
"""

import pytest
import numpy as np
from src.data_loader import load_market_data
from src.portfolio_optimizer import (
    shrink_covariance_ledoit_wolf,
    portfolio_performance,
    optimize_max_sharpe,
    optimize_min_volatility,
    optimize_target_return,
    calculate_efficient_frontier,
    generate_monte_carlo_portfolios
)

@pytest.fixture(scope="module")
def market_data():
    prices, returns, ann_returns, ann_cov = load_market_data()
    return {
        "returns_df": returns,
        "expected_returns": ann_returns.values,
        "cov_matrix": ann_cov.values
    }

def test_ledoit_wolf_shrinkage(market_data):
    shrunk_cov, shrinkage = shrink_covariance_ledoit_wolf(market_data["returns_df"], annualize=True)
    assert 0.0 <= shrinkage <= 1.0
    assert shrunk_cov.shape == (8, 8)
    
    # Strictly positive definite
    eigvals = np.linalg.eigvalsh(shrunk_cov)
    assert np.all(eigvals > 1e-6)

def test_portfolio_performance_math():
    w = np.array([0.5, 0.5])
    mu = np.array([0.10, 0.20])
    cov = np.array([[0.04, 0.01], [0.01, 0.09]])
    
    ret, vol, sharpe = portfolio_performance(w, mu, cov, risk_free_rate=0.04)
    assert np.isclose(ret, 0.15, atol=1e-6)
    
    expected_var = 0.25 * 0.04 + 0.25 * 0.09 + 2 * 0.25 * 0.01 # 0.01 + 0.0225 + 0.005 = 0.0375
    expected_vol = np.sqrt(expected_var)
    assert np.isclose(vol, expected_vol, atol=1e-6)
    assert np.isclose(sharpe, (0.15 - 0.04) / expected_vol, atol=1e-6)

def test_max_sharpe_optimization(market_data):
    mu = market_data["expected_returns"]
    cov = market_data["cov_matrix"]
    
    res = optimize_max_sharpe(mu, cov, risk_free_rate=0.05)
    weights = res["weights"]
    
    # 1. Weights must sum to 1.0
    assert np.isclose(np.sum(weights), 1.0, atol=1e-5)
    # 2. Long only: weights >= 0
    assert np.all(weights >= -1e-6)
    # 3. Sharpe must be positive and greater than naive 1/N Sharpe
    naive_w = np.ones(len(mu)) / len(mu)
    _, _, naive_sharpe = portfolio_performance(naive_w, mu, cov, risk_free_rate=0.05)
    assert res["sharpe_ratio"] >= naive_sharpe - 1e-4

def test_min_volatility_optimization(market_data):
    mu = market_data["expected_returns"]
    cov = market_data["cov_matrix"]
    
    res = optimize_min_volatility(mu, cov)
    weights = res["weights"]
    
    assert np.isclose(np.sum(weights), 1.0, atol=1e-5)
    assert np.all(weights >= -1e-6)
    
    # Must have lower volatility than naive equal weight
    naive_w = np.ones(len(mu)) / len(mu)
    _, naive_vol, _ = portfolio_performance(naive_w, mu, cov)
    assert res["volatility"] <= naive_vol + 1e-4

def test_efficient_frontier_generation(market_data):
    mu = market_data["expected_returns"]
    cov = market_data["cov_matrix"]
    
    frontier = calculate_efficient_frontier(mu, cov, n_points=15)
    assert len(frontier) == 15
    
    # Returns should be monotonically non-decreasing
    returns = [p["return"] for p in frontier]
    for i in range(1, len(returns)):
        assert returns[i] >= returns[i-1] - 1e-6

def test_monte_carlo_portfolio_simulation(market_data):
    mu = market_data["expected_returns"]
    cov = market_data["cov_matrix"]
    
    sim = generate_monte_carlo_portfolios(mu, cov, n_portfolios=500, seed=123)
    assert len(sim["returns"]) == 500
    assert len(sim["volatilities"]) == 500
    assert len(sim["sharpe_ratios"]) == 500
    assert sim["weights"].shape == (500, 8)
    # All rows must sum to 1.0
    row_sums = np.sum(sim["weights"], axis=1)
    assert np.allclose(row_sums, 1.0, atol=1e-5)
