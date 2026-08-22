def reconcile_payments(ledger_df, gateway_df):
    ledger_ids = set(ledger_df["transaction_id"])
    gateway_ids = set(gateway_df["transaction_id"])

    missing_in_gateway = ledger_df[
        ledger_df["transaction_id"].isin(ledger_ids - gateway_ids)
    ]

    missing_in_ledger = gateway_df[
        gateway_df["transaction_id"].isin(gateway_ids - ledger_ids)
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
        status_mismatches,
    )
