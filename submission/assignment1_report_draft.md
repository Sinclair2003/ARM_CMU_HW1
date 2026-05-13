# Assignment 1: Cointegration & Pairs Trading

## Team Information

Names and Andrew IDs: [Fill in team member names and Andrew IDs]

## 1. Overview

This report applies a two-stage cointegration and pairs trading workflow to two selected pairs:

| Category | Pair | Instruments |
|---|---|---|
| Stock pair | MU / WDC | Micron Technology and Western Digital |
| ETF pair | EWA / EWC | iShares MSCI Australia ETF and iShares MSCI Canada ETF |

Daily adjusted close prices were downloaded from Yahoo Finance using the `yfinance` Python package. To reduce look-ahead bias, the analysis separates the sample into a formation period and a trading period:

| Period | Dates | Purpose |
|---|---|---|
| Formation period | 2021-01-04 to 2023-12-29 | Correlation, cointegration testing, hedge-ratio estimation |
| Trading period | 2024-01-02 to 2026-05-12 | Out-of-sample strategy backtest |

The spread is constructed as:

```text
spread = first asset - alpha - beta * second asset
```

The hedge ratio `beta` and intercept `alpha` are estimated by OLS during the formation period and then fixed during the trading period.

## 2. Pair 1: MU / WDC

### Economic Motivation

Micron Technology (`MU`) and Western Digital (`WDC`) are both exposed to the memory and data storage cycle. Micron is strongly linked to DRAM and NAND memory, while Western Digital is exposed to NAND flash and storage devices. Both firms are affected by semiconductor demand, cloud and data-center investment, inventory cycles, and pricing pressure in memory/storage markets. This makes a long-run relationship plausible, although it must be verified empirically.

### Preliminary Screening

During the formation period, the price-level correlation between `MU` and `WDC` was:

```text
Correlation = 0.7997
```

This indicates meaningful co-movement, but correlation alone is not sufficient because two non-stationary assets can appear correlated without having a stable mean-reverting spread.

### Cointegration Results

The Engle-Granger cointegration test was applied to the formation-period prices.

| Metric | Result |
|---|---:|
| Test statistic | -2.1042 |
| p-value | 0.4742 |
| OLS alpha | 31.9935 |
| OLS beta | 0.9943 |

The null hypothesis is no cointegration. Since the p-value is above conventional 10%, 5%, and 1% levels, we do not reject the null hypothesis during the formation period. Therefore, the strict split-sample evidence for cointegration is weak.

### Strategy Design

The trading strategy uses the fixed formation-period spread:

```text
spread_t = MU_t - 31.9935 - 0.9943 * WDC_t
```

A 60-day rolling z-score is computed on the trading-period spread.

Trading rules:

| Signal | Action |
|---|---|
| z-score > 2.0 | Short spread: short MU, long beta-adjusted WDC |
| z-score < -2.0 | Long spread: long MU, short beta-adjusted WDC |
| abs(z-score) < 0.5 | Close position |

Positions are shifted by one day before calculating returns to avoid look-ahead bias.

### Backtesting Results

| Metric | Result |
|---|---:|
| Trading period | 2024-01-02 to 2026-05-12 |
| Total return | 39.98% |
| Annualized Sharpe ratio | 0.6299 |
| Maximum drawdown | -20.04% |

The strategy generated a positive total return, but the Sharpe ratio is moderate and the drawdown is material. Because the formation-period cointegration test did not reject the null of no cointegration, this result should be interpreted as exploratory rather than strong evidence of a persistent equilibrium relationship.

## 3. Pair 2: EWA / EWC

### Economic Motivation

`EWA` tracks Australian equities and `EWC` tracks Canadian equities. Australia and Canada are both developed, commodity-sensitive markets. Their equity markets are influenced by global growth, resource demand, energy and materials prices, exchange-rate cycles, and global risk appetite. These shared macro drivers make a long-run relationship plausible.

### Preliminary Screening

During the formation period, the price-level correlation between `EWA` and `EWC` was:

```text
Correlation = 0.7214
```

This shows moderate-to-high co-movement, but correlation alone does not prove that the spread is stationary.

### Cointegration Results

The Engle-Granger cointegration test was applied to the formation-period prices.

| Metric | Result |
|---|---:|
| Test statistic | -2.6586 |
| p-value | 0.2148 |
| OLS alpha | 7.4876 |
| OLS beta | 0.3986 |

The null hypothesis is no cointegration. The p-value is above conventional significance thresholds, so we do not reject the null hypothesis during the formation period. The formation-period evidence for cointegration is therefore weak.

### Strategy Design

The trading strategy uses the fixed formation-period spread:

```text
spread_t = EWA_t - 7.4876 - 0.3986 * EWC_t
```

A 60-day rolling z-score is computed on the trading-period spread.

Trading rules:

| Signal | Action |
|---|---|
| z-score > 2.0 | Short spread: short EWA, long beta-adjusted EWC |
| z-score < -2.0 | Long spread: long EWA, short beta-adjusted EWC |
| abs(z-score) < 0.5 | Close position |

Positions are shifted by one day before calculating returns to avoid look-ahead bias.

### Backtesting Results

| Metric | Result |
|---|---:|
| Trading period | 2024-01-02 to 2026-05-12 |
| Total return | 15.40% |
| Annualized Sharpe ratio | 0.6448 |
| Maximum drawdown | -10.06% |

The strategy produced a positive out-of-sample return with a moderate Sharpe ratio and lower drawdown than the stock pair. However, because the formation-period cointegration evidence is weak, the result should be interpreted cautiously.

## 4. Summary of Results

| Pair | Correlation | Cointegration statistic | p-value | Hedge ratio beta | Total return | Sharpe ratio | Max drawdown |
|---|---:|---:|---:|---:|---:|---:|---:|
| MU / WDC | 0.7997 | -2.1042 | 0.4742 | 0.9943 | 39.98% | 0.6299 | -20.04% |
| EWA / EWC | 0.7214 | -2.6586 | 0.2148 | 0.3986 | 15.40% | 0.6448 | -10.06% |

## 5. Interpretation and Limitations

The results illustrate the difference between economic intuition, correlation, cointegration, and trading performance. Both pairs have plausible economic relationships and positive out-of-sample backtest returns. However, under the strict split-sample design, neither pair passes the Engle-Granger cointegration test during the formation period. This means the statistical evidence for a stable long-run equilibrium is weak.

The positive backtest performance may reflect short-term mean reversion, favorable market conditions during the trading period, or parameter choices rather than a robust cointegration relationship. The strategy should therefore be treated as an empirical experiment rather than a fully validated trading model.

Important limitations include:

- Transaction costs, bid-ask spreads, slippage, short-sale constraints, and borrowing costs are ignored.
- The hedge ratio is estimated once and kept fixed, although relationships can change over time.
- Cointegration relationships may break during regime shifts, earnings shocks, commodity cycles, or macroeconomic changes.
- The strategy uses daily close data and does not model intraday execution.
- The sample period is limited, so results may not generalize to future markets.

## Appendix: Python Code

The working assignment notebook is provided in:

```text
analysis/assignment1_pairs_trading_report.ipynb
```

The equivalent Python script is provided in:

```text
analysis/assignment1_pairs_trading_report.py
```

The code downloads data from Yahoo Finance, computes correlations, estimates OLS hedge ratios, runs Engle-Granger cointegration tests, constructs spreads and rolling z-scores, backtests the trading strategy, and reports total return, Sharpe ratio, and maximum drawdown.
