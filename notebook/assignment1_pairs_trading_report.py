# %% [markdown]
# # Assignment 1: Cointegration & Pairs Trading
#
# This notebook analyzes two selected pairs:
#
# - Stock pair: `MU / WDC`
# - ETF pair: `EWA / EWC`
#
# The workflow uses a two-stage design:
#
# - Formation period: 2021-01-01 to 2023-12-31
# - Trading period: 2024-01-01 to latest available Yahoo Finance data
#
# The formation period is used for correlation, cointegration testing, and hedge
# ratio estimation. The trading period is used for out-of-sample backtesting.

# %% [markdown]
# ## 1. Install Dependencies
#
# Run this setup cell before the analysis. If the packages are already installed,
# Python will simply report that the requirements are satisfied.

# %%
# !pip install yfinance statsmodels seaborn -q

# %% [markdown]
# ## 2. Imports and Configuration

# %%
import warnings
import sys

warnings.filterwarnings("ignore")

import matplotlib
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
import yfinance as yf
from statsmodels.tsa.stattools import coint

if "google.colab" not in sys.modules:
    matplotlib.use("Agg")

import matplotlib.pyplot as plt

try:
    from IPython.display import display
except ImportError:
    def display(obj):
        print(obj)

sns.set_theme(style="whitegrid")

PAIRS = {
    "Stock Pair: MU/WDC": ("MU", "WDC"),
    "ETF Pair: EWA/EWC": ("EWA", "EWC"),
}

START_DATE = "2021-01-01"
FORMATION_END = "2023-12-31"
TRADING_START = "2024-01-01"
END_DATE = None  # None means yfinance will use the latest available data.

ROLLING_WINDOW = 60
ENTRY_Z = 2.0
EXIT_Z = 0.5
TRADING_DAYS = 252

# %% [markdown]
# ## 3. Helper Functions

# %%
def download_adjusted_close(symbols, start_date=START_DATE, end_date=END_DATE):
    """Download daily adjusted close prices from Yahoo Finance."""
    raw = yf.download(
        symbols,
        start=start_date,
        end=end_date,
        auto_adjust=True,
        progress=False,
        timeout=30,
    )

    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"].copy()
    else:
        prices = raw[["Close"]].copy()
        prices.columns = symbols

    prices = prices.dropna(how="all").sort_index()
    prices = prices.dropna(axis=1, how="all")
    return prices


def estimate_ols_spread(y, x):
    """Estimate y = alpha + beta * x + residual."""
    aligned = pd.concat([y, x], axis=1).dropna()
    aligned.columns = ["y", "x"]

    model = sm.OLS(aligned["y"], sm.add_constant(aligned["x"])).fit()
    alpha = float(model.params["const"])
    beta = float(model.params["x"])
    spread = aligned["y"] - alpha - beta * aligned["x"]
    return alpha, beta, spread, model


def compute_rolling_zscore(spread, window=ROLLING_WINDOW):
    """Compute rolling z-score of a spread."""
    rolling_mean = spread.rolling(window).mean()
    rolling_std = spread.rolling(window).std()
    return (spread - rolling_mean) / rolling_std


def generate_positions(zscore, entry_z=ENTRY_Z, exit_z=EXIT_Z):
    """
    Generate spread positions from z-score signals.

    Position convention:
      +1 = long spread: long first asset, short beta-adjusted second asset.
      -1 = short spread: short first asset, long beta-adjusted second asset.
       0 = flat.
    """
    position = pd.Series(0.0, index=zscore.index)
    current_position = 0.0

    for date, z_value in zscore.items():
        if np.isnan(z_value):
            position.loc[date] = current_position
            continue

        if current_position == 0.0:
            if z_value > entry_z:
                current_position = -1.0
            elif z_value < -entry_z:
                current_position = 1.0
        elif abs(z_value) < exit_z:
            current_position = 0.0

        position.loc[date] = current_position

    return position


def max_drawdown(cumulative_returns):
    """Calculate maximum drawdown from cumulative return index."""
    running_max = cumulative_returns.cummax()
    drawdown = cumulative_returns / running_max - 1.0
    return float(drawdown.min()), drawdown


def backtest_pair(prices, first_asset, second_asset, alpha, beta):
    """Backtest the z-score spread strategy on the trading period."""
    trading_prices = prices.loc[TRADING_START:, [first_asset, second_asset]].dropna()
    if trading_prices.empty:
        raise ValueError(f"No trading-period data for {first_asset}/{second_asset}.")

    spread = trading_prices[first_asset] - alpha - beta * trading_prices[second_asset]
    zscore = compute_rolling_zscore(spread)
    raw_position = generate_positions(zscore)

    returns = trading_prices.pct_change()
    spread_return = returns[first_asset] - beta * returns[second_asset]

    # Shift positions by one day so today's signal affects tomorrow's return.
    executed_position = raw_position.shift(1).fillna(0.0)
    strategy_return = (executed_position * spread_return).fillna(0.0)
    cumulative_return = (1.0 + strategy_return).cumprod()

    total_return = float(cumulative_return.iloc[-1] - 1.0)
    volatility = strategy_return.std()
    sharpe = np.nan
    if volatility and not np.isnan(volatility):
        sharpe = float(np.sqrt(TRADING_DAYS) * strategy_return.mean() / volatility)

    mdd, drawdown = max_drawdown(cumulative_return)

    return {
        "trading_prices": trading_prices,
        "spread": spread,
        "zscore": zscore,
        "raw_position": raw_position,
        "executed_position": executed_position,
        "spread_return": spread_return,
        "strategy_return": strategy_return,
        "cumulative_return": cumulative_return,
        "drawdown": drawdown,
        "total_return": total_return,
        "sharpe": sharpe,
        "max_drawdown": mdd,
    }


