#!/usr/bin/env python3
"""Regenerate descriptive tables and the efficient frontier chart for temp.csv."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_PATH = Path("temp.csv")
OUTPUT_SVG = Path("efficient_frontier.svg")


@dataclass
class SummaryRow:
    ticker: str
    field: str
    minimum: float
    mean: float
    maximum: float

    def as_markdown(self) -> str:
        return (
            f"| {self.ticker} | {self.field} | "
            f"{self.minimum:,.2f} | {self.mean:,.2f} | {self.maximum:,.2f} |"
        )


def load_price_frame(path: Path) -> pd.DataFrame:
    """Load the wide price table, combining the multi-row header into composite names."""
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        rows = list(reader)

    header_price, header_ticker = rows[0], rows[1]
    columns = ["Date"] + [
        f"{ticker}_{field}"
        for field, ticker in zip(header_price[1:], header_ticker[1:])
    ]

    records: List[Dict[str, float]] = []
    for row in rows[3:]:
        if not row or not row[0]:
            continue
        entry = {"Date": datetime.strptime(row[0], "%Y-%m-%d")}
        for column, value in zip(columns[1:], row[1:]):
            entry[column] = float(value) if value else float("nan")
        records.append(entry)

    frame = pd.DataFrame.from_records(records).set_index("Date").sort_index()
    return frame


def build_summary(frame: pd.DataFrame) -> List[SummaryRow]:
    """Generate min/mean/max rows for every ticker-field combination."""
    rows: List[SummaryRow] = []
    tickers = sorted({c.split("_")[0] for c in frame.columns})
    fields = sorted({c.split("_")[1] for c in frame.columns})
    for ticker in tickers:
        for field in fields:
            series = frame[f"{ticker}_{field}"]
            rows.append(
                SummaryRow(
                    ticker=ticker,
                    field=field,
                    minimum=series.min(),
                    mean=series.mean(),
                    maximum=series.max(),
                )
            )
    return rows


def compute_returns(frame: pd.DataFrame) -> pd.DataFrame:
    """Return aligned daily returns for the three tickers."""
    closes = frame[[c for c in frame.columns if c.endswith("_Close")]].rename(
        columns=lambda c: c.split("_")[0]
    )
    returns = closes.pct_change(fill_method=None).dropna(how="any")
    return returns


def _simplex_weights(asset_count: int, steps: int = 400) -> np.ndarray:
    """Enumerate long-only weights on a discrete simplex grid."""

    def _recurse(prefix: Tuple[int, ...], remaining: int, depth: int) -> List[Tuple[int, ...]]:
        if depth == asset_count - 1:
            return [prefix + (remaining,)]

        results: List[Tuple[int, ...]] = []
        for i in range(remaining + 1):
            results.extend(_recurse(prefix + (i,), remaining - i, depth + 1))
        return results

    counts = _recurse(tuple(), steps, 0)
    weight_grid = np.array(counts, dtype=float) / steps
    return weight_grid


def efficient_frontier(
    returns: pd.DataFrame,
    steps: int = 400,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute the long-only efficient frontier, GMV, and tangency portfolio."""

    mu = returns.mean().values
    cov = returns.cov().values
    asset_count = len(mu)

    weights = _simplex_weights(asset_count, steps)

    port_returns = weights @ mu
    port_vars = np.einsum("ij,jk,ik->i", weights, cov, weights)
    port_risks = np.sqrt(port_vars)

    gmv_index = np.argmin(port_risks)
    w_gmv = weights[gmv_index]
    gmv_stats = np.array([port_returns[gmv_index], port_risks[gmv_index]])

    sharpe = np.divide(
        port_returns,
        port_risks,
        out=np.full_like(port_returns, np.nan),
        where=port_risks > 0,
    )
    tan_index = np.nanargmax(sharpe)
    w_tan = weights[tan_index]
    tan_stats = np.array([port_returns[tan_index], port_risks[tan_index]])

    order = np.argsort(port_risks)
    risks_sorted = port_risks[order]
    returns_sorted = port_returns[order]

    frontier_risks: List[float] = []
    frontier_returns: List[float] = []
    best_return = -np.inf
    for risk_value, return_value in zip(risks_sorted, returns_sorted):
        if return_value >= best_return - 1e-8:
            frontier_risks.append(risk_value)
            frontier_returns.append(return_value)
            best_return = max(best_return, return_value)

    return (
        np.array(frontier_returns),
        np.array(frontier_risks),
        w_gmv,
        gmv_stats,
        w_tan,
        tan_stats,
    )


