"""
Institutional Multi-Asset Market Data Generator
===============================================
Generates 5 full trading years (1,260 days) of realistic daily price and return
time series across 8 diversified global and regional institutional asset classes:
- BIST 100 Index Fund (BIST 100 Endeks Fonu)
- S&P 500 Global ETF (S&P 500 Küresel Hisse Fonu)
- BIST Banking Index (BIST Bankacılık Sektör Endeksi)
- US Treasury 10Y Bond (ABD 10 Yıllık Hazine Tahvili)
- Gold Bullion USD (Altın Ons Güvenli Liman)
- Brent Crude Oil (Brent Ham Petrol Emtiası)
- EUR/TRY Currency (Euro / Türk Lirası Döviz)
- Bitcoin Digital Asset (Bitcoin Alternatif Dijital Varlık)

Includes realistic cross-asset correlation matrix, macro regime shocks (2022 Fed rate hike shock,
2023 banking turmoil), fat tails (Student-t copula characteristics), and realistic drift/volatility.
"""

import os
import numpy as np
import pandas as pd

ASSET_DEFINITIONS = {
    "bist_100": {
        "name_tr": "BIST 100 Endeks Fonu",
        "name_en": "BIST 100 Index Fund",
        "asset_class": "Yerel Hisse Senedi / Turkish Equities",
        "annual_return": 0.28,
        "annual_vol": 0.24,
        "base_price": 100.0,
        "market_cap_weight": 0.20
    },
    "sp_500": {
        "name_tr": "S&P 500 Küresel Hisse ETF",
        "name_en": "S&P 500 Global Equity ETF",
        "asset_class": "Küresel Hisse Senedi / Global Equities",
        "annual_return": 0.14,
        "annual_vol": 0.16,
        "base_price": 380.0,
        "market_cap_weight": 0.25
    },
    "bist_bank": {
        "name_tr": "BIST Bankacılık Endeksi",
        "name_en": "BIST Banking Sector Index",
        "asset_class": "Finansal Sektör / Banking Equities",
        "annual_return": 0.31,
        "annual_vol": 0.30,
        "base_price": 120.0,
        "market_cap_weight": 0.10
    },
    "us_treasury": {
        "name_tr": "ABD 10 Yıllık Hazine Tahvili",
        "name_en": "US 10Y Treasury Bond ETF",
        "asset_class": "Sabit Getirili Menkul / Fixed Income",
        "annual_return": 0.05,
        "annual_vol": 0.08,
        "base_price": 105.0,
        "market_cap_weight": 0.15
    },
    "gold": {
        "name_tr": "Altın Ons (USD)",
        "name_en": "Gold Bullion (USD)",
        "asset_class": "Değerli Metal / Safe Haven",
        "annual_return": 0.11,
        "annual_vol": 0.14,
        "base_price": 1850.0,
        "market_cap_weight": 0.10
    },
    "brent_crude": {
        "name_tr": "Brent Ham Petrol",
        "name_en": "Brent Crude Oil",
        "asset_class": "Enerji Emtiası / Commodities",
        "annual_return": 0.12,
        "annual_vol": 0.28,
        "base_price": 75.0,
        "market_cap_weight": 0.05
    },
    "usd_try": {
        "name_tr": "Amerikan Doları / Türk Lirası (USD/TRY)",
        "name_en": "US Dollar / Turkish Lira (USD/TRY)",
        "asset_class": "Döviz Kuru / Foreign Exchange",
        "currency": "TRY",
        "annual_return": 0.25,
        "annual_vol": 0.18,
        "base_price": 8.50,
        "market_cap_weight": 0.10
    },
    "bitcoin": {
        "name_tr": "Bitcoin (BTC/USD)",
        "name_en": "Bitcoin Digital Asset",
        "asset_class": "Kripto / Alternative Assets",
        "annual_return": 0.35,
        "annual_vol": 0.52,
        "base_price": 29000.0,
        "market_cap_weight": 0.05
    }
}

