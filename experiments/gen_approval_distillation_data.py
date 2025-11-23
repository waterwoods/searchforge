#!/usr/bin/env python3
"""
gen_approval_distillation_data.py - Generate Training Data for ML-Based ApprovalScore

This script generates synthetic training data by distilling the existing rule-based
approval decision logic. It calls run_stress_check for each synthetic borrower/property
configuration and extracts features + labels for ML training.

IMPORTANT NOTES:
- This is DISTILLATION from existing rules, NOT real production loan history.
- We focus more samples around "borderline" regions: DTI ~ 35-55%, LTV ~ 70-100%.
- Uses fixed random seeds for reproducibility.
- Does NOT include stress_band, approval_score numeric value, or risk_flags as features
  to avoid label leakage.
"""

import sys
import random
import argparse
import logging
from pathlib import Path
from typing import List, Optional
from collections import defaultdict

import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.mortgage import (
    run_stress_check,
    StressCheckRequest,
    StressCheckResponse,
)
from experiments.approval_ml_schema import TrainingSample


# ============================================================================
# Configuration
# ============================================================================

# Mock ZIP codes and states used in existing tests
MOCK_ZIP_STATES = [
    ("90803", "CA"),  # Long Beach, CA
    ("92648", "CA"),  # Huntington Beach, CA
    ("90210", "CA"),  # Beverly Hills, CA
    ("73301", "TX"),  # Austin, TX
    ("78701", "TX"),  # Austin, TX
    ("98101", "WA"),  # Seattle, WA
    ("75001", "TX"),  # Dallas, TX
]

# Interest rate range (annual, as decimal)
INTEREST_RATE_RANGE = (0.05, 0.08)  # 5% to 8%

# Loan term (fixed at 30 years for now, matching run_stress_check default)
LOAN_TERM_YEARS = 30


# ============================================================================
# Synthetic Sample Generation
# ============================================================================

def generate_sample_config(
    regime: str,
    rng: random.Random,
    np_rng: np.random.Generator,
) -> dict:
    """
    Generate a single borrower + property configuration.
    
    Args:
        regime: "around_threshold" or "broad"
        rng: Python random.Random instance
        np_rng: NumPy random generator
    
    Returns:
        Dict with: income_monthly, other_debt_monthly, home_price, down_payment_pct,
                   interest_rate, loan_term_years, state, zip_code
    """
    zip_code, state = rng.choice(MOCK_ZIP_STATES)
    
    if regime == "around_threshold":
        # Target DTI ~ 35-55% and LTV ~ 70-100%
        # Strategy: sample income, then adjust home_price and down_payment to hit targets
        
        # Sample income (monthly)
        income_monthly = rng.uniform(6000, 15000)
        
        # Sample other debt (5-15% of income)
        other_debt_monthly = income_monthly * rng.uniform(0.05, 0.15)
        
        # Sample target DTI (35-55%)
        target_dti = rng.uniform(0.35, 0.55)
        
        # Sample target LTV (70-100%)
        target_ltv = rng.uniform(0.70, 1.00)
        
        # Sample interest rate
        interest_rate = np_rng.uniform(*INTEREST_RATE_RANGE)
        
        # Back out home_price and down_payment_pct from target DTI and LTV
        # We need to solve:
        #   DTI = (monthly_payment + other_debt) / monthly_income
        #   LTV = loan_amount / home_price = (home_price * (1 - down_payment_pct)) / home_price
        #   monthly_payment = calc_monthly_payment(loan_amount, interest_rate, term_years) + tax/ins/hoa
        
        # Approximate: assume monthly_payment ≈ loan_amount * monthly_rate_factor
        # For 30-year at 6%: monthly_rate_factor ≈ 0.006
        monthly_rate_factor = interest_rate / 12.0 * (1 + interest_rate / 12.0) ** (LOAN_TERM_YEARS * 12) / \
                              ((1 + interest_rate / 12.0) ** (LOAN_TERM_YEARS * 12) - 1)
        
        # Add rough estimate for tax/ins/hoa (assume ~1.5% of home_price annually = 0.125% monthly)
        tax_ins_hoa_factor = 0.00125
        
        # Target total monthly payment from DTI
        target_total_payment = income_monthly * target_dti - other_debt_monthly
        
        # Solve for home_price:
        #   target_total_payment = loan_amount * monthly_rate_factor + home_price * tax_ins_hoa_factor
        #   loan_amount = home_price * target_ltv
        #   target_total_payment = home_price * target_ltv * monthly_rate_factor + home_price * tax_ins_hoa_factor
        #   target_total_payment = home_price * (target_ltv * monthly_rate_factor + tax_ins_hoa_factor)
        
        denominator = target_ltv * monthly_rate_factor + tax_ins_hoa_factor
        if denominator > 0:
            home_price = target_total_payment / denominator
        else:
            # Fallback
            home_price = income_monthly * 12 * 4.0  # 4x annual income
        
        # Ensure reasonable bounds
        home_price = max(200000, min(home_price, 2000000))
        
        # Compute down_payment_pct from target LTV
        # LTV = loan_amount / home_price = (home_price * (1 - down_payment_pct)) / home_price
        # So: down_payment_pct = 1 - LTV
        down_payment_pct = 1.0 - target_ltv
        down_payment_pct = max(0.05, min(down_payment_pct, 0.30))  # Clamp to 5-30%
        
    else:  # regime == "broad"
        # Wider variety of configurations
        income_monthly = rng.uniform(4000, 20000)
        other_debt_monthly = income_monthly * rng.uniform(0.0, 0.20)
        
        # Sample home_price (2x to 8x annual income)
        annual_income = income_monthly * 12
        home_price = annual_income * rng.uniform(2.0, 8.0)
        home_price = max(150000, min(home_price, 3000000))
        
        # Sample down_payment_pct
        down_payment_pct = rng.uniform(0.05, 0.30)
        
        # Sample interest rate
        interest_rate = np_rng.uniform(*INTEREST_RATE_RANGE)
    
    return {
        "income_monthly": income_monthly,
        "other_debt_monthly": other_debt_monthly,
        "home_price": home_price,
        "down_payment_pct": down_payment_pct,
        "interest_rate": interest_rate,
        "loan_term_years": LOAN_TERM_YEARS,
        "state": state,
        "zip_code": zip_code,
    }


