import pandas as pd
import joblib
import os

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    classification_report
)

# =========================
# 1. Load Dataset
# =========================

df = pd.read_csv("data/baseline.csv")

# =========================
# 2. Data Cleaning
# =========================

df = df.drop_duplicates()
df = df.dropna(subset=["defect"])
df = df.fillna(0)
df["defect"] = df["defect"].astype(int)

# =========================
# 3. Use Top 10 Selected Features
# =========================

selected_features = [
    "nosi",
    "dit",
    "cbo",
    "rfc",
    "loc",
    "comparisonsQty",
    "returnQty",
    "wmc",
    "lcom",
    "totalMethods"
]

X = df[selected_features]
y = df["defect"]

# =========================
# 4. Train-Test Split
# =========================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# =========================
# 5. Train Logistic Regression
# =========================

model = Pipeline([
    ("scaler", StandardScaler()),
    ("classifier", LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        random_state=42
    ))
])

model.fit(X_train, y_train)

# =========================
# 6. Evaluate
# =========================

y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
roc_auc = roc_auc_score(y_test, y_prob)
pr_auc = average_precision_score(y_test, y_prob)

print("Selected Feature Model Result")
print("=============================")

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_pred, digits=3))

print("Accuracy:", round(accuracy, 4))
print("Precision:", round(precision, 4))
print("Recall:", round(recall, 4))
print("F1-score:", round(f1, 4))
print("ROC-AUC:", round(roc_auc, 4))
print("PR-AUC:", round(pr_auc, 4))

# =========================
# 7. Save Model and Result
# =========================

os.makedirs("models", exist_ok=True)
os.makedirs("results", exist_ok=True)

result_df = pd.DataFrame([{
    "model": "Logistic Regression - Top 10 Features",
    "accuracy": accuracy,
    "precision": precision,
    "recall": recall,
    "f1": f1,
    "roc_auc": roc_auc,
    "pr_auc": pr_auc
}])

result_df.to_csv("results/selected_feature_model_result.csv", index=False)

joblib.dump(model, "models/selected_feature_logistic_model.pkl")
joblib.dump(selected_features, "models/selected_feature_names.pkl")

print("\nSaved model to: models/selected_feature_logistic_model.pkl")
print("Saved selected features to: models/selected_feature_names.pkl")
print("Saved result to: results/selected_feature_model_result.csv")