"""
Market Data Loader & Financial Timeseries Processor
===================================================
Provides robust loading, multi-currency conversion (TRY vs USD), return transformations,
annualization, and bilingual metadata mappings for multi-asset institutional investment portfolios.
Strictly ensures zero raw code identifiers in human-facing outputs.
"""

import os
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd

ASSET_METADATA: Dict[str, Dict[str, any]] = {
    "bist_100": {
        "title_tr": "BIST 100 Endeks Fonu",
        "title_en": "BIST 100 Index Fund",
        "category_tr": "Yerel Pay Piyasası",
        "category_en": "Turkish Equities",
        "currency": "TRY",
        "benchmark_weight": 0.20,
        "color": "#8b5cf6",
        "description_tr": "Türkiye hisse senedi piyasasını temsil eden gösterge fonu."
    },
    "sp_500": {
        "title_tr": "S&P 500 Küresel Hisse ETF",
        "title_en": "S&P 500 Global Equity ETF",
        "category_tr": "Küresel Pay Piyasası",
        "category_en": "Global Equities",
        "currency": "USD",
        "benchmark_weight": 0.25,
        "color": "#6366f1",
        "description_tr": "ABD'nin en büyük 500 şirketinin performansını izleyen endeks."
    },
    "bist_bank": {
        "title_tr": "BIST Bankacılık Endeksi",
        "title_en": "BIST Banking Sector Index",
        "category_tr": "Finansal Sektör",
        "category_en": "Banking Sector",
        "currency": "TRY",
        "benchmark_weight": 0.10,
        "color": "#a855f7",
        "description_tr": "Türkiye bankacılık sektörünün performansını yansıtan endeks."
    },
    "us_treasury": {
        "title_tr": "ABD 10 Yıllık Hazine Tahvili",
        "title_en": "US 10Y Treasury Bond ETF",
        "category_tr": "Sabit Getirili Menkul Kıymet",
        "category_en": "Fixed Income Sovereign",
        "currency": "USD",
        "benchmark_weight": 0.15,
        "color": "#10b981",
        "description_tr": "Küresel risksiz faiz oranı ve sabit getiri göstergesi."
    },
    "gold": {
        "title_tr": "Altın Ons (USD)",
        "title_en": "Gold Bullion (USD)",
        "category_tr": "Değerli Metal / Güvenli Liman",
        "category_en": "Precious Metals / Safe Haven",
        "currency": "USD",
        "benchmark_weight": 0.10,
        "color": "#f59e0b",
        "description_tr": "Enflasyon ve jeopolitik risklere karşı koruma sağlayan emtia."
    },
    "brent_crude": {
        "title_tr": "Brent Ham Petrol",
        "title_en": "Brent Crude Oil",
        "category_tr": "Enerji Emtiası",
        "category_en": "Energy Commodity",
        "currency": "USD",
        "benchmark_weight": 0.05,
        "color": "#ef4444",
        "description_tr": "Küresel sanayi ve enerji döngüsüne duyarlı hammadde varlığı."
    },
    "usd_try": {
        "title_tr": "Amerikan Doları / Türk Lirası (USD/TRY)",
        "title_en": "US Dollar / Turkish Lira (USD/TRY)",
        "category_tr": "Döviz Kuru",
        "category_en": "Foreign Exchange",
        "currency": "TRY",
        "benchmark_weight": 0.10,
        "color": "#06b6d4",
        "description_tr": "Döviz kuru dalgalanmalarına karşı getiri ve kur riski enstrümanı."
    },
    "bitcoin": {
        "title_tr": "Bitcoin (BTC/USD)",
        "title_en": "Bitcoin Digital Asset",
        "category_tr": "Alternatif Kripto Varlık",
        "category_en": "Alternative Digital Assets",
        "currency": "USD",
        "benchmark_weight": 0.05,
        "color": "#ec4899",
        "description_tr": "Yüksek asimetrik getiri ve yüksek volatilite profilli dijital varlık."
    }
}

TRADING_DAYS_PER_YEAR = 252

def get_asset_universe() -> List[str]:
    """Returns the ordered list of asset keys."""
    return list(ASSET_METADATA.keys())

def get_human_name(asset_key: str, lang: str = "tr") -> str:
    """Returns human-friendly asset label without technical codes or underscores."""
    meta = ASSET_METADATA.get(asset_key)
    if not meta:
        return asset_key.replace("_", " ").title()
    return meta["title_tr"] if lang == "tr" else meta["title_en"]

def get_benchmark_weights() -> np.ndarray:
    """Returns the market-cap benchmark weight vector normalized to 1.0."""
    weights = np.array([ASSET_METADATA[k]["benchmark_weight"] for k in get_asset_universe()])
    return weights / np.sum(weights)

