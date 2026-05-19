import os
import json
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, train_test_split
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


RANDOM_STATE = 42

PROCESS_FEATURES_TO_COMPRESS = [
    "file_change_count",
    "file_bug_fix_count",
    "recent_file_change_count",
    "days_since_last_change",
    "last_change_lines_added",
    "last_change_lines_deleted",
    "last_change_churn",
    "last_change_file_count",
    "author_file_change_count",
]

PROCESS_FEATURE_CAPS = {
    "file_change_count": 50,
    "file_bug_fix_count": 20,
    "recent_file_change_count": 20,
    "days_since_last_change": 3650,
    "last_change_lines_added": 1000,
    "last_change_lines_deleted": 1000,
    "last_change_churn": 1500,
    "last_change_file_count": 30,
    "author_file_change_count": 30,
}


def transform_model_features(
    features_df: pd.DataFrame,
    transform_stats: dict = None
) -> pd.DataFrame:
    transformed_df = features_df.copy()

    for feature in PROCESS_FEATURES_TO_COMPRESS:
        if feature not in transformed_df.columns:
            continue

        cap_value = PROCESS_FEATURE_CAPS.get(feature)
        numeric_values = pd.to_numeric(transformed_df[feature], errors="coerce").fillna(0)
        numeric_values = numeric_values.clip(lower=0)

        if cap_value is not None:
            numeric_values = numeric_values.clip(upper=cap_value)

        transformed_df[feature] = np.log1p(numeric_values)

    if transform_stats:
        transformed_df = scale_process_features(transformed_df, transform_stats)

    return transformed_df


def fit_process_scaling_stats(features_df: pd.DataFrame) -> dict:
    process_scaling = {}

    for feature in PROCESS_FEATURES_TO_COMPRESS:
        if feature not in features_df.columns:
            continue

        mean_value = float(features_df[feature].mean())
        std_value = float(features_df[feature].std(ddof=0))

        process_scaling[feature] = {
            "mean": mean_value,
            "std": std_value if std_value > 0 else 1.0,
        }

    return {
        "process_metric_scaling": process_scaling
    }


def scale_process_features(features_df: pd.DataFrame, transform_stats: dict) -> pd.DataFrame:
    transformed_df = features_df.copy()
    process_scaling = transform_stats.get("process_metric_scaling", {})

    for feature, stats in process_scaling.items():
        if feature not in transformed_df.columns:
            continue

        transformed_df[feature] = (
            transformed_df[feature] - float(stats.get("mean", 0))
        ) / (float(stats.get("std", 1)) or 1)

    return transformed_df


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
    "totalMethods",
    "file_change_count",
    "file_bug_fix_count",
    "recent_file_change_count",
    "days_since_last_change",
    "last_change_lines_added",
    "last_change_lines_deleted",
    "last_change_churn",
    "last_change_file_count",
    "author_file_change_count"
]

missing_features = [feature for feature in selected_features if feature not in df.columns]

if missing_features:
    raise ValueError(f"Missing features in GitHub dataset: {missing_features}")

X_raw = df[selected_features]
y = df["defect"]

print("\nApplied process metric compression:")
for feature in PROCESS_FEATURES_TO_COMPRESS:
    print(f"- {feature}: cap at {PROCESS_FEATURE_CAPS[feature]}, log1p, then train-set standard scaling")


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

X_train_full_raw, X_test_raw, y_train_full, y_test = train_test_split(
    X_raw,
    y,
    test_size=0.2,
    random_state=RANDOM_STATE,
    stratify=y
)

X_train_raw, X_valid_raw, y_train, y_valid = train_test_split(
    X_train_full_raw,
    y_train_full,
    test_size=0.2,
    random_state=RANDOM_STATE,
    stratify=y_train_full
)

X_train_full_compressed = transform_model_features(X_train_full_raw)
feature_transform_stats = fit_process_scaling_stats(X_train_full_compressed)

X_train_full = transform_model_features(X_train_full_raw, feature_transform_stats)
X_test = transform_model_features(X_test_raw, feature_transform_stats)
X_train = transform_model_features(X_train_raw, feature_transform_stats)
X_valid = transform_model_features(X_valid_raw, feature_transform_stats)


# =========================
# 6. Handle Imbalance
# =========================

