# ==========================================================
# ISOLATION FOREST ANOMALY DETECTION ON TRANSACTION DATA
# ==========================================================
#
# Task:
# 1. Load txn_behaviour.csv
# 2. Select numeric behavioural features:
#       - txn_hour
#       - is_new_device
#       - txn_amount_inr
# 3. Standardize features
# 4. Run IsolationForest
#       contamination = 15 / 265 ≈ 0.0566
#       random_state = 42
# 5. Identify anomalies
# 6. Compare predictions against injected ground truth:
#       txn_id starts with "BTXNA"
# 7. Report:
#       - Total anomalies flagged
#       - Number of seeded anomalies detected
#       - Recall on seeded anomalies
#
# ==========================================================

import pandas as pd
import numpy as np

from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import confusion_matrix

# ==========================================================
# LOAD DATA
# ==========================================================

txn = pd.read_csv("txn_behaviour.csv")

print("Dataset Shape:", txn.shape)

# ==========================================================
# GROUND TRUTH ANOMALIES
# Injected anomalies have txn_id starting with BTXNA
# ==========================================================

txn["is_seeded_anomaly"] = (
    txn["txn_id"]
    .str.startswith("BTXNA")
    .astype(int)
)

num_seeded_anomalies = txn["is_seeded_anomaly"].sum()

print("\nSeeded Anomalies:", num_seeded_anomalies)

# ==========================================================
# SELECT NUMERIC BEHAVIOURAL FEATURES
# ==========================================================

feature_cols = [
    "txn_hour",
    "is_new_device",
    "txn_amount_inr"
]

X = txn[feature_cols]

# ==========================================================
# STANDARDIZE FEATURES
# ==========================================================

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)

# ==========================================================
# CONTAMINATION RATE
# ==========================================================

contamination_rate = 15 / 265

print(
    "\nContamination Rate:",
    round(contamination_rate, 4)
)

# ==========================================================
# ISOLATION FOREST
# ==========================================================

iso = IsolationForest(
    contamination=contamination_rate,
    random_state=42
)

iso.fit(X_scaled)

# ==========================================================
# PREDICTIONS
#
# IsolationForest output:
#   1  = normal
#  -1  = anomaly
# ==========================================================

txn["iforest_prediction"] = iso.predict(X_scaled)

txn["flagged_anomaly"] = (
    txn["iforest_prediction"] == -1
).astype(int)

# ==========================================================
# OVERALL RESULTS
# ==========================================================

total_flagged = txn["flagged_anomaly"].sum()

print("\nTotal Flagged as Anomalous:", total_flagged)

# ==========================================================
# RECALL AGAINST SEEDED GROUND TRUTH
# ==========================================================

seeded = txn["is_seeded_anomaly"] == 1

detected_seeded = txn.loc[
    seeded,
    "flagged_anomaly"
].sum()

recall = (
    detected_seeded
    / num_seeded_anomalies
)

print("\nRecall Check")
print("------------")
print("Seeded Anomalies:", num_seeded_anomalies)
print("Detected Seeded Anomalies:", detected_seeded)
print(f"Recall: {recall:.4f}")

# ==========================================================
# CONFUSION MATRIX
# (only meaningful because we know injected labels)
# ==========================================================

cm = confusion_matrix(
    txn["is_seeded_anomaly"],
    txn["flagged_anomaly"]
)

tn, fp, fn, tp = cm.ravel()

print("\nConfusion Matrix")
print(cm)

print("\nTN:", tn)
print("FP:", fp)
print("FN:", fn)
print("TP:", tp)

# ==========================================================
# SHOW DETECTED SEEDED ANOMALIES
# ==========================================================

detected_anomalies = txn[
    (txn["is_seeded_anomaly"] == 1) &
    (txn["flagged_anomaly"] == 1)
]

print("\nDetected Seeded Anomaly IDs")
print(
    detected_anomalies["txn_id"]
    .tolist()
)

# ==========================================================
# OPTIONAL SUMMARY TABLE
# ==========================================================

summary = pd.DataFrame({
    "Metric": [
        "Total Transactions",
        "Seeded Anomalies",
        "Flagged Anomalies",
        "Detected Seeded Anomalies",
        "Recall"
    ],
    "Value": [
        len(txn),
        num_seeded_anomalies,
        total_flagged,
        detected_seeded,
        round(recall, 4)
    ]
})

print("\nSummary")
print(summary)