def generate_market_dataset(
    n_days: int = 1260,
    seed: int = 42,
    output_path: str = None
) -> pd.DataFrame:
    """
    Generates daily closing prices for 8 institutional assets with correlated shocks.
    """
    np.random.seed(seed)
    
    asset_keys = list(ASSET_DEFINITIONS.keys())
    n_assets = len(asset_keys)
    
    # Target correlation matrix (cross-asset macro relationships)
    corr = np.array([
        [ 1.00,  0.35,  0.78, -0.15,  0.18,  0.22,  0.38,  0.25], # bist_100
        [ 0.35,  1.00,  0.28, -0.22,  0.08,  0.30,  0.05,  0.42], # sp_500
        [ 0.78,  0.28,  1.00, -0.18,  0.12,  0.18,  0.32,  0.20], # bist_bank
        [-0.15, -0.22, -0.18,  1.00,  0.28, -0.12, -0.05, -0.18], # us_treasury
        [ 0.18,  0.08,  0.12,  0.28,  1.00,  0.20,  0.22,  0.15], # gold
        [ 0.22,  0.30,  0.18, -0.12,  0.20,  1.00,  0.18,  0.20], # brent_crude
        [ 0.38,  0.05,  0.32, -0.05,  0.22,  0.18,  1.00,  0.15], # usd_try
        [ 0.25,  0.42,  0.20, -0.18,  0.15,  0.20,  0.15,  1.00]  # bitcoin
    ])
    
    # Ensure positive semi-definite correlation
    eigvals, eigvecs = np.linalg.eigh(corr)
    eigvals = np.maximum(eigvals, 1e-6)
    corr = eigvecs @ np.diag(eigvals) @ eigvecs.T
    d = np.sqrt(np.diag(corr))
    corr = corr / np.outer(d, d)
    
    cholesky = np.linalg.cholesky(corr)
    
    # Daily parameters (252 trading days/year)
    dt = 1.0 / 252.0
    mu_daily = np.array([ASSET_DEFINITIONS[k]["annual_return"] for k in asset_keys]) * dt
    sigma_daily = np.array([ASSET_DEFINITIONS[k]["annual_vol"] for k in asset_keys]) * np.sqrt(dt)
    
    # Dates: 5 years up to end of 2025
    dates = pd.bdate_range(end="2025-12-31", periods=n_days)
    
    # Generate uncorrelated standard normal with mild t-distribution heavy tails (df=7)
    raw_shocks = np.random.standard_t(df=7, size=(n_days, n_assets))
    raw_shocks = raw_shocks / np.sqrt(7.0 / 5.0)
    
    # Correlate shocks
    correlated_shocks = raw_shocks @ cholesky.T
    
    # Daily log-returns with Ito's lemma drift adjustment: (mu - 0.5 * sigma^2) * dt + sigma * dW
    drift = mu_daily - 0.5 * (sigma_daily ** 2)
    daily_log_returns = drift + sigma_daily * correlated_shocks
    
    # Inject 2 historical macro shock regimes:
    # 1. 2022 Global Rate Shock / Risk-off (approx index 260:320)
    daily_log_returns[260:320, 1] -= 0.0018  # SP500 drawdown
    daily_log_returns[260:320, 3] -= 0.0015  # US Treasury bond yield spike (bond prices drop)
    daily_log_returns[260:320, 4] += 0.0012  # Gold hedge flight
    daily_log_returns[260:320, 7] -= 0.0040  # Bitcoin crypto winter
    
    # 2. 2023 Energy/Geopolitical Shock (approx index 560:590)
    daily_log_returns[560:590, 5] += 0.0035  # Brent oil surge
    daily_log_returns[560:590, 4] += 0.0020  # Gold flight
    
    # Compute cumulative price levels
    prices = np.zeros((n_days, n_assets))
    for i, k in enumerate(asset_keys):
        base_p = ASSET_DEFINITIONS[k]["base_price"]
        cum_ret = np.exp(np.cumsum(daily_log_returns[:, i]))
        prices[:, i] = base_p * (cum_ret / cum_ret[0])
    
    df = pd.DataFrame(prices, columns=asset_keys, index=dates)
    df.index.name = "date"
    df = df.round(4)
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path)
        print(f"Generated {len(df)} records across {n_assets} assets saved to {output_path}")
        
    return df

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_csv = os.path.join(base_dir, "data", "institutional_market_data.csv")
    generate_market_dataset(output_path=target_csv)
