#!/usr/bin/env python3
"""
train_approval_score_ml.py - Train ML Model for ApprovalScore

This script trains an ML model to mimic the existing rule-based approval decision
(teacher-student distillation). The model learns to predict the approval bucket
(likely/borderline/unlikely) from primitive borrower and property features.

IMPORTANT NOTES:
- This script trains an ML model to MIMIC the existing rule-based approval decision
  (teacher-student distillation).
- We will later integrate this model into runtime via a separate ml_approval_score module.
- No runtime behavior is changed by this script yet.
- The training data should be generated using gen_approval_distillation_data.py.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Tuple, Optional, Any

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ============================================================================
# Model Training Functions
# ============================================================================

def prepare_features_and_labels(
    df: pd.DataFrame,
) -> Tuple[np.ndarray, np.ndarray, list, dict]:
    """
    Prepare feature matrix X and label vector y from DataFrame.
    
    Args:
        df: DataFrame with training samples
    
    Returns:
        Tuple of (X, y, feature_names, label_encoders)
        - X: Feature matrix (n_samples, n_features)
        - y: Label vector (n_samples,) with binary labels (0 or 1)
        - feature_names: List of feature names
        - label_encoders: Dict of fitted LabelEncoders for categorical features
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
    
    return X, y, feature_names, label_encoders


def train_logistic_regression(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_valid: np.ndarray,
    y_valid: np.ndarray,
) -> Tuple[Any, StandardScaler]:
    """
    Train a logistic regression model.
    
    Args:
        X_train: Training feature matrix
        y_train: Training labels
        X_valid: Validation feature matrix
        y_valid: Validation labels
    
    Returns:
        Tuple of (trained_model, scaler)
    """
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_valid_scaled = scaler.transform(X_valid)
    
    # Train model
    model = LogisticRegression(
        max_iter=1000,
        random_state=42,
        class_weight="balanced",  # Handle class imbalance
    )
    model.fit(X_train_scaled, y_train)
    
    # Evaluate on validation set
    y_pred = model.predict(X_valid_scaled)
    y_pred_proba = model.predict_proba(X_valid_scaled)[:, 1]
    accuracy = accuracy_score(y_valid, y_pred)
    
    # Calculate AUC
    try:
        auc = roc_auc_score(y_valid, y_pred_proba)
        logging.info(f"Logistic Regression - Validation Accuracy: {accuracy:.3f}, AUC: {auc:.3f}")
    except ValueError as e:
        # AUC calculation may fail if only one class present
        logging.warning(f"Could not calculate AUC: {e}")
        auc = None
        logging.info(f"Logistic Regression - Validation Accuracy: {accuracy:.3f}")
    
    return model, scaler


def train_xgboost_classifier(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_valid: np.ndarray,
    y_valid: np.ndarray,
) -> Tuple[Any, Optional[StandardScaler]]:
    """
    Train an XGBoost classifier.
    
    Note: XGBoost typically doesn't require scaling, but we return None for scaler
    for consistency with the interface.
    
    Args:
        X_train: Training feature matrix
        y_train: Training labels
        X_valid: Validation feature matrix
        y_valid: Validation labels
    
    Returns:
        Tuple of (trained_model, None) - XGBoost doesn't need scaling
    """
    try:
        import xgboost as xgb
    except ImportError:
        logging.warning("XGBoost not installed. Install with: pip install xgboost")
        logging.warning("Returning None model - implement this function when XGBoost is available")
        return None, None
    
    # Train model
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        eval_metric="logloss",
    )
    model.fit(
        X_train,
        y_train,
        eval_set=[(X_valid, y_valid)],
        verbose=False,
    )
    
    # Evaluate on validation set
    y_pred = model.predict(X_valid)
    y_pred_proba = model.predict_proba(X_valid)[:, 1]
    accuracy = accuracy_score(y_valid, y_pred)
    
    # Calculate AUC
    try:
        auc = roc_auc_score(y_valid, y_pred_proba)
        logging.info(f"XGBoost - Validation Accuracy: {accuracy:.3f}, AUC: {auc:.3f}")
    except ValueError as e:
        logging.warning(f"Could not calculate AUC: {e}")
        auc = None
        logging.info(f"XGBoost - Validation Accuracy: {accuracy:.3f}")
    
    return model, None


# ============================================================================
# Main Training Pipeline
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


def print_dataset_info(df: pd.DataFrame) -> None:
    """Print dataset information."""
    print("\n" + "=" * 80)
    print("Dataset Information")
    print("=" * 80)
    print(f"Total samples: {len(df)}")
    print(f"Features: {len(df.columns)}")
    
    # Class balance
    if "teacher_approve_label" in df.columns:
        approve_count = df["teacher_approve_label"].sum()
        reject_count = len(df) - approve_count
        approve_pct = (approve_count / len(df) * 100) if len(df) > 0 else 0.0
        
        print(f"\nClass Balance:")
        print(f"  Approve (1): {approve_count} ({approve_pct:.1f}%)")
        print(f"  Reject (0):  {reject_count} ({100 - approve_pct:.1f}%)")
    
    # Bucket distribution
    if "teacher_bucket" in df.columns:
        bucket_counts = df["teacher_bucket"].value_counts()
        print(f"\nTeacher Bucket Distribution:")
        for bucket, count in bucket_counts.items():
            pct = (count / len(df) * 100) if len(df) > 0 else 0.0
            print(f"  {bucket:12s}: {count:4d} ({pct:5.1f}%)")
    
    print("=" * 80 + "\n")


