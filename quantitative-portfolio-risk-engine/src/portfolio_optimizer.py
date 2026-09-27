"""
Markowitz Modern Portfolio Theory & Efficient Frontier Optimization Engine
==========================================================================
Provides quadratic programming solvers for:
- Maximum Sharpe Ratio (Tangency Portfolio)
- Global Minimum Variance (Min Volatility Portfolio)
- Target Return Constrained Portfolios
- Full Markowitz Efficient Frontier Generation (Filtering infeasible points)
- Ledoit-Wolf Covariance Matrix Shrinkage (Enhanced Matrix Conditioning)
- Monte Carlo Portfolio Universe Simulation (Dirichlet Sampling with modern RNG)
"""

from typing import Tuple, Dict, List, Optional
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.covariance import LedoitWolf

def shrink_covariance_ledoit_wolf(daily_returns_df: pd.DataFrame, annualize: bool = True) -> Tuple[np.ndarray, float]:
    """
    Applies the Ledoit-Wolf analytical shrinkage estimator to improve covariance conditioning.
    
    Formula:
        Sigma_shrunk = delta * F + (1 - delta) * S
        where S is sample covariance, F is structured constant correlation target,
        and delta is the optimal shrinkage intensity.
        
    Returns:
        shrunk_cov (np.ndarray): Positive-definite shrunk covariance matrix.
        shrinkage_intensity (float): Optimal shrinkage constant delta in [0, 1].
    """
    lw = LedoitWolf(assume_centered=False)
    lw.fit(daily_returns_df.values)
    cov_shrunk = lw.covariance_
    shrinkage = float(lw.shrinkage_)
    
    if annualize:
        cov_shrunk = cov_shrunk * 252.0
        
    return cov_shrunk, shrinkage

def portfolio_performance(
    weights: np.ndarray,
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float = 0.05
) -> Tuple[float, float, float]:
    """
    Calculates expected annual return, volatility, and Sharpe ratio of an allocation.
    
    Returns:
        port_return (float): w^T * mu
        port_volatility (float): sqrt(w^T * Sigma * w)
        sharpe_ratio (float): (port_return - risk_free_rate) / port_volatility
    """
    weights = np.asarray(weights, dtype=float)
    port_return = float(np.dot(weights, expected_returns))
    port_variance = float(np.dot(weights.T, np.dot(cov_matrix, weights)))
    port_vol = float(np.sqrt(max(port_variance, 1e-12)))
    sharpe = float((port_return - risk_free_rate) / port_vol)
    return port_return, port_vol, sharpe

def optimize_max_sharpe(
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float = 0.05,
    min_weight: float = 0.0,
    max_weight: float = 1.0
) -> Dict[str, any]:
    """
    Finds weights maximizing the Sharpe ratio (Tangency Portfolio).
    Transparently reports solver failure rather than silently defaulting to equal weights.
    """
    n_assets = len(expected_returns)
    
    # Feasibility pre-check
    if n_assets * min_weight > 1.0001 or n_assets * max_weight < 0.9999:
        return {
            "weights": None,
            "expected_return": None,
            "volatility": None,
            "sharpe_ratio": None,
            "success": False,
            "solver_message": f"Kısıtlar çözümsüz (Infeasible): {n_assets} varlık için [{min_weight:.2f}, {max_weight:.2f}] ağırlık kısıtları toplamı 1.0 yapamaz."
        }
        
    init_weights = np.ones(n_assets) / n_assets
    bounds = tuple((min_weight, max_weight) for _ in range(n_assets))
    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})
    
    def neg_sharpe(w):
        ret, vol, _ = portfolio_performance(w, expected_returns, cov_matrix, risk_free_rate)
        return -(ret - risk_free_rate) / vol
        
    res = minimize(
        neg_sharpe,
        init_weights,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 500, 'ftol': 1e-9}
    )
    
    if not res.success:
        return {
            "weights": None,
            "expected_return": None,
            "volatility": None,
            "sharpe_ratio": None,
            "success": False,
            "solver_message": f"SLSQP optimizasyon çözücüsü başarısız oldu: {res.message}"
        }
        
    weights = np.maximum(res.x, 0.0)
    weights = weights / np.sum(weights)
    ret, vol, sharpe = portfolio_performance(weights, expected_returns, cov_matrix, risk_free_rate)
    
    return {
        "weights": weights,
        "expected_return": ret,
        "volatility": vol,
        "sharpe_ratio": sharpe,
        "success": True,
        "solver_message": "Optimal çözüm başarıyla bulundu (SLSQP Yakınsadı)."
    }

