"""
ml_approval_score.py - ML-Based ApprovalScore Runtime Module
============================================================

This module encapsulates all runtime ML logic for ApprovalScore prediction.
It is a student model distilled from the existing rule-based teacher (compute_rule_based_approval_score).

IMPORTANT NOTES:
- This module should never change the API contracts of upstream/downstream modules.
- It gracefully falls back to rule-based approval if ML model is unavailable.
- The model is loaded once per process (singleton pattern).
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import numpy as np

try:
    import joblib
    from sklearn.preprocessing import LabelEncoder
except ImportError:
    joblib = None
    LabelEncoder = None

logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================

class MLApprovalUnavailable(Exception):
    """Raised when ML approval score cannot be computed."""
    pass


# ============================================================================
# Model Loading (Singleton Pattern)
# ============================================================================

# Module-level cache for loaded model
_cached_model: Optional[Dict[str, Any]] = None
_cached_model_path: Optional[str] = None


def load_approval_model(model_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the approval score ML model from disk (singleton pattern).
    
    Loads once per process and caches the result. Subsequent calls with the
    same path return the cached model.
    
    Args:
        model_path: Path to joblib model file. If None, reads from
                   APPROVAL_SCORE_MODEL_PATH env var or defaults to
                   ml_models/approval_score_logreg_v1.joblib
    
    Returns:
        Dict containing:
        - "model": Trained sklearn model
        - "scaler": Optional StandardScaler (None for XGBoost)
        - "feature_names": List of feature names
        - "model_type": "logistic" or "xgboost"
        - "label_encoders": Optional dict of fitted LabelEncoders for categorical features
    
    Raises:
        MLApprovalUnavailable: If model cannot be loaded
    """
    global _cached_model, _cached_model_path
    
    if joblib is None:
        raise MLApprovalUnavailable("joblib not installed - ML approval unavailable")
    
    # Determine model path
    if model_path is None:
        model_path = os.getenv(
            "APPROVAL_SCORE_MODEL_PATH",
            "ml_models/approval_score_logreg_v1.joblib"
        )
    
    # Check cache
    if _cached_model is not None and _cached_model_path == model_path:
        logger.debug(f"[ML_APPROVAL] Using cached model from {model_path}")
        return _cached_model
    
    # Resolve model path (try relative to project root)
    model_path_obj = Path(model_path)
    if not model_path_obj.is_absolute():
        # Try relative to project root
        project_root = Path(__file__).parent.parent.parent.parent.parent
        model_path_obj = project_root / model_path
    
    if not model_path_obj.exists():
        raise MLApprovalUnavailable(
            f"Model file not found: {model_path_obj}. "
            f"Set APPROVAL_SCORE_MODEL_PATH env var to point to the model file."
        )
    
    # Load model
    try:
        model_dict = joblib.load(model_path_obj)
        logger.info(f"[ML_APPROVAL] Successfully loaded model from {model_path_obj}")
        
        # Cache it
        _cached_model = model_dict
        _cached_model_path = str(model_path_obj)
        
        return model_dict
    
    except Exception as e:
        raise MLApprovalUnavailable(
            f"Failed to load model from {model_path_obj}: {e}"
        ) from e


# ============================================================================
# Feature Extraction
# ============================================================================

