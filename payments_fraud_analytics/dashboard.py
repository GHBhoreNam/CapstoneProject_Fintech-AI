import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

sns.set_style("whitegrid")

OUTPUT_DIR = Path("dashboard_outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# RECONCILIATION
# ============================================================

def reconcile_payments(ledger_df, gateway_df):

    ledger_ids = set(ledger_df["transaction_id"])
    gateway_ids = set(gateway_df["transaction_id"])

    missing_in_gateway_ids = ledger_ids - gateway_ids
    missing_in_ledger_ids = gateway_ids - ledger_ids

    missing_in_gateway = ledger_df[
        ledger_df["transaction_id"].isin(missing_in_gateway_ids)
    ]

    missing_in_ledger = gateway_df[
        gateway_df["transaction_id"].isin(missing_in_ledger_ids)
    ]

    common = pd.merge(
        ledger_df,
        gateway_df,
        on="transaction_id",
        suffixes=("_ledger", "_gateway")
    )

    amount_mismatches = common[
        common["amount_inr_ledger"] != common["amount_inr_gateway"]
    ].copy()

    amount_mismatches["difference"] = (
        amount_mismatches["amount_inr_ledger"]
        - amount_mismatches["amount_inr_gateway"]
    )

    status_mismatches = common[
        common["status_ledger"] != common["status_gateway"]
    ].copy()

    return (
        missing_in_gateway,
        missing_in_ledger,
        amount_mismatches,
        status_mismatches
    )


# ============================================================
# LOAD DATA
# ============================================================

ledger = pd.read_csv("ledger.csv")
gateway = pd.read_csv("gateway_export.csv")
merchants = pd.read_csv("merchants.csv")

ledger["transaction_time"] = pd.to_datetime(
    ledger["transaction_time"]
)

# ============================================================
# HEADLINE SCORECARDS
# ============================================================

total_gmv = ledger["amount_inr"].sum()

success_rate = (
    (ledger["status"] == "captured").sum()
    / len(ledger)
) * 100

chargeback_ratio = (
    (ledger["status"] == "chargeback").sum()
    / len(ledger)
) * 100

# ---------------------------------------
# Match Rate Definition
# ---------------------------------------

merged_match = pd.merge(
    ledger[["transaction_id", "amount_inr", "status"]],
    gateway[["transaction_id", "amount_inr", "status"]],
    on="transaction_id",
    suffixes=("_ledger", "_gateway")
)

matched_count = (
    (merged_match["amount_inr_ledger"]
     == merged_match["amount_inr_gateway"])
    &
    (merged_match["status_ledger"]
     == merged_match["status_gateway"])
).sum()

match_rate = (
    matched_count / len(ledger)
) * 100

# ============================================================
# SAVE SCORECARD IMAGE
# ============================================================

fig = plt.figure(figsize=(14, 4))
fig.patch.set_facecolor("white")

plt.axis("off")

score_text = f"""
TOTAL GMV (INR): ₹{total_gmv:,.0f}

SUCCESS RATE: {success_rate:.2f}%

RECONCILIATION MATCH RATE: {match_rate:.2f}%

CHARGEBACK RATIO: {chargeback_ratio:.2f}%
"""

plt.text(
    0.05,
    0.5,
    score_text,
    fontsize=18,
    va="center"
)

plt.savefig(
    OUTPUT_DIR / "headline_scorecards.png",
    bbox_inches="tight"
)

plt.close()

# ============================================================
# TRENDS LAYER
# ============================================================

ledger["date"] = ledger["transaction_time"].dt.date

daily_gmv = (
    ledger
    .groupby("date")["amount_inr"]
    .sum()
)

daily_chargebacks = (
    ledger[ledger["status"] == "chargeback"]
    .groupby("date")
    .size()
)

fig, ax1 = plt.subplots(figsize=(14, 6))

ax1.plot(
    daily_gmv.index,
    daily_gmv.values,
    color="blue",
    linewidth=3,
    label="Daily GMV"
)

ax1.set_ylabel("GMV (INR)")

ax2 = ax1.twinx()

ax2.plot(
    daily_chargebacks.index,
    daily_chargebacks.values,
    color="red",
    linewidth=2,
    label="Chargebacks"
)

ax2.set_ylabel("Chargeback Count")

plt.title(
    "Daily GMV and Chargebacks"
)

plt.savefig(
    OUTPUT_DIR / "daily_trends.png",
    bbox_inches="tight"
)

plt.close()

# ============================================================
# BREAKDOWN LAYER
# ============================================================

# BY PAYMENT METHOD

payment_breakdown = (
    ledger.groupby("payment_method")["amount_inr"]
    .sum()
    .sort_values(ascending=False)
)

plt.figure(figsize=(8, 5))

sns.barplot(
    x=payment_breakdown.index,
    y=payment_breakdown.values
)

plt.title("GMV by Payment Method")
plt.ylabel("GMV (INR)")
plt.xlabel("Payment Method")

plt.savefig(
    OUTPUT_DIR / "gmv_by_payment_method.png",
    bbox_inches="tight"
)

plt.close()

# -------------------------------------------------
# MERCHANT CATEGORY BREAKDOWN
# -------------------------------------------------

ledger_merchants = ledger.merge(
    merchants,
    on="merchant_id",
    how="left"
)

category_breakdown = (
    ledger_merchants
    .groupby("category")["amount_inr"]
    .sum()
    .sort_values(ascending=False)
)

plt.figure(figsize=(10, 5))

sns.barplot(
    x=category_breakdown.index,
    y=category_breakdown.values
)

plt.xticks(rotation=45)

plt.title(
    "GMV by Merchant Category"
)

plt.ylabel("GMV (INR)")
plt.xlabel("Category")

plt.savefig(
    OUTPUT_DIR / "gmv_by_category.png",
    bbox_inches="tight"
)

plt.close()

# ============================================================
# DETAILS LAYER
# ============================================================

merchant_stats = (
    ledger.groupby("merchant_id")
    .agg(
        transaction_count=("transaction_id", "count"),
        chargebacks=("status",
                     lambda x: (x == "chargeback").sum())
    )
    .reset_index()
)

merchant_stats["chargeback_ratio"] = (
    merchant_stats["chargebacks"]
    / merchant_stats["transaction"])
