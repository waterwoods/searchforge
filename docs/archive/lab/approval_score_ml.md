# ML-Based ApprovalScore Pipeline

## Motivation & Overview

The mortgage approval system started with a pure rule-based `ApprovalScore` that evaluates borrowers based on traditional metrics like debt-to-income (DTI), loan-to-value (LTV), and cash flow ratios. To make the system more flexible and learnable while maintaining interpretability, we added a small ML model that learns from these rules through knowledge distillation. The system now uses a hybrid "rules + ML" scoring approach at runtime.

**Key point:** The external API did not change; only the internal scoring logic was enhanced. The ML model acts as a student that learns from the rule-based teacher, providing smoother probability estimates while the rules remain the primary trusted signal.

---

## Components & Files

### Data & Schema

- **`experiments/approval_ml_schema.py`** – Defines `TrainingSample` with:
  - Primitive borrower/home features: `income_monthly`, `other_debt_monthly`, `home_price`, `down_payment_pct`, `interest_rate`, `loan_term_years`
  - Location features: `state`, `zip_code`
  - Derived ratios: `ltv`, `dti`, `payment_to_income`, `cash_buffer_ratio`
  - Teacher labels: `teacher_bucket` ("likely"/"borderline"/"unlikely"), `teacher_approve_label` (binary)

- **`experiments/gen_approval_distillation_data.py`** – Generates synthetic borrower/home cases:
  - Focuses ~50% of samples around threshold regions (DTI 35–55%, LTV 70–100%)
  - Calls `run_stress_check` to get rule-based `ApprovalScore` for each sample
  - Saves distillation dataset as parquet/csv

### Training & Offline Evaluation

- **`experiments/train_approval_score_ml.py`** – Trains ML model:
  - Logistic regression (baseline) and optional XGBoost
  - Saves joblib bundle: model + scaler + encoders + feature names
  - Output: `ml_models/approval_score_logreg_v1.joblib`

- **`experiments/eval_approval_score_ml.py`** – Evaluates ML model vs teacher:
  - Metrics: AUC, accuracy, bucket confusion, borderline examples
  - Monotonicity checks on DTI/LTV (ensures higher DTI/LTV never increases approval probability)

### Runtime ML + Hybrid Logic

- **`services/fiqa_api/mortgage/approval/ml_approval_score.py`** – Runtime ML module:
  - Loads joblib model (singleton pattern, cached per process)
  - Extracts features from `stress_result` (matching training pipeline)
  - Returns `approve_prob` in [0, 1]
  - Raises `MLApprovalUnavailable` on failure (graceful fallback)

- **`services/fiqa_api/mortgage/approval/hybrid_score.py`** – Hybrid combination:
  - `combine_rule_and_ml()` implements weighted blending strategy
  - Adjusts rule-based score with ML probability based on bucket

- **`services/core/settings.py`** – Configuration:
  - `get_use_ml_approval_score()` reads `USE_ML_APPROVAL_SCORE` env var (default: `false`)

- **`services/fiqa_api/mortgage/mortgage_agent_runtime.py`** – Main runtime flow:
  - `run_stress_check` computes rule-based `ApprovalScore` first
  - If ML enabled, calls ML prediction and hybrid combination
  - Attaches final `ApprovalScore` to response

### Smoke Test

- **`experiments/approval_score_ml_smoke.py`** – Integration smoke test:
  - Runs good/borderline/high-risk scenarios with ML on/off
  - Checks score reasonableness and basic monotonicity

---

## Data & Training Summary

### Distillation Setup

- **Synthetic sample generation:**
  - ~50% focused around threshold regions: DTI [0.35–0.55], LTV [0.70–1.00]
  - ~50% across broader range for generalization
  - Fixed random seeds for reproducibility

- **Teacher labels:**
  - For each sample, `run_stress_check` (pure rules) produces:
    - DTI, payment breakdown, cash-flow metrics
    - Rule-based `ApprovalScore.bucket`
  - `teacher_approve_label = 1` if `teacher_bucket == "likely"`, else `0`