def optimize_min_volatility(
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float = 0.05,
    min_weight: float = 0.0,
    max_weight: float = 1.0
) -> Dict[str, any]:
    """
    Finds weights minimizing the total portfolio variance (Global Minimum Variance).
    """
    n_assets = len(expected_returns)
    
    if n_assets * min_weight > 1.0001 or n_assets * max_weight < 0.9999:
        return {
            "weights": None,
            "expected_return": None,
            "volatility": None,
            "sharpe_ratio": None,
            "success": False,
            "solver_message": f"Kısıtlar çözümsüz: Varlık sınırları [{min_weight:.2f}, {max_weight:.2f}] toplamı 1.0 yapamaz."
        }
        
    init_weights = np.ones(n_assets) / n_assets
    bounds = tuple((min_weight, max_weight) for _ in range(n_assets))
    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})
    
    def portfolio_var(w):
        return np.dot(w.T, np.dot(cov_matrix, w))
        
    res = minimize(
        portfolio_var,
        init_weights,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 500, 'ftol': 1e-9}
    )
    
    if not res.success:
        return {
            "weights": None,
            "expected_return": None,
            "volatility": None,
            "sharpe_ratio": None,
            "success": False,
            "solver_message": f"SLSQP optimizasyon çözücüsü başarısız: {res.message}"
        }
        
    weights = np.maximum(res.x, 0.0)
    weights = weights / np.sum(weights)
    ret, vol, sharpe = portfolio_performance(weights, expected_returns, cov_matrix, risk_free_rate)
    
    return {
        "weights": weights,
        "expected_return": ret,
        "volatility": vol,
        "sharpe_ratio": sharpe,
        "success": True,
        "solver_message": "Optimal çözüm başarıyla bulundu (SLSQP Yakınsadı)."
    }

def optimize_target_return(
    target_return: float,
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float = 0.05,
    min_weight: float = 0.0,
    max_weight: float = 1.0
) -> Dict[str, any]:
    """
    Finds the minimum variance portfolio achieving at least the specified target return.
    Returns success=False if target return is infeasible under bounds.
    """
    n_assets = len(expected_returns)
    init_weights = np.ones(n_assets) / n_assets
    bounds = tuple((min_weight, max_weight) for _ in range(n_assets))
    constraints = (
        {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},
        {'type': 'eq', 'fun': lambda w: np.dot(w, expected_returns) - target_return}
    )
    
    def portfolio_var(w):
        return np.dot(w.T, np.dot(cov_matrix, w))
        
    res = minimize(
        portfolio_var,
        init_weights,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 500, 'ftol': 1e-9}
    )
    
    if not res.success:
        return {
            "weights": None,
            "expected_return": None,
            "volatility": None,
            "sharpe_ratio": None,
            "success": False,
            "solver_message": f"Hedef getiri ({target_return:.2%}) bu kısıtlar altında çözülemedi: {res.message}"
        }
        
    weights = np.maximum(res.x, 0.0)
    weights = weights / np.sum(weights)
    ret, vol, sharpe = portfolio_performance(weights, expected_returns, cov_matrix, risk_free_rate)
    
    return {
        "weights": weights,
        "expected_return": ret,
        "volatility": vol,
        "sharpe_ratio": sharpe,
        "success": True,
        "solver_message": "Hedef getiri için optimal portföy bulundu."
    }

def calculate_efficient_frontier(
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float = 0.05,
    n_points: int = 40
) -> List[Dict[str, any]]:
    """
    Generates points tracing the efficient frontier curve from min volatility to max return.
    Filters out any infeasible points to prevent duplicate or false frontier points.
    """
    min_vol_opt = optimize_min_volatility(expected_returns, cov_matrix, risk_free_rate)
    if not min_vol_opt["success"]:
        return []
        
    max_ret = float(np.max(expected_returns))
    min_ret = min_vol_opt["expected_return"]
    
    target_returns = np.linspace(min_ret, max_ret * 0.98, n_points)
    frontier_points = []
    
    for t_ret in target_returns:
        opt = optimize_target_return(t_ret, expected_returns, cov_matrix, risk_free_rate)
        if opt["success"] and opt["weights"] is not None:
            frontier_points.append({
                "return": opt["expected_return"],
                "volatility": opt["volatility"],
                "sharpe_ratio": opt["sharpe_ratio"],
                "weights": opt["weights"]
            })
            
    return frontier_points

def generate_monte_carlo_portfolios(
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float = 0.05,
    n_portfolios: int = 4000,
    seed: int = 42
) -> Dict[str, np.ndarray]:
    """
    Generates random Dirichlet-distributed allocations for visual portfolio dispersion cloud
    using isolated default_rng without mutating global random state.
    """
    rng = np.random.default_rng(seed)
    n_assets = len(expected_returns)
    
    # Dirichlet uniform sampling ensures sum(w) = 1 and w >= 0
    weights_matrix = rng.dirichlet(np.ones(n_assets) * 0.8, size=n_portfolios)
    
    returns_arr = np.dot(weights_matrix, expected_returns)
    variances = np.einsum('ij,jk,ik->i', weights_matrix, cov_matrix, weights_matrix)
    volatilities_arr = np.sqrt(np.maximum(variances, 1e-12))
    sharpes_arr = (returns_arr - risk_free_rate) / volatilities_arr
    
    return {
        "returns": returns_arr,
        "volatilities": volatilities_arr,
        "sharpe_ratios": sharpes_arr,
        "weights": weights_matrix
    }