def extract_training_sample(
    config: dict,
    stress_response: StressCheckResponse,
) -> Optional[TrainingSample]:
    """
    Extract a TrainingSample from a config and stress_response.
    
    Args:
        config: Borrower/property configuration dict
        stress_response: StressCheckResponse from run_stress_check
    
    Returns:
        TrainingSample or None if extraction fails
    """
    try:
        # Extract primitive features from config
        income_monthly = config["income_monthly"]
        other_debt_monthly = config["other_debt_monthly"]
        home_price = config["home_price"]
        down_payment_pct = config["down_payment_pct"]
        # Use actual interest rate from stress_response (convert from percent to decimal)
        interest_rate = (stress_response.assumed_interest_rate_pct / 100.0) if stress_response.assumed_interest_rate_pct else config["interest_rate"]
        loan_term_years = config["loan_term_years"]  # Fixed at 30 years in run_stress_check
        state = config["state"]
        zip_code = config["zip_code"]
        
        # Extract derived ratios from stress_response
        dti = stress_response.dti_ratio
        total_monthly_payment = stress_response.total_monthly_payment
        
        # Compute LTV
        loan_amount = home_price * (1 - down_payment_pct)
        ltv = loan_amount / home_price if home_price > 0 else 0.0
        
        # Compute payment_to_income
        payment_to_income = total_monthly_payment / income_monthly if income_monthly > 0 else 0.0
        
        # Compute cash_buffer_ratio
        # (income - total_payment - other_debt) / total_payment
        cash_buffer = income_monthly - total_monthly_payment - other_debt_monthly
        cash_buffer_ratio = cash_buffer / total_monthly_payment if total_monthly_payment > 0 else 0.0
        
        # Extract teacher labels from approval_score
        if stress_response.approval_score is None:
            return None
        
        teacher_bucket = stress_response.approval_score.bucket
        teacher_approve_label = 1 if teacher_bucket == "likely" else 0
        
        return TrainingSample(
            income_monthly=income_monthly,
            other_debt_monthly=other_debt_monthly,
            home_price=home_price,
            down_payment_pct=down_payment_pct,
            interest_rate=interest_rate,
            loan_term_years=loan_term_years,
            state=state,
            zip_code=zip_code,
            ltv=ltv,
            dti=dti,
            payment_to_income=payment_to_income,
            cash_buffer_ratio=cash_buffer_ratio,
            teacher_bucket=teacher_bucket,
            teacher_approve_label=teacher_approve_label,
        )
    
    except Exception as e:
        logging.warning(f"Failed to extract training sample: {e}")
        return None


