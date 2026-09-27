"""
Bayesian Black-Litterman Asset Allocation Engine
================================================
Combines CAPM Market Equilibrium Prior with subjective investor views
and confidence intervals to produce robust Bayesian posterior returns and weights.

Mathematical Formulation:
- Implied Equilibrium Returns: Pi = lambda * Sigma * w_mkt
- Uncertainty Scaling: tau in [0.025, 0.05]
- View Uncertainty Matrix: Omega = diag(P * (tau * Sigma) * P^T) * ((1 - c) / c)
- Posterior Expected Returns: mu_BL = [ (tau*Sigma)^-1 + P^T*Omega^-1*P ]^-1 * [ (tau*Sigma)^-1 * Pi + P^T*Omega^-1 * Q ]
- Posterior Covariance: Sigma_BL = Sigma + [ (tau*Sigma)^-1 + P^T*Omega^-1*P ]^-1
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from .portfolio_optimizer import optimize_max_sharpe

def compute_risk_aversion(
    benchmark_weights: np.ndarray,
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float = 0.05
) -> float:
    """
    Computes market risk aversion coefficient lambda from CAPM equilibrium.
    lambda = (E[R_mkt] - R_f) / Var(R_mkt)
    """
    w = np.asarray(benchmark_weights, dtype=float)
    mkt_return = float(np.dot(w, expected_returns))
    mkt_variance = float(np.dot(w.T, np.dot(cov_matrix, w)))
    lambda_val = (mkt_return - risk_free_rate) / max(mkt_variance, 1e-8)
    return float(np.clip(lambda_val, 1.0, 10.0))

def compute_implied_equilibrium_returns(
    benchmark_weights: np.ndarray,
    cov_matrix: np.ndarray,
    risk_aversion: float
) -> np.ndarray:
    """
    Reverse optimizes market equilibrium expected returns:
    Pi = lambda * Sigma * w_benchmark
    """
    w = np.asarray(benchmark_weights, dtype=float)
    return risk_aversion * np.dot(cov_matrix, w)

class BlackLittermanModel:
    """
    Full Bayesian Black-Litterman Portfolio Asset Allocation Framework.
    Supports user-configurable risk aversion, tau uncertainty, and strict dimension validation.
    """
    def __init__(
        self,
        asset_names: List[str],
        cov_matrix: np.ndarray,
        benchmark_weights: np.ndarray,
        expected_returns: Optional[np.ndarray] = None,
        risk_free_rate: float = 0.05,
        risk_aversion: Optional[float] = None,
        market_risk_premium: float = 0.075,
        tau: float = 0.04
    ):
        self.asset_names = asset_names
        self.n_assets = len(asset_names)
        self.cov_matrix = np.asarray(cov_matrix, dtype=float)
        self.benchmark_weights = np.asarray(benchmark_weights, dtype=float) / np.sum(benchmark_weights)
        self.risk_free_rate = risk_free_rate
        self.tau = tau
        
        # Calculate market equilibrium risk aversion
        if risk_aversion is not None:
            self.risk_aversion = float(risk_aversion)
        elif expected_returns is not None:
            self.risk_aversion = compute_risk_aversion(
                self.benchmark_weights, expected_returns, self.cov_matrix, risk_free_rate
            )
        else:
            mkt_variance = float(np.dot(self.benchmark_weights.T, np.dot(self.cov_matrix, self.benchmark_weights)))
            self.risk_aversion = market_risk_premium / max(mkt_variance, 1e-8)
            
        self.pi = compute_implied_equilibrium_returns(self.benchmark_weights, self.cov_matrix, self.risk_aversion)
        
    def run_bayesian_update(
        self,
        P: np.ndarray,
        Q: np.ndarray,
        confidences: Optional[List[float]] = None
    ) -> Dict[str, any]:
        """
        Executes Bayesian updating blending the market prior (Pi, tau*Sigma) with investor views (P, Q, Omega).
        
        Args:
            P (np.ndarray): (K x N) Pick matrix mapping views to assets.
            Q (np.ndarray): (K x 1) Vector of view returns.
            confidences (List[float]): List of investor confidence levels in [0.05, 0.95] per view.
            
        Returns:
            Dict containing:
                - implied_prior_returns (Pi)
                - posterior_returns (mu_BL)
                - posterior_cov (Sigma_BL)
                - optimal_weights (constrained max Sharpe)
                - benchmark_weights
        """
        K = len(Q)
        if K == 0:
            # No views provided: return pure equilibrium market prior
            opt = optimize_max_sharpe(self.pi, self.cov_matrix, self.risk_free_rate)
            return {
                "implied_prior_returns": self.pi,
                "posterior_returns": self.pi,
                "posterior_cov": self.cov_matrix,
                "optimal_weights": opt["weights"] if opt["success"] else self.benchmark_weights,
                "benchmark_weights": self.benchmark_weights,
                "views_p": np.empty((0, self.n_assets)),
                "views_q": np.empty(0),
                "omega_diag": np.empty(0)
            }
            
        P = np.asarray(P, dtype=float)
        Q = np.asarray(Q, dtype=float).reshape(-1, 1)
        
        # Dimensions & finite value validation
        if P.shape != (K, self.n_assets):
            raise ValueError(f"Pick matrix P shape {P.shape} does not match (K={K}, N={self.n_assets})")
        if not np.all(np.isfinite(P)) or not np.all(np.isfinite(Q)):
            raise ValueError("Views matrices P and Q must contain only finite numbers (no NaN or Inf).")
            
        tau_sigma = self.tau * self.cov_matrix
        inv_tau_sigma = np.linalg.pinv(tau_sigma)
        
        # Construct Omega (View uncertainty covariance matrix)
        if confidences is None:
            confidences = [0.65] * K
        elif len(confidences) != K:
            raise ValueError(f"Length of confidences ({len(confidences)}) must match number of views ({K})")
            
        omega_diag = []
        for k in range(K):
            conf = float(np.clip(confidences[k], 0.05, 0.95))
            # He-Litterman variance scaled by investor confidence
            p_k = P[k, :].reshape(1, -1)
            var_k = float((p_k @ tau_sigma @ p_k.T).item())
            # Higher confidence -> lower variance (omega)
            scaling = (1.0 - conf) / conf
            omega_diag.append(max(var_k * scaling, 1e-8))
            
        Omega = np.diag(omega_diag)
        inv_Omega = np.linalg.pinv(Omega)
        
        # Bayesian Posterior Mean Calculation:
        # M_inv = (tau*Sigma)^-1 + P^T * Omega^-1 * P
        M_inv = inv_tau_sigma + P.T @ inv_Omega @ P
        M = np.linalg.pinv(M_inv)
        
        # mu_BL = M * [ (tau*Sigma)^-1 * Pi + P^T * Omega^-1 * Q ]
        pi_col = self.pi.reshape(-1, 1)
        rhs = inv_tau_sigma @ pi_col + P.T @ inv_Omega @ Q
        mu_bl = (M @ rhs).flatten()
        
        # Posterior Covariance: Sigma_BL = Sigma + M
        sigma_bl = self.cov_matrix + M
        
        # Optimize constrained weights under Black-Litterman posterior
        opt = optimize_max_sharpe(mu_bl, sigma_bl, self.risk_free_rate)
        weights = opt["weights"] if opt["success"] else self.benchmark_weights
        
        return {
            "implied_prior_returns": self.pi,
            "posterior_returns": mu_bl,
            "posterior_cov": sigma_bl,
            "optimal_weights": weights,
            "benchmark_weights": self.benchmark_weights,
            "views_p": P,
            "views_q": Q.flatten(),
            "omega_diag": np.array(omega_diag)
        }
