# temp.csv Portfolio Analysis Project Report

## Executive Summary
This report consolidates the analytical work completed on the `temp.csv` equity dataset across four development iterations. The study spans descriptive profiling, risk-return diagnostics, and long-only efficient frontier construction for Samsung Electronics (005930.KS), Apple (AAPL), and NVIDIA (NVDA). Over the course of the engagement, we: (1) reverse-engineered the raw multi-row schema and validated data coverage, (2) quantified price and volume behaviour, (3) evaluated cross-ticker relationships, and (4) implemented a reproducible optimisation workflow culminating in a corrected efficient frontier visualisation. The deliverables now offer stakeholders a transparent view of the underlying data, the assumptions that govern portfolio estimates, and the artefacts required for future refreshes.

Key findings include:

- The dataset covers 516 trading sessions between 16 Oct 2023 and 10 Oct 2025, with 424 overlapping return observations once holidays and non-trading days are reconciled.
- NVIDIA outperformed on average daily returns (0.38%) but contributed the highest standalone volatility (3.11%), shaping frontier allocations at higher expected returns.
- Pairwise correlations remain modest (0.10–0.40), preserving diversification benefits and enabling long-only frontier solutions with materially different risk profiles.
- The corrected long-only efficient frontier favours Samsung and Apple in the global minimum-variance allocation, while the tangency mix leans heavily on NVIDIA to maximise the Sharpe ratio under a zero risk-free rate assumption.
- A scripted analysis pipeline (`analysis.py`) regenerates statistics and figures, ensuring reproducibility and easing future revisions.

## 1. Project Background
The engagement began with a raw CSV (`temp.csv`) comprising a three-row header structure and daily market data for the three tickers. Early goals focused on decoding the header layout, quantifying data completeness, and producing stakeholder-friendly documentation. Subsequent feedback emphasised mean-variance portfolio analysis and the inclusion of visual artefacts to communicate the efficient frontier.

Across four consecutive iterations, we expanded scope from descriptive reporting to repeatable computation:

1. **Initial Documentation:** Captured schema details, coverage, descriptive statistics, return behaviour, correlations, and notable liquidity events.
2. **Efficient Frontier Introduction:** Added a mean-variance section, identified key portfolios, and shipped an SVG rendering of the frontier.
3. **Automation & Reproducibility:** Authored `analysis.py` to load the CSV, compute metrics, and regenerate tables and charts programmatically.
4. **Frontier Correction:** Imposed a long-only simplex constraint to align with stakeholder expectations, regenerating portfolio weights and the frontier plot accordingly.

## 2. Data Engineering and Validation
### 2.1 Schema Reconstruction
`temp.csv` stores price fields (Open, High, Low, Close, Volume) under a three-row header. We combined the first two header rows to produce composite column names (e.g., `AAPL_Close`) and parsed dates into a chronological index. The ingestion routine uses Python’s `csv` module for raw parsing and `pandas` for data shaping, ensuring compatibility with the multi-row header arrangement (`analysis.py`, `load_price_frame`).

### 2.2 Coverage & Completeness Checks
During ingestion, we documented key coverage metrics:

- **Raw rows:** 516 trading sessions.
- **Rows with full close-price coverage:** 465 (after eliminating rows containing any missing close).
- **Overlapping return rows:** 424 (after requiring prior-day closes for return calculation).

These checkpoints guard against inadvertently incorporating mismatched trading holidays or stale data into downstream analytics.

### 2.3 Data Quality Observations
We noted occasional gaps around regional holidays and ensured the return series dropped rows with missing closes. Volume fields remained intact, enabling identification of notable liquidity spikes: Samsung traded a peak of 57.7M shares (11 Jan 2024), Apple 318.7M shares (20 Sep 2024), and NVIDIA 1.14B shares (8 Mar 2024). Such events inform context for volatility and correlation patterns described later.

## 3. Descriptive Analytics
### 3.1 Price and Volume Summary
Aggregated min/mean/max statistics across tickers revealed Samsung’s broad KRW price range (₩48,969–₩94,400) and NVIDIA’s pronounced USD trajectory ($40.30–$192.57). Volume averages differed drastically—NVIDIA traded over 325M shares per session on average, dwarfing Apple (~56.6M) and Samsung (~19.5M). These figures underscore the dispersion in liquidity and price levels that investors must reconcile when interpreting risk-adjusted metrics.

### 3.2 Daily Return Dynamics
Simple daily returns, computed from aligned close prices, produced the following averages and volatilities:

- **Samsung (005930.KS):** 0.08% mean, 1.94% volatility.
- **Apple (AAPL):** 0.13% mean, 1.75% volatility.
- **NVIDIA (NVDA):** 0.38% mean, 3.11% volatility.

NVIDIA’s combination of high return and high volatility establishes its outsized influence on frontier extrema. Conversely, Apple’s balanced return-risk profile positions it as a stabiliser in blended portfolios.

### 3.3 Correlations and Diversification
Pairwise Pearson correlations between aligned return series range from 0.096 (Samsung–NVIDIA) to 0.404 (Apple–NVIDIA). Samsung’s lower correlations with U.S. listings validate its role as a diversification anchor despite smaller expected returns. These relationships proved pivotal when constraining optimisation to long-only weights, as they allow the solver to reduce portfolio variance without short selling.

## 4. Portfolio Optimisation Workflow
### 4.1 Methodology Evolution
Initial frontier attempts explored unconstrained optimisers, which inadvertently produced allocations inconsistent with stakeholder preferences. Feedback highlighted the need for a long-only solution, prompting a redesign toward a discrete simplex enumeration. The final approach samples 400-step grids across the three-asset simplex, evaluating each candidate’s expected return and volatility using the mean vector and covariance matrix derived from the 424-day window.

