"""
Unit tests for Bayesian Black-Litterman Asset Allocation Engine
"""

import pytest
import numpy as np
from src.data_loader import load_market_data, get_asset_universe, get_benchmark_weights
from src.black_litterman import (
    BlackLittermanModel,
    compute_risk_aversion,
    compute_implied_equilibrium_returns
)

@pytest.fixture(scope="module")
def bl_setup():
    prices, returns, ann_returns, ann_cov = load_market_data()
    assets = get_asset_universe()
    bm_weights = get_benchmark_weights()
    model = BlackLittermanModel(
        asset_names=assets,
        cov_matrix=ann_cov.values,
        benchmark_weights=bm_weights,
        risk_free_rate=0.05,
        tau=0.04
    )
    return {
        "model": model,
        "assets": assets,
        "cov": ann_cov.values,
        "bm_weights": bm_weights
    }

def test_risk_aversion_and_prior(bl_setup):
    model = bl_setup["model"]
    assert model.risk_aversion > 0.0
    assert len(model.pi) == 8
    # Overall market implied prior return must be positive and equities > 0
    assert np.mean(model.pi) > 0.0
    assert model.pi[0] > 0.0 # BIST 100
    assert model.pi[1] > 0.0 # S&P 500

def test_bayesian_update_no_views(bl_setup):
    model = bl_setup["model"]
    res = model.run_bayesian_update(P=np.empty((0, 8)), Q=np.empty(0))
    # Posterior must match prior exactly
    assert np.allclose(res["posterior_returns"], model.pi, atol=1e-6)
    assert np.isclose(np.sum(res["optimal_weights"]), 1.0, atol=1e-5)

def test_bayesian_update_absolute_bullish_view(bl_setup):
    model = bl_setup["model"]
    assets = bl_setup["assets"]
    gold_idx = assets.index("gold")
    prior_gold_ret = model.pi[gold_idx]
    
    # Absolute view: Gold will return 25% (substantially above implied prior)
    P = np.zeros((1, 8))
    P[0, gold_idx] = 1.0
    Q = np.array([0.25])
    
    res = model.run_bayesian_update(P, Q, confidences=[0.80])
    post_returns = res["posterior_returns"]
    
    # Posterior expected return for gold must increase
    assert post_returns[gold_idx] > prior_gold_ret
    assert np.isclose(np.sum(res["optimal_weights"]), 1.0, atol=1e-5)

def test_bayesian_update_relative_view(bl_setup):
    model = bl_setup["model"]
    assets = bl_setup["assets"]
    bist_idx = assets.index("bist_100")
    sp_idx = assets.index("sp_500")
    
    # Relative view: BIST 100 will outperform S&P 500 by +8%
    P = np.zeros((1, 8))
    P[0, bist_idx] = 1.0
    P[0, sp_idx] = -1.0
    Q = np.array([0.08])
    
    res = model.run_bayesian_update(P, Q, confidences=[0.85])
    post_returns = res["posterior_returns"]
    weights = res["optimal_weights"]
    
    # Return spread should expand in favor of BIST 100
    spread = post_returns[bist_idx] - post_returns[sp_idx]
    assert spread > 0.0
    assert np.isclose(np.sum(weights), 1.0, atol=1e-5)

def test_confidence_sensitivity(bl_setup):
    model = bl_setup["model"]
    assets = bl_setup["assets"]
    btc_idx = assets.index("bitcoin")
    
    P = np.zeros((1, 8))
    P[0, btc_idx] = 1.0
    Q = np.array([0.50]) # Bullish view
    
    # Low confidence update
    res_low = model.run_bayesian_update(P, Q, confidences=[0.10])
    # High confidence update
    res_high = model.run_bayesian_update(P, Q, confidences=[0.90])
    
    # Higher confidence must pull the posterior return closer to Q=0.50
    dist_low = abs(res_low["posterior_returns"][btc_idx] - 0.50)
    dist_high = abs(res_high["posterior_returns"][btc_idx] - 0.50)
    assert dist_high < dist_low
