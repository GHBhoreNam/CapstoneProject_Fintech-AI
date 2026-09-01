import os

MOCK_LLM = int(os.getenv("MOCK_LLM", "1"))

# Example:
# Import from your assignment's stock universe module instead
# from stock_data import STOCK_UNIVERSE

STOCK_UNIVERSE = {
    "PAYTECH": {
        "beta": 1.60,
        "analyst_expected_return": 0.19,
        "std_dev": 0.26,
    }
}


def bull_agent(ticker: str, data: dict) -> str:
    """
    Bull case argument.
    """
    beta = data["beta"]
    expected_return = data["analyst_expected_return"]

    return (
        f"BULL: With an analyst expected return of "
        f"{expected_return:.1%} and a beta of {beta:.2f}, "
        f"{ticker} offers attractive upside potential. "
        f"Investors seeking growth may view the elevated beta "
        f"as an opportunity to benefit from favorable market conditions."
    )


def bear_agent(ticker: str, data: dict) -> str:
    """
    Bear case argument.
    """
    beta = data["beta"]
    std_dev = data["std_dev"]

    return (
        f"BEAR: {ticker} carries a beta of {beta:.2f} and a "
        f"volatility (standard deviation) of {std_dev:.1%}, "
        f"indicating meaningful risk. Investors should consider "
        f"that higher volatility may lead to larger losses during "
        f"periods of market weakness."
    )


def synthesizer_agent(
    ticker: str,
    bull_argument: str,
    bear_argument: str,
    data: dict,
) -> str:
    """
    Produces a balanced 2-3 sentence summary.
    """
    expected_return = data["analyst_expected_return"]
    std_dev = data["std_dev"]

    return (
        f"SYNTHESIZER: {ticker} presents a trade-off between return "
        f"potential and risk. The bullish case highlights the "
        f"{expected_return:.1%} expected return, while the bearish "
        f"view emphasizes the {std_dev:.1%} volatility. Investors "
        f"should weigh their risk tolerance before making an allocation decision."
    )


def run_debate(ticker: str):
    if ticker not in STOCK_UNIVERSE:
        raise ValueError(f"{ticker} not found in STOCK_UNIVERSE")

    data = STOCK_UNIVERSE[ticker]

    if MOCK_LLM == 1:
        bull = bull_agent(ticker, data)
        bear = bear_agent(ticker, data)
        synthesis = synthesizer_agent(
            ticker,
            bull,
            bear,
            data,
        )
    else:
        # Optional enhancement
        bull = call_llm(
            f"Provide a bullish investment argument for {ticker} "
            f"using beta={data['beta']}, "
            f"expected_return={data['analyst_expected_return']:.1%}, "
            f"std_dev={data['std_dev']:.1%}"
        )

        bear = call_llm(
            f"Provide a bearish investment argument for {ticker} "
            f"using beta={data['beta']}, "
            f"expected_return={data['analyst_expected_return']:.1%}, "
            f"std_dev={data['std_dev']:.1%}"
        )

        synthesis = call_llm(
            f"Summarize these viewpoints:\n\nBull:{bull}\n\nBear:{bear}"
        )

    return {
        "ticker": ticker,
        "bull_argument": bull,
        "bear_argument": bear,
        "synthesizer_summary": synthesis,
    }


if __name__ == "__main__":
    result = run_debate("PAYTECH")

    print("\n=== INVESTMENT DEBATE ===\n")
    print(result["bull_argument"])
    print()
    print(result["bear_argument"])
    print()
    print(result["synthesizer_summary"])
