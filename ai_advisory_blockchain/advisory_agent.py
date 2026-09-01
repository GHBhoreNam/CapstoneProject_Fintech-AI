"""
advisory_agent.py

Portfolio advisory agent implementing an explicit:
Think -> Act -> Observe -> Decide workflow.
"""

from itertools import combinations
from typing import Dict, List, Any


# ---------------------------------------------------------------------------
# Market assumptions
# ---------------------------------------------------------------------------

RISK_FREE_RATE = 0.06
EXPECTED_MARKET_RETURN = 0.12
PAIRWISE_CORRELATION = 0.30
HUMAN_ESCALATION_THRESHOLD = 0.20


# ---------------------------------------------------------------------------
# Prescribed allocation lookup table
# ---------------------------------------------------------------------------

ALLOCATION_LOOKUP = {
    "conservative": ["PAYBOND", "PAYGOLD", "PAYRETAIL"],
    "moderate": ["PAYRETAIL", "PAYINFRA", "PAYGOLD"],
    "aggressive": ["PAYTECH", "PAYFIN", "PAYINFRA"],
}


# ---------------------------------------------------------------------------
# Local stock universe
#
# If STOCK_UNIVERSE is already supplied in your starter project, remove this
# sample dictionary and import the provided STOCK_UNIVERSE instead.
#
# Standard deviations must be expressed as decimals:
# 0.10 means 10%.
# ---------------------------------------------------------------------------

STOCK_UNIVERSE = {
    "PAYBOND": {
        "beta": 0.40,
        "analyst_expected_return": 0.075,
        "std_dev": 0.07,
    },
    "PAYGOLD": {
        "beta": 0.60,
        "analyst_expected_return": 0.095,
        "std_dev": 0.10,
    },
    "PAYRETAIL": {
        "beta": 1.00,
        "analyst_expected_return": 0.130,
        "std_dev": 0.13,
    },
    "PAYINFRA": {
        "beta": 1.20,
        "analyst_expected_return": 0.145,
        "std_dev": 0.17,
    },
    "PAYTECH": {
        "beta": 1.60,
        "analyst_expected_return": 0.190,
        "std_dev": 0.26,
    },
    "PAYFIN": {
        "beta": 1.40,
        "analyst_expected_return": 0.170,
        "std_dev": 0.22,
    },
}


# ---------------------------------------------------------------------------
# Tool function
# ---------------------------------------------------------------------------

def get_stock_data(ticker: str) -> Dict[str, float]:
    """
    Simulates an external stock-data API call.

    Returns beta, analyst_expected_return and std_dev from the local
    STOCK_UNIVERSE. The analyst_expected_return is retrieved as required,
    but it is never used in the CAPM calculation.
    """
    normalized_ticker = ticker.strip().upper()

    if normalized_ticker not in STOCK_UNIVERSE:
        raise ValueError(
            f"Ticker '{normalized_ticker}' was not found in STOCK_UNIVERSE."
        )

    stock = STOCK_UNIVERSE[normalized_ticker]

    required_fields = {
        "beta",
        "analyst_expected_return",
        "std_dev",
    }

    missing_fields = required_fields.difference(stock.keys())

    if missing_fields:
        raise ValueError(
            f"Ticker '{normalized_ticker}' is missing fields: "
            f"{sorted(missing_fields)}"
        )

    return {
        "ticker": normalized_ticker,
        "beta": float(stock["beta"]),
        "analyst_expected_return": float(
            stock["analyst_expected_return"]
        ),
        "std_dev": float(stock["std_dev"]),
    }


# ---------------------------------------------------------------------------
# Portfolio advisory agent
# ---------------------------------------------------------------------------

