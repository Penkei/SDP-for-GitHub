import os
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
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

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier


# =========================
# 1. Load GitHub Dataset
# =========================

df = pd.read_csv("data/github_defect_dataset.csv")

print("Dataset shape:", df.shape)

if df.empty:
    raise ValueError("Dataset is empty. Please build github_defect_dataset.csv first.")

print("\nLabel distribution:")
print(df["defect"].value_counts())


# =========================
# 2. Data Cleaning
# =========================

df = df.drop_duplicates()
df = df.dropna(subset=["defect"])
df = df.fillna(0)
df["defect"] = df["defect"].astype(int)

# Keep only rows with valid labels
df = df[df["defect"].isin([0, 1])]

print("\nAfter cleaning:")
print("Dataset shape:", df.shape)
print(df["defect"].value_counts())


# =========================
# 3. Feature Selection
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

missing_features = [feature for feature in selected_features if feature not in df.columns]

if missing_features:
    raise ValueError(f"Missing features in GitHub dataset: {missing_features}")

X = df[selected_features]
y = df["defect"]


# =========================
# 4. Check Label Count
# =========================

if y.nunique() < 2:
    raise ValueError(
        "Only one label exists in the dataset. Need both defect = 0 and defect = 1 before training."
    )


# =========================
# 5. Train-Test Split
# =========================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


# =========================
# 6. Handle Imbalance
# =========================

neg_count = (y_train == 0).sum()
pos_count = (y_train == 1).sum()

scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1

print("\nTraining label count:")
print("Non-defective:", neg_count)
print("Defective:", pos_count)
print("scale_pos_weight:", round(scale_pos_weight, 4))


# =========================
# 7. Define Models
# =========================

models = {
    "Logistic Regression": Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=42
        ))
    ]),

    "Random Forest": RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced"
    ),

    "XGBoost": XGBClassifier(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
        random_state=42
    )
}


# =========================
# 8. Train and Evaluate
# =========================

results = []

best_model = None
best_model_name = None
best_f1 = -1

for model_name, model in models.items():
    print("\n==============================")
    print("Training:", model_name)
    print("==============================")

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    if hasattr(model, "predict_proba"):
        y_prob = model.predict_proba(X_test)[:, 1]
    else:
        y_prob = y_pred

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_prob)
    pr_auc = average_precision_score(y_test, y_prob)

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, digits=3, zero_division=0))

    print("Accuracy:", round(accuracy, 4))
    print("Precision:", round(precision, 4))
    print("Recall:", round(recall, 4))
    print("F1-score:", round(f1, 4))
    print("ROC-AUC:", round(roc_auc, 4))
    print("PR-AUC:", round(pr_auc, 4))

    results.append({
        "model": model_name,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc
    })

    if f1 > best_f1:
        best_f1 = f1
        best_model = model
        best_model_name = model_name


# =========================
# 9. Save Results
# =========================

os.makedirs("models", exist_ok=True)
os.makedirs("results", exist_ok=True)

results_df = pd.DataFrame(results)
results_df.to_csv("results/github_model_comparison.csv", index=False)

joblib.dump(best_model, "models/github_defect_prediction_model.pkl")
joblib.dump(selected_features, "models/github_model_features.pkl")

print("\n==============================")
print("Best GitHub-trained model:", best_model_name)
print("Best F1-score:", round(best_f1, 4))
print("Saved model to: models/github_defect_prediction_model.pkl")
print("Saved features to: models/github_model_features.pkl")
print("Saved comparison to: results/github_model_comparison.csv")