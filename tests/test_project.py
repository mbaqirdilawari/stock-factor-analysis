"""Tests. Run with:  python -m pytest

They use made-up random numbers, so they need no internet. They check that the
code does what it says, for example that it can find a beta we planted.
"""
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from run_all import analyze  # noqa: E402
from src import data, models  # noqa: E402

FACTORS = ["Mkt-RF", "SMB", "HML", "RMW", "CMA"]


def fake_data(n=180, seed=1):
    """Random factors, and stocks built from them with betas we know."""
    rng = np.random.default_rng(seed)
    index = pd.period_range("2010-01", periods=n, freq="M")
    factors = pd.DataFrame(rng.normal(0.005, 0.04, (n, 5)), index=index, columns=FACTORS)
    factors["RF"] = 0.001
    noise = lambda: rng.normal(0, 0.01, n)  # noqa: E731
    excess = pd.DataFrame(
        {
            "AAA": 0.002 + 1.2 * factors["Mkt-RF"] + 0.5 * factors["SMB"] + noise(),
            "BBB": 0.8 * factors["Mkt-RF"] - 0.4 * factors["HML"] + noise(),
            "CCC": 1.0 * factors["Mkt-RF"] + noise(),
        },
        index=index,
    )
    return excess, factors


SAMPLE_FILE = """This file was created by CMPT_ME_BEME_RETS using the 202508 CRSP database.

,Mkt-RF,SMB,HML,RMW,CMA,RF
196307,   -0.39,   -0.46,   -0.81,    0.64,   -1.15,    0.27
196308,    5.07,   -0.80,    1.65,    0.40,   -0.38,    0.25

 Annual Factors: January-December
,Mkt-RF,SMB,HML,RMW,CMA,RF
1964,   12.44,   -1.20,    8.94,    2.36,    5.64,    3.35
"""


def test_parse_reads_only_the_monthly_table_and_converts_percent():
    table = data.parse_french_csv(SAMPLE_FILE)
    assert len(table) == 2
    assert str(table.index[0]) == "1963-07"
    assert abs(table.loc[pd.Period("1963-08"), "Mkt-RF"] - 0.0507) < 1e-12


def test_parse_fails_clearly_on_a_bad_file():
    try:
        data.parse_french_csv("nothing useful here")
    except ValueError:
        return
    raise AssertionError("expected a ValueError")


def test_regression_finds_the_planted_betas():
    excess, factors = fake_data()
    out = models.fit_one(excess["AAA"], factors, FACTORS)
    assert abs(out["beta_Mkt-RF"] - 1.2) < 0.1
    assert abs(out["beta_SMB"] - 0.5) < 0.1
    assert abs(out["beta_HML"]) < 0.1  # planted as zero
    assert abs(out["alpha_per_month"] - 0.002) < 0.003


def test_planted_effects_are_significant():
    excess, factors = fake_data()
    out = models.fit_one(excess["AAA"], factors, FACTORS)
    assert out["p_Mkt-RF"] < 0.001
    assert out["p_SMB"] < 0.001


def test_newey_west_errors_are_close_to_classical_errors_on_random_data():
    excess, factors = fake_data(n=400, seed=7)
    y = excess["CCC"].to_numpy()
    X = np.column_stack([np.ones(len(y)), factors["Mkt-RF"].to_numpy()])
    _, se, _, _, _, _ = models.ols_newey_west(y, X, lags=3)
    resid = y - X @ np.linalg.lstsq(X, y, rcond=None)[0]
    classical = np.sqrt(np.diag(np.linalg.inv(X.T @ X)) * resid.var(ddof=2))
    assert np.all(np.abs(se / classical - 1) < 0.3)


def test_r_squared_is_between_0_and_1_and_more_factors_never_lower_it():
    excess, factors = fake_data()
    results = models.run_models(excess, factors)
    assert results["r2"].between(0, 1).all()
    for ticker in excess.columns:
        pair = results[results["ticker"] == ticker].set_index("model")["r2"]
        assert pair["FF5"] >= pair["CAPM"] - 1e-12


def test_correlation_matrix_is_symmetric_with_ones_on_the_diagonal():
    excess, _ = fake_data()
    corr = models.correlation_matrix(excess)
    assert np.allclose(corr.to_numpy(), corr.to_numpy().T)
    assert np.allclose(np.diag(corr.to_numpy()), 1.0)


def test_rolling_beta_of_the_market_against_itself_is_one():
    _, factors = fake_data()
    beta = models.rolling_beta(factors["Mkt-RF"], factors["Mkt-RF"], window=36).dropna()
    assert np.allclose(beta.to_numpy(), 1.0)


def test_line_up_keeps_shared_months_and_subtracts_the_risk_free_rate():
    excess, factors = fake_data(n=24)
    returns = excess.add(factors["RF"], axis=0).iloc[:20]  # stocks cover fewer months
    out_excess, out_factors = data.line_up(returns, factors)
    assert len(out_excess) == 20
    assert np.allclose(out_excess.to_numpy(), excess.iloc[:20].to_numpy())
    assert list(out_factors.columns) == FACTORS + ["RF"]


def test_whole_pipeline_writes_files_and_fills_the_readme():
    excess, factors = fake_data()
    with tempfile.TemporaryDirectory() as folder:
        folder = Path(folder)
        readme = folder / "README.md"
        readme.write_text("Intro\n<!-- RESULTS:START -->\nold\n<!-- RESULTS:END -->\nOutro\n", encoding="utf-8")
        summary = analyze(excess, factors, folder / "outputs", readme)

        for name in ["model_results.csv", "correlation_matrix.csv", "summary.md",
                     "correlation_heatmap.png", "r2_capm_vs_ff5.png",
                     "factor_loadings.png", "rolling_market_beta.png"]:
            assert (folder / "outputs" / name).stat().st_size > 0, name

        text = readme.read_text(encoding="utf-8")
        assert "old" not in text and "Intro" in text and "Outro" in text
        assert "AAA" in text and "What the numbers say" in text
        assert summary in text