class PortfolioAdvisoryAgent:
    """
    Agent that processes one investor profile through explicit stages:
    Think, Act, Observe and Decide.
    """

    def __init__(
        self,
        risk_free_rate: float = RISK_FREE_RATE,
        expected_market_return: float = EXPECTED_MARKET_RETURN,
        correlation: float = PAIRWISE_CORRELATION,
        escalation_threshold: float = HUMAN_ESCALATION_THRESHOLD,
    ):
        self.risk_free_rate = risk_free_rate
        self.expected_market_return = expected_market_return
        self.correlation = correlation
        self.escalation_threshold = escalation_threshold

    def think(self, investor_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reads one investor profile and applies the prescribed lookup table.
        """
        investor_id = investor_profile.get(
            "investor_id",
            investor_profile.get("id", "UNKNOWN"),
        )

        risk_tolerance = str(
            investor_profile.get("risk_tolerance", "")
        ).strip().lower()

        if risk_tolerance not in ALLOCATION_LOOKUP:
            raise ValueError(
                f"Unsupported risk_tolerance '{risk_tolerance}' for "
                f"investor '{investor_id}'. Expected Conservative, "
                f"Moderate or Aggressive."
            )

        tickers = ALLOCATION_LOOKUP[risk_tolerance]
        equal_weight = 1.0 / len(tickers)

        allocation = {
            ticker: equal_weight
            for ticker in tickers
        }

        return {
            "investor_id": investor_id,
            "risk_tolerance": risk_tolerance,
            "allocation": allocation,
        }

    def act(
        self,
        allocation: Dict[str, float],
    ) -> Dict[str, Dict[str, float]]:
        """
        Calls get_stock_data once for every ticker in the allocation.
        """
        observations = {}

        for ticker in allocation:
            observations[ticker] = get_stock_data(ticker)

        return observations

    def observe(
        self,
        allocation: Dict[str, float],
        stock_observations: Dict[str, Dict[str, float]],
    ) -> Dict[str, Any]:
        """
        Calculates:
        1. CAPM expected return for each stock
        2. Weighted portfolio CAPM expected return
        3. Portfolio variance
        4. Portfolio standard deviation
        """
        market_risk_premium = (
            self.expected_market_return - self.risk_free_rate
        )

        per_stock_results = {}
        portfolio_expected_return = 0.0

        # CAPM expected return:
        # E(R_i) = R_f + beta_i * (E(R_m) - R_f)
        for ticker, weight in allocation.items():
            beta = stock_observations[ticker]["beta"]

            capm_expected_return = (
                self.risk_free_rate
                + beta * market_risk_premium
            )

            weighted_expected_return = (
                weight * capm_expected_return
            )

            portfolio_expected_return += weighted_expected_return

            per_stock_results[ticker] = {
                "weight": weight,
                "beta": beta,
                "std_dev": stock_observations[ticker]["std_dev"],
                "capm_expected_return": capm_expected_return,
                "weighted_capm_return": weighted_expected_return,
            }

        # First variance component:
        # sum(w_i^2 * sigma_i^2)
        individual_variance_component = sum(
            allocation[ticker] ** 2
            * stock_observations[ticker]["std_dev"] ** 2
            for ticker in allocation
        )

        # Second variance component:
        # 2 * sum(w_i * w_j * covariance_ij)
        covariance_component = 0.0

        for ticker_i, ticker_j in combinations(allocation.keys(), 2):
            weight_i = allocation[ticker_i]
            weight_j = allocation[ticker_j]

            std_dev_i = stock_observations[ticker_i]["std_dev"]
            std_dev_j = stock_observations[ticker_j]["std_dev"]

            covariance_ij = (
                self.correlation
                * std_dev_i
                * std_dev_j
            )

            covariance_component += (
                2.0
                * weight_i
                * weight_j
                * covariance_ij
            )

        portfolio_variance = (
            individual_variance_component
            + covariance_component
        )

        portfolio_std_dev = portfolio_variance ** 0.5

        return {
            "portfolio_expected_return": portfolio_expected_return,
            "portfolio_variance": portfolio_variance,
            "portfolio_std_dev": portfolio_std_dev,
            "pairwise_correlation": self.correlation,
            "per_stock_results": per_stock_results,
        }

    def decide(
        self,
        thought: Dict[str, Any],
        observation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Escalates when portfolio standard deviation is greater than 20%.
        Otherwise, finalizes the recommendation.
        """
        portfolio_std_dev = observation["portfolio_std_dev"]

        if portfolio_std_dev > self.escalation_threshold:
            status = "ESCALATED_TO_HUMAN_ADVISOR"
            finalized = False
        else:
            status = "RECOMMENDATION_FINALIZED"
            finalized = True

        return {
            "investor_id": thought["investor_id"],
            "risk_tolerance": thought["risk_tolerance"].title(),
            "allocation": thought["allocation"],
            "portfolio_expected_return": observation[
                "portfolio_expected_return"
            ],
            "portfolio_expected_return_pct": round(
                observation["portfolio_expected_return"] * 100,
                2,
            ),
            "portfolio_variance": observation["portfolio_variance"],
            "portfolio_std_dev": portfolio_std_dev,
            "portfolio_std_dev_pct": round(
                portfolio_std_dev * 100,
                2,
            ),
            "pairwise_correlation": observation[
                "pairwise_correlation"
            ],
            "escalation_threshold_pct": (
                self.escalation_threshold * 100
            ),
            "status": status,
            "finalized": finalized,
            "stock_details": observation["per_stock_results"],
        }

    def run(self, investor_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the complete agent loop for one investor profile.
        """
        print("\nTHINK")
        thought = self.think(investor_profile)
        print(
            f"Investor: {thought['investor_id']}, "
            f"risk tolerance: {thought['risk_tolerance'].title()}"
        )
        print(f"Prescribed allocation: {thought['allocation']}")

        print("\nACT")
        stock_observations = self.act(thought["allocation"])

        for ticker, stock_data in stock_observations.items():
            print(
                f"get_stock_data({ticker}) -> "
                f"beta={stock_data['beta']:.2f}, "
                f"analyst_expected_return="
                f"{stock_data['analyst_expected_return']:.2%}, "
                f"std_dev={stock_data['std_dev']:.2%}"
            )

        print("\nOBSERVE")
        observation = self.observe(
            thought["allocation"],
            stock_observations,
        )

        print(
            "Portfolio CAPM expected return: "
            f"{observation['portfolio_expected_return']:.2%}"
        )
        print(
            "Portfolio variance: "
            f"{observation['portfolio_variance']:.6f}"
        )
        print(
            "Portfolio standard deviation: "
            f"{observation['portfolio_std_dev']:.2%}"
        )

        print("\nDECIDE")
        decision = self.decide(thought, observation)
        print(f"Status: {decision['status']}")

        return decision


# ---------------------------------------------------------------------------
# Example investor profiles
# ---------------------------------------------------------------------------

INVESTOR_PROFILES = [
    {
        "investor_id": "INV01",
        "risk_tolerance": "Conservative",
    },
    {
        "investor_id": "INV02",
        "risk_tolerance": "Moderate",
    },
    {
        "investor_id": "INV03",
        "risk_tolerance": "Aggressive",
    },
    {
        "investor_id": "INV04",
        "risk_tolerance": "Moderate",
    },
    {
        "investor_id": "INV05",
        "risk_tolerance": "Aggressive",
    },
]


def main() -> None:
    agent = PortfolioAdvisoryAgent()
    all_results: List[Dict[str, Any]] = []

    for profile in INVESTOR_PROFILES:
        result = agent.run(profile)
        all_results.append(result)

        print(
            f"\nRESULT: {result['investor_id']} | "
            f"Expected return: "
            f"{result['portfolio_expected_return_pct']:.2f}% | "
            f"Std dev: {result['portfolio_std_dev_pct']:.2f}% | "
            f"{result['status']}"
        )

        print("=" * 75)

    print("\nFINAL SUMMARY")

    for result in all_results:
        print(
            f"{result['investor_id']}: "
            f"{result['risk_tolerance']}, "
            f"return={result['portfolio_expected_return_pct']:.2f}%, "
            f"std_dev={result['portfolio_std_dev_pct']:.2f}%, "
            f"status={result['status']}"
        )


if __name__ == "__main__":
    main()
