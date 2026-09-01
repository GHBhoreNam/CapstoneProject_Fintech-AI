import os

MOCK_LLM = int(os.getenv("MOCK_LLM", "1"))


def generate_recommendation_text(
    investor_id,
    risk_tolerance,
    tickers,
    portfolio_return,
    portfolio_volatility,
):
    """
    Only the narrative sentence is gated by MOCK_LLM.
    All calculations remain deterministic.
    """

    if MOCK_LLM == 1:
        return (
            f"For {risk_tolerance} investor {investor_id}, "
            f"we recommend an equal-weight allocation across "
            f"{', '.join(tickers)} with an expected portfolio return of "
            f"{portfolio_return:.1%} and volatility of "
            f"{portfolio_volatility:.1%}."
        )

    # Optional LLM mode (MOCK_LLM=0)
    prompt = (
        f"Create a professional investment recommendation using only these facts: "
        f"Investor={investor_id}, Risk Tolerance={risk_tolerance}, "
        f"Allocation={', '.join(tickers)}, "
        f"Expected Return={portfolio_return:.1%}, "
        f"Portfolio Volatility={portfolio_volatility:.1%}."
    )

    return call_llm(prompt)

recommendation_text = generate_recommendation_text(
    thought["investor_id"],
    thought["risk_tolerance"].title(),
    list(thought["allocation"].keys()),
    observation["portfolio_expected_return"],
    observation["portfolio_std_dev"],
)