def analyze_pair(prices, label, first_asset, second_asset):
    """Run formation-period analysis and trading-period backtest for one pair."""
    pair_prices = prices[[first_asset, second_asset]].dropna()
    formation_prices = pair_prices.loc[:FORMATION_END].dropna()

    if formation_prices.empty:
        raise ValueError(f"No formation-period data for {first_asset}/{second_asset}.")

    correlation = float(formation_prices[first_asset].corr(formation_prices[second_asset]))
    coint_stat, p_value, _ = coint(
        formation_prices[first_asset],
        formation_prices[second_asset],
    )
    alpha, beta, formation_spread, ols_model = estimate_ols_spread(
        formation_prices[first_asset],
        formation_prices[second_asset],
    )
    backtest = backtest_pair(prices, first_asset, second_asset, alpha, beta)

    summary = {
        "pair_label": label,
        "first_asset": first_asset,
        "second_asset": second_asset,
        "formation_start": str(formation_prices.index.min().date()),
        "formation_end": str(formation_prices.index.max().date()),
        "trading_start": str(backtest["trading_prices"].index.min().date()),
        "trading_end": str(backtest["trading_prices"].index.max().date()),
        "formation_observations": int(len(formation_prices)),
        "trading_observations": int(len(backtest["trading_prices"])),
        "correlation": correlation,
        "coint_stat": float(coint_stat),
        "p_value": float(p_value),
        "alpha": alpha,
        "beta": beta,
        "total_return": backtest["total_return"],
        "sharpe": backtest["sharpe"],
        "max_drawdown": backtest["max_drawdown"],
    }

    return summary, formation_prices, formation_spread, backtest


def plot_pair_results(label, first_asset, second_asset, formation_prices, formation_spread, backtest):
    """Create the main plots required for the assignment."""
    fig, axes = plt.subplots(4, 1, figsize=(12, 16), sharex=False)

    formation_prices.plot(ax=axes[0])
    axes[0].set_title(f"{label}: Formation-Period Adjusted Close Prices")
    axes[0].set_ylabel("Adjusted Close")

    formation_spread.plot(ax=axes[1], color="tab:blue")
    axes[1].axhline(formation_spread.mean(), color="black", linestyle="--", linewidth=1)
    axes[1].set_title(f"{label}: Formation-Period OLS Spread")
    axes[1].set_ylabel("Spread")

    backtest["zscore"].plot(ax=axes[2], color="tab:purple")
    axes[2].axhline(ENTRY_Z, color="red", linestyle="--", linewidth=1)
    axes[2].axhline(-ENTRY_Z, color="green", linestyle="--", linewidth=1)
    axes[2].axhline(EXIT_Z, color="gray", linestyle=":", linewidth=1)
    axes[2].axhline(-EXIT_Z, color="gray", linestyle=":", linewidth=1)
    axes[2].set_title(f"{label}: Trading-Period Rolling Z-Score")
    axes[2].set_ylabel("Z-Score")

    backtest["cumulative_return"].plot(ax=axes[3], color="tab:orange")
    axes[3].set_title(f"{label}: Strategy Cumulative Return")
    axes[3].set_ylabel("Growth of $1")
    axes[3].set_xlabel("Date")

    plt.tight_layout()
    plt.show()

    fig, ax = plt.subplots(figsize=(12, 3))
    backtest["executed_position"].plot(ax=ax, drawstyle="steps-post", color="tab:brown")
    ax.set_title(f"{label}: Executed Spread Position")
    ax.set_ylabel("Position")
    ax.set_yticks([-1, 0, 1])
    ax.set_yticklabels(["Short spread", "Flat", "Long spread"])
    plt.tight_layout()
    plt.show()


def format_percentage(value):
    return f"{100 * value:.2f}%"


