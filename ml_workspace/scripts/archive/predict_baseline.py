import pandas as pd
import joblib


# =========================
# 1. Load Final Model
# =========================

model = joblib.load("models/final_baseline_model.pkl")
feature_names = joblib.load("models/final_baseline_features.pkl")


# =========================
# 2. Sample Input
# =========================
# This represents one source code file after metric extraction.

sample_file = {
    "nosi": 12,
    "dit": 2,
    "cbo": 8,
    "rfc": 20,
    "loc": 150,
    "comparisonsQty": 10,
    "returnQty": 5,
    "wmc": 12,
    "lcom": 4,
    "totalMethods": 8
}


# =========================
# 3. Convert to DataFrame
# =========================

X_new = pd.DataFrame([sample_file])

# Make sure column order matches training features
X_new = X_new[feature_names]


# =========================
# 4. Predict
# =========================

prediction = model.predict(X_new)[0]
probability = model.predict_proba(X_new)[0][1]


# =========================
# 5. Display Result
# =========================

print("Prediction Result")
print("=================")

if prediction == 1:
    print("Prediction: Defective")
else:
    print("Prediction: Non-defective")

print("Defect Risk Probability:", round(probability, 4))