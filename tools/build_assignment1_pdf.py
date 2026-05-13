from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    ListFlowable,
    ListItem,
)


OUT = Path("submission/assignment1_report_draft.pdf")


def styles():
    base = getSampleStyleSheet()
    base["Title"].fontName = "Helvetica-Bold"
    base["Title"].fontSize = 20
    base["Title"].leading = 24
    base["Title"].textColor = colors.HexColor("#0B2545")
    base["Title"].spaceAfter = 14

    base["Heading1"].fontName = "Helvetica-Bold"
    base["Heading1"].fontSize = 15
    base["Heading1"].leading = 18
    base["Heading1"].textColor = colors.HexColor("#2E74B5")
    base["Heading1"].spaceBefore = 12
    base["Heading1"].spaceAfter = 8

    base["Heading2"].fontName = "Helvetica-Bold"
    base["Heading2"].fontSize = 12
    base["Heading2"].leading = 15
    base["Heading2"].textColor = colors.HexColor("#1F4D78")
    base["Heading2"].spaceBefore = 8
    base["Heading2"].spaceAfter = 5

    base["BodyText"].fontName = "Helvetica"
    base["BodyText"].fontSize = 10
    base["BodyText"].leading = 13
    base["BodyText"].spaceAfter = 6

    base.add(
        ParagraphStyle(
            name="Small",
            parent=base["BodyText"],
            fontSize=9,
            leading=11,
        )
    )
    base.add(
        ParagraphStyle(
            name="CodeBlock",
            parent=base["BodyText"],
            fontName="Courier",
            fontSize=9,
            leading=11,
            leftIndent=18,
            spaceBefore=3,
            spaceAfter=8,
        )
    )
    return base


def p(text, style):
    return Paragraph(text, style)


def tbl(headers, rows, widths):
    data = [[Paragraph(str(x), ST["Small"]) for x in headers]]
    data += [[Paragraph(str(x), ST["Small"]) for x in row] for row in rows]
    table = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#DADCE0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return [table, Spacer(1, 8)]


def bullets(items):
    return ListFlowable(
        [ListItem(Paragraph(item, ST["BodyText"])) for item in items],
        bulletType="bullet",
        start="circle",
        leftIndent=18,
    )


