"""Step 2: the statistics.

For each stock we fit two simple models with ordinary least squares (OLS):

  CAPM : stock excess return = alpha + beta x market
  FF5  : stock excess return = alpha + 5 factor betas (market, size, value,
         profitability, investment)

Standard errors use the Newey-West method (3 lags), which stays reliable when
the errors in neighbouring months are related to each other.
"""
import math

import numpy as np
import pandas as pd

FIVE_FACTORS = ["Mkt-RF", "SMB", "HML", "RMW", "CMA"]
MODELS = {"CAPM": ["Mkt-RF"], "FF5": FIVE_FACTORS}


def two_sided_p_value(t_stat):
    """p-value from a t-statistic, using the normal curve (fine for 100+ months)."""
    return math.erfc(abs(t_stat) / math.sqrt(2))


def ols_newey_west(y, X, lags=3):
    """Fit y = X b with OLS and return b, its standard errors, t-stats, p-values, R-squared.

    y is a 1-D array. X is a 2-D array whose first column is all ones.
    """
    n, k = X.shape
    xtx_inv = np.linalg.inv(X.T @ X)
    coef = xtx_inv @ (X.T @ y)
    resid = y - X @ coef

    # Newey-West "sandwich" for the covariance of the coefficients.
    scores = X * resid[:, None]
    middle = scores.T @ scores
    for lag in range(1, lags + 1):
        weight = 1 - lag / (lags + 1)
        cross = scores[lag:].T @ scores[:-lag]
        middle += weight * (cross + cross.T)
    cov = xtx_inv @ middle @ xtx_inv

    se = np.sqrt(np.diag(cov))
    t_stats = coef / se
    p_values = np.array([two_sided_p_value(t) for t in t_stats])

    ss_res = float(resid @ resid)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot
    adj_r2 = 1 - (1 - r2) * (n - 1) / (n - k)
    return coef, se, t_stats, p_values, r2, adj_r2


def fit_one(y, factors, factor_names, lags=3):
    """Fit one stock against a list of factors. Returns a dictionary of results."""
    X = np.column_stack([np.ones(len(y))] + [factors[f].to_numpy() for f in factor_names])
    coef, se, t_stats, p_values, r2, adj_r2 = ols_newey_west(y.to_numpy(), X, lags)
    out = {
        "alpha_per_month": coef[0],
        "alpha_p_value": p_values[0],
        "r2": r2,
        "adj_r2": adj_r2,
        "n_months": len(y),
    }
    for i, name in enumerate(factor_names, start=1):
        out[f"beta_{name}"] = coef[i]
        out[f"p_{name}"] = p_values[i]
    return out


def run_models(excess, factors):
    """Fit CAPM and FF5 for every stock. Returns one row per stock and model."""
    rows = []
    for ticker in excess.columns:
        for model_name, factor_names in MODELS.items():
            row = {"ticker": ticker, "model": model_name}
            row.update(fit_one(excess[ticker], factors, factor_names))
            row["alpha_per_year"] = row["alpha_per_month"] * 12
            rows.append(row)
    return pd.DataFrame(rows)


def correlation_matrix(excess):
    """How closely do the stocks move together? (-1 to +1)"""
    return excess.corr()


def rolling_beta(stock_excess, market_excess, window=36):
    """Market beta measured over a moving window of months."""
    return stock_excess.rolling(window).cov(market_excess) / market_excess.rolling(window).var()
