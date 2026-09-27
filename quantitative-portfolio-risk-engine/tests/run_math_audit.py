import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import numpy as np
import pandas as pd
from src.data_loader import load_market_data, get_benchmark_weights, get_asset_universe
from src.portfolio_optimizer import shrink_covariance_ledoit_wolf, optimize_max_sharpe, optimize_min_volatility
from src.black_litterman import BlackLittermanModel
from src.risk_engine import (
    calculate_parametric_var_cvar,
    calculate_historical_var_cvar,
    calculate_monte_carlo_var_cvar,
    GARCH11,
    compute_portfolio_returns
)

prices, returns, ann_ret, ann_cov = load_market_data()
cov, delta = shrink_covariance_ledoit_wolf(returns)
weights = get_benchmark_weights()

print("=== MATHEMATICAL & STATISTICAL SELF-AUDIT ===")
# 1. Covariance Positive Definiteness
eigvals = np.linalg.eigvalsh(cov)
assert np.all(eigvals > 0), "FAILED: Covariance not positive definite"
print(f"1. Covariance Positive Definite: PASS (min eigval: {np.min(eigvals):.6f})")

# 2. Ledoit-Wolf Shrinkage
assert 0.0 <= delta <= 1.0, "FAILED: Shrinkage intensity out of bounds"
print(f"2. Ledoit-Wolf Shrinkage Delta: PASS ({delta:.4f})")

# 3. Markowitz Max Sharpe & Min Vol
ms = optimize_max_sharpe(ann_ret.values, cov)
mv = optimize_min_volatility(ann_ret.values, cov)
assert np.isclose(np.sum(ms['weights']), 1.0, atol=1e-5), "FAILED: Max Sharpe weights != 1"
assert np.isclose(np.sum(mv['weights']), 1.0, atol=1e-5), "FAILED: Min Vol weights != 1"
assert ms['sharpe_ratio'] >= mv['sharpe_ratio'], "FAILED: Max Sharpe ratio < Min Vol Sharpe"
print(f"3. Markowitz Weights & Sharpe: PASS (Max Sharpe: {ms['sharpe_ratio']:.2f}, Min Vol Sharpe: {mv['sharpe_ratio']:.2f})")

# 4. Black-Litterman
bl = BlackLittermanModel(get_asset_universe(), cov, weights)
P = np.zeros((1, 8))
P[0, 0] = 1.0
Q = np.array([0.25])
res_bl = bl.run_bayesian_update(P, Q)
assert np.isclose(np.sum(res_bl['optimal_weights']), 1.0, atol=1e-5), "FAILED: BL weights != 1"
print(f"4. Black-Litterman Bayesian Posterior: PASS (Prior Ret BIST: {bl.pi[0]:.2%}, Posterior: {res_bl['posterior_returns'][0]:.2%})")

# 5. VaR and CVaR Consistency
port_ret = compute_portfolio_returns(returns, ms['weights'])
p_var = calculate_parametric_var_cvar(port_ret)
assert p_var['gaussian_cvar'] >= p_var['gaussian_var'], "FAILED: Gaussian CVaR < VaR"
assert p_var['cornish_fisher_cvar'] >= p_var['cornish_fisher_var'], "FAILED: CF CVaR < VaR"
h_var, h_cvar = calculate_historical_var_cvar(port_ret)
assert h_cvar >= h_var, "FAILED: Historical CVaR < VaR"
print(f"5. VaR & CVaR Ordering: PASS (Parametric VaR: {p_var['gaussian_var']:.2%}, CVaR: {p_var['gaussian_cvar']:.2%})")

# 6. GARCH(1,1) Stationarity
g = GARCH11().fit(port_ret.values)
assert g.alpha + g.beta < 1.0, "FAILED: GARCH non-stationary"
print(f"6. GARCH(1,1) Stationarity: PASS (alpha+beta = {g.alpha + g.beta:.4f} < 1.0, uncond vol: {g.unconditional_vol:.2%})")

# 7. Cornish-Fisher Closed-Form vs Independent Numerical Quadrature
from scipy.stats import norm, skew, kurtosis
from scipy.integrate import quad
s_val = float(skew(port_ret))
k_val = float(kurtosis(port_ret, fisher=True))
z_95 = float(norm.ppf(0.95))
cf_bracket = 1.0 + (s_val / 6.0) * z_95 + (k_val / 24.0) * (z_95**2 - 1.0) - (s_val**2 / 36.0) * (2.0 * z_95**2 - 1.0)
closed_form_val = float(norm.pdf(z_95)) * cf_bracket

def num_integrand(z):
    z_cf = z + (s_val / 6.0) * (z**2 - 1.0) + (k_val / 24.0) * (z**3 - 3.0 * z) - (s_val**2 / 36.0) * (2.0 * z**3 - 5.0 * z)
    return z_cf * norm.pdf(z)

num_val, _ = quad(num_integrand, z_95, 12.0)
diff_cf = abs(closed_form_val - num_val)
assert diff_cf < 1e-8, f"FAILED: Analytical CF and numerical quad diverge: {diff_cf}"
print(f"7. Cornish-Fisher Analytical Closed-Form: PASS (Divergence vs Quad: {diff_cf:.2e} < 1e-8)")

# 8. Basel III / BCBS Kupiec POF VaR Backtesting
from src.risk_engine import run_var_backtest
bt = run_var_backtest(port_ret, confidence_level=0.99, test_window=250, estimation_window=250)
assert bt["test_days"] == 250
assert bt["basel_zone"].startswith("GREEN") or bt["basel_zone"].startswith("YELLOW"), f"FAILED: Basel zone unexpected: {bt['basel_zone']}"
assert bt["kupiec_lr_stat"] >= 0.0
print(f"8. Basel III & Kupiec POF Backtest: PASS ({bt['breaches']} breaches in 250d, {bt['basel_zone'].split('(')[0].strip()}, LR: {bt['kupiec_lr_stat']:.2f}, p: {bt['kupiec_p_value']:.4f})")

print("=== ALL 8 MATHEMATICAL CHECKS PASSED PERFECTLY! ===")

