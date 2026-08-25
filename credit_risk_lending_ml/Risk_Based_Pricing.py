# =====================================================
# RISK-BASED PRICING USING LOGISTIC REGRESSION
# =====================================================

import pandas as pd
import numpy as np

# -----------------------------------------------------
# Predicted probabilities from trained logistic model
# -----------------------------------------------------

logit_model = models["Logistic Regression"]

pd_default = logit_model.predict_proba(
    X_test_scaled
)[:, 1]

# -----------------------------------------------------
# Create evaluation dataframe
# -----------------------------------------------------

risk_df = pd.DataFrame({
    "actual_default": y_test.values,
    "predicted_default_probability": pd_default
})

# -----------------------------------------------------
# Create 4 risk tiers (quartiles)
# Q1 = lowest risk
# Q4 = highest risk
# -----------------------------------------------------

risk_df["risk_tier"] = pd.qcut(
    risk_df["predicted_default_probability"],
    q=4,
    labels=[
        "Tier 1 - Lowest Risk",
        "Tier 2 - Low Risk",
        "Tier 3 - Medium Risk",
        "Tier 4 - Highest Risk"
    ]
)

# -----------------------------------------------------
# Illustrative pricing ranges
# -----------------------------------------------------

pricing_map = {
    "Tier 1 - Lowest Risk": "8% - 10%",
    "Tier 2 - Low Risk": "10% - 14%",
    "Tier 3 - Medium Risk": "14% - 18%",
    "Tier 4 - Highest Risk": "18% - 24%"
}

risk_df["interest_rate_range"] = (
    risk_df["risk_tier"]
    .map(pricing_map)
)

# -----------------------------------------------------
# Tier-level performance
# -----------------------------------------------------

tier_summary = (
    risk_df
    .groupby("risk_tier", observed=False)
    .agg(
        applicants=(
            "actual_default",
            "count"
        ),
        avg_predicted_pd=(
            "predicted_default_probability",
            "mean"
        ),
        observed_default_rate=(
            "actual_default",
            "mean"
        )
    )
    .reset_index()
)

# Convert to percentages

tier_summary["avg_predicted_pd"] = (
    tier_summary["avg_predicted_pd"] * 100
)

tier_summary["observed_default_rate"] = (
    tier_summary["observed_default_rate"] * 100
)

# Attach pricing

tier_summary["interest_rate_range"] = (
    tier_summary["risk_tier"]
    .map(pricing_map)
)

# Reorder columns

tier_summary = tier_summary[
    [
        "risk_tier",
        "applicants",
        "avg_predicted_pd",
        "observed_default_rate",
        "interest_rate_range"
    ]
]

# Format

tier_summary["avg_predicted_pd"] = (
    tier_summary["avg_predicted_pd"]
    .round(2)
)

tier_summary["observed_default_rate"] = (
    tier_summary["observed_default_rate"]
    .round(2)
)

print("\nRISK-BASED PRICING TABLE")
print(tier_summary)

# -----------------------------------------------------
# Monotonicity Check
# -----------------------------------------------------

rates = tier_summary[
    "observed_default_rate"
].values

is_monotonic = all(
    rates[i] <= rates[i+1]
    for i in range(len(rates)-1)
)

print("\nMONOTONICITY CHECK")

if is_monotonic:
    print(
        "PASS: Observed default rates increase "
        "from lower-risk tiers to higher-risk tiers."
    )
else:
    print(
        "WARNING: Observed default rates are not "
        "strictly monotonic."
    )

# -----------------------------------------------------
# Optional: Detailed Tier Boundaries
# -----------------------------------------------------

tier_boundaries = (
    risk_df
    .groupby("risk_tier", observed=False)
    ["predicted_default_probability"]
    .agg(["min", "max"])
    .reset_index()
)

tier_boundaries["min"] = (
    tier_boundaries["min"] * 100
).round(2)

tier_boundaries["max"] = (
    tier_boundaries["max"] * 100
).round(2)

print("\nRISK TIER PROBABILITY RANGES (%)")
print(tier_boundaries)