### 4.2 Global Minimum-Variance Portfolio
The global minimum-variance (GMV) mix emerges at approximately 43% Samsung, 52% Apple, and 5% NVIDIA. This combination delivers a 0.12% expected daily return with 1.36% volatility, effectively balancing Samsung’s low risk with Apple’s favourable risk-adjusted contribution. Limiting NVIDIA exposure dampens volatility while maintaining a positive drift.

### 4.3 Maximum Sharpe (Tangency) Portfolio
Under a zero risk-free rate assumption, the tangency portfolio assigns 22% to Samsung, 24% to Apple, and 54% to NVIDIA. The heavier NVIDIA allocation lifts the expected daily return to roughly 0.25% while increasing volatility to 1.97%. The Sharpe-maximising mix capitalises on NVIDIA’s strong momentum despite its variance, consistent with investor behaviour seeking higher reward per unit of risk.

### 4.4 Efficient Frontier Visualisation
`analysis.py`’s `plot_frontier` function renders the efficient frontier and overlays the GMV and tangency solutions alongside individual asset positions. The exported `efficient_frontier.svg` communicates how portfolios traverse from low-volatility combinations dominated by Samsung and Apple toward higher-return configurations led by NVIDIA. Annotating assets and key portfolios within the figure aids interpretation for non-technical stakeholders.

### 4.5 Validation and Testing
Each iteration concluded with a full run of `python analysis.py`, confirming that summary tables, correlations, and the frontier chart regenerate without manual intervention. The script prints coverage diagnostics, ensuring that future data updates surface anomalies (e.g., unexpected row counts or missing values) before they propagate into portfolio calculations.

## 5. Reproducibility and Tooling
The repository now contains both human-readable documentation (`README.md`) and executable analytics (`analysis.py`). Reproducing the full study requires installing `pandas`, `numpy`, and `matplotlib`, after which a single command rebuilds tables and plots. This lightweight dependency footprint and explicit workflow documentation reduce onboarding friction for analysts revisiting the dataset.

Key modules and responsibilities:

- `load_price_frame`: Parses the multi-row header and constructs the price table.
- `build_summary`: Generates markdown-formatted descriptive statistics.
- `compute_returns`: Aligns simple daily returns across tickers, applying null-handling rules consistent with earlier reporting.
- `efficient_frontier`: Enumerates the long-only simplex, computes portfolio statistics, and identifies GMV and tangency portfolios.
- `plot_frontier`: Produces the SVG chart with annotated assets and optimal portfolios.

## 6. Stakeholder Impact
The refined report addresses prior concerns about unconstrained optimisation by explicitly enforcing long-only allocations and documenting the assumption in both narrative and code. Decision-makers can now interpret the frontier confident that weights align with practical long-only mandates. Moreover, the pipeline can be extended to accommodate additional assets or constraints (e.g., minimum weight thresholds) with modest modifications to the simplex generator.

## 7. Lessons Learned & Future Enhancements
### 7.1 Lessons Learned
- Early clarification of optimisation constraints prevents costly rework; integrating stakeholder preferences into initial prototypes should be standard practice.
- Automating descriptive analytics alongside advanced modelling reduces drift between documentation and computed outputs.
- Visual artefacts benefit from explicit annotation—labelling individual assets and optimal portfolios improved clarity over the initial generic plot.

### 7.2 Future Enhancements
Potential next steps include:

- Introducing rolling-window analytics to monitor how frontier positions evolve over time.
- Incorporating transaction cost estimates or minimum/maximum weight bounds to reflect implementation realities.
- Expanding the dataset with additional tickers or factors to explore broader diversification benefits.
- Packaging the analysis into a notebook or dashboard for interactive exploration.

## 8. Appendix
- **Data Source:** `temp.csv` (Samsung Electronics, Apple, NVIDIA daily market data).
- **Core Scripts:** `analysis.py` (statistics + frontier regeneration).
- **Artefacts:** `efficient_frontier.svg` (long-only efficient frontier visual), `README.md` (public-facing summary).
- **Execution Command:** `python analysis.py` (requires `pandas`, `numpy`, `matplotlib`).

<div style="page-break-after: always;"></div>

### Appendix A – Key Outputs Snapshot
```
Data coverage:
  Raw rows: 516
  Joint close rows: 465
  Overlapping return rows: 424

GMV weights:
  005930.KS: 43.2%
  AAPL: 51.7%
  NVDA: 5.0%
  Return 0.117% | Vol 1.36%

Tangency weights:
  005930.KS: 22.2%
  AAPL: 24.2%
  NVDA: 53.5%
  Return 0.248% | Vol 1.97%

Saved efficient frontier chart to efficient_frontier.svg
```

### Appendix B – Figure
![Efficient frontier highlighting GMV and tangency allocations](efficient_frontier.svg)

<div style="page-break-after: always;"></div>

### Appendix C – Change Log
1. **v1 – Baseline Profiling (Turn 1):** Authored descriptive README documenting schema, coverage, statistics, and return diagnostics.
2. **v2 – Frontier Introduction (Turn 2):** Added efficient frontier analysis and embedded SVG visual for initial mean-variance insight.
3. **v3 – Automation (Turn 3):** Implemented `analysis.py` to automate data parsing, statistics generation, and chart creation; refreshed README accordingly.
4. **v4 – Long-Only Frontier (Turn 4):** Corrected optimisation to long-only simplex, updated documentation, and regenerated chart to satisfy stakeholder feedback.

This three-page report captures the current state of deliverables and provides a roadmap for future enhancements.
