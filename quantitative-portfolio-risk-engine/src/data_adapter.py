"""
Market Data Adapter Layer
=========================
Provides modular interfaces for sourcing historical prices from:
1. Synthetic institutional simulation datasets (local CSV)
2. Live market data providers (e.g. Yahoo Finance / REST APIs)
Strictly avoids silent fallbacks to ensure full transparency of data origin.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import os
import pandas as pd
import numpy as np

class BaseMarketDataAdapter(ABC):
    """Abstract base class for all market data providers."""
    
    @abstractmethod
    def fetch_prices(self, asset_tickers: List[str], start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """Fetches daily price time series for given asset list."""
        pass
        
    @abstractmethod
    def get_source_info(self) -> Dict[str, any]:
        """Returns provenance, currency, and data type metadata."""
        pass

class SyntheticCSVAdapter(BaseMarketDataAdapter):
    """Adapter for reproducible institutional simulation datasets."""
    
    def __init__(self, filepath: Optional[str] = None):
        if filepath is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            filepath = os.path.join(base_dir, "data", "institutional_market_data.csv")
        self.filepath = filepath
        
    def fetch_prices(self, asset_tickers: Optional[List[str]] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Data file not found at: {self.filepath}")
            
        df = pd.read_csv(self.filepath, parse_dates=["date"], index_col="date")
        if asset_tickers:
            missing = [t for t in asset_tickers if t not in df.columns]
            if missing:
                raise KeyError(f"Assets not found in dataset: {missing}")
            df = df[asset_tickers]
            
        if start_date:
            df = df[df.index >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df.index <= pd.to_datetime(end_date)]
            
        return df
        
    def get_source_info(self) -> Dict[str, any]:
        return {
            "source_type": "Sentetik Simülasyon (Synthetic Simulation)",
            "is_live": False,
            "generator": "Monte Carlo + Student-t Copula Drift Model (Seed: 42)",
            "update_status": "Statik Dosya (Offline Reproducible)",
            "description": "5 yıllık günlük parametrik şok ve korelasyon modeliyle üretilmiş sentetik veri kümesi."
        }

class YahooFinanceAdapter(BaseMarketDataAdapter):
    """
    Adapter skeleton for live Yahoo Finance market data feeds.
    Does NOT silently fall back if live feed fails or library is not installed.
    """
    
    TICKER_MAP = {
        "bist_100": "XU100.IS",
        "sp_500": "SPY",
        "bist_bank": "XBANK.IS",
        "us_treasury": "IEF",
        "gold": "GLD",
        "brent_crude": "BNO",
        "usd_try": "USDTRY=X",
        "bitcoin": "BTC-USD"
    }
    
    def __init__(self):
        self.is_available = False
        try:
            import yfinance as yf
            self._yf = yf
            self.is_available = True
        except ImportError:
            self._yf = None
            
    def fetch_prices(self, asset_tickers: Optional[List[str]] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        if not self.is_available:
            raise ImportError(
                "Canlı veri adaptörü 'yfinance' kütüphanesini gerektirir. "
                "Lütfen 'pip install yfinance' komutunu çalıştırın. "
                "Sistem sessizce sentetik veriye geçiş yapmamaktadır."
            )
            
        tickers = [self.TICKER_MAP.get(k, k) for k in (asset_tickers or list(self.TICKER_MAP.keys()))]
        raw = self._yf.download(tickers, start=start_date or "2021-01-01", end=end_date, progress=False)
        if raw.empty:
            raise ValueError(f"Yahoo Finance returned empty dataset for tickers: {tickers}")
            
        if isinstance(raw.columns, pd.MultiIndex):
            lvl0 = raw.columns.get_level_values(0)
            if "Adj Close" in lvl0:
                data = raw["Adj Close"]
            elif "Close" in lvl0:
                data = raw["Close"]
            else:
                data = raw.iloc[:, :len(tickers)]
        else:
            if "Adj Close" in raw.columns:
                data = raw[["Adj Close"]]
            elif "Close" in raw.columns:
                data = raw[["Close"]]
            else:
                data = raw
                
        # Invert ticker map
        rev_map = {v: k for k, v in self.TICKER_MAP.items()}
        data = data.rename(columns=rev_map)
        valid_cols = [c for c in data.columns if c in self.TICKER_MAP]
        data = data[valid_cols].dropna()
        return data
        
    def get_source_info(self) -> Dict[str, any]:
        return {
            "source_type": "Piyasa Verisi (Yahoo Finance API)",
            "is_live": True,
            "provider": "Yahoo Finance Günlük Kapanış (yfinance)",
            "is_installed": self.is_available,
            "description": "Yahoo Finance üzerinden çekilen hisse senedi, tahvil, emtia ve kur kapanış fiyatları."
        }