neg_count = (y_train_full == 0).sum()
pos_count = (y_train_full == 1).sum()

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
            max_iter=3000,
            class_weight="balanced",
            random_state=RANDOM_STATE
        ))
    ]),

    "Random Forest": RandomForestClassifier(
        random_state=RANDOM_STATE,
        class_weight="balanced"
    ),

    "XGBoost": XGBClassifier(
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
        random_state=RANDOM_STATE
    )
}

param_distributions = {
    "Logistic Regression": {
        "classifier__C": [0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10],
        "classifier__solver": ["lbfgs", "liblinear"]
    },
    "Random Forest": {
        "n_estimators": [200, 300, 500, 700],
        "max_depth": [None, 6, 10, 14, 20],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
        "max_features": ["sqrt", "log2", None]
    },
    "XGBoost": {
        "n_estimators": [200, 300, 500],
        "learning_rate": [0.01, 0.03, 0.05, 0.08, 0.1],
        "max_depth": [3, 4, 5, 6],
        "subsample": [0.75, 0.85, 1.0],
        "colsample_bytree": [0.75, 0.85, 1.0],
        "min_child_weight": [1, 3, 5],
        "gamma": [0, 0.1, 0.3]
    }
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)


def get_probabilities(model, features):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(features)[:, 1]

    return model.predict(features)


def find_best_threshold(y_true, y_prob):
    best_threshold = 0.5
    best_f1 = -1

    for threshold in np.arange(0.25, 0.76, 0.01):
        y_pred = (y_prob >= threshold).astype(int)
        score = f1_score(y_true, y_pred, zero_division=0)

        if score > best_f1:
            best_f1 = score
            best_threshold = threshold

    return round(float(best_threshold), 2), best_f1


def evaluate_model(model, threshold):
    y_prob = get_probabilities(model, X_test)
    y_pred = (y_prob >= threshold).astype(int)

    return {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, y_prob),
        "pr_auc": average_precision_score(y_test, y_prob),
        "confusion_matrix": confusion_matrix(y_test, y_pred),
        "classification_report": classification_report(
            y_test,
            y_pred,
            digits=3,
            zero_division=0
        )
    }


def extract_feature_importance(model, feature_names):
    estimator = model

    if hasattr(model, "named_steps"):
        estimator = model.named_steps.get("classifier", model)

    if hasattr(estimator, "feature_importances_"):
        importance = estimator.feature_importances_
    elif hasattr(estimator, "coef_"):
        importance = np.abs(estimator.coef_[0])
    else:
        importance = np.zeros(len(feature_names))

    total = importance.sum()

    if total > 0:
        importance = importance / total

    return pd.DataFrame({
        "feature": feature_names,
        "importance": importance
    }).sort_values(by="importance", ascending=False)


# =========================
# 8. Train and Evaluate
# =========================

results = []

best_model = None
best_model_name = None
best_f1 = -1
best_prediction_threshold = 0.5
best_evaluation = None

for model_name, model in models.items():
    print("\n==============================")
    print("Training:", model_name)
    print("==============================")

    search = RandomizedSearchCV(
        estimator=model,
        param_distributions=param_distributions[model_name],
        n_iter=15,
        scoring="f1",
        cv=cv,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=1
    )

    search.fit(X_train, y_train)

    tuned_model = search.best_estimator_
    valid_prob = get_probabilities(tuned_model, X_valid)
    model_threshold, validation_f1 = find_best_threshold(y_valid, valid_prob)

    tuned_model.fit(X_train_full, y_train_full)

    evaluation = evaluate_model(tuned_model, model_threshold)

    print("\nConfusion Matrix:")
    print(evaluation["confusion_matrix"])

    print("\nClassification Report:")
    print(evaluation["classification_report"])

    print("Best params:", search.best_params_)
    print("Optimized threshold:", model_threshold)
    print("Validation F1 at threshold:", round(validation_f1, 4))
    print("Accuracy:", round(evaluation["accuracy"], 4))
    print("Precision:", round(evaluation["precision"], 4))
    print("Recall:", round(evaluation["recall"], 4))
    print("F1-score:", round(evaluation["f1"], 4))
    print("ROC-AUC:", round(evaluation["roc_auc"], 4))
    print("PR-AUC:", round(evaluation["pr_auc"], 4))

    results.append({
        "model": model_name,
        "best_params": search.best_params_,
        "threshold": model_threshold,
        "validation_f1": validation_f1,
        "accuracy": evaluation["accuracy"],
        "precision": evaluation["precision"],
        "recall": evaluation["recall"],
        "f1": evaluation["f1"],
        "roc_auc": evaluation["roc_auc"],
        "pr_auc": evaluation["pr_auc"]
    })

    if evaluation["f1"] > best_f1:
        best_f1 = evaluation["f1"]
        best_model = tuned_model
        best_model_name = model_name
        best_prediction_threshold = model_threshold
        best_evaluation = evaluation


