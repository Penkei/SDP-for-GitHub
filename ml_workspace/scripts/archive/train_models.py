import pandas as pd
import joblib
import os


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
# 1. Load Dataset
# =========================

df = pd.read_csv("data/baseline.csv")

print("Dataset shape:", df.shape)
print("Columns:", df.columns.tolist())
print("\nDefect label distribution:")
print(df["defect"].value_counts())


# =========================
# 2. Data Cleaning
# =========================

# Remove duplicate rows
df = df.drop_duplicates()

# Remove rows without target label
df = df.dropna(subset=["defect"])

# Fill missing feature values with 0
df = df.fillna(0)

# Make sure target is integer
df["defect"] = df["defect"].astype(int)


# =========================
# 3. Feature / Target Split
# =========================

# SHA is only an identifier, not a useful ML feature
X = df.drop(columns=["SHA", "defect"])
y = df["defect"]

feature_names = X.columns.tolist()

print("\nSelected features:")
for feature in feature_names:
    print("-", feature)


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
# 5. Define Models
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
        n_estimators=200,
        random_state=42,
        class_weight="balanced"
    ),

    "XGBoost": XGBClassifier(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=42
    )
}


# =========================
# 6. Train and Evaluate
# =========================

results = []

best_model = None
best_model_name = None
best_f1 = 0

for model_name, model in models.items():
    print("\n==============================")
    print("Training:", model_name)
    print("==============================")

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_prob)
    pr_auc = average_precision_score(y_test, y_prob)

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
# 7. Save Results
# =========================

os.makedirs("models", exist_ok=True)
os.makedirs("results", exist_ok=True)

results_df = pd.DataFrame(results)
results_df.to_csv("results/model_comparison.csv", index=False)

joblib.dump(best_model, "models/final_defect_prediction_model.pkl")
joblib.dump(feature_names, "models/feature_names.pkl")

print("\n==============================")
print("Best Model:", best_model_name)
print("Best F1-score:", round(best_f1, 4))
print("Saved model to: models/final_defect_prediction_model.pkl")
print("Saved feature names to: models/feature_names.pkl")
print("Saved comparison result to: results/model_comparison.csv")

# =========================
# 8. Save Feature Importance
# =========================

if best_model_name == "Random Forest":
    importances = best_model.feature_importances_

elif best_model_name == "XGBoost":
    importances = best_model.feature_importances_

else:
    classifier = best_model.named_steps["classifier"]
    importances = abs(classifier.coef_[0])

feature_importance_df = pd.DataFrame({
    "feature": feature_names,
    "importance": importances
}).sort_values(by="importance", ascending=False)

feature_importance_df.to_csv("results/feature_importance.csv", index=False)

print("\nSaved feature importance to: results/feature_importance.csv")