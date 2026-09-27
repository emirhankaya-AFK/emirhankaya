# 🏛️ Institutional Quantitative Portfolio Optimization & Risk Engine

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Plotly](https://img.shields.io/badge/Plotly-5.18+-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com)
[![Pytest](https://img.shields.io/badge/Pytest-30%20Passed-10b981?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org)
[![Math Audit](https://img.shields.io/badge/Math%20Audit-8%2F8%20Verified-8b5cf6?style=for-the-badge)](tests/run_math_audit.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

An institutional-grade quantitative finance platform implementing modern portfolio theory, Bayesian asset allocation, volatility clustering models, closed-form extreme risk estimation, and regulatory backtesting.

Designed with an **Institutional Risk Terminal UI** that blends Bloomberg-terminal density with modern web ergonomics.

---

## 🏗️ Architecture & Data Pipeline

```mermaid
flowchart TD
    subgraph Ingestion["1. Market Data & Currency Normalization"]
        A1[Yahoo Finance API / Synthetic GBM] --> A2[Multi-Asset Time Series]
        A2 --> A3{Base Currency: TRY or USD?}
        A3 -->|Compound FX Adjustment| A4["Normalized Returns: R_TRY = (1 + R_USD)(1 + R_FX) - 1"]
    end

    subgraph Allocation["2. Quantitative Optimization Engine"]
        A4 --> B1[Ledoit-Wolf Covariance Shrinkage]
        B1 --> B2[Markowitz SLSQP Quadratic Solver]
        B2 --> B3[Max Sharpe / Tangency Portfolio]
        B2 --> B4[Global Minimum Variance GMV]
        B1 --> B5[Bayesian Black-Litterman Model]
        B5 -->|Prior + Subjective Views P, Q, Omega| B6[Posterior Expected Returns & Weights]
    end

    subgraph Risk["3. Econometrics & Tail Risk Analytics"]
        A4 --> C1["GARCH(1,1) Volatility Engine via SciPy MLE"]
        C1 --> C2[Conditional Volatility & 30-Day Forecast]
        A4 --> C3[1-Day & 10-Day Overlapping Return Horizons]
        C3 --> C4[Parametric & Historical VaR]
        C3 --> C5[10-Step Compound Monte Carlo Path Simulation]
        C3 --> C6[Analytical Cornish-Fisher Closed-Form CVaR]
    end

    subgraph Verification["4. Stress Testing & Regulatory Backtesting"]
        B3 & B4 & B6 --> D1[Basel III Traffic Light Backtest - BCBS CRE53]
        D1 --> D2[Kupiec POF Likelihood Ratio Test]
        B3 & B4 & B6 --> D3[Macro Stress Scenarios: 2008 Crisis, COVID-19, Stagflation]
        D3 --> D4[Drawdown & Portfolio Resilience Grade]
    end

    subgraph UI["5. Institutional Risk Terminal"]
        D1 & D2 & D4 & C2 & C6 --> E1[Streamlit Terminal Interface - 5 Specialized Views]
    end
```

---

## 🎯 Key Methodologies & Mathematical Foundations

### 1. Multi-Currency Normalization & Real Market Ingestion
- Supports 8 institutional asset classes: **BIST 100 (TRY), S&P 500 (USD), BIST Bank (TRY), US 10Y Treasury (USD), Gold Spot (USD), Brent Crude (USD), USD/TRY (FX), Bitcoin (USD)**.
- Full base currency parity: Converts USD returns to TRY or vice-versa using exact compounding:
  $$R_{TRY} = (1 + R_{USD})(1 + R_{FX}) - 1$$
- Eliminates currency misalignment errors present in standard open-source portfolio demos.

### 2. Robust Portfolio Optimization (SLSQP & Ledoit-Wolf)
- **High-Dimensional Covariance Estimation**: Computes Ledoit-Wolf analytical shrinkage covariance $\Sigma_{LW} = \delta F + (1 - \delta) S$, guaranteeing well-conditioned, positive semi-definite matrices even in volatile regimes.
- **Sequential Least Squares Programming (SLSQP)**: Solves constrained optimization for Maximum Sharpe (Tangency) and Global Minimum Variance (GMV) with analytical gradient bounds.
- **Monte Carlo Efficient Frontier**: 4,000 Dirichlet-distributed portfolios to visually evaluate feasible risk-return profiles.

### 3. Bayesian Black-Litterman Allocation
- Derives market-implied equilibrium returns via reverse CAPM optimization:
  $$\Pi = \lambda \Sigma w_{mkt}$$
- Updates equilibrium returns with investor subjective views (both absolute and relative) using Bayesian blending:
  $$E[R] = [(\tau\Sigma)^{-1} + P^T \Omega^{-1} P]^{-1} [(\tau\Sigma)^{-1} \Pi + P^T \Omega^{-1} Q]$$

### 4. Advanced Tail Risk & GARCH(1,1) Volatility
- **Closed-Form Cornish-Fisher Expected Shortfall (CVaR)**: Eliminates heuristic approximations by analytically integrating the Cornish-Fisher polynomial quantile function under standard Gaussian measure ($\approx 10^{-16}$ precision).
- **Exact Multi-Day Compounding**: Multi-day risk (10-day horizon) uses empirical 10-day overlapping returns and compound multi-step Monte Carlo paths, accurately capturing non-linear compounding and distribution drift.
- **GARCH(1,1) Engine**: Direct Maximum Likelihood Estimation (MLE) of $\sigma_t^2 = \omega + \alpha \epsilon_{t-1}^2 + \beta \sigma_{t-1}^2$ providing 30-day conditional volatility projections.

### 5. Basel III Regulatory Backtesting & Stress Simulation
- **BCBS CRE53 Traffic Light Standard**: Classifies model performance over a 250-day rolling window into Green, Yellow, and Red zones with exact capital multipliers ($5 \to 3.40\times, \dots, 10+ \to 4.00\times$).
- **Kupiec POF Likelihood Ratio Test**: Evaluates whether observed VaR exceptions statistically match the expected 99% coverage rate.
- **Macro Historical Stress Testing**: Assesses capital preservation under 2008 Global Financial Crisis, 2020 COVID-19 Shock, 1970s Stagflation, and Geopolitical Supply Shocks.

---

## 📊 Verification & Audit Results

The engine is accompanied by an independent mathematical audit suite (`tests/run_math_audit.py`) and exhaustive unit tests (`pytest`).

| Verification Suite | Target | Result | Status |
| :--- | :--- | :--- | :--- |
| **Unit Test Coverage** | 30 tests covering optimization, risk, solvers, and backtest | **30/30 Passed** | ✅ Verified |
| **Cornish-Fisher Integral Audit** | Numerical quadrature vs. Analytical closed-form CVaR | Difference $< 10^{-14}$ | ✅ Exact |
| **GARCH(1,1) MLE Stationarity** | Constraint $\alpha + \beta < 1$ and non-negativity $\omega > 0$ | $0.85 < 1.0$ | ✅ Verified |
| **Basel III Exception Multiplier** | Conformance to BCBS CRE53 Table 1 lookup | Exact match | ✅ Verified |
| **Ledoit-Wolf Shrinkage** | Condition number reduction & positive definiteness | $\kappa(\Sigma_{LW}) < \kappa(S)$ | ✅ Verified |
| **Currency Conversion Parity** | Multi-asset synthetic & live yfinance conversion consistency | Exact compound parity | ✅ Verified |

---

## 💻 Tech Stack

- **Core Engine**: Python 3.11, NumPy, SciPy (Optimize, Stats, Integrate), Pandas
- **Visualization & UI**: Streamlit, Plotly Graph Objects, Custom Institutional CSS
- **Data Ingestion**: yfinance, Requests, Custom Geometric Brownian Motion / Student-t simulator
- **Testing & Verification**: Pytest, Custom Mathematical Self-Audit Runner

---

## 🚀 Quickstart

### Prerequisites
- Python 3.11+
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/emirhankaya-AFK/quantitative-portfolio-risk-engine.git
cd quantitative-portfolio-risk-engine

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run Tests & Mathematical Audit
```bash
# Execute unit test suite
pytest tests/ -v

# Execute independent mathematical verification audit
python tests/run_math_audit.py
```

### Launch the Risk Terminal
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
