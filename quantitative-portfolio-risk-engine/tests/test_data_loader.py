"""
Unit tests for data loader and timeseries processor
"""

import pytest
import numpy as np
import pandas as pd
from src.data_loader import (
    load_market_data,
    get_asset_universe,
    get_human_name,
    get_benchmark_weights,
    calculate_cumulative_performance,
    ASSET_METADATA
)

def test_asset_universe_and_metadata():
    assets = get_asset_universe()
    assert len(assets) == 8
    assert "bist_100" in assets
    assert "sp_500" in assets
    assert "gold" in assets
    
    # Verify no underscores in human titles
    for k in assets:
        tr_name = get_human_name(k, lang="tr")
        en_name = get_human_name(k, lang="en")
        assert "_" not in tr_name, f"Underscore found in Turkish name: {tr_name}"
        assert "_" not in en_name, f"Underscore found in English name: {en_name}"
        assert len(tr_name) > 3
        assert len(en_name) > 3

def test_benchmark_weights():
    weights = get_benchmark_weights()
    assert len(weights) == 8
    assert np.isclose(np.sum(weights), 1.0, atol=1e-7)
    assert np.all(weights > 0.0)

def test_load_market_data():
    prices, returns, ann_returns, ann_cov = load_market_data()
    
    # 1. Price checks
    assert len(prices) == 1260
    assert len(prices.columns) == 8
    assert not prices.isnull().any().any()
    assert (prices > 0).all().all()
    
    # 2. Return checks
    assert len(returns) == 1259
    assert not returns.isnull().any().any()
    
    # 3. Annualized metrics
    assert len(ann_returns) == 8
    assert ann_cov.shape == (8, 8)
    
    # Covariance matrix must be symmetric and positive semi-definite
    cov_vals = ann_cov.values
    assert np.allclose(cov_vals, cov_vals.T, atol=1e-8)
    eigvals = np.linalg.eigvalsh(cov_vals)
    assert np.all(eigvals >= -1e-8), f"Negative eigenvalues found: {eigvals}"

def test_cumulative_performance():
    _, returns, _, _ = load_market_data()
    cum = calculate_cumulative_performance(returns, base_val=100.0)
    assert len(cum) == len(returns)
    assert (cum > 0).all().all()
    assert np.isclose(cum.iloc[0, 0], 100.0 * (1.0 + returns.iloc[0, 0]), atol=1e-4)