def main():
    """Main training pipeline."""
    parser = argparse.ArgumentParser(
        description="Train ML model for ApprovalScore (distillation from rules)"
    )
    parser.add_argument(
        "--data-path",
        type=str,
        required=True,
        help="Path to training data file (.parquet or .csv)",
    )
    parser.add_argument(
        "--model-out",
        type=str,
        default="models/approval_score_ml.joblib",
        help="Output path for trained model (default: models/approval_score_ml.joblib)",
    )
    parser.add_argument(
        "--model-type",
        type=str,
        choices=["logistic", "xgboost"],
        default="logistic",
        help="Model type to train (default: logistic)",
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
    
    # Load dataset
    logging.info(f"Loading dataset from {args.data_path}...")
    df = load_dataset(args.data_path)
    print_dataset_info(df)
    
    # Prepare features and labels
    logging.info("Preparing features and labels...")
    X, y, feature_names, label_encoders = prepare_features_and_labels(df)
    logging.info(f"Feature matrix shape: {X.shape}")
    logging.info(f"Label vector shape: {y.shape}")
    logging.info(f"Feature names: {feature_names}")
    logging.info(f"Label encoders: {list(label_encoders.keys())}")
    
    # Split into train/valid/test
    logging.info(f"Splitting data (test_size={args.test_size}, seed={args.random_seed})...")
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y,
        test_size=args.test_size,
        random_state=args.random_seed,
        stratify=y,  # Preserve class distribution
    )
    
    # Further split temp into validation and test
    val_size = 0.5  # 50% of test_size goes to validation
    X_valid, X_test, y_valid, y_test = train_test_split(
        X_temp, y_temp,
        test_size=val_size,
        random_state=args.random_seed,
        stratify=y_temp,
    )
    
    logging.info(f"Train set: {X_train.shape[0]} samples")
    logging.info(f"Validation set: {X_valid.shape[0]} samples")
    logging.info(f"Test set: {X_test.shape[0]} samples")
    
    # Train model
    logging.info(f"Training {args.model_type} model...")
    if args.model_type == "logistic":
        model, scaler = train_logistic_regression(X_train, y_train, X_valid, y_valid)
    elif args.model_type == "xgboost":
        model, scaler = train_xgboost_classifier(X_train, y_train, X_valid, y_valid)
    else:
        raise ValueError(f"Unknown model type: {args.model_type}")
    
    if model is None:
        logging.error("Model training failed or not implemented")
        return 1
    
    # Evaluate on test set
    logging.info("Evaluating on test set...")
    if scaler is not None:
        X_test_scaled = scaler.transform(X_test)
        y_pred = model.predict(X_test_scaled)
        y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    else:
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    test_accuracy = accuracy_score(y_test, y_pred)
    
    # Calculate AUC
    try:
        test_auc = roc_auc_score(y_test, y_pred_proba)
        logging.info(f"Test Accuracy: {test_accuracy:.3f}, AUC: {test_auc:.3f}")
        
        # Verify AUC meets threshold (≥ 0.85)
        if test_auc >= 0.85:
            logging.info(f"✓ AUC {test_auc:.3f} meets threshold (≥ 0.85) - features are learnable!")
        else:
            logging.warning(f"⚠ AUC {test_auc:.3f} is below threshold (≥ 0.85) - may need feature engineering")
    except ValueError as e:
        logging.warning(f"Could not calculate AUC: {e}")
        test_auc = None
        logging.info(f"Test Accuracy: {test_accuracy:.3f}")
    
    # Print classification report
    print("\n" + "=" * 80)
    print("Test Set Classification Report")
    print("=" * 80)
    print(classification_report(y_test, y_pred, target_names=["Reject", "Approve"]))
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    if test_auc is not None:
        print(f"\nTest AUC: {test_auc:.3f}")
        if test_auc >= 0.85:
            print("✓ AUC meets threshold (≥ 0.85) - features are learnable!")
        else:
            print(f"⚠ AUC below threshold (≥ 0.85)")
    print("=" * 80 + "\n")
    
    # Save model
    model_out_path = Path(args.model_out)
    model_out_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save model and scaler together
    # Note: label_encoders are already returned from prepare_features_and_labels
    model_dict = {
        "model": model,
        "scaler": scaler,
        "feature_names": feature_names,
        "model_type": args.model_type,
        "label_encoders": label_encoders if label_encoders else None,
    }
    
    joblib.dump(model_dict, model_out_path)
    logging.info(f"Saved model to {model_out_path}")
    if label_encoders:
        logging.info(f"Saved {len(label_encoders)} label encoders: {list(label_encoders.keys())}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

