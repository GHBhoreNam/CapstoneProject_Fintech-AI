import pandas as pd
import numpy as np

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import calinski_harabasz_score

# --------------------------------------------------
# Load data
# --------------------------------------------------

df = pd.read_csv("credit_applicants.csv")

# --------------------------------------------------
# Feature engineering
# --------------------------------------------------

df["is_thin_file"] = df["credit_bureau_score"].isna().astype(int)

# Median imputation
median_score = df["credit_bureau_score"].median()
df["credit_bureau_score"] = df["credit_bureau_score"].fillna(median_score)

# --------------------------------------------------
# One-hot encode employment_type
# --------------------------------------------------

X = pd.get_dummies(
    df.drop(columns=["default", "applicant_id"]),
    columns=["employment_type"],
    drop_first=False
)

# --------------------------------------------------
# Standardize features
# --------------------------------------------------

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# --------------------------------------------------
# Choose k using Calinski-Harabasz Index
# --------------------------------------------------

results = []

for k in range(2, 11):
    km = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=10
    )

    labels = km.fit_predict(X_scaled)

    ch_score = calinski_harabasz_score(
        X_scaled,
        labels
    )

    results.append((k, ch_score))

scores_df = pd.DataFrame(
    results,
    columns=["k", "calinski_harabasz"]
)

best_k = scores_df.loc[
    scores_df["calinski_harabasz"].idxmax(),
    "k"
]

print("\nCalinski-Harabasz Scores")
print(scores_df)

print(f"\nSelected k = {best_k}")

# --------------------------------------------------
# Fit final KMeans
# --------------------------------------------------

kmeans = KMeans(
    n_clusters=int(best_k),
    random_state=42,
    n_init=10
)

df["cluster"] = kmeans.fit_predict(X_scaled)

# --------------------------------------------------
# Cluster summary
# --------------------------------------------------

cluster_summary = (
    df.groupby("cluster")
      .agg(
          applicants=("cluster", "size"),
          defaults=("default", "sum"),
          default_rate=("default", "mean"),
          avg_income=("monthly_income_inr", "mean"),
          avg_bureau_score=("credit_bureau_score", "mean"),
          avg_utilization=("credit_utilization_ratio", "mean")
      )
      .reset_index()
)

cluster_summary["default_rate"] *= 100

print("\nCluster Summary")
print(cluster_summary.round(2))

# --------------------------------------------------
# Compare cluster default rates
# --------------------------------------------------

overall_default_rate = df["default"].mean() * 100

print(
    f"\nOverall default rate: "
    f"{overall_default_rate:.2f}%"
)

cluster_summary["lift_vs_overall"] = (
    cluster_summary["default_rate"]
    / overall_default_rate
)

print(
    "\nDefault-rate lift versus overall portfolio:"
)
print(
    cluster_summary[
        ["cluster",
         "default_rate",
         "lift_vs_overall"]
    ].round(2)
)

# --------------------------------------------------
# Highest-risk cluster
# --------------------------------------------------

highest_risk_cluster = cluster_summary.loc[
    cluster_summary["default_rate"].idxmax()
]

print("\nHighest-risk cluster:")
print(highest_risk_cluster)
