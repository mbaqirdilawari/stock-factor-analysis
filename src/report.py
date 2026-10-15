"""Step 4: write the results in plain words.

Every sentence below is built from the numbers of the run, so the text always
matches the data. Nothing is typed in by hand.
"""
from pathlib import Path

import numpy as np

from .models import FIVE_FACTORS

START_MARK = "<!-- RESULTS:START -->"
END_MARK = "<!-- RESULTS:END -->"


def markdown_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def build_summary(excess, results, corr, alpha_level=0.05):
    ff5 = results[results["model"] == "FF5"].set_index("ticker")
    capm = results[results["model"] == "CAPM"].set_index("ticker")
    tickers = list(ff5.index)
    n_stocks = len(tickers)

    # Table of results.
    headers = ["Stock", "Market beta", "Size", "Value", "Profitability", "Investment",
               "Alpha per year", "Alpha p-value", "R-squared (CAPM)", "R-squared (FF5)"]
    rows = []
    for t in tickers:
        rows.append([
            t,
            f"{ff5.loc[t, 'beta_Mkt-RF']:.2f}",
            f"{ff5.loc[t, 'beta_SMB']:.2f}",
            f"{ff5.loc[t, 'beta_HML']:.2f}",
            f"{ff5.loc[t, 'beta_RMW']:.2f}",
            f"{ff5.loc[t, 'beta_CMA']:.2f}",
            f"{ff5.loc[t, 'alpha_per_year'] * 100:.1f}%",
            f"{ff5.loc[t, 'alpha_p_value']:.2f}",
            f"{capm.loc[t, 'r2']:.2f}",
            f"{ff5.loc[t, 'r2']:.2f}",
        ])

    # Plain-language findings.
    avg_capm = capm["r2"].mean()
    avg_ff5 = ff5["r2"].mean()
    mkt = ff5["beta_Mkt-RF"]
    hml = ff5["beta_HML"]
    n_alpha = int((ff5["alpha_p_value"] < alpha_level).sum())

    pairs = corr.where(np.triu(np.ones(corr.shape, dtype=bool), k=1)).stack()
    top_pair, bottom_pair = pairs.idxmax(), pairs.idxmin()

    first = excess.index.min()
    last = excess.index.max()
    lines = [
        "### Data used",
        f"- Period: {first} to {last} ({len(excess)} months)",
        f"- Stocks ({n_stocks}): {', '.join(tickers)}",
        "",
        "### Results table (five-factor model)",
        markdown_table(headers, rows),
        "",
        "### What the numbers say",
        f"- The market alone (CAPM) explains {avg_capm * 100:.0f}% of the monthly moves on average. "
        f"Adding the four other factors (FF5) raises this to {avg_ff5 * 100:.0f}%.",
        f"- Highest market beta: {mkt.idxmax()} ({mkt.max():.2f}). Lowest: {mkt.idxmin()} ({mkt.min():.2f}). "
        "A beta above 1 means the stock tends to move more than the market.",
        f"- Most value-tilted (highest Value loading): {hml.idxmax()} ({hml.max():.2f}). "
        f"Most growth-tilted (lowest): {hml.idxmin()} ({hml.min():.2f}).",
        f"- Alpha (return not explained by the factors) is statistically different from zero at the "
        f"{int(alpha_level * 100)}% level for {n_alpha} of {n_stocks} stocks.",
        f"- Stocks that moved most closely together: {top_pair[0]} and {top_pair[1]} ({pairs.max():.2f}). "
        f"Least: {bottom_pair[0]} and {bottom_pair[1]} ({pairs.min():.2f}).",
        "",
        "### Charts",
        "![Correlation heatmap](outputs/correlation_heatmap.png)",
        "![R-squared, CAPM vs FF5](outputs/r2_capm_vs_ff5.png)",
        "![Factor loadings](outputs/factor_loadings.png)",
        "![Rolling market beta](outputs/rolling_market_beta.png)",
    ]
    return "\n".join(lines)


def write_summary(summary, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.md").write_text(summary + "\n", encoding="utf-8")


def update_readme(readme_path, summary):
    """Put the summary between the two markers in README.md."""
    readme_path = Path(readme_path)
    text = readme_path.read_text(encoding="utf-8")
    if START_MARK not in text or END_MARK not in text:
        raise ValueError("README.md is missing the RESULTS markers.")
    before = text.split(START_MARK)[0]
    after = text.split(END_MARK)[1]
    readme_path.write_text(before + START_MARK + "\n" + summary + "\n" + END_MARK + after, encoding="utf-8")