def print_report_text(summary):
    """Print concise report-ready interpretation text."""
    first_asset = summary["first_asset"]
    second_asset = summary["second_asset"]
    label = summary["pair_label"]

    print(f"\nReport-ready notes for {label}")
    print("-" * 80)
    print(
        f"Economic motivation: {first_asset} and {second_asset} are exposed to related "
        "economic drivers, so a stable long-run relationship is plausible but still "
        "must be tested empirically."
    )
    print(
        f"Cointegration result: During the formation period, the price correlation was "
        f"{summary['correlation']:.3f}. The Engle-Granger test statistic was "
        f"{summary['coint_stat']:.3f} with p-value {summary['p_value']:.4f}. "
        "A lower p-value provides stronger evidence against the null hypothesis of no cointegration."
    )
    if summary["p_value"] >= 0.10:
        print(
            "Interpretation caution: Because this p-value is above the conventional 10% "
            "threshold, the split-sample evidence for cointegration is weak. Any positive "
            "backtest result should therefore be interpreted as exploratory rather than "
            "strong confirmation of a stable equilibrium relationship."
        )
    print(
        f"Strategy behavior: The spread was defined as {first_asset} - alpha - "
        f"beta * {second_asset}, with alpha={summary['alpha']:.4f} and "
        f"beta={summary['beta']:.4f}. The strategy enters when the trading-period "
        "rolling z-score exceeds +/-2 and exits when the absolute z-score falls below 0.5."
    )
    print(
        f"Backtest interpretation: From {summary['trading_start']} to "
        f"{summary['trading_end']}, the strategy generated total return "
        f"{format_percentage(summary['total_return'])}, Sharpe ratio "
        f"{summary['sharpe']:.2f}, and maximum drawdown "
        f"{format_percentage(summary['max_drawdown'])}."
    )
    print(
        "Limitations: The baseline ignores transaction costs, slippage, borrowing costs, "
        "and short-sale constraints. Cointegration relationships may also break during "
        "regime shifts or firm-specific events."
    )

# %% [markdown]
# ## 4. Download Data

# %%
symbols = sorted({ticker for pair in PAIRS.values() for ticker in pair})
prices = download_adjusted_close(symbols)

print(f"Downloaded {len(prices)} daily observations.")
print(f"Date range: {prices.index.min().date()} to {prices.index.max().date()}")
print("Tickers:", ", ".join(prices.columns))

display(prices.tail())

# %% [markdown]
# ## 5. Run Pair Analysis

# %%
all_summaries = []
all_results = {}

for pair_label, (first_asset, second_asset) in PAIRS.items():
    summary, formation_prices, formation_spread, backtest = analyze_pair(
        prices,
        pair_label,
        first_asset,
        second_asset,
    )

    all_summaries.append(summary)
    all_results[pair_label] = {
        "summary": summary,
        "formation_prices": formation_prices,
        "formation_spread": formation_spread,
        "backtest": backtest,
    }

    print("\n" + "=" * 80)
    print(pair_label)
    print("=" * 80)
    print(f"Formation period: {summary['formation_start']} to {summary['formation_end']}")
    print(f"Trading period:   {summary['trading_start']} to {summary['trading_end']}")
    print(f"Correlation:      {summary['correlation']:.4f}")
    print(f"Coint statistic:  {summary['coint_stat']:.4f}")
    print(f"Coint p-value:    {summary['p_value']:.4f}")
    print(f"OLS alpha:        {summary['alpha']:.4f}")
    print(f"OLS beta:         {summary['beta']:.4f}")
    print(f"Total return:     {format_percentage(summary['total_return'])}")
    print(f"Sharpe ratio:     {summary['sharpe']:.4f}")
    print(f"Max drawdown:     {format_percentage(summary['max_drawdown'])}")
    if summary["p_value"] >= 0.10:
        print(
            "Interpretation note: the formation-period p-value is above 0.10, "
            "so this strict split-sample test does not reject the null of no cointegration."
        )

    plot_pair_results(
        pair_label,
        first_asset,
        second_asset,
        formation_prices,
        formation_spread,
        backtest,
    )

# %% [markdown]
# ## 6. Final Summary Table

# %%
summary_table = pd.DataFrame(all_summaries)

display_columns = [
    "pair_label",
    "first_asset",
    "second_asset",
    "formation_start",
    "formation_end",
    "trading_start",
    "trading_end",
    "correlation",
    "coint_stat",
    "p_value",
    "alpha",
    "beta",
    "total_return",
    "sharpe",
    "max_drawdown",
]

summary_display = summary_table[display_columns].copy()
summary_display["correlation"] = summary_display["correlation"].round(4)
summary_display["coint_stat"] = summary_display["coint_stat"].round(4)
summary_display["p_value"] = summary_display["p_value"].round(4)
summary_display["alpha"] = summary_display["alpha"].round(4)
summary_display["beta"] = summary_display["beta"].round(4)
summary_display["total_return"] = summary_display["total_return"].map(format_percentage)
summary_display["sharpe"] = summary_display["sharpe"].round(4)
summary_display["max_drawdown"] = summary_display["max_drawdown"].map(format_percentage)

display(summary_display)

# %% [markdown]
# ## 7. Report-Ready Interpretation Notes

# %%
for summary in all_summaries:
    print_report_text(summary)

# %% [markdown]
# ## 8. Optional: Export Summary Table
#
# Uncomment the next line if you want to export the results table as CSV.

# %%
# summary_display.to_csv("pairs_trading_summary.csv", index=False)
