### Data used
- Period: 2015-02 to 2026-08 (139 months)
- Stocks (12): AAPL, MSFT, NVDA, JPM, GS, XOM, JNJ, PG, KO, WMT, BTI, UL

### Results table (five-factor model)
| Stock | Market beta | Size | Value | Profitability | Investment | Alpha per year | Alpha p-value | R-squared (CAPM) | R-squared (FF5) |
|---|---|---|---|---|---|---|---|---|---|
| AAPL | 1.14 | -0.06 | -0.44 | 0.47 | -0.13 | 7.8% | 0.14 | 0.43 | 0.50 |
| MSFT | 1.05 | -0.63 | -0.37 | 0.44 | -0.19 | 8.9% | 0.04 | 0.38 | 0.59 |
| NVDA | 1.65 | -0.21 | -0.65 | 0.37 | -0.73 | 40.0% | 0.00 | 0.34 | 0.43 |
| JPM | 1.05 | 0.01 | 0.98 | -0.21 | -0.36 | 7.1% | 0.07 | 0.51 | 0.72 |
| GS | 1.30 | 0.14 | 0.87 | -0.28 | -0.42 | 3.9% | 0.38 | 0.57 | 0.70 |
| XOM | 0.80 | 0.24 | 0.75 | 0.34 | 0.60 | 1.5% | 0.79 | 0.18 | 0.48 |
| JNJ | 0.55 | -0.10 | -0.05 | 0.18 | 0.71 | 3.7% | 0.40 | 0.16 | 0.29 |
| PG | 0.54 | -0.33 | -0.26 | 0.51 | 0.89 | -1.0% | 0.75 | 0.11 | 0.41 |
| KO | 0.56 | -0.45 | 0.25 | 0.37 | 0.28 | 0.7% | 0.86 | 0.17 | 0.39 |
| WMT | 0.52 | -0.23 | -0.23 | 0.38 | 0.27 | 5.5% | 0.26 | 0.13 | 0.20 |
| BTI | 0.65 | -0.15 | 0.26 | 0.18 | 0.55 | -1.1% | 0.85 | 0.13 | 0.22 |
| UL | 0.50 | -0.04 | -0.23 | 0.45 | 0.45 | -1.6% | 0.73 | 0.13 | 0.21 |

### What the numbers say
- The market alone (CAPM) explains 27% of the monthly moves on average. Adding the four other factors (FF5) raises this to 43%.
- Highest market beta: NVDA (1.65). Lowest: UL (0.50). A beta above 1 means the stock tends to move more than the market.
- Most value-tilted (highest Value loading): JPM (0.98). Most growth-tilted (lowest): NVDA (-0.65).
- Alpha (return not explained by the factors) is statistically different from zero at the 5% level for 2 of 12 stocks.
- Stocks that moved most closely together: JPM and GS (0.82). Least: NVDA and PG (-0.00).

### Charts
![Correlation heatmap](outputs/correlation_heatmap.png)
![R-squared, CAPM vs FF5](outputs/r2_capm_vs_ff5.png)
![Factor loadings](outputs/factor_loadings.png)
![Rolling market beta](outputs/rolling_market_beta.png)
