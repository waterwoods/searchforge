#!/usr/bin/env python3
"""
eval_approval_score_ml.py - Evaluate ML ApprovalScore Model Against Teacher

This script compares the trained ML approval model against the rule-based teacher
and runs basic monotonicity sanity checks. It does NOT modify any runtime APIs.

Usage:
    python experiments/eval_approval_score_ml.py \
        --data-path data/approval_distill_v1.csv \
        --model-path ml_models/approval_score_logreg_v1.joblib \
        --test-size 0.2 \
        --random-seed 42
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ============================================================================
# Feature Preparation (must match train_approval_score_ml.py exactly)
# ============================================================================

def prepare_features_and_labels(
    df: pd.DataFrame,
) -> Tuple[np.ndarray, np.ndarray, list]:
    """
    Prepare feature matrix X and label vector y from DataFrame.
    
    This function must match the implementation in train_approval_score_ml.py
    exactly to ensure consistent feature preprocessing.
    
    Args:
        df: DataFrame with training samples
    
    Returns:
        Tuple of (X, y, feature_names)
        - X: Feature matrix (n_samples, n_features)
        - y: Label vector (n_samples,) with binary labels (0 or 1)
        - feature_names: List of feature names
    """
    # Feature columns (primitive features and ratios only)
    feature_cols = [
        "income_monthly",
        "other_debt_monthly",
        "home_price",
        "down_payment_pct",
        "interest_rate",
        "loan_term_years",
        "ltv",
        "dti",
        "payment_to_income",
        "cash_buffer_ratio",
    ]
    
    # Categorical features (state, zip_code) - encode them
    categorical_cols = ["state", "zip_code"]
    
    # Extract numeric features
    X_numeric = df[feature_cols].values
    
    # Encode categorical features
    label_encoders = {}
    X_categorical = []
    categorical_feature_names = []
    
    for col in categorical_cols:
        if col in df.columns:
            le = LabelEncoder()
            encoded = le.fit_transform(df[col].astype(str))
            label_encoders[col] = le
            X_categorical.append(encoded.reshape(-1, 1))
            categorical_feature_names.extend([f"{col}_{val}" for val in le.classes_])
    
    # Combine features
    if X_categorical:
        X_categorical_array = np.hstack(X_categorical)
        X = np.hstack([X_numeric, X_categorical_array])
    else:
        X = X_numeric
    
    # Extract labels
    y = df["teacher_approve_label"].values
    
    # Feature names
    feature_names = feature_cols + categorical_feature_names
    
    return X, y, feature_names


# ============================================================================
# ML Bucket Assignment
# ============================================================================

def assign_ml_bucket(ml_prob: np.ndarray, threshold_likely: float = 0.7, threshold_unlikely: float = 0.3) -> np.ndarray:
    """
    Assign ML bucket based on predicted probability.
    
    Args:
        ml_prob: Array of predicted approval probabilities
        threshold_likely: Probability threshold for "likely" (default: 0.7)
        threshold_unlikely: Probability threshold for "unlikely" (default: 0.3)
    
    Returns:
        Array of bucket labels ("likely", "borderline", "unlikely")
    """
    buckets = np.full(len(ml_prob), "borderline", dtype=object)
    buckets[ml_prob >= threshold_likely] = "likely"
    buckets[ml_prob <= threshold_unlikely] = "unlikely"
    return buckets


# ============================================================================
# Monotonicity Checks
# ============================================================================

def check_monotonicity(
    model: any,
    scaler: StandardScaler,
    X_test: np.ndarray,
    df_test: pd.DataFrame,
    feature_names: list,
    n_samples: int = 500,
    dti_increase_pct: float = 0.05,
    ltv_increase_pct: float = 0.05,
) -> dict:
    """
    Run monotonicity sanity checks.
    
    For each sample, create modified versions with increased DTI/LTV and check
    if approval probability decreases (as expected).
    
    Args:
        model: Trained ML model
        scaler: Fitted StandardScaler
        X_test: Test feature matrix
        df_test: Test DataFrame (for accessing original feature values)
        feature_names: List of feature names
        n_samples: Number of samples to test
        dti_increase_pct: Relative increase in DTI (e.g., 0.05 = +5 percentage points)
        ltv_increase_pct: Relative increase in LTV (e.g., 0.05 = +5 percentage points)
    
    Returns:
        Dict with violation statistics
    """
    # Randomly select samples
    n_test = len(X_test)
    n_select = min(n_samples, n_test)
    indices = np.random.choice(n_test, size=n_select, replace=False)
    
    # Find feature indices
    dti_idx = feature_names.index("dti")
    ltv_idx = feature_names.index("ltv")
    
    # Get original probabilities
    X_test_scaled = scaler.transform(X_test[indices])
    prob_original = model.predict_proba(X_test_scaled)[:, 1]
    
    # Test DTI increase
    X_test_dti_modified = X_test[indices].copy()
    dti_violations = 0
    
    for i, idx in enumerate(indices):
        original_dti = df_test.iloc[idx]["dti"]
        # Increase DTI by fixed percentage points
        new_dti = min(1.0, original_dti + dti_increase_pct)
        X_test_dti_modified[i, dti_idx] = new_dti
    
    X_test_dti_modified_scaled = scaler.transform(X_test_dti_modified)
    prob_dti_modified = model.predict_proba(X_test_dti_modified_scaled)[:, 1]
    
    # Count violations: modified should have LOWER probability
    dti_violations = (prob_dti_modified > prob_original).sum()
    dti_violation_rate = (dti_violations / n_select) * 100
    
    # Test LTV increase
    X_test_ltv_modified = X_test[indices].copy()
    ltv_violations = 0
    
    for i, idx in enumerate(indices):
        original_ltv = df_test.iloc[idx]["ltv"]
        # Increase LTV by fixed percentage points
        new_ltv = min(1.0, original_ltv + ltv_increase_pct)
        X_test_ltv_modified[i, ltv_idx] = new_ltv
    
    X_test_ltv_modified_scaled = scaler.transform(X_test_ltv_modified)
    prob_ltv_modified = model.predict_proba(X_test_ltv_modified_scaled)[:, 1]
    
    # Count violations: modified should have LOWER probability
    ltv_violations = (prob_ltv_modified > prob_original).sum()
    ltv_violation_rate = (ltv_violations / n_select) * 100
    
    return {
        "n_samples_tested": n_select,
        "dti_violations": dti_violations,
        "dti_violation_rate": dti_violation_rate,
        "ltv_violations": ltv_violations,
        "ltv_violation_rate": ltv_violation_rate,
    }


# ============================================================================
# Main Evaluation Pipeline
# ============================================================================

def load_dataset(data_path: str) -> pd.DataFrame:
    """Load dataset from parquet or CSV file."""
    data_path_obj = Path(data_path)
    
    if data_path_obj.suffix == ".parquet":
        df = pd.read_parquet(data_path)
    else:
        df = pd.read_csv(data_path)
    
    logging.info(f"Loaded dataset: {len(df)} samples, {len(df.columns)} columns")
    return df


def print_comparison_summary(
    teacher_bucket: np.ndarray,
    ml_bucket: np.ndarray,
    teacher_label: np.ndarray,
    ml_prob: np.ndarray,
    ml_pred: np.ndarray,
) -> None:
    """Print comparison summary between teacher and ML."""
    print("\n" + "=" * 80)
    print("Teacher vs ML Comparison")
    print("=" * 80)
    
    # AUC and accuracy
    try:
        auc = roc_auc_score(teacher_label, ml_prob)
        print(f"\nAUC vs teacher: {auc:.3f}")
    except ValueError as e:
        logging.warning(f"Could not calculate AUC: {e}")
        auc = None
    
    accuracy = accuracy_score(teacher_label, ml_pred)
    print(f"Accuracy vs teacher: {accuracy:.3f}")
    
    # Bucket distributions
    print("\nBucket Distributions:")
    print("\nTeacher buckets:")
    teacher_counts = pd.Series(teacher_bucket).value_counts()
    for bucket, count in teacher_counts.items():
        pct = (count / len(teacher_bucket)) * 100
        print(f"  {bucket:12s}: {count:4d} ({pct:5.1f}%)")
    
    print("\nML buckets:")
    ml_counts = pd.Series(ml_bucket).value_counts()
    for bucket, count in ml_counts.items():
        pct = (count / len(ml_bucket)) * 100
        print(f"  {bucket:12s}: {count:4d} ({pct:5.1f}%)")
    
    # Confusion matrix
    print("\nTeacher vs ML Bucket Confusion Matrix:")
    cm = confusion_matrix(teacher_bucket, ml_bucket, labels=["likely", "borderline", "unlikely"])
    cm_df = pd.DataFrame(
        cm,
        index=["Teacher: likely", "Teacher: borderline", "Teacher: unlikely"],
        columns=["ML: likely", "ML: borderline", "ML: unlikely"],
    )
    print(cm_df.to_string())
    
    print("\n" + "=" * 80)


def print_borderline_cases(
    df_test: pd.DataFrame,
    teacher_bucket: np.ndarray,
    ml_prob: np.ndarray,
    n_rows: int = 20,
) -> None:
    """Print borderline teacher cases sorted by ML probability."""
    print("\n" + "=" * 80)
    print("Borderline Teacher Cases (sorted by ML probability)")
    print("=" * 80)
    
    # Filter borderline cases
    borderline_mask = teacher_bucket == "borderline"
    borderline_df = df_test[borderline_mask].copy()
    borderline_ml_prob = ml_prob[borderline_mask]
    
    if len(borderline_df) == 0:
        print("\nNo borderline cases found in test set.")
        return
    
    # Sort by ML probability (ascending - lowest prob first)
    sort_indices = np.argsort(borderline_ml_prob)
    borderline_df_sorted = borderline_df.iloc[sort_indices].copy()
    borderline_ml_prob_sorted = borderline_ml_prob[sort_indices]
    
    # Select key columns to display
    display_cols = [
        "income_monthly",
        "dti",
        "ltv",
        "home_price",
        "down_payment_pct",
        "teacher_bucket",
    ]
    
    # Create display DataFrame
    display_df = borderline_df_sorted[display_cols].copy()
    display_df["ml_prob"] = borderline_ml_prob_sorted
    display_df = display_df.head(n_rows)
    
    print(f"\nTop {len(display_df)} borderline cases (lowest ML prob first):")
    print(display_df.to_string(index=False))
    
    print("\n" + "=" * 80)


def print_monotonicity_summary(monotonicity_results: dict) -> None:
    """Print monotonicity check summary."""
    print("\n" + "=" * 80)
    print("Monotonicity Sanity Checks")
    print("=" * 80)
    
    n_tested = monotonicity_results["n_samples_tested"]
    dti_violations = monotonicity_results["dti_violations"]
    dti_rate = monotonicity_results["dti_violation_rate"]
    ltv_violations = monotonicity_results["ltv_violations"]
    ltv_rate = monotonicity_results["ltv_violation_rate"]
    
    print(f"\nSamples tested: {n_tested}")
    print(f"\nDTI Increase (+5 percentage points):")
    print(f"  Violations: {dti_violations} ({dti_rate:.1f}%)")
    print(f"  Expected: Higher DTI → Lower approval probability")
    
    print(f"\nLTV Increase (+5 percentage points):")
    print(f"  Violations: {ltv_violations} ({ltv_rate:.1f}%)")
    print(f"  Expected: Higher LTV → Lower approval probability")
    
    # Overall assessment
    print("\n" + "-" * 80)
    if dti_rate < 5.0 and ltv_rate < 5.0:
        print("✓ Monotonicity checks passed: violation rates < 5%")
    elif dti_rate < 10.0 and ltv_rate < 10.0:
        print("⚠ Monotonicity checks acceptable: violation rates < 10%")
    else:
        print("✗ Monotonicity checks failed: violation rates ≥ 10%")
    
    print("=" * 80 + "\n")


def main():
    """Main evaluation pipeline."""
    parser = argparse.ArgumentParser(
        description="Evaluate ML approval model against rule-based teacher"
    )
    parser.add_argument(
        "--data-path",
        type=str,
        required=True,
        help="Path to distillation dataset (.parquet or .csv)",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="Path to trained joblib model",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Test set size fraction (default: 0.2)",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed for train/test split (default: 42)",
    )
    parser.add_argument(
        "--monotonicity-samples",
        type=int,
        default=500,
        help="Number of samples for monotonicity checks (default: 500)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Set random seed
    np.random.seed(args.random_seed)
    
    # Load dataset
    logging.info(f"Loading dataset from {args.data_path}...")
    df = load_dataset(args.data_path)
    
    # Load model
    logging.info(f"Loading model from {args.model_path}...")
    model_dict = joblib.load(args.model_path)
    model = model_dict["model"]
    scaler = model_dict.get("scaler")
    model_feature_names = model_dict.get("feature_names")
    
    # Prepare features (must match training script exactly)
    # Note: We prepare features on full dataset, then split (same as training script)
    logging.info("Preparing features and labels...")
    X, y, feature_names = prepare_features_and_labels(df)
    
    # Verify feature names match
    if model_feature_names and set(feature_names) != set(model_feature_names):
        logging.warning(
            f"Feature name mismatch! Model: {len(model_feature_names)} features, "
            f"Data: {len(feature_names)} features"
        )
        # Try to align features
        if len(feature_names) == len(model_feature_names):
            logging.warning("Feature count matches, but names differ. Proceeding with caution...")
    
    # Split into train/test (same logic as training script)
    logging.info(f"Splitting data (test_size={args.test_size}, seed={args.random_seed})...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=args.test_size,
        random_state=args.random_seed,
        stratify=y,
    )
    
    # Also split DataFrame for accessing original columns
    df_train, df_test = train_test_split(
        df,
        test_size=args.test_size,
        random_state=args.random_seed,
        stratify=y,
    )
    
    logging.info(f"Test set: {X_test.shape[0]} samples")
    
    # Get teacher labels and buckets from test set
    teacher_label = df_test["teacher_approve_label"].values
    teacher_bucket = df_test["teacher_bucket"].values
    
    # Get ML predictions
    logging.info("Computing ML predictions...")
    if scaler is not None:
        X_test_scaled = scaler.transform(X_test)
        ml_prob = model.predict_proba(X_test_scaled)[:, 1]
        ml_pred = model.predict(X_test_scaled)
    else:
        ml_prob = model.predict_proba(X_test)[:, 1]
        ml_pred = model.predict(X_test)
    
    # Assign ML buckets
    ml_bucket = assign_ml_bucket(ml_prob)
    
    # Print comparison summary
    print_comparison_summary(teacher_bucket, ml_bucket, teacher_label, ml_prob, ml_pred)
    
    # Print borderline cases
    print_borderline_cases(df_test, teacher_bucket, ml_prob, n_rows=20)
    
    # Run monotonicity checks
    logging.info("Running monotonicity checks...")
    monotonicity_results = check_monotonicity(
        model=model,
        scaler=scaler,
        X_test=X_test,
        df_test=df_test,
        feature_names=feature_names,
        n_samples=args.monotonicity_samples,
    )
    print_monotonicity_summary(monotonicity_results)
    
    # Final summary
    print("\n" + "=" * 80)
    print("Evaluation Summary")
    print("=" * 80)
    try:
        auc = roc_auc_score(teacher_label, ml_prob)
        print(f"✓ AUC vs teacher: {auc:.3f}")
    except ValueError:
        print("⚠ Could not calculate AUC")
    
    accuracy = accuracy_score(teacher_label, ml_pred)
    print(f"✓ Accuracy vs teacher: {accuracy:.3f}")
    
    dti_rate = monotonicity_results["dti_violation_rate"]
    ltv_rate = monotonicity_results["ltv_violation_rate"]
    print(f"✓ Monotonicity violation rate (higher DTI → higher prob): {dti_rate:.1f}%")
    print(f"✓ Monotonicity violation rate (higher LTV → higher prob): {ltv_rate:.1f}%")
    
    print("=" * 80 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