def convert_returns_to_base_currency(
    returns_df: pd.DataFrame,
    base_currency: str = "TRY"
) -> pd.DataFrame:
    """
    Translates asset returns into a single target base currency (TRY or USD).
    
    Economic Formulations:
    - Base = TRY:
      USD Assets: R_TRY = (1 + R_USD) * (1 + R_USDTRY) - 1
      TRY Assets: R_TRY = R_TRY
    - Base = USD:
      USD Assets: R_USD = R_USD
      TRY Assets: R_USD = (1 + R_TRY) / (1 + R_USDTRY) - 1
      USD/TRY Asset (holding TRY in USD): R_USD = 1 / (1 + R_USDTRY) - 1
    """
    base_currency = base_currency.upper()
    if base_currency not in ["TRY", "USD"]:
        raise ValueError(f"Unsupported base currency: {base_currency}. Must be 'TRY' or 'USD'.")
        
    converted_df = returns_df.copy()
    
    if "usd_try" not in returns_df.columns:
        # If usd_try is not in columns, return unmodified
        return converted_df
        
    r_fx = returns_df["usd_try"]
    
    for col in converted_df.columns:
        native_curr = ASSET_METADATA.get(col, {}).get("currency", "USD")
        
        if base_currency == "TRY":
            if native_curr == "USD":
                # Convert USD return to TRY return
                converted_df[col] = (1.0 + returns_df[col]) * (1.0 + r_fx) - 1.0
            # TRY assets stay unchanged
        elif base_currency == "USD":
            if col == "usd_try":
                # Holding TRY from a USD reference frame
                converted_df[col] = 1.0 / (1.0 + r_fx) - 1.0
            elif native_curr == "TRY":
                # Convert TRY return to USD return
                converted_df[col] = (1.0 + returns_df[col]) / (1.0 + r_fx) - 1.0
            # USD assets stay unchanged
            
    return converted_df

def load_market_data(
    filepath: Optional[str] = None,
    base_currency: str = "TRY",
    adapter: Optional[any] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.DataFrame]:
    """
    Loads price dataset and calculates daily returns, annualized returns, and sample covariance
    normalized to the specified base currency. Supports modular market data adapters.
    
    Returns:
        prices_df (pd.DataFrame): Daily asset prices.
        returns_df (pd.DataFrame): Daily simple percentage returns in base currency.
        annual_returns (pd.Series): Annualized mean returns (r * 252).
        annual_cov (pd.DataFrame): Annualized sample covariance matrix (cov * 252).
    """
    if adapter is not None:
        prices_df = adapter.fetch_prices(get_asset_universe())
    else:
        if filepath is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            filepath = os.path.join(base_dir, "data", "institutional_market_data.csv")
            
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Market data file not found at: {filepath}")
            
        prices_df = pd.read_csv(filepath, parse_dates=["date"], index_col="date")
    
    # Validation checks
    if prices_df.isnull().any().any():
        raise ValueError("Market data contains missing or NaN values.")
    if (prices_df <= 0).any().any():
        raise ValueError("Market data contains non-positive asset prices.")
        
    # Calculate daily simple returns: (P_t / P_{t-1}) - 1
    raw_returns_df = prices_df.pct_change().dropna()
    
    # Translate returns to chosen base currency (TRY or USD)
    returns_df = convert_returns_to_base_currency(raw_returns_df, base_currency=base_currency)
    
    # Annualized mean return vector and sample covariance matrix
    annual_returns = returns_df.mean() * TRADING_DAYS_PER_YEAR
    annual_cov = returns_df.cov() * TRADING_DAYS_PER_YEAR
    
    return prices_df, returns_df, annual_returns, annual_cov

def calculate_cumulative_performance(returns_df: pd.DataFrame, base_val: float = 100.0) -> pd.DataFrame:
    """Computes growth of base investment (e.g. 100 TL/USD) over the sample period."""
    return base_val * (1.0 + returns_df).cumprod()

def get_dataset_metadata(prices_df: Optional[pd.DataFrame] = None, is_synthetic: bool = True, source_name: Optional[str] = None) -> Dict[str, any]:
    """Returns dataset provenance and transparency metadata."""
    if is_synthetic:
        data_type_tr = "Sentetik Simülasyon Veri Kümesi (Monte Carlo + Student-t)"
        data_type_en = "Synthetic Simulated Dataset (Monte Carlo + Student-t)"
    else:
        data_type_tr = f"Piyasa Verisi ({source_name or 'Yahoo Finance Günlük Kapanış'})"
        data_type_en = f"Market Data ({source_name or 'Yahoo Finance Daily Close'})"
        
    return {
        "is_synthetic": is_synthetic,
        "data_type_tr": data_type_tr,
        "data_type_en": data_type_en,
        "seed": 42 if is_synthetic else "N/A (Piyasa Verisi)",
        "n_trading_days": 1260 if prices_df is None else len(prices_df),
        "start_date": "2021-01-01" if prices_df is None else str(prices_df.index[0].date()),
        "end_date": "2025-12-31" if prices_df is None else str(prices_df.index[-1].date()),
        "base_currencies_supported": ["TRY", "USD"]
    }

