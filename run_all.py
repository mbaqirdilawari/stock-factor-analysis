"""Run the whole project:  python run_all.py

1. Download stock returns and Fama-French factors (saved in data/).
2. Fit the two models for every stock.
3. Save tables, charts and a plain-language summary in outputs/.
4. Fill the Results section of README.md.
"""
import argparse
from pathlib import Path

from src import data, models, plots, report

ROOT = Path(__file__).parent
TICKERS = ["AAPL", "MSFT", "NVDA", "JPM", "GS", "XOM", "JNJ", "PG", "KO", "WMT", "BTI", "UL"]
START = "2015-01-01"


def analyze(excess, factors, out_dir, readme_path=None):
    """Steps 2 to 4. Takes aligned data, writes everything, returns the summary text."""
    results = models.run_models(excess, factors)
    corr = models.correlation_matrix(excess)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results.to_csv(out_dir / "model_results.csv", index=False)
    corr.to_csv(out_dir / "correlation_matrix.csv")

    plots.make_all(excess, factors, results, corr, out_dir)
    summary = report.build_summary(excess, results, corr)
    report.write_summary(summary, out_dir)
    if readme_path is not None:
        report.update_readme(readme_path, summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description="Factor analysis of stock returns")
    parser.add_argument("--start", default=START, help="first date to download, for example 2015-01-01")
    parser.add_argument("--refresh", action="store_true", help="download the data again")
    parser.add_argument("--no-readme", action="store_true", help="do not change README.md")
    args = parser.parse_args()

    print("Step 1 of 3: downloading data...")
    factors = data.download_factors(ROOT / "data", refresh=args.refresh)
    returns = data.download_returns(TICKERS, args.start, ROOT / "data", refresh=args.refresh)
    excess, factor_table = data.line_up(returns, factors)
    print(f"  {len(excess)} months, {len(excess.columns)} stocks")

    print("Step 2 of 3: fitting models and drawing charts...")
    readme = None if args.no_readme else ROOT / "README.md"
    summary = analyze(excess, factor_table, ROOT / "outputs", readme)

    print("Step 3 of 3: done. Files are in the outputs/ folder.\n")
    print(summary)


if __name__ == "__main__":
    main()
