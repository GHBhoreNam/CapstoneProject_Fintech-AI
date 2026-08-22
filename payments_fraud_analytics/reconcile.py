import pandas as pd


def reconcile_payments(ledger_df, gateway_df):
    """
    Returns:
        missing_in_gateway
        missing_in_ledger
        amount_mismatches
        status_mismatches
    """

    # Set-based reconciliation
    ledger_ids = set(ledger_df["transaction_id"])
    gateway_ids = set(gateway_df["transaction_id"])

    missing_in_gateway = ledger_df[
        ledger_df["transaction_id"].isin(ledger_ids - gateway_ids)
    ].copy()

    missing_in_ledger = gateway_df[
        gateway_df["transaction_id"].isin(gateway_ids - ledger_ids)
    ].copy()

    # Pairwise comparison using merge
    common = pd.merge(
        ledger_df,
        gateway_df,
        on="transaction_id",
        suffixes=("_ledger", "_gateway")
    )

    amount_mismatches = common[
        common["amount_inr_ledger"] != common["amount_inr_gateway"]
    ].copy()

    amount_mismatches["amount_difference"] = (
        amount_mismatches["amount_inr_gateway"]
        - amount_mismatches["amount_inr_ledger"]
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


if __name__ == "__main__":
    ledger_df = pd.read_csv("ledger.csv")
    gateway_df = pd.read_csv("gateway_export.csv")

    (
        missing_in_gateway,
        missing_in_ledger,
        amount_mismatches,
        status_mismatches
    ) = reconcile_payments(ledger_df, gateway_df)

    print("Missing in gateway:", len(missing_in_gateway))
    print("Missing in ledger:", len(missing_in_ledger))
    print("Amount mismatches:", len(amount_mismatches))
    print("Status mismatches:", len(status_mismatches))

    print("\nSample amount mismatches:")
    print(
        amount_mismatches[
            [
                "transaction_id",
                "amount_inr_ledger",
                "amount_inr_gateway",
                "amount_difference"
            ]
        ].head()
    )

    print("\nSample status mismatches:")
    print(
        status_mismatches[
            [
                "transaction_id",
                "status_ledger",
                "status_gateway"
            ]
        ].head()
    )
