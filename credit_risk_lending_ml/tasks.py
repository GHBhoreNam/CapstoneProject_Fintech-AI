# ==========================================
# CREDIT DEFAULT MODELING PIPELINE
# ==========================================
# Steps:
# 1. Load data
# 2. Report default rate
# 3. Report bureau-score missing rate
# 4. Create is_thin_file flag
# 5. Train/test split (75/25, stratified, random_state=42)
# 6. Median imputation using TRAINING DATA ONLY
# 7. One-hot encode employment_type
# 8. Standardize numeric features
# 9. Train Logistic Regression and Random Forest
# 10. Evaluate using:
#       - Confusion Matrix
#       - Accuracy
#       - Precision
#       - Recall
#       - F1
#       - ROC Curve
#       - AUC
# ==========================================

import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import (
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_curve,
    roc_auc_score
)

import matplotlib.pyplot as plt

# =====================================================
# 1. LOAD DATA
# =====================================================

df = pd.read_csv("credit_applicants.csv")

print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")

# =====================================================
# 2. DEFAULT RATE
# =====================================================

default_rate = df["default"].mean() * 100

print("\nDEFAULT RATE")
print(f"{default_rate:.2f}%")

# =====================================================
# 3. MISSING BUREAU SCORE %
# =====================================================

missing_pct = (
    df["credit_bureau_score"]
    .isna()
    .mean()
    * 100
)

print("\nMISSING CREDIT_BUREAU_SCORE")
print(f"{missing_pct:.2f}%")

# =====================================================
# 4. CREATE THIN-FILE INDICATOR
# =====================================================

df["is_thin_file"] = (
    df["credit_bureau_score"]
    .isna()
    .astype(int)
)

# =====================================================
# 5. TRAIN / TEST SPLIT
# =====================================================

X = df.drop(columns=["default"])
y = df["default"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    stratify=y,
    random_state=42
)

print("\nTRAIN SIZE:", len(X_train))
print("TEST SIZE:", len(X_test))

print(
    "Train Default Rate:",
    round(y_train.mean() * 100, 2),
    "%"
)

print(
    "Test Default Rate:",
    round(y_test.mean() * 100, 2),
    "%"
)

# =====================================================
# 6. MEDIAN IMPUTATION
# TRAINING DATA ONLY
# =====================================================

training_median = (
    X_train["credit_bureau_score"]
    .median()
)

print("\nTRAINING MEDIAN CREDIT SCORE")
print(training_median)

X_train["credit_bureau_score"] = (
    X_train["credit_bureau_score"]
    .fillna(training_median)
)

X_test["credit_bureau_score"] = (
    X_test["credit_bureau_score"]
    .fillna(training_median)
)

# =====================================================
# 7. ONE-HOT ENCODE EMPLOYMENT TYPE
# =====================================================

X_train = pd.get_dummies(
    X_train,
    columns=["employment_type"],
    drop_first=False
)

X_test = pd.get_dummies(
    X_test,
    columns=["employment_type"],
    drop_first=False
)

# ensure identical columns

X_test = X_test.reindex(
    columns=X_train.columns,
    fill_value=0
)

# remove identifier from modeling

if "applicant_id" in X_train.columns:
    X_train = X_train.drop(columns=["applicant_id"])
    X_test = X_test.drop(columns=["applicant_id"])

# =====================================================
# 8. STANDARDIZE NUMERIC FEATURES
# FIT ON TRAIN ONLY
# =====================================================

scaler = StandardScaler()

X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# =====================================================
# 9. TRAIN MODELS
# =====================================================

models = {
    "Logistic Regression":
        LogisticRegression(
            max_iter=1000,
            random_state=42
        ),

    "Random Forest":
        RandomForestClassifier(
            n_estimators=300,
            random_state=42
        )
}

# =====================================================
# 10. EVALUATION
# =====================================================

results = []

plt.figure(figsize=(8, 6))

for name, model in models.items():

    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)

    y_prob = model.predict_proba(
        X_test_scaled
    )[:, 1]

    tn, fp, fn, tp = confusion_matrix(
        y_test,
        y_pred
    ).ravel()

    accuracy = accuracy_score(
        y_test,
        y_pred
    )

    precision = precision_score(
        y_test,
        y_pred,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        y_pred
    )

    f1 = f1_score(
        y_test,
        y_pred
    )

    auc = roc_auc_score(
        y_test,
        y_prob
    )

    results.append({
        "Model": name,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "TP": tp,
        "Accuracy": round(accuracy, 4),
        "Precision": round(precision, 4),
        "Recall": round(recall, 4),
        "F1": round(f1, 4),
        "AUC": round(auc, 4)
    })

    # ROC Curve

    fpr, tpr, _ = roc_curve(
        y_test,
        y_prob
    )

    plt.plot(
        fpr,
        tpr,
        label=f"{name} (AUC={auc:.3f})"
    )

# =====================================================
# COMPARISON TABLE
# =====================================================

comparison = pd.DataFrame(results)

print("\nMODEL COMPARISON")
print(comparison)

# =====================================================
# ROC CURVE
# =====================================================

plt.plot(
    [0, 1],
    [0, 1],
    linestyle="--",
    color="black"
)

plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve Comparison")
plt.legend()
plt.grid(True)

plt.show()

# =====================================================
# INDIVIDUAL CONFUSION MATRICES
# =====================================================

for row in results:

    print("\n" + "="*50)
    print(row["Model"])
    print("="*50)

    print(
        np.array([
            [row["TN"], row["FP"]],
            [row["FN"], row["TP"]]
        ])
    )