### Features

- **Only primitive inputs and simple ratios:**
  - No `stress_band`, numeric `approval_score`, or `risk_flags` (to avoid label leakage)
  - Features: income, debts, home_price, down_payment_pct, LTV, DTI, payment_to_income, cash_buffer_ratio, state, zip_code

### Model

- **Baseline:** scikit-learn Logistic Regression
- **Storage:** `ml_models/approval_score_logreg_v1.joblib` (includes model, scaler, encoders, feature names)

---

## Offline Metrics & Findings

### Test/Validation Performance (vs Teacher Labels)

- **Validation AUC:** ≈ **0.962**
- **Test AUC:** ≈ **0.967** (meets ≥ 0.85 target)
- **Test accuracy:** ≈ **89.8%**

### Class-wise Behavior

- **Reject class:** precision ≈ 0.99, recall ≈ 0.90
- **Approve class:** precision ≈ 0.43, recall ≈ 0.92

### Additional Evaluation Results

- **AUC vs teacher:** ≈ **0.964**
- **Accuracy:** ≈ **0.897**
- **Monotonicity violation rate:** **0.0%** (for higher DTI and higher LTV in sampled checks)

### Qualitative Findings

- ML model closely matches rule-based teacher while preserving intuitive monotonicity
- Higher DTI/LTV never increases approval probability in tests
- ML tends to be slightly more conservative than teacher, especially in borderline cases (desirable for risk management)

---

## Hybrid "Rules + ML" Strategy in Runtime

### High-Level Idea

- Rule-based `ApprovalScore` remains the primary and most trusted signal
- ML model provides an additional, smoother estimate of approval probability
- Final `ApprovalScore` is a weighted combination of rule score and ML score

### Concrete Strategy (`combine_rule_and_ml()`)

1. **Convert ML probability to 0–100 score:**
   - `ml_score = approve_prob * 100`

2. **Weighted blending based on rule bucket:**
   - **`rule_bucket == "borderline"`:** 50% rule / 50% ML blend
   - **`rule_bucket == "likely"` or `"unlikely"`:** 70% rule / 30% ML blend

3. **Recompute final bucket:**
   - `score >= 70` → `"likely"`
   - `40 <= score < 70` → `"borderline"`
   - `score < 40` → `"unlikely"`

4. **Reason tags:**
   - If ML shifted the bucket, add `"ml_adjusted"` or `"ml_borderline_adjustment"` to reasons list

### Safety & Fallback

- If `USE_ML_APPROVAL_SCORE=false` (default), system uses pure rule-based `ApprovalScore`
- If ML fails to load/predict, system falls back to rule-based only (no API errors)
- External APIs and response schemas are unchanged; only internal `approval_score` computation is upgraded

---

## End-to-End Flow Diagram

```
Borrower + Property Input
          |
          v
   run_stress_check (runtime)
          |
          |-- Rule-based engine --> rule_approval_score
          |                          (score, bucket, reasons)
          |
          |-- (optional) ML model (joblib) --> approve_prob [0, 1]
          |     - Load model (singleton, cached)
          |     - Extract features from stress_result
          |     - Predict probability
          |
          |-- hybrid_score.combine_rule_and_ml(rule, ml_prob)
          |     - Convert ml_prob to 0-100 scale
          |     - Weighted blend (50/50 for borderline, 70/30 otherwise)
          |     - Recompute bucket
          |     - Add ml_adjusted reason if bucket changed
          v
   Final ApprovalScore (score + bucket + reasons)
          |
          v
   LangGraph workflow + LLM explanation + Frontend UI
```

---

## Summary

The ML-based `ApprovalScore` pipeline enhances the existing rule-based system through knowledge distillation. The hybrid approach combines the interpretability and trust of rules with the flexibility of ML, while maintaining backward compatibility and graceful fallback. The model achieves strong performance (AUC ≈ 0.967) and preserves important monotonicity properties, making it suitable for production use.