def generate_training_data(
    n_samples: int,
    random_seed: int,
) -> List[TrainingSample]:
    """
    Generate training samples by calling run_stress_check on synthetic configs.
    
    Args:
        n_samples: Target number of valid samples to generate
        random_seed: Random seed for reproducibility
    
    Returns:
        List of TrainingSample instances
    """
    # Set random seeds
    rng = random.Random(random_seed)
    np_rng = np.random.default_rng(random_seed)
    
    samples: List[TrainingSample] = []
    error_count = 0
    
    # Generate samples: 50% around-threshold, 50% broad
    n_around_threshold = n_samples // 2
    n_broad = n_samples - n_around_threshold
    
    logging.info(f"Generating {n_samples} samples (seed={random_seed})...")
    logging.info(f"  - {n_around_threshold} around-threshold regime")
    logging.info(f"  - {n_broad} broad regime")
    
    # Generate around-threshold samples
    for i in range(n_around_threshold * 2):  # Generate extra to account for failures
        if len(samples) >= n_samples:
            break
        
        try:
            config = generate_sample_config("around_threshold", rng, np_rng)
            
            # Build StressCheckRequest
            req = StressCheckRequest(
                monthly_income=config["income_monthly"],
                other_debts_monthly=config["other_debt_monthly"],
                list_price=config["home_price"],
                down_payment_pct=config["down_payment_pct"],
                zip_code=config["zip_code"],
                state=config["state"],
                hoa_monthly=0.0,  # Can vary this if needed
                risk_preference=rng.choice(["conservative", "neutral", "aggressive"]),
            )
            
            # Call run_stress_check
            stress_response = run_stress_check(req)
            
            # Extract training sample
            sample = extract_training_sample(config, stress_response)
            if sample is not None:
                samples.append(sample)
            
            if (i + 1) % 100 == 0:
                logging.info(f"  Generated {len(samples)}/{n_samples} valid samples...")
        
        except Exception as e:
            error_count += 1
            if error_count <= 10:  # Log first 10 errors
                logging.warning(f"Error generating sample {i+1}: {e}")
            continue
    
    # Generate broad regime samples
    for i in range(n_broad * 2):  # Generate extra to account for failures
        if len(samples) >= n_samples:
            break
        
        try:
            config = generate_sample_config("broad", rng, np_rng)
            
            # Build StressCheckRequest
            req = StressCheckRequest(
                monthly_income=config["income_monthly"],
                other_debts_monthly=config["other_debt_monthly"],
                list_price=config["home_price"],
                down_payment_pct=config["down_payment_pct"],
                zip_code=config["zip_code"],
                state=config["state"],
                hoa_monthly=rng.uniform(0.0, 500.0),
                risk_preference=rng.choice(["conservative", "neutral", "aggressive"]),
            )
            
            # Call run_stress_check
            stress_response = run_stress_check(req)
            
            # Extract training sample
            sample = extract_training_sample(config, stress_response)
            if sample is not None:
                samples.append(sample)
            
            if (i + 1) % 100 == 0:
                logging.info(f"  Generated {len(samples)}/{n_samples} valid samples...")
        
        except Exception as e:
            error_count += 1
            if error_count <= 10:  # Log first 10 errors
                logging.warning(f"Error generating sample {i+1}: {e}")
            continue
    
    logging.info(f"Generated {len(samples)} valid samples (errors: {error_count})")
    return samples[:n_samples]  # Return exactly n_samples