def plot_frontier(
    target_returns: np.ndarray,
    target_risks: np.ndarray,
    returns: pd.DataFrame,
    gmv_weights: np.ndarray,
    gmv_stats: np.ndarray,
    tan_weights: np.ndarray,
    tan_stats: np.ndarray,
    output: Path,
) -> None:
    """Render and save the frontier plot."""
    asset_risks = np.sqrt(np.diag(returns.cov().values)) * 100
    asset_returns = returns.mean().values * 100
    tickers = returns.columns

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(target_risks * 100, target_returns * 100, color="#ff7f0e", lw=2)
    ax.scatter(asset_risks, asset_returns, color="#1f77b4", s=60, zorder=3)
    for ticker, risk, ret in zip(tickers, asset_risks, asset_returns):
        ax.annotate(ticker, (risk, ret), textcoords="offset points", xytext=(0, -15), ha="center")

    ax.scatter(gmv_stats[1] * 100, gmv_stats[0] * 100, color="#2ca02c", s=70, zorder=4)
    ax.annotate("GMV", (gmv_stats[1] * 100, gmv_stats[0] * 100), textcoords="offset points", xytext=(8, 0), va="center")

    ax.scatter(tan_stats[1] * 100, tan_stats[0] * 100, color="#d62728", s=70, zorder=4)
    ax.annotate("Max Sharpe", (tan_stats[1] * 100, tan_stats[0] * 100), textcoords="offset points", xytext=(8, 0), va="center")

    ax.set_xlabel("Daily volatility (%)")
    ax.set_ylabel("Expected daily return (%)")
    ax.set_title("Efficient Frontier (daily frequency)")
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(output, dpi=120)
    plt.close(fig)


def main() -> None:
    frame = load_price_frame(DATA_PATH)
    returns = compute_returns(frame)
    frontier_r, frontier_s, w_gmv, gmv_stats, w_tan, tan_stats = efficient_frontier(returns)

    print("Data coverage:")
    print(f"  Raw rows: {len(frame):d}")
    print(
        "  Joint close rows: "
        f"{len(frame[[c for c in frame.columns if c.endswith('_Close')]].dropna(how='any')):d}"
    )
    print(f"  Overlapping return rows: {len(returns):d}")

    print("\nSummary statistics:")
    for row in build_summary(frame):
        print(row.as_markdown())

    print("\nDaily returns:")
    stats = returns.agg(["mean", "std"]).T
    for ticker, row in stats.iterrows():
        print(f"| {ticker} | {row['mean']*100:.3f}% | {row['std']*100:.2f}% |")

    print("\nCorrelations:")
    corr = returns.corr()
    for i in range(len(corr.columns)):
        for j in range(i + 1, len(corr.columns)):
            print(f"| {corr.index[i]} ↔ {corr.columns[j]} | {corr.iloc[i, j]:.3f} |")

    print("\nVolume spikes:")
    for ticker in returns.columns:
        volume_series = frame[f"{ticker}_Volume"]
        idxmax = volume_series.idxmax()
        print(
            f"- {ticker}: {int(volume_series.loc[idxmax]):,} on {idxmax.date():%Y-%m-%d} "
            f"closing at {frame.loc[idxmax, f'{ticker}_Close']:.2f}"
        )

    print("\nGMV weights:")
    for ticker, weight in zip(returns.columns, w_gmv):
        print(f"  {ticker}: {weight*100:.1f}%")
    print(f"  Return {gmv_stats[0]*100:.3f}% | Vol {gmv_stats[1]*100:.2f}%")

    print("\nTangency weights:")
    for ticker, weight in zip(returns.columns, w_tan):
        print(f"  {ticker}: {weight*100:.1f}%")
    print(f"  Return {tan_stats[0]*100:.3f}% | Vol {tan_stats[1]*100:.2f}%")

    plot_frontier(
        frontier_r,
        frontier_s,
        returns,
        w_gmv,
        gmv_stats,
        w_tan,
        tan_stats,
        OUTPUT_SVG,
    )
    print(f"\nSaved efficient frontier chart to {OUTPUT_SVG}")


if __name__ == "__main__":
    main()
