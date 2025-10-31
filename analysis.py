#!/usr/bin/env python3
"""`temp.csv` 분석 결과표와 효율적 투자선 차트를 재생성합니다."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams["font.family"] = "NanumGothic"
plt.rcParams["axes.unicode_minus"] = False

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
    """다중 헤더를 결합해 넓은 형태의 가격 테이블을 생성합니다."""
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
    """각 티커-필드 조합에 대한 최소·평균·최대값을 생성합니다."""
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
    """세 종목의 일별 수익률을 정렬해 반환합니다."""
    closes = frame[[c for c in frame.columns if c.endswith("_Close")]].rename(
        columns=lambda c: c.split("_")[0]
    )
    returns = closes.pct_change(fill_method=None).dropna(how="any")
    return returns


def _simplex_weights(asset_count: int, steps: int = 400) -> np.ndarray:
    """롱온리 단순체 격자에서 가능한 가중치를 모두 생성합니다."""

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
    """롱온리 효율적 투자선, GMV, 최대 샤프 포트폴리오를 계산합니다."""

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
    """투자선 그래프를 렌더링해 저장합니다."""
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
    ax.annotate("최대 샤프", (tan_stats[1] * 100, tan_stats[0] * 100), textcoords="offset points", xytext=(8, 0), va="center")

    ax.set_xlabel("일별 변동성 (%)")
    ax.set_ylabel("기대 일별 수익률 (%)")
    ax.set_title("효율적 투자선 (일별 기준)")
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(output, dpi=120)
    plt.close(fig)


def main() -> None:
    frame = load_price_frame(DATA_PATH)
    returns = compute_returns(frame)
    frontier_r, frontier_s, w_gmv, gmv_stats, w_tan, tan_stats = efficient_frontier(returns)

    print("데이터 커버리지:")
    print(f"  원본 행 수: {len(frame):d}")
    print(
        "  종가 결측 제거 후 행 수: "
        f"{len(frame[[c for c in frame.columns if c.endswith('_Close')]].dropna(how='any')):d}"
    )
    print(f"  공통 수익률 행 수: {len(returns):d}")

    print("\n요약 통계:")
    for row in build_summary(frame):
        print(row.as_markdown())

    print("\n일별 수익률:")
    stats = returns.agg(["mean", "std"]).T
    for ticker, row in stats.iterrows():
        print(f"| {ticker} | {row['mean']*100:.3f}% | {row['std']*100:.2f}% |")

    print("\n상관계수:")
    corr = returns.corr()
    for i in range(len(corr.columns)):
        for j in range(i + 1, len(corr.columns)):
            print(f"| {corr.index[i]} ↔ {corr.columns[j]} | {corr.iloc[i, j]:.3f} |")

    print("\n거래량 급증:")
    for ticker in returns.columns:
        volume_series = frame[f"{ticker}_Volume"]
        idxmax = volume_series.idxmax()
        print(
            f"- {ticker}: {idxmax.date():%Y-%m-%d}에 {int(volume_series.loc[idxmax]):,}주 거래, "
            f"종가 {frame.loc[idxmax, f'{ticker}_Close']:.2f}"
        )

    print("\nGMV 가중치:")
    for ticker, weight in zip(returns.columns, w_gmv):
        print(f"  {ticker}: {weight*100:.1f}%")
    print(f"  기대수익 {gmv_stats[0]*100:.3f}% | 변동성 {gmv_stats[1]*100:.2f}%")

    print("\n최대 샤프 가중치:")
    for ticker, weight in zip(returns.columns, w_tan):
        print(f"  {ticker}: {weight*100:.1f}%")
    print(f"  기대수익 {tan_stats[0]*100:.3f}% | 변동성 {tan_stats[1]*100:.2f}%")

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
    print(f"\n효율적 투자선 차트를 {OUTPUT_SVG} 파일로 저장했습니다")


if __name__ == "__main__":
    main()