def build():
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=LETTER,
        rightMargin=0.8 * inch,
        leftMargin=0.8 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    story = []
    story.append(p("Assignment 1: Cointegration & Pairs Trading", ST["Title"]))
    story.append(p("<i>Concise Report Draft</i>", ST["BodyText"]))
    story.append(p("<b>Team Information:</b> [Fill in team member names and Andrew IDs]", ST["BodyText"]))

    story.append(p("1. Overview", ST["Heading1"]))
    story.append(
        p(
            "This report applies a two-stage cointegration and pairs trading workflow to two selected pairs. "
            "Daily adjusted close prices were downloaded from Yahoo Finance using the yfinance Python package. "
            "To reduce look-ahead bias, the sample is separated into a formation period and a trading period.",
            ST["BodyText"],
        )
    )
    story += tbl(
        ["Category", "Pair", "Instruments"],
        [
            ["Stock pair", "MU / WDC", "Micron Technology and Western Digital"],
            ["ETF pair", "EWA / EWC", "iShares MSCI Australia ETF and iShares MSCI Canada ETF"],
        ],
        [1.0 * inch, 1.0 * inch, 4.4 * inch],
    )
    story += tbl(
        ["Period", "Dates", "Purpose"],
        [
            ["Formation period", "2021-01-04 to 2023-12-29", "Correlation, cointegration testing, hedge-ratio estimation"],
            ["Trading period", "2024-01-02 to 2026-05-12", "Out-of-sample strategy backtest"],
        ],
        [1.25 * inch, 1.75 * inch, 3.4 * inch],
    )
    story.append(p("The spread is constructed as:", ST["BodyText"]))
    story.append(p("spread = first asset - alpha - beta * second asset", ST["CodeBlock"]))
    story.append(
        p(
            "The hedge ratio beta and intercept alpha are estimated by OLS during the formation period and then fixed during the trading period.",
            ST["BodyText"],
        )
    )

    story.append(p("2. Pair 1: MU / WDC", ST["Heading1"]))
    story.append(p("Economic Motivation", ST["Heading2"]))
    story.append(
        p(
            "Micron Technology (MU) and Western Digital (WDC) are both exposed to the memory and data storage cycle. "
            "Micron is strongly linked to DRAM and NAND memory, while Western Digital is exposed to NAND flash and storage devices. "
            "Both firms are affected by semiconductor demand, cloud and data-center investment, inventory cycles, and pricing pressure "
            "in memory/storage markets. This makes a long-run relationship plausible, although it must be verified empirically.",
            ST["BodyText"],
        )
    )
    story.append(p("Preliminary Screening", ST["Heading2"]))
    story.append(
        p(
            "During the formation period, the price-level correlation between MU and WDC was 0.7997. "
            "This indicates meaningful co-movement, but correlation alone is not sufficient because two non-stationary assets "
            "can appear correlated without having a stable mean-reverting spread.",
            ST["BodyText"],
        )
    )
    story.append(p("Cointegration Results", ST["Heading2"]))
    story += tbl(
        ["Metric", "Result"],
        [["Test statistic", "-2.1042"], ["p-value", "0.4742"], ["OLS alpha", "31.9935"], ["OLS beta", "0.9943"]],
        [3.0 * inch, 1.6 * inch],
    )
    story.append(
        p(
            "The null hypothesis is no cointegration. Since the p-value is above conventional 10%, 5%, and 1% levels, "
            "we do not reject the null hypothesis during the formation period. Therefore, the strict split-sample evidence "
            "for cointegration is weak.",
            ST["BodyText"],
        )
    )
    story.append(p("Strategy Design", ST["Heading2"]))
    story.append(p("spread_t = MU_t - 31.9935 - 0.9943 * WDC_t", ST["CodeBlock"]))
    story += tbl(
        ["Signal", "Action"],
        [
            ["z-score > 2.0", "Short spread: short MU, long beta-adjusted WDC"],
            ["z-score < -2.0", "Long spread: long MU, short beta-adjusted WDC"],
            ["abs(z-score) < 0.5", "Close position"],
        ],
        [1.8 * inch, 4.6 * inch],
    )
    story.append(p("Positions are shifted by one day before calculating returns to avoid look-ahead bias.", ST["BodyText"]))
    story.append(p("Backtesting Results", ST["Heading2"]))
    story += tbl(
        ["Metric", "Result"],
        [
            ["Trading period", "2024-01-02 to 2026-05-12"],
            ["Total return", "39.98%"],
            ["Annualized Sharpe ratio", "0.6299"],
            ["Maximum drawdown", "-20.04%"],
        ],
        [3.0 * inch, 2.2 * inch],
    )
    story.append(
        p(
            "The strategy generated a positive total return, but the Sharpe ratio is moderate and the drawdown is material. "
            "Because the formation-period cointegration test did not reject the null of no cointegration, this result should be "
            "interpreted as exploratory rather than strong evidence of a persistent equilibrium relationship.",
            ST["BodyText"],
        )
    )

    story.append(PageBreak())
    story.append(p("3. Pair 2: EWA / EWC", ST["Heading1"]))
    story.append(p("Economic Motivation", ST["Heading2"]))
    story.append(
        p(
            "EWA tracks Australian equities and EWC tracks Canadian equities. Australia and Canada are both developed, "
            "commodity-sensitive markets. Their equity markets are influenced by global growth, resource demand, energy and "
            "materials prices, exchange-rate cycles, and global risk appetite. These shared macro drivers make a long-run "
            "relationship plausible.",
            ST["BodyText"],
        )
    )
    story.append(p("Preliminary Screening", ST["Heading2"]))
    story.append(
        p(
            "During the formation period, the price-level correlation between EWA and EWC was 0.7214. "
            "This shows moderate-to-high co-movement, but correlation alone does not prove that the spread is stationary.",
            ST["BodyText"],
        )
    )
    story.append(p("Cointegration Results", ST["Heading2"]))
    story += tbl(
        ["Metric", "Result"],
        [["Test statistic", "-2.6586"], ["p-value", "0.2148"], ["OLS alpha", "7.4876"], ["OLS beta", "0.3986"]],
        [3.0 * inch, 1.6 * inch],
    )
    story.append(
        p(
            "The null hypothesis is no cointegration. The p-value is above conventional significance thresholds, so we do not "
            "reject the null hypothesis during the formation period. The formation-period evidence for cointegration is therefore weak.",
            ST["BodyText"],
        )
    )
    story.append(p("Strategy Design", ST["Heading2"]))
    story.append(p("spread_t = EWA_t - 7.4876 - 0.3986 * EWC_t", ST["CodeBlock"]))
    story += tbl(
        ["Signal", "Action"],
        [
            ["z-score > 2.0", "Short spread: short EWA, long beta-adjusted EWC"],
            ["z-score < -2.0", "Long spread: long EWA, short beta-adjusted EWC"],
            ["abs(z-score) < 0.5", "Close position"],
        ],
        [1.8 * inch, 4.6 * inch],
    )
    story.append(p("Positions are shifted by one day before calculating returns to avoid look-ahead bias.", ST["BodyText"]))
    story.append(p("Backtesting Results", ST["Heading2"]))
    story += tbl(
        ["Metric", "Result"],
        [
            ["Trading period", "2024-01-02 to 2026-05-12"],
            ["Total return", "15.40%"],
            ["Annualized Sharpe ratio", "0.6448"],
            ["Maximum drawdown", "-10.06%"],
        ],
        [3.0 * inch, 2.2 * inch],
    )
    story.append(
        p(
            "The strategy produced a positive out-of-sample return with a moderate Sharpe ratio and lower drawdown than the stock pair. "
            "However, because the formation-period cointegration evidence is weak, the result should be interpreted cautiously.",
            ST["BodyText"],
        )
    )

    story.append(p("4. Summary of Results", ST["Heading1"]))
    story += tbl(
        ["Pair", "Corr.", "Coint stat", "p-value", "Beta", "Total return", "Sharpe", "Max DD"],
        [
            ["MU / WDC", "0.7997", "-2.1042", "0.4742", "0.9943", "39.98%", "0.6299", "-20.04%"],
            ["EWA / EWC", "0.7214", "-2.6586", "0.2148", "0.3986", "15.40%", "0.6448", "-10.06%"],
        ],
        [0.8 * inch, 0.65 * inch, 0.85 * inch, 0.7 * inch, 0.6 * inch, 0.85 * inch, 0.65 * inch, 0.75 * inch],
    )
    story.append(p("5. Interpretation and Limitations", ST["Heading1"]))
    story.append(
        p(
            "The results illustrate the difference between economic intuition, correlation, cointegration, and trading performance. "
            "Both pairs have plausible economic relationships and positive out-of-sample backtest returns. However, under the strict "
            "split-sample design, neither pair passes the Engle-Granger cointegration test during the formation period. This means "
            "the statistical evidence for a stable long-run equilibrium is weak.",
            ST["BodyText"],
        )
    )
    story.append(
        p(
            "The positive backtest performance may reflect short-term mean reversion, favorable market conditions during the trading "
            "period, or parameter choices rather than a robust cointegration relationship. The strategy should therefore be treated "
            "as an empirical experiment rather than a fully validated trading model.",
            ST["BodyText"],
        )
    )
    story.append(
        bullets(
            [
                "Transaction costs, bid-ask spreads, slippage, short-sale constraints, and borrowing costs are ignored.",
                "The hedge ratio is estimated once and kept fixed, although relationships can change over time.",
                "Cointegration relationships may break during regime shifts, earnings shocks, commodity cycles, or macroeconomic changes.",
                "The strategy uses daily close data and does not model intraday execution.",
                "The sample period is limited, so results may not generalize to future markets.",
            ]
        )
    )
    story.append(p("Appendix: Python Code", ST["Heading1"]))
    story.append(p("The working Colab-ready notebook is provided in:", ST["BodyText"]))
    story.append(p("notebook/pairs_trading_colab.ipynb", ST["CodeBlock"]))
    story.append(p("The equivalent Python script is provided in:", ST["BodyText"]))
    story.append(p("notebook/pairs_trading_colab.py", ST["CodeBlock"]))
    story.append(
        p(
            "The code downloads data from Yahoo Finance, computes correlations, estimates OLS hedge ratios, runs Engle-Granger "
            "cointegration tests, constructs spreads and rolling z-scores, backtests the trading strategy, and reports total return, "
            "Sharpe ratio, and maximum drawdown.",
            ST["BodyText"],
        )
    )

    doc.build(story)


if __name__ == "__main__":
    ST = styles()
    build()
    print(f"Wrote {OUT.resolve()}")
