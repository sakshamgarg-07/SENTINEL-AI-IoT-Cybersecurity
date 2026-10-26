"""Train Isolation Forest using the real TON_IoT Weather dataset.

Methodology:
- Reads the verified TON_IoT Weather CSV (650,242 rows).
- Features: temperature, pressure, humidity.
- The model is trained EXCLUSIVELY on normal telemetry (label=0).
- Normal records are split into training (80%) and held-out test (20%).
- Evaluation is performed on unseen data (held-out normal + all attack records).
- No data leakage: training records are never used during evaluation.
"""
from datetime import datetime
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split

from config import MODEL_FILE, REAL_DATASET

FEATURES = ["temperature", "pressure", "humidity"]


def load_dataset():
    path = Path(REAL_DATASET)
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {path}. Place TON_IoT_Weather.csv in the data directory."
        )

    df = pd.read_csv(path)
    # Strip whitespace from column headers
    df.columns = df.columns.str.strip()

    col_lookup = {c.lower(): c for c in df.columns}

    # Verify required features
    missing_features = [f for f in FEATURES if f not in col_lookup]
    if missing_features:
        raise ValueError(
            f"Dataset missing required feature columns: {missing_features}. Available: {list(df.columns)}"
        )

    # Identify label column
    label_col = None
    for cand in ["label", "lable"]:
        if cand in col_lookup:
            label_col = col_lookup[cand]
            break
    if not label_col:
        raise ValueError("Could not find a label column (expected 'label').")

    # Identify attack type column (optional)
    type_col = col_lookup.get("type", None)

    rename_map = {col_lookup[f]: f for f in FEATURES}
    rename_map[label_col] = "label"
    if type_col:
        rename_map[type_col] = "attack_type"
    df = df.rename(columns=rename_map)

    # Validate label values
    df["label"] = pd.to_numeric(df["label"], errors="coerce")
    if df["label"].isna().any():
        raise ValueError("Label column contains missing or non-numeric values.")

    unique_labels = set(df["label"].unique())
    if not unique_labels.issubset({0, 1}):
        raise ValueError(
            f"Unexpected label values found: {unique_labels}. Expected binary labels [0, 1]."
        )

    # Validate numeric features
    for f in FEATURES:
        df[f] = pd.to_numeric(df[f], errors="coerce")
    df = df.dropna(subset=FEATURES + ["label"])

    return df


def main():
    print(f"Loading dataset from: {REAL_DATASET}")
    df = load_dataset()
    print(f"Loaded {len(df):,} total valid records.")

    normal_df = df[df["label"].astype(int) == 0].copy()
    attack_df = df[df["label"].astype(int) == 1].copy()

    print(f"Total Normal records (label=0): {len(normal_df):,}")
    print(f"Total Attack records (label=1): {len(attack_df):,}")

    if len(normal_df) < 1000:
        raise ValueError("Insufficient normal records for training.")
    if len(attack_df) == 0:
        raise ValueError("No attack records found for evaluation.")

    # 1. Leak-free split: Split normal records into train (80%) and held-out test (20%)
    train_normal, test_normal = train_test_split(
        normal_df, test_size=0.20, random_state=42
    )

    # 2. Assemble unseen test set: held-out normal + all attack records
    test_df = pd.concat([test_normal, attack_df], ignore_index=True)

    print(f"\n--- Data Partitioning (Leak-Free) ---")
    print(f"Normal Training Set: {len(train_normal):,} records (used ONLY for fitting)")
    print(f"Held-Out Normal Test: {len(test_normal):,} records (never seen during fitting)")
    print(f"Attack Test Set:      {len(attack_df):,} records (never seen during fitting)")
    print(f"Total Unseen Test Set: {len(test_df):,} records")

    # 3. Model Configuration
    # - contamination='auto': Appropriate because training set contains 100% normal data.
    #   Using a fixed rate (e.g. 0.05) would force an artificial 5% false alarm rate on clean baseline data.
    # - max_samples=10000: Subsamples 10,000 points per tree to prevent tree swamping,
    #   drastically reduce training memory/time, and provide robust isolation boundaries.
    max_samples = 10000
    n_estimators = 150
    model = IsolationForest(
        n_estimators=n_estimators,
        max_samples=max_samples,
        contamination="auto",
        random_state=42,
        n_jobs=-1,
    )

    print(f"\nTraining Isolation Forest on {len(train_normal):,} normal samples...")
    model.fit(train_normal[FEATURES])
    print("Model training completed.")

    # 4. Evaluation on UNSEEN test set
    # Isolation Forest: -1 = Anomaly/Outlier, +1 = Inlier/Normal
    raw_pred = model.predict(test_df[FEATURES])
    y_pred = (raw_pred == -1).astype(int)  # 1 for predicted attack, 0 for predicted normal
    y_true = (test_df["label"].astype(int) == 1).astype(int)

    # Anomaly scores: decision_function yields higher values for inliers (normal).
    # We negate it so higher values indicate higher anomaly/attack probability for ROC-AUC.
    anomaly_scores = -model.decision_function(test_df[FEATURES])
    auc_score = roc_auc_score(y_true, anomaly_scores)

    # 5. Display Evaluation Results
    print("\n================ EVALUATION ON UNSEEN TEST DATA ================")
    print("Confusion Matrix [rows=True, columns=Predicted]:")
    print("                 Predicted Normal (0)   Predicted Attack (1)")
    cm = confusion_matrix(y_true, y_pred)
    print(f"Actual Normal:   {cm[0][0]:>15,}        {cm[0][1]:>15,}")
    print(f"Actual Attack:   {cm[1][0]:>15,}        {cm[1][1]:>15,}")

    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, target_names=["Normal (0)", "Attack (1)"], zero_division=0))
    print(f"ROC-AUC Score: {auc_score:.4f}")
    print("================================================================")

    # 6. Save Model Artifact
    # Retain exact compatibility with mqtt_subscriber.py: expects a dict with "model" and "features"
    model_path = Path(MODEL_FILE)
    model_path.parent.mkdir(parents=True, exist_ok=True)

    model_payload = {
        "model": model,
        "features": FEATURES,
        "dataset": "TON_IoT_Weather",
        "algorithm": "IsolationForest",
        "contamination": "auto",
        "max_samples": max_samples,
        "n_estimators": n_estimators,
        "metrics": {
            "roc_auc": float(auc_score),
            "test_normal_records": len(test_normal),
            "test_attack_records": len(attack_df),
        },
        "trained_at": datetime.now().isoformat(),
    }
    joblib.dump(model_payload, model_path)
    print(f"\nModel saved successfully to: {model_path}")


if __name__ == "__main__":
    main()

