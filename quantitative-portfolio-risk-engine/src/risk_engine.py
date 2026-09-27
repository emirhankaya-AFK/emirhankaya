"""
Risk Analytics, Value-at-Risk (VaR), GARCH(1,1) & Macro Stress Testing Engine
=============================================================================
Provides institutional-grade risk metrics:
- Parametric (Gaussian & Cornish-Fisher expansion), Historical, and Monte Carlo VaR
- Conditional Value-at-Risk (CVaR / Expected Shortfall)
- GARCH(1,1) Dynamic Volatility Clustering with pure SciPy Maximum Likelihood Estimation (MLE)
- Multi-step forward conditional volatility forecasting
- Macroeconomic scenario stress testing & capital drawdown simulation
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import norm, skew, kurtosis, chi2, binom
from scipy.integrate import quad

def compute_portfolio_returns(returns_df: pd.DataFrame, weights: np.ndarray) -> pd.Series:
    """Computes daily portfolio return series given asset weight vector."""
    weights = np.asarray(weights, dtype=float)
    return pd.Series(np.dot(returns_df.values, weights), index=returns_df.index, name="portfolio_return")

def calculate_parametric_var_cvar(
    port_returns: pd.Series,
    confidence_level: float = 0.95,
    horizon_days: int = 1
) -> Dict[str, float]:
    r"""
    Computes Gaussian and Cornish-Fisher VaR and CVaR.
    For multi-day horizons (horizon_days > 1), distribution parameters (mean, volatility,
    skewness, and kurtosis) are computed directly from the true empirical rolling compound return
    series: R_T = \prod_{t=1}^T (1 + r_t) - 1, properly capturing non-linear distribution distortion.
    Cornish-Fisher CVaR is derived analytically via exact closed-form integration
    of the Cornish-Fisher quantile function against the standard Gaussian measure:
        \int_\alpha^1 z_{CF}(u) du = \phi(z_\alpha) * [ 1 + (S/6)*z_\alpha + (K/24)*(z_\alpha^2 - 1) - (S^2/36)*(2*z_\alpha^2 - 1) ]
    This eliminates numerical quadrature cutoff heuristics and evaluates with machine precision.
    """
    if horizon_days > 1:
        # Multi-day rolling compound returns: \prod(1 + r_t) - 1
        returns_horizon = (1.0 + port_returns).rolling(horizon_days).apply(np.prod, raw=True) - 1.0
        returns_horizon = returns_horizon.dropna()
        if len(returns_horizon) > 10:
            mu = float(returns_horizon.mean())
            sigma = float(returns_horizon.std())
            s = float(skew(returns_horizon))
            k = float(kurtosis(returns_horizon, fisher=True))
        else:
            mu = float(port_returns.mean()) * horizon_days
            sigma = float(port_returns.std()) * np.sqrt(horizon_days)
            s = float(skew(port_returns)) / np.sqrt(horizon_days)
            k = float(kurtosis(port_returns, fisher=True)) / horizon_days
    else:
        mu = float(port_returns.mean())
        sigma = float(port_returns.std())
        s = float(skew(port_returns))
        k = float(kurtosis(port_returns, fisher=True))
    
    alpha = 1.0 - confidence_level
    z_alpha = float(norm.ppf(confidence_level))
    
    # Standard Gaussian VaR & CVaR
    gaussian_var = -(mu - z_alpha * sigma)
    # Expected shortfall for standard normal: E[X | X > z] = phi(z) / (1 - alpha)
    gaussian_cvar = -(mu - (float(norm.pdf(z_alpha)) / alpha) * sigma)
    
    # Cornish-Fisher quantile at confidence_level with horizon-specific moments:
    z_cf_alpha = (
        z_alpha
        + (s / 6.0) * (z_alpha**2 - 1.0)
        + (k / 24.0) * (z_alpha**3 - 3.0 * z_alpha)
        - (s**2 / 36.0) * (2.0 * z_alpha**3 - 5.0 * z_alpha)
    )
    cf_var = -(mu - z_cf_alpha * sigma)
    
    # Exact Analytical Closed-Form Expected Shortfall:
    # \int_\alpha^1 z_{CF}(u) du = \int_{z_\alpha}^\infty z_{CF}(\Phi(z)) \phi(z) dz
    # Integrating Hermite polynomials against \phi(z):
    #   \int z \phi(z) dz = \phi(z_\alpha)
    #   \int (z^2 - 1) \phi(z) dz = z_\alpha \phi(z_\alpha)
    #   \int (z^3 - 3z) \phi(z) dz = (z_\alpha^2 - 1) \phi(z_\alpha)
    #   \int (2z^3 - 5z) \phi(z) dz = (2z_\alpha^2 - 1) \phi(z_\alpha)
    cf_integral_bracket = (
        1.0
        + (s / 6.0) * z_alpha
        + (k / 24.0) * (z_alpha**2 - 1.0)
        - (s**2 / 36.0) * (2.0 * z_alpha**2 - 1.0)
    )
    cf_cvar = -mu + sigma * (float(norm.pdf(z_alpha)) / alpha) * cf_integral_bracket
    # Ensure coherent risk measure consistency (CVaR >= VaR)
    cf_cvar = max(cf_cvar, cf_var)
    
    return {
        "gaussian_var": max(gaussian_var, 0.0),
        "gaussian_cvar": max(gaussian_cvar, 0.0),
        "cornish_fisher_var": max(cf_var, 0.0),
        "cornish_fisher_cvar": max(cf_cvar, 0.0)
    }

def calculate_historical_var_cvar(
    port_returns: pd.Series,
    confidence_level: float = 0.95,
    horizon_days: int = 1
) -> Tuple[float, float]:
    """
    Computes Historical Empirical Quantile VaR and CVaR.
    For multi-day horizons (e.g. 10 days), uses real rolling compound returns
    instead of square-root-of-time scaling.
    """
    if horizon_days > 1:
        # True multi-day rolling compounding: (1 + r_1)(1 + r_2)...(1 + r_k) - 1
        returns_horizon = (1.0 + port_returns).rolling(horizon_days).apply(np.prod, raw=True) - 1.0
        returns_scaled = returns_horizon.dropna()
    else:
        returns_scaled = port_returns
        
    alpha = 1.0 - confidence_level
    cutoff_ret = float(np.percentile(returns_scaled, alpha * 100.0))
    hist_var = -cutoff_ret
    
    # CVaR is average of returns worse than the VaR cutoff
    tail_losses = returns_scaled[returns_scaled <= cutoff_ret]
    hist_cvar = -float(tail_losses.mean()) if len(tail_losses) > 0 else hist_var
    
    return max(hist_var, 0.0), max(hist_cvar, hist_var)

def calculate_monte_carlo_var_cvar(
    port_returns: pd.Series,
    confidence_level: float = 0.95,
    horizon_days: int = 1,
    n_simulations: int = 10000,
    seed: int = 42
) -> Tuple[float, float, np.ndarray]:
    r"""
    Computes Monte Carlo simulated VaR and CVaR with Student-t heavy tail sampling.
    For horizon_days > 1, executes full multi-step compound path simulation:
        R_i = \prod_{t=1}^{horizon_days} (1 + r_{i,t}) - 1
    accurately capturing time-dependent compounding and heavy-tail shock accumulation.
    """
    rng = np.random.default_rng(seed)
    mu_daily = float(port_returns.mean())
    sigma_daily = float(port_returns.std())
    
    # Degrees of freedom for heavy tail realistic shocks
    df = 7.0
    scale_norm = np.sqrt(df / (df - 2.0)) # sqrt(7/5)
    
    if horizon_days <= 1:
        shocks = rng.standard_t(df=df, size=n_simulations) / scale_norm
        sim_returns = mu_daily + sigma_daily * shocks
    else:
        # Multi-step path simulation: (n_simulations, horizon_days)
        daily_shocks = rng.standard_t(df=df, size=(n_simulations, horizon_days)) / scale_norm
        daily_step_returns = mu_daily + sigma_daily * daily_shocks
        # Cumulative compound return over horizon: \prod(1 + r_t) - 1
        sim_returns = np.prod(1.0 + daily_step_returns, axis=1) - 1.0
        
    alpha = 1.0 - confidence_level
    cutoff = float(np.percentile(sim_returns, alpha * 100.0))
    mc_var = -cutoff
    
    tail = sim_returns[sim_returns <= cutoff]
    mc_cvar = -float(np.mean(tail)) if len(tail) > 0 else mc_var
    
    return max(mc_var, 0.0), max(mc_cvar, mc_var), sim_returns

class GARCH11:
    """
    Univariate GARCH(1,1) Volatility Model with pure SciPy Maximum Likelihood Estimation.
    sigma_t^2 = omega + alpha * eps_{t-1}^2 + beta * sigma_{t-1}^2
    Stationarity condition: alpha + beta < 1
    """
    def __init__(self):
        self.omega = 0.0
        self.alpha = 0.0
        self.beta = 0.0
        self.unconditional_vol = 0.0
        self.conditional_vol = None
        self.is_fitted = False
        self.solver_message = ""
        self.log_likelihood = 0.0
        
    def fit(self, returns: np.ndarray) -> "GARCH11":
        """
        Fits GARCH(1,1) parameters via constrained Maximum Likelihood Estimation (MLE).
        Transparently sets is_fitted=False if optimizer fails.
        """
        r = np.asarray(returns, dtype=float)
        # Demean returns
        eps = r - np.mean(r)
        var_sample = float(np.var(eps))
        
        # Initial guesses: omega, alpha, beta
        init_params = [var_sample * 0.05, 0.08, 0.88]
        bounds = ((1e-7, var_sample * 0.5), (0.01, 0.30), (0.60, 0.98))
        
        # Stationarity constraint: 1 - alpha - beta >= 1e-4
        constraints = ({'type': 'ineq', 'fun': lambda p: 0.999 - (p[1] + p[2])})
        
        def neg_log_likelihood(params):
            omega, a, b = params
            T = len(eps)
            sigma2 = np.zeros(T)
            sigma2[0] = var_sample
            
            for t in range(1, T):
                sigma2[t] = omega + a * (eps[t-1]**2) + b * sigma2[t-1]
                
            sigma2 = np.maximum(sigma2, 1e-8)
            # Log-likelihood: -0.5 * sum( ln(2pi) + ln(sigma_t^2) + eps_t^2 / sigma_t^2 )
            llh = -0.5 * np.sum(np.log(2.0 * np.pi) + np.log(sigma2) + (eps**2) / sigma2)
            return -llh
            
        res = minimize(
            neg_log_likelihood,
            init_params,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 300, 'ftol': 1e-7}
        )
        
        if res.success:
            self.omega, self.alpha, self.beta = res.x
            self.is_fitted = True
            self.solver_message = "GARCH(1,1) MLE başarıyla yakınsadı."
            self.log_likelihood = float(-res.fun)
        else:
            self.omega, self.alpha, self.beta = init_params
            self.is_fitted = False
            self.solver_message = f"GARCH(1,1) optimizasyonu yakınsamadı: {res.message}"
            self.log_likelihood = float(-res.fun)
            return self
            
        # Compute conditional volatility series
        T = len(eps)
        sigma2 = np.zeros(T)
        sigma2[0] = var_sample
        for t in range(1, T):
            sigma2[t] = self.omega + self.alpha * (eps[t-1]**2) + self.beta * sigma2[t-1]
            
        self.conditional_vol = np.sqrt(sigma2) * np.sqrt(252.0) # Annualized
        persistence = self.alpha + self.beta
        if persistence < 1.0:
            self.unconditional_vol = np.sqrt((self.omega / (1.0 - persistence)) * 252.0)
        else:
            self.unconditional_vol = np.sqrt(var_sample * 252.0)
            
        return self
        
    def forecast_volatility(self, n_days: int = 30) -> np.ndarray:
        """
        Multi-step forward conditional volatility forecast using textbook recursive formulation:
        sigma_{t+1}^2 = omega + alpha * eps_t^2 + beta * sigma_t^2
        sigma_{t+k}^2 = VL + (alpha + beta)^{k-1} * (sigma_{t+1}^2 - VL)
        """
        if not self.is_fitted:
            raise ValueError(f"GARCH modeli yakınsamadan tahmin üretilemez: {self.solver_message}")
            
        last_sigma2 = (self.conditional_vol[-1] / np.sqrt(252.0)) ** 2
        uncond_var = (self.unconditional_vol / np.sqrt(252.0)) ** 2
        persistence = self.alpha + self.beta
        
        forecasts = np.zeros(n_days)
        # Step 1
        forecasts[0] = np.sqrt(max(last_sigma2, 1e-8)) * np.sqrt(252.0)
        
        for k in range(2, n_days + 1):
            var_k = uncond_var + (persistence ** (k - 1)) * (last_sigma2 - uncond_var)
            forecasts[k-1] = np.sqrt(max(var_k, 1e-8)) * np.sqrt(252.0)
            
        return forecasts

STRESS_SCENARIOS: Dict[str, Dict[str, any]] = {
    "scen_2008_crisis": {
        "title_tr": "2008 Küresel Likidite & Kredi Krizi Şoku",
        "title_en": "2008 Global Liquidity & Credit Crunch",
        "description_tr": "Bankacılık krizi, küresel hisselerde sert satış ve güvenli limanlara kaçış.",
        "shocks": {
            "bist_100": -0.36,
            "sp_500": -0.38,
            "bist_bank": -0.48,
            "us_treasury": 0.12,
            "gold": 0.16,
            "brent_crude": -0.42,
            "usd_try": 0.22,
            "bitcoin": -0.55
        }
    },
    "scen_covid_shock": {
        "title_tr": "COVID-19 Pandemi Volatilite Patlaması",
        "title_en": "COVID-19 Pandemic Volatility Spike",
        "description_tr": "Küresel tedarik zinciri kesintisi, petrol çöküşü ve olağanüstü parasal genişleme.",
        "shocks": {
            "bist_100": -0.25,
            "sp_500": -0.32,
            "bist_bank": -0.30,
            "us_treasury": 0.15,
            "gold": 0.18,
            "brent_crude": -0.50,
            "usd_try": 0.14,
            "bitcoin": -0.38
        }
    },
    "scen_stagflation": {
        "title_tr": "Stagflasyon & Şahin Faiz Sıkılaşması",
        "title_en": "Stagflation & Aggressive Rate Hikes",
        "description_tr": "Kalıcı yüksek enflasyon, merkez bankası faiz artışları, tahvil satışları ve emtia rallisi.",
        "shocks": {
            "bist_100": -0.12,
            "sp_500": -0.22,
            "bist_bank": -0.18,
            "us_treasury": -0.18,
            "gold": 0.24,
            "brent_crude": 0.38,
            "usd_try": 0.18,
            "bitcoin": -0.28
        }
    },
    "scen_geopolitical_energy": {
        "title_tr": "Jeopolitik Enerji & Tedarik Şoku",
        "title_en": "Geopolitical Energy & Supply Disruption",
        "description_tr": "Boğazlar ve kritik enerji koridorlarında kesinti, petrol ve altın sıçraması.",
        "shocks": {
            "bist_100": -0.15,
            "sp_500": -0.14,
            "bist_bank": -0.20,
            "us_treasury": -0.04,
            "gold": 0.22,
            "brent_crude": 0.45,
            "usd_try": 0.16,
            "bitcoin": -0.15
        }
    }
}

def simulate_stress_test(
    weights: np.ndarray,
    asset_keys: List[str],
    scenario_key: str
) -> Dict[str, any]:
    """
    Simulates portfolio impact under a macro stress scenario.
    """
    scenario = STRESS_SCENARIOS.get(scenario_key)
    if not scenario:
        raise ValueError(f"Unknown scenario: {scenario_key}")
        
    shocks = scenario["shocks"]
    shock_vector = np.array([shocks.get(k, 0.0) for k in asset_keys])
    
    port_impact = float(np.dot(weights, shock_vector))
    
    # Asset level contributions
    contributions = {}
    for i, k in enumerate(asset_keys):
        contributions[k] = float(weights[i] * shock_vector[i])
        
    # Resilience rating
    if port_impact > -0.05:
        resilience_grade = "A+ (Olağanüstü Direnç / Highly Resilient)"
    elif port_impact > -0.12:
        resilience_grade = "A (Yüksek Direnç / Strong Resilience)"
    elif port_impact > -0.20:
        resilience_grade = "B (Dengeli / Moderate Resilience)"
    elif port_impact > -0.30:
        resilience_grade = "C (Hassas / Vulnerable)"
    else:
        resilience_grade = "D (Yüksek Risk / High Vulnerability)"
        
    return {
        "scenario_title_tr": scenario["title_tr"],
        "scenario_title_en": scenario["title_en"],
        "description_tr": scenario["description_tr"],
        "portfolio_impact": port_impact,
        "asset_contributions": contributions,
        "resilience_grade": resilience_grade,
        "shock_vector": shock_vector
    }

def compute_basel_zone_and_multiplier(exceptions: int) -> Tuple[str, float]:
    """
    Computes the regulatory Basel Committee on Banking Supervision (BCBS CRE53) Traffic Light Zone
    and supervisory capital scaling factor multiplier for 250 trading days at 99% 1-day VaR.
    
    Standard BCBS CRE53 Schedule:
        0 to 4 breaches: GREEN Zone, multiplier = 3.00
        5 breaches: YELLOW Zone, multiplier = 3.40
        6 breaches: YELLOW Zone, multiplier = 3.50
        7 breaches: YELLOW Zone, multiplier = 3.65
        8 breaches: YELLOW Zone, multiplier = 3.75
        9 breaches: YELLOW Zone, multiplier = 3.85
        10+ breaches: RED Zone, multiplier = 4.00
    """
    BASEL_SCALING_MAP = {
        0: 3.00, 1: 3.00, 2: 3.00, 3: 3.00, 4: 3.00,
        5: 3.40,
        6: 3.50,
        7: 3.65,
        8: 3.75,
        9: 3.85
    }
    if exceptions <= 4:
        return "GREEN (Yeşil Bölge - Geçerli Model)", 3.00
    elif 5 <= exceptions <= 9:
        return "YELLOW (Sarı Bölge - Denetim Uyarısı)", BASEL_SCALING_MAP.get(exceptions, 3.85)
    else:
        return "RED (Kırmızı Bölge - Model Reddedildi)", 4.00

def run_var_backtest(
    port_returns: pd.Series,
    confidence_level: float = 0.99,
    test_window: int = 250,
    estimation_window: int = 250
) -> Dict[str, any]:
    """
    Performs out-of-sample rolling VaR backtesting with Kupiec POF Likelihood Ratio test
    and Basel Committee on Banking Supervision (BCBS) Traffic Light classification.
    """
    total_days = len(port_returns)
    min_required = estimation_window + test_window
    if total_days < min_required:
        test_window = max(10, total_days - estimation_window)
        
    actual_returns = []
    var_forecasts = []
    dates = []
    
    alpha = 1.0 - confidence_level
    z_alpha = float(norm.ppf(confidence_level))
    start_idx = len(port_returns) - test_window
    
    for i in range(start_idx, len(port_returns)):
        hist_slice = port_returns.iloc[i - estimation_window:i]
        mu = float(hist_slice.mean())
        sigma = float(hist_slice.std())
        
        # Cornish-Fisher rolling 1-day VaR
        s = float(skew(hist_slice))
        k = float(kurtosis(hist_slice, fisher=True))
        z_cf = (
            z_alpha
            + (s / 6.0) * (z_alpha**2 - 1.0)
            + (k / 24.0) * (z_alpha**3 - 3.0 * z_alpha)
            - (s**2 / 36.0) * (2.0 * z_alpha**3 - 5.0 * z_alpha)
        )
        day_var = max(-(mu - z_cf * sigma), 0.0001)
        
        actual_ret = float(port_returns.iloc[i])
        actual_returns.append(actual_ret)
        var_forecasts.append(day_var)
        dates.append(port_returns.index[i])
        
    actual_returns = np.array(actual_returns)
    var_forecasts = np.array(var_forecasts)
    
    # Breaches: day return is less than -VaR
    breach_mask = actual_returns < -var_forecasts
    x = int(np.sum(breach_mask))
    n = len(actual_returns)
    p = alpha
    p_hat = x / n if n > 0 else 0.0
    
    # Kupiec POF Likelihood Ratio Test
    if x == 0:
        lr_stat = -2.0 * np.log((1.0 - p)**n)
    elif x == n:
        lr_stat = -2.0 * np.log(p**n)
    else:
        lr_stat = 2.0 * (
            x * np.log(p_hat / p) + (n - x) * np.log((1.0 - p_hat) / (1.0 - p))
        )
    lr_stat = max(0.0, float(lr_stat))
    p_value = float(1.0 - chi2.cdf(lr_stat, df=1))
    kupiec_decision = "Kabul (Model Tutarlı)" if p_value >= 0.05 else "Red (Sapma İstatistiki Olarak Anlamlı)"
    
    basel_zone, basel_multiplier = compute_basel_zone_and_multiplier(x)
    
    return {
        "test_days": n,
        "breaches": x,
        "breach_rate": p_hat,
        "expected_breaches": p * n,
        "kupiec_lr_stat": lr_stat,
        "kupiec_p_value": p_value,
        "kupiec_decision": kupiec_decision,
        "basel_zone": basel_zone,
        "basel_multiplier": basel_multiplier,
        "dates": dates,
        "actual_returns": actual_returns,
        "var_forecasts": var_forecasts,
        "breach_indices": np.where(breach_mask)[0]
    }