# =========================
# 9. Save Results
# =========================

os.makedirs("models", exist_ok=True)
os.makedirs("results", exist_ok=True)

results_df = pd.DataFrame(results)
results_df["best_params"] = results_df["best_params"].apply(
    lambda params: json.dumps(params)
)
results_df.to_csv("results/github_model_comparison.csv", index=False)

feature_importance_df = extract_feature_importance(best_model, selected_features)
feature_importance_df.to_csv("results/github_feature_importance.csv", index=False)
feature_importance_df.head(10).to_csv("results/github_top_10_features.csv", index=False)

if best_evaluation is not None:
    confusion_matrix_df = pd.DataFrame(
        best_evaluation["confusion_matrix"],
        index=["actual_non_defective", "actual_defective"],
        columns=["predicted_non_defective", "predicted_defective"]
    )
    confusion_matrix_df.to_csv("results/github_confusion_matrix.csv")

    with open("results/github_classification_report.txt", "w", encoding="utf-8") as file:
        file.write(best_evaluation["classification_report"])

joblib.dump(best_model, "models/github_defect_prediction_model.pkl")
joblib.dump(selected_features, "models/github_model_features.pkl")
joblib.dump(best_prediction_threshold, "models/github_prediction_threshold.pkl")
joblib.dump(feature_transform_stats, "models/github_feature_transform_stats.pkl")

metadata = {
    "best_model_name": best_model_name,
    "best_f1": best_f1,
    "prediction_threshold": best_prediction_threshold,
    "selected_features": selected_features,
    "random_state": RANDOM_STATE,
    "optimization": "RandomizedSearchCV with 5-fold StratifiedKFold and validation threshold tuning",
    "feature_transformations": {
        "process_metric_compression": {
            "method": "clip raw value to configured cap, apply log1p, then standard-scale process metrics using training-set mean/std",
            "reason": "Reduce dominance of large process-history counts such as files changed together and place process metrics on a more comparable scale",
            "caps": PROCESS_FEATURE_CAPS
        },
        "process_metric_scaling": {
            "method": "standard scaling after compression",
            "stats_source": "training split only",
            "stats": feature_transform_stats["process_metric_scaling"]
        }
    },
    "feature_groups": {
        "static_code_metrics": [
            "nosi", "dit", "cbo", "rfc", "loc",
            "comparisonsQty", "returnQty", "wmc", "lcom", "totalMethods"
        ],
        "process_metrics": [
            "file_change_count", "file_bug_fix_count",
            "recent_file_change_count", "days_since_last_change",
            "last_change_lines_added", "last_change_lines_deleted",
            "last_change_churn", "last_change_file_count",
            "author_file_change_count"
        ]
    }
}

with open("results/github_training_metadata.json", "w", encoding="utf-8") as file:
    json.dump(metadata, file, indent=2)

print("\n==============================")
print("Best GitHub-trained model:", best_model_name)
print("Best F1-score:", round(best_f1, 4))
print("Saved model to: models/github_defect_prediction_model.pkl")
print("Saved features to: models/github_model_features.pkl")
print("Saved threshold to: models/github_prediction_threshold.pkl")
print("Saved feature transform stats to: models/github_feature_transform_stats.pkl")
print("Saved comparison to: results/github_model_comparison.csv")
print("Saved feature importance to: results/github_feature_importance.csv")
print("Saved metadata to: results/github_training_metadata.json")
print("Saved confusion matrix to: results/github_confusion_matrix.csv")
print("Saved classification report to: results/github_classification_report.txt")
