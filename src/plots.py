"""Step 3: four simple charts, saved as PNG files."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # draw to files, no window needed
import matplotlib.pyplot as plt
import numpy as np

from .models import FIVE_FACTORS, rolling_beta

FACTOR_LABELS = {
    "Mkt-RF": "Market",
    "SMB": "Size",
    "HML": "Value",
    "RMW": "Profitability",
    "CMA": "Investment",
}


def _heatmap(ax, values, row_labels, col_labels, vmin, vmax, cmap):
    image = ax.imshow(values, vmin=vmin, vmax=vmax, cmap=cmap)
    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, rotation=45, ha="right")
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels)
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            strong = abs(values[i, j]) > 0.6 * max(abs(vmin), abs(vmax))
            ax.text(j, i, f"{values[i, j]:.2f}", ha="center", va="center", fontsize=7,
                    color="white" if strong else "black")
    return image


def correlation_chart(corr, path):
    fig, ax = plt.subplots(figsize=(7, 6))
    image = _heatmap(ax, corr.to_numpy(), list(corr.index), list(corr.columns), -1, 1, "RdBu_r")
    ax.set_title("How closely do the stocks move together?\n(monthly excess returns, 1 = move exactly together)")
    fig.colorbar(image, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def r2_chart(results, path):
    capm = results[results["model"] == "CAPM"].set_index("ticker")["r2"]
    ff5 = results[results["model"] == "FF5"].set_index("ticker")["r2"]
    x = np.arange(len(capm))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(x - 0.2, capm.to_numpy(), width=0.4, label="Market only (CAPM)")
    ax.bar(x + 0.2, ff5.loc[capm.index].to_numpy(), width=0.4, label="Five factors (FF5)")
    ax.set_xticks(x)
    ax.set_xticklabels(capm.index)
    ax.set_ylabel("Share of monthly moves explained (R-squared)")
    ax.set_title("Do four more factors explain more than the market alone?")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def loadings_chart(results, path):
    ff5 = results[results["model"] == "FF5"].set_index("ticker")
    values = ff5[[f"beta_{f}" for f in FIVE_FACTORS]].to_numpy()
    limit = max(1.0, float(np.abs(values).max()))
    fig, ax = plt.subplots(figsize=(6.5, 6))
    image = _heatmap(
        ax, values, list(ff5.index), [FACTOR_LABELS[f] for f in FIVE_FACTORS], -limit, limit, "RdBu_r"
    )
    ax.set_title("How much does each stock lean on each factor?\n(FF5 betas)")
    fig.colorbar(image, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def rolling_beta_chart(excess, factors, path, tickers=("BTI", "UL")):
    chosen = [t for t in tickers if t in excess.columns] or list(excess.columns[:2])
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for ticker in chosen:
        beta = rolling_beta(excess[ticker], factors["Mkt-RF"], window=36).dropna()
        ax.plot(beta.index.to_timestamp(), beta.to_numpy(), label=ticker)
    ax.axhline(1.0, color="grey", linestyle="--", linewidth=1)
    ax.set_ylabel("Market beta (36-month window)")
    ax.set_title("Does a stock's market beta stay the same over time?")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def make_all(excess, factors, results, corr, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    correlation_chart(corr, out_dir / "correlation_heatmap.png")
    r2_chart(results, out_dir / "r2_capm_vs_ff5.png")
    loadings_chart(results, out_dir / "factor_loadings.png")
    rolling_beta_chart(excess, factors, out_dir / "rolling_market_beta.png")