def build_feature_vector_from_stress_result(
    stress_result: Any,  # StressCheckResponse, but use Any to avoid circular imports
) -> np.ndarray:
    """
    Build feature vector from stress check result, matching training pipeline.
    
    Extracts the same features as used during training:
    - Primitive features: income_monthly, other_debt_monthly, home_price,
      down_payment_pct, interest_rate, loan_term_years
    - Derived ratios: ltv, dti, payment_to_income, cash_buffer_ratio
    - Categorical features: state, zip_code (label-encoded)
    
    Args:
        stress_result: StressCheckResponse with computed metrics
    
    Returns:
        Feature vector as numpy array (1D, shape: (n_features,))
    
    Raises:
        MLApprovalUnavailable: If feature extraction fails
    """
    try:
        # Extract primitive features from snapshots
        wallet = stress_result.wallet_snapshot or {}
        home = stress_result.home_snapshot or {}
        
        income_monthly = wallet.get("monthly_income", 0.0)
        other_debt_monthly = wallet.get("other_debts_monthly", 0.0)
        home_price = home.get("list_price", 0.0)
        down_payment_pct = home.get("down_payment_pct", 0.20)
        
        # Interest rate from stress_result (convert from percent to decimal)
        interest_rate = (stress_result.assumed_interest_rate_pct / 100.0) if stress_result.assumed_interest_rate_pct else 0.06
        loan_term_years = 30  # Fixed at 30 years in run_stress_check
        
        # Extract state and zip_code from home_snapshot or from request context
        # Note: We need these from the original request, but they're not always in snapshots
        # Try to extract from case_state if available
        state = home.get("state", "CA")  # Default fallback
        zip_code = home.get("zip_code", "90210")  # Default fallback
        
        if stress_result.case_state and stress_result.case_state.inputs:
            inputs = stress_result.case_state.inputs
            state = inputs.get("state", state)
            zip_code = inputs.get("zip_code", zip_code)
        
        # Extract derived ratios
        dti = stress_result.dti_ratio or 0.0
        total_monthly_payment = stress_result.total_monthly_payment or 0.0
        
        # Compute LTV
        loan_amount = home.get("loan_amount", 0.0)
        if loan_amount == 0.0 and home_price > 0:
            loan_amount = home_price * (1 - down_payment_pct)
        ltv = loan_amount / home_price if home_price > 0 else 0.0
        
        # Compute payment_to_income
        payment_to_income = total_monthly_payment / income_monthly if income_monthly > 0 else 0.0
        
        # Compute cash_buffer_ratio
        # (income - total_payment - other_debt) / total_payment
        cash_buffer = income_monthly - total_monthly_payment - other_debt_monthly
        cash_buffer_ratio = cash_buffer / total_monthly_payment if total_monthly_payment > 0 else 0.0
        
        # Build numeric feature array (matching training order)
        numeric_features = np.array([
            income_monthly,
            other_debt_monthly,
            home_price,
            down_payment_pct,
            interest_rate,
            loan_term_years,
            ltv,
            dti,
            payment_to_income,
            cash_buffer_ratio,
        ])
        
        # Handle categorical features (state, zip_code)
        # Use label encoders from the model if available, otherwise use fallback
        try:
            model_dict = load_approval_model()
            label_encoders = model_dict.get("label_encoders")
            
            # Encode state
            if label_encoders and "state" in label_encoders and label_encoders["state"] is not None:
                state_encoder = label_encoders["state"]
                try:
                    state_encoded = state_encoder.transform([str(state)])[0]
                except (ValueError, KeyError):
                    # Unseen category - try to use 0 or fallback to hash
                    logger.warning(f"[ML_APPROVAL] Unseen state '{state}', using fallback encoding")
                    state_encoded = hash(str(state)) % 100
            else:
                # No encoder saved - use simple hash-based encoding
                state_encoded = hash(str(state)) % 100
            
            # Encode zip_code
            if label_encoders and "zip_code" in label_encoders and label_encoders["zip_code"] is not None:
                zip_encoder = label_encoders["zip_code"]
                try:
                    zip_encoded = zip_encoder.transform([str(zip_code)])[0]
                except (ValueError, KeyError):
                    # Unseen category - use fallback
                    logger.warning(f"[ML_APPROVAL] Unseen zip_code '{zip_code}', using fallback encoding")
                    zip_encoded = hash(str(zip_code)) % 1000
            else:
                # No encoder saved - use simple hash-based encoding
                zip_encoded = hash(str(zip_code)) % 1000
            
            categorical_features = np.array([state_encoded, zip_encoded])
            
        except MLApprovalUnavailable:
            # If model not loaded yet, use simple encoding
            state_encoded = hash(str(state)) % 100
            zip_encoded = hash(str(zip_code)) % 1000
            categorical_features = np.array([state_encoded, zip_encoded])
        
        # Combine features (matching training: numeric first, then categorical)
        feature_vector = np.concatenate([numeric_features, categorical_features])
        
        return feature_vector
    
    except Exception as e:
        raise MLApprovalUnavailable(f"Feature extraction failed: {e}") from e


# ============================================================================
# Prediction
# ============================================================================

def predict_ml_approval_prob(stress_result: Any) -> float:  # StressCheckResponse, but use Any to avoid circular imports
    """
    Predict approval probability using ML model.
    
    Args:
        stress_result: StressCheckResponse with computed metrics
    
    Returns:
        Approval probability in [0, 1] range (probability of "likely" bucket)
    
    Raises:
        MLApprovalUnavailable: If prediction fails
    """
    try:
        # Load model
        model_dict = load_approval_model()
        model = model_dict["model"]
        scaler = model_dict.get("scaler")
        
        # Build feature vector
        features = build_feature_vector_from_stress_result(stress_result)
        features = features.reshape(1, -1)  # Reshape for sklearn (1 sample, n features)
        
        # Apply scaling if scaler exists (for logistic regression)
        if scaler is not None:
            features = scaler.transform(features)
        
        # Predict probability
        proba = model.predict_proba(features)
        approve_prob = float(proba[0, 1])  # Probability of class 1 (approve)
        
        logger.debug(
            f"[ML_APPROVAL] Predicted approval probability: {approve_prob:.3f}"
        )
        
        return approve_prob
    
    except MLApprovalUnavailable:
        raise
    except Exception as e:
        raise MLApprovalUnavailable(f"ML prediction failed: {e}") from e

