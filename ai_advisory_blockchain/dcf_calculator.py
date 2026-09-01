"""
dcf_calculator.py

Illustrative discounted-cash-flow valuation for a hypothetical Paytm business line.
All currency inputs and outputs are in Indian rupees (INR).

Chosen assumptions
------------------
Base FCFF inputs:
    EBIT                         = INR 10.0 billion
    Tax rate                     = 25.0%
    Depreciation & amortization  = INR 2.0 billion
    Capital expenditure         = INR 2.5 billion
    Change in net working capital= INR 0.5 billion

FCFF = EBIT * (1 - tax rate) + D&A - CapEx - change in NWC
     = INR 6.5 billion

Five-year FCFF growth rates fade as follows: 18%, 15%, 12%, 9%, 7%.
Terminal growth rate: 5.0%.

WACC inputs:
    Risk-free rate              = 6.0%
    Expected market return      = 12.0%
    Beta (illustrative PAYRETAIL beta from STOCK_UNIVERSE) = 1.00
    Pre-tax cost of debt        = 9.0%
    Tax rate                    = 25.0%
    Equity weight               = 80.0%
    Debt weight                 = 20.0%

Cost of equity = R_f + beta * (E(R_m) - R_f)
After-tax cost of debt = pre-tax cost of debt * (1 - tax rate)
WACC = equity weight * cost of equity + debt weight * after-tax cost of debt

EV/EBITDA cross-check:
    Illustrative EBITDA         = INR 12.0 billion
    Illustrative EV/EBITDA      = 12.0x
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple


INR_CRORE = 10_000_000.0


STOCK_UNIVERSE: Dict[str, Dict[str, float]] = {
    "PAYRETAIL": {
        "beta": 1.00,
        "analyst_expected_return": 0.13,
        "std_dev": 0.13,
    }
}


@dataclass(frozen=True)
class DCFInputs:
    ebit: float = 10_000_000_000.0
    tax_rate: float = 0.25
    depreciation_amortization: float = 2_000_000_000.0
    capex: float = 2_500_000_000.0
    change_in_nwc: float = 500_000_000.0
    annual_growth_rates: Tuple[float, ...] = (0.18, 0.15, 0.12, 0.09, 0.07)
    terminal_growth_rate: float = 0.05
    risk_free_rate: float = 0.06
    expected_market_return: float = 0.12
    beta_ticker: str = "PAYRETAIL"
    pre_tax_cost_of_debt: float = 0.09
    equity_weight: float = 0.80
    debt_weight: float = 0.20
    illustrative_ebitda: float = 12_000_000_000.0
    illustrative_ev_ebitda_multiple: float = 12.0


def calculate_base_fcff(inputs: DCFInputs) -> float:
    """Calculate unlevered Free Cash Flow to the Firm."""
    return (
        inputs.ebit * (1.0 - inputs.tax_rate)
        + inputs.depreciation_amortization
        - inputs.capex
        - inputs.change_in_nwc
    )


def calculate_wacc(inputs: DCFInputs) -> Tuple[float, float, float]:
    """Return WACC, CAPM cost of equity, and after-tax cost of debt."""
    if abs(inputs.equity_weight + inputs.debt_weight - 1.0) > 1e-12:
        raise ValueError("Equity and debt weights must sum to 1.0.")

    try:
        beta = STOCK_UNIVERSE[inputs.beta_ticker]["beta"]
    except KeyError as exc:
        raise ValueError(
            f"Missing ticker or beta for {inputs.beta_ticker!r} in STOCK_UNIVERSE."
        ) from exc

    cost_of_equity = inputs.risk_free_rate + beta * (
        inputs.expected_market_return - inputs.risk_free_rate
    )
    after_tax_cost_of_debt = inputs.pre_tax_cost_of_debt * (1.0 - inputs.tax_rate)
    wacc = (
        inputs.equity_weight * cost_of_equity
        + inputs.debt_weight * after_tax_cost_of_debt
    )
    return wacc, cost_of_equity, after_tax_cost_of_debt


def validate_inputs(inputs: DCFInputs, wacc: float) -> None:
    """Validate DCF and sensitivity assumptions before valuation."""
    if len(inputs.annual_growth_rates) != 5:
        raise ValueError("Exactly five annual growth rates are required.")
    if any(
        later > earlier
        for earlier, later in zip(
            inputs.annual_growth_rates, inputs.annual_growth_rates[1:]
        )
    ):
        raise ValueError("The five-year projected growth rates must fade or stay flat.")

    # Required base-case constraint: terminal growth at least 3 percentage points
    # below WACC.
    base_gap = wacc - inputs.terminal_growth_rate
    if base_gap < 0.03 - 1e-12:
        raise ValueError(
            "Terminal growth must be at least 3 percentage points below base WACC."
        )

    # Required worst-case sensitivity self-check:
    # lowest discount rate equals WACC - 1pp; highest growth equals terminal g + 1pp.
    worst_case_gap = (wacc - 0.01) - (inputs.terminal_growth_rate + 0.01)
    if worst_case_gap < 0.01 - 1e-12:
        raise ValueError(
            "Worst-case sensitivity cell must retain a WACC-minus-growth gap "
            "of at least 1 percentage point."
        )


def project_fcff(base_fcff: float, growth_rates: Tuple[float, ...]) -> List[float]:
    """Project five years of FCFF using sequential annual growth rates."""
    projected: List[float] = []
    current_fcff = base_fcff
    for growth_rate in growth_rates:
        current_fcff *= 1.0 + growth_rate
        projected.append(current_fcff)
    return projected


def calculate_enterprise_value(
    projected_fcff: List[float], discount_rate: float, terminal_growth_rate: float
) -> Dict[str, float]:
    """Discount explicit FCFF and a Gordon-growth terminal value to present."""
    if discount_rate <= terminal_growth_rate:
        raise ValueError("Discount rate must exceed terminal growth rate.")

    pv_explicit_fcff = sum(
        fcff / ((1.0 + discount_rate) ** year)
        for year, fcff in enumerate(projected_fcff, start=1)
    )
    terminal_value = (
        projected_fcff[-1]
        * (1.0 + terminal_growth_rate)
        / (discount_rate - terminal_growth_rate)
    )
    pv_terminal_value = terminal_value / (
        (1.0 + discount_rate) ** len(projected_fcff)
    )
    return {
        "pv_explicit_fcff": pv_explicit_fcff,
        "terminal_value_at_year_5": terminal_value,
        "pv_terminal_value": pv_terminal_value,
        "enterprise_value": pv_explicit_fcff + pv_terminal_value,
    }


def build_sensitivity_table(
    projected_fcff: List[float], base_wacc: float, base_terminal_growth: float
) -> Tuple[List[float], List[float], List[List[float]]]:
    """Create a 3x3 EV grid for WACC and terminal growth at -1pp, base, +1pp."""
    discount_rates = [base_wacc - 0.01, base_wacc, base_wacc + 0.01]
    growth_rates = [
        base_terminal_growth - 0.01,
        base_terminal_growth,
        base_terminal_growth + 0.01,
    ]
    grid = [
        [
            calculate_enterprise_value(projected_fcff, rate, growth)[
                "enterprise_value"
            ]
            for growth in growth_rates
        ]
        for rate in discount_rates
    ]
    return discount_rates, growth_rates, grid


def format_inr_crore(value: float) -> str:
    return f"INR {value / INR_CRORE:,.2f} crore"


def print_sensitivity_table(
    discount_rates: List[float], growth_rates: List[float], grid: List[List[float]]
) -> None:
    print("\nSensitivity table: Enterprise Value (INR crore)")
    header = "WACC \\ Terminal g" + "".join(
        f" | {growth:>9.2%}" for growth in growth_rates
    )
    print(header)
    print("-" * len(header))
    for rate, row in zip(discount_rates, grid):
        values = "".join(f" | {value / INR_CRORE:>9,.2f}" for value in row)
        print(f"{rate:>17.2%}{values}")


def main() -> Dict[str, object]:
    inputs = DCFInputs()
    base_fcff = calculate_base_fcff(inputs)
    wacc, cost_of_equity, after_tax_cost_of_debt = calculate_wacc(inputs)
    validate_inputs(inputs, wacc)

    projected_fcff = project_fcff(base_fcff, inputs.annual_growth_rates)
    dcf = calculate_enterprise_value(
        projected_fcff, wacc, inputs.terminal_growth_rate
    )
    discount_rates, terminal_growth_rates, sensitivity_grid = (
        build_sensitivity_table(projected_fcff, wacc, inputs.terminal_growth_rate)
    )
    comparable_ev = (
        inputs.illustrative_ebitda * inputs.illustrative_ev_ebitda_multiple
    )
    worst_case_gap = (wacc - 0.01) - (inputs.terminal_growth_rate + 0.01)

    print("Hypothetical Paytm Business-Line DCF")
    print(f"Base unlevered FCFF: {format_inr_crore(base_fcff)}")
    print(f"CAPM cost of equity: {cost_of_equity:.2%}")
    print(f"After-tax cost of debt: {after_tax_cost_of_debt:.2%}")
    print(f"WACC: {wacc:.2%}")
    print(f"Terminal growth rate: {inputs.terminal_growth_rate:.2%}")
    print(
        "Worst-case sensitivity gap: "
        f"(WACC - 1pp) - (terminal growth + 1pp) = {worst_case_gap:.2%}"
    )
    print("Self-check passed: worst-case gap is at least 1.00 percentage point.")

    print("\nProjected FCFF")
    for year, (growth, fcff) in enumerate(
        zip(inputs.annual_growth_rates, projected_fcff), start=1
    ):
        print(f"Year {year}: growth={growth:.1%}, FCFF={format_inr_crore(fcff)}")

    print(f"\nPV of explicit FCFF: {format_inr_crore(dcf['pv_explicit_fcff'])}")
    print(
        "Terminal value at end of Year 5: "
        f"{format_inr_crore(dcf['terminal_value_at_year_5'])}"
    )
    print(f"PV of terminal value: {format_inr_crore(dcf['pv_terminal_value'])}")
    print(f"DCF enterprise value: {format_inr_crore(dcf['enterprise_value'])}")

    print_sensitivity_table(
        discount_rates, terminal_growth_rates, sensitivity_grid
    )

    print("\nEV/EBITDA cross-check")
    print(f"Illustrative EBITDA: {format_inr_crore(inputs.illustrative_ebitda)}")
    print(f"Illustrative multiple: {inputs.illustrative_ev_ebitda_multiple:.1f}x")
    print(f"Implied enterprise value: {format_inr_crore(comparable_ev)}")

    difference = dcf["enterprise_value"] - comparable_ev
    difference_pct = difference / comparable_ev
    comparison = "above" if difference >= 0 else "below"
    print(
        f"The base-case DCF estimate is {abs(difference_pct):.1%} {comparison} "
        "the illustrative EV/EBITDA estimate. The difference reflects the DCF's "
        "explicit growth, WACC, and terminal-growth assumptions, while the multiple "
        "method applies a simpler market-style benchmark to EBITDA."
    )

    return {
        "base_fcff": base_fcff,
        "wacc": wacc,
        "cost_of_equity": cost_of_equity,
        "after_tax_cost_of_debt": after_tax_cost_of_debt,
        "projected_fcff": projected_fcff,
        "dcf": dcf,
        "sensitivity_discount_rates": discount_rates,
        "sensitivity_terminal_growth_rates": terminal_growth_rates,
        "sensitivity_grid": sensitivity_grid,
        "ev_ebitda_enterprise_value": comparable_ev,
        "worst_case_gap": worst_case_gap,
    }


if __name__ == "__main__":
    main()