def save_training_data(
    samples: List[TrainingSample],
    output_path: str,
) -> None:
    """
    Save training samples to parquet or CSV.
    
    Args:
        samples: List of TrainingSample instances
        output_path: Output file path (.parquet or .csv)
    """
    # Convert to DataFrame
    data = []
    for sample in samples:
        data.append({
            "income_monthly": sample.income_monthly,
            "other_debt_monthly": sample.other_debt_monthly,
            "home_price": sample.home_price,
            "down_payment_pct": sample.down_payment_pct,
            "interest_rate": sample.interest_rate,
            "loan_term_years": sample.loan_term_years,
            "state": sample.state,
            "zip_code": sample.zip_code,
            "ltv": sample.ltv,
            "dti": sample.dti,
            "payment_to_income": sample.payment_to_income,
            "cash_buffer_ratio": sample.cash_buffer_ratio,
            "teacher_bucket": sample.teacher_bucket,
            "teacher_approve_label": sample.teacher_approve_label,
        })
    
    df = pd.DataFrame(data)
    
    # Save to file
    output_path_obj = Path(output_path)
    if output_path_obj.suffix == ".parquet":
        try:
            df.to_parquet(output_path, index=False)
        except ImportError as e:
            # Fallback to CSV if parquet engine not available
            logging.warning(f"Parquet engine not available: {e}")
            logging.warning(f"Falling back to CSV format...")
            csv_path = str(output_path_obj.with_suffix(".csv"))
            df.to_csv(csv_path, index=False)
            logging.info(f"Saved to {csv_path} instead")
            return
    else:
        df.to_csv(output_path, index=False)
    
    logging.info(f"Saved {len(samples)} samples to {output_path}")


def print_summary(samples: List[TrainingSample]) -> None:
    """Print summary statistics of generated samples."""
    if not samples:
        print("No samples generated!")
        return
    
    # Count by teacher_bucket
    bucket_counts = defaultdict(int)
    for sample in samples:
        bucket_counts[sample.teacher_bucket] += 1
    
    # Compute DTI and LTV stats
    dti_values = [s.dti for s in samples]
    ltv_values = [s.ltv for s in samples]
    
    print("\n" + "=" * 80)
    print("Training Data Generation Summary")
    print("=" * 80)
    print(f"\nTotal valid samples: {len(samples)}")
    
    print(f"\nTeacher Bucket Distribution:")
    for bucket in ["likely", "borderline", "unlikely"]:
        count = bucket_counts[bucket]
        pct = (count / len(samples) * 100) if samples else 0.0
        print(f"  {bucket:12s}: {count:4d} ({pct:5.1f}%)")
    
    print(f"\nDTI Statistics:")
    print(f"  Mean:   {np.mean(dti_values):.3f}")
    print(f"  Median: {np.median(dti_values):.3f}")
    print(f"  Min:    {np.min(dti_values):.3f}")
    print(f"  Max:    {np.max(dti_values):.3f}")
    print(f"  Samples in 35-55% range: {sum(0.35 <= d <= 0.55 for d in dti_values)} ({sum(0.35 <= d <= 0.55 for d in dti_values) / len(dti_values) * 100:.1f}%)")
    
    print(f"\nLTV Statistics:")
    print(f"  Mean:   {np.mean(ltv_values):.3f}")
    print(f"  Median: {np.median(ltv_values):.3f}")
    print(f"  Min:    {np.min(ltv_values):.3f}")
    print(f"  Max:    {np.max(ltv_values):.3f}")
    print(f"  Samples in 70-100% range: {sum(0.70 <= l <= 1.00 for l in ltv_values)} ({sum(0.70 <= l <= 1.00 for l in ltv_values) / len(ltv_values) * 100:.1f}%)")
    
    print("\n" + "=" * 80)


# ============================================================================
# Main
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate training data for ML-based ApprovalScore (distillation from rules)"
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=5000,
        help="Target number of valid samples to generate (default: 5000)",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output file path (.parquet or .csv)",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
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
    
    # Generate training data
    samples = generate_training_data(
        n_samples=args.n_samples,
        random_seed=args.random_seed,
    )
    
    # Save to file
    save_training_data(samples, args.output)
    
    # Print summary
    print_summary(samples)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

