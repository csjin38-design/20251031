# Stock Price Dataset Analysis

This repository documents `temp.csv`, a multi-ticker price history spanning Samsung Electronics (005930.KS), Apple (AAPL), and NVIDIA (NVDA). The data were ingested with Python's standard `csv` module and shaped into analysis-ready frames with `pandas` for statistics and mean-variance optimisation.

## Data Overview
- **Coverage:** 516 trading days from 16 Oct 2023 through 10 Oct 2025.
- **Schema:** The raw file stores a three-row header (price field, ticker, blank spacer) followed by daily observations. Stitching the first two header rows produces composite column names such as `AAPL_Close` and `NVDA_Volume`.
- **Completeness:** Each ticker has occasional holiday gaps. After dropping rows with any missing close, 465 dates remain; requiring a prior observation for returns yields 424 overlapping daily return points for portfolio work.
- **Units:** Prices are quoted in each listing currency (KRW for 005930.KS, USD for AAPL and NVDA). Volumes represent shares traded.

## Summary Statistics
Minimum, average, and maximum values for every tracked field:

| Ticker | Field | Min | Mean | Max |
| ------ | ----- | ---: | ---: | ---: |
| 005930.KS | Close | 48,968.97 | 66,471.53 | 94,400.00 |
| 005930.KS | High | 50,784.92 | 67,202.08 | 94,500.00 |
| 005930.KS | Low | 48,968.97 | 65,822.65 | 92,700.00 |
| 005930.KS | Open | 49,263.38 | 66,509.00 | 94,000.00 |
| 005930.KS | Volume | 2,957,915.00 | 19,481,204.69 | 57,691,266.00 |
| AAPL | Close | 163.82 | 209.52 | 258.10 |
| AAPL | High | 165.21 | 211.47 | 259.24 |
| AAPL | Low | 162.91 | 207.33 | 256.72 |
| AAPL | Open | 164.17 | 209.29 | 257.99 |
| AAPL | Volume | 23,234,700.00 | 56,558,297.39 | 318,679,900.00 |
| NVDA | Close | 40.30 | 115.60 | 192.57 |
| NVDA | High | 40.85 | 117.54 | 195.62 |
| NVDA | Low | 39.21 | 113.41 | 191.06 |
| NVDA | Open | 40.43 | 115.59 | 193.51 |
| NVDA | Volume | 105,157,000.00 | 325,122,504.81 | 1,142,269,000.00 |

## Daily Return Profile
Simple daily returns were calculated from close prices using the 424-day intersection where all tickers report consecutive observations:

| Ticker | Avg. Daily Return | Daily Volatility |
| ------ | ----------------: | ---------------: |
| 005930.KS | 0.080% | 1.94% |
| AAPL | 0.129% | 1.75% |
| NVDA | 0.375% | 3.11% |

NVDA led the period with a 0.38% mean daily gain but carried roughly 3% day-to-day volatility—nearly twice Apple and over 50% higher than Samsung.

## Cross-Ticker Relationships
Pearson correlations use the same 424 aligned return days:

| Pair | Correlation |
| ---- | ----------: |
| 005930.KS ↔ AAPL | 0.119 |
| 005930.KS ↔ NVDA | 0.096 |
| AAPL ↔ NVDA | 0.404 |

The modest positive links between Samsung and the U.S. listings underscore partial diversification benefits, while the stronger Apple–NVIDIA relationship reflects their shared exposure to the U.S. tech cycle.

## Notable Volume Spikes
- **005930.KS:** 57.7M shares traded on 11 Jan 2024 while closing at ₩70,794.53.
- **AAPL:** 318.7M shares exchanged on 20 Sep 2024, finishing at $227.14.
- **NVDA:** 1.14B shares on 8 Mar 2024 with a $87.49 close.

These events coincide with earnings windows and macro catalysts that temporarily lifted liquidity.

## Efficient Frontier
Mean-variance optimisation was run on the 424-day return window with a zero risk-free rate and long-only weights. The resulting efficient frontier, global minimum-variance (GMV) portfolio, and maximum Sharpe (tangency) mix are plotted below.

![Efficient frontier chart showing GMV and tangency portfolios](efficient_frontier.svg)

Key allocations:

- **GMV portfolio:** 43.2% Samsung, 51.7% Apple, 5.0% NVIDIA targets a 0.12% expected daily return at 1.36% volatility by leaning on Samsung's lower risk and modest correlations.
- **Maximum Sharpe:** 22.2% Samsung, 24.2% Apple, 53.5% NVIDIA lifts the expected return to 0.25% per day with 1.97% volatility, rewarding NVIDIA's outsized momentum despite its higher standalone variance.
- **Frontier behaviour:** The curve begins in a low-volatility regime dominated by Samsung and Apple weights, then bows upward as additional return relies on progressively larger NVIDIA exposure.

## Reproducibility
Install `pandas`, `numpy`, and `matplotlib`, then run the following script to regenerate the tables and SVG:

```bash
pip install pandas numpy matplotlib
python analysis.py
```

The included `analysis.py` script parses the CSV, prints the tables above, and refreshes `efficient_frontier.svg`.
