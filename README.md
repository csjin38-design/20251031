# Stock Price Dataset Analysis

This repository contains a cleaned analysis of `temp.csv`, a multi-ticker price history that tracks Samsung Electronics (005930.KS), Apple (AAPL), and NVIDIA (NVDA) across daily open, high, low, close, and volume fields.

## Data Overview
- **Coverage:** 516 trading days from 16 Oct 2023 through 10 Oct 2025.
- **Schema:** The raw file stores a three-row header—price field, ticker, and an empty spacer row—followed by daily observations. Columns expand to `Close`, `High`, `Low`, `Open`, and `Volume` for each ticker after the date column.
- **Units:** Prices are quoted in each security’s native listing currency (KRW for 005930.KS, USD for AAPL and NVDA); volume represents the number of shares traded.

## Summary Statistics
Daily observations were parsed with Python’s standard library (`csv`) to avoid external dependencies. The table below reports minima, means, and maxima for each price/volume field by ticker.

| Ticker | Field  | Min | Mean | Max |
| ------ | ------ | ---: | ---: | ---: |
| 005930.KS | Close | 48,968.97 | 66,471.53 | 94,400.00 |
| 005930.KS | High | 50,784.92 | 67,202.08 | 94,500.00 |
| 005930.KS | Low | 48,968.97 | 65,822.65 | 92,700.00 |
| 005930.KS | Open | 49,263.38 | 66,509.00 | 94,000.00 |
| 005930.KS | Volume | 2,957,915 | 19,481,204.69 | 57,691,266 |
| AAPL | Close | 163.82 | 209.52 | 258.10 |
| AAPL | High | 165.21 | 211.47 | 259.24 |
| AAPL | Low | 162.91 | 207.33 | 256.72 |
| AAPL | Open | 164.17 | 209.29 | 257.99 |
| AAPL | Volume | 23,234,700 | 56,558,297.39 | 318,679,900 |
| NVDA | Close | 40.30 | 115.60 | 192.57 |
| NVDA | High | 40.85 | 117.54 | 195.62 |
| NVDA | Low | 39.21 | 113.41 | 191.06 |
| NVDA | Open | 40.43 | 115.59 | 193.51 |
| NVDA | Volume | 105,157,000 | 325,122,504.81 | 1,142,269,000 |

## Daily Return Profile
Average log-free (simple) daily returns and sample standard deviation (volatility) derived from close prices:

| Ticker | Avg. Daily Return | Daily Volatility |
| ------ | ----------------: | ---------------: |
| 005930.KS | 0.097% | 1.93% |
| AAPL | 0.081% | 1.77% |
| NVDA | 0.329% | 3.21% |

NVDA delivered the strongest average momentum but with materially higher day-to-day variability.

## Cross-Ticker Relationships
Pearson correlations of close-price series highlight diverging behavior between Samsung and the U.S.-listed names, and a strong positive co-movement between Apple and NVIDIA:

| Pair | Correlation |
| ---- | ----------: |
| 005930.KS ↔ AAPL | -0.417 |
| 005930.KS ↔ NVDA | -0.202 |
| AAPL ↔ NVDA | 0.733 |

## Notable Volume Spikes
- **005930.KS:** 57.7M shares traded on 11 Jan 2024 while closing at ₩70,794.53.
- **AAPL:** 318.7M shares on 20 Sep 2024, closing at $227.14.
- **NVDA:** 1.14B shares on 8 Mar 2024, closing at $87.49.

These spikes may align with earnings releases or macro catalysts and warrant deeper investigation if unusual liquidity matters.

## Reproducibility Notes
Because the header repeats field names per ticker, parsing can be accomplished with Python’s `csv` module by stitching the first two header rows (field + ticker) into composite column names before iterating over the records. This avoids reliance on external libraries that may be unavailable in constrained environments.
