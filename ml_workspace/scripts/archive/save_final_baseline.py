import shutil

shutil.copy("models/selected_feature_logistic_model.pkl", "models/final_baseline_model.pkl")
shutil.copy("models/selected_feature_names.pkl", "models/final_baseline_features.pkl")

print("Final baseline model saved.")