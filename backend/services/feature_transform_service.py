import numpy as np
import pandas as pd


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


def transform_model_features(features_df: pd.DataFrame) -> pd.DataFrame:
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

    return transformed_df
