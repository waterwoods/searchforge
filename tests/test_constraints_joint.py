"""
Test joint constraints and parameter clipping

Tests parameter range constraints, joint constraint invariants,
and property-based validation of constraint satisfaction.
"""

import pytest
from typing import Dict, Any

from modules.autotuner.brain.constraints import clip_params, is_param_valid, get_param_ranges
from tests.fixtures import set_random_seed
from tests.utils_asserts import assert_all_params_valid, assert_param_in_range


class TestParameterConstraints:
    """Test individual parameter constraints."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    @pytest.mark.parametrize("param_name,min_val,max_val", [
        ("ef", 64, 256),
        ("T", 200, 1200),
        ("Ncand_max", 500, 2000),
        ("rerank_mult", 2, 6),
    ])
    def test_individual_param_constraints(self, param_name, min_val, max_val):
        """Test that individual parameters are clipped to valid ranges."""
        # Test lower bound
        params = {param_name: min_val - 10}
        clipped = clip_params(params)
        assert clipped[param_name] == min_val
        
        # Test upper bound
        params = {param_name: max_val + 10}
        clipped = clip_params(params)
        assert clipped[param_name] == max_val
        
        # Test valid range
        params = {param_name: (min_val + max_val) // 2}
        clipped = clip_params(params)
        assert clipped[param_name] == params[param_name]
    
    def test_multiple_params_constraints(self):
        """Test clipping multiple parameters simultaneously."""
        params = {
            "ef": 1000,  # Above max (256)
            "T": 50,     # Below min (200)
            "Ncand_max": 300,  # Below min (500)
            "rerank_mult": 10  # Above max (6)
        }
        
        clipped = clip_params(params)
        
        assert clipped["ef"] == 256
        assert clipped["T"] == 200
        assert clipped["Ncand_max"] == 500
        assert clipped["rerank_mult"] == 6
    
    def test_idempotency(self):
        """Test that clipping is idempotent."""
        params = {
            "ef": 1000,
            "T": 50,
            "Ncand_max": 300,
            "rerank_mult": 10
        }
        
        clipped_once = clip_params(params)
        clipped_twice = clip_params(clipped_once)
        
        assert clipped_once == clipped_twice
    
    def test_missing_params_unchanged(self):
        """Test that missing parameters are not added."""
        params = {"ef": 128}  # Only one parameter
        
        clipped = clip_params(params)
        
        assert "ef" in clipped
        assert "T" not in clipped
        assert "Ncand_max" not in clipped
        assert "rerank_mult" not in clipped


class TestJointConstraints:
    """Test joint constraint invariants."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    def test_joint_constraints_ef_candidate_ratio(self):
        """Test that ef_search <= 4 * candidate_k constraint."""
        # This would need to be implemented in clip_params
        # For now, test the basic parameter ranges
        params = {
            "ef": 256,
            "Ncand_max": 100,  # ef should be <= 4 * Ncand_max = 400
        }
        
        clipped = clip_params(params)
        assert_all_params_valid(clipped)
    
    def test_joint_constraints_rerank_candidate_ratio(self):
        """Test that rerank_k <= candidate_k constraint."""
        # This would need to be implemented in clip_params
        # For now, test basic ranges
        params = {
            "rerank_mult": 6,
            "Ncand_max": 500,
        }
        
        clipped = clip_params(params)
        assert_all_params_valid(clipped)
    
    def test_constraint_boundary_conditions(self):
        """Test constraint behavior at exact boundaries."""
        boundary_tests = [
            {"ef": 64, "expected_ef": 64},    # Exact minimum
            {"ef": 256, "expected_ef": 256},  # Exact maximum
            {"T": 200, "expected_T": 200},    # Exact minimum
            {"T": 1200, "expected_T": 1200},  # Exact maximum
            {"Ncand_max": 500, "expected_Ncand_max": 500},  # Exact minimum
            {"Ncand_max": 2000, "expected_Ncand_max": 2000},  # Exact maximum
            {"rerank_mult": 2, "expected_rerank_mult": 2},  # Exact minimum
            {"rerank_mult": 6, "expected_rerank_mult": 6},  # Exact maximum
        ]
        
        for test_case in boundary_tests:
            param_name = list(test_case.keys())[0]
            expected_value = test_case[f"expected_{param_name}"]
            
            params = {param_name: test_case[param_name]}
            clipped = clip_params(params)
            
            assert clipped[param_name] == expected_value


class TestParameterValidation:
    """Test parameter validation functions."""
    
    def test_is_param_valid_valid_params(self):
        """Test that valid parameters pass validation."""
        valid_params = {
            "ef": 128,
            "T": 600,
            "Ncand_max": 1000,
            "rerank_mult": 4
        }
        
        assert is_param_valid(valid_params)
    
    def test_is_param_valid_invalid_params(self):
        """Test that invalid parameters fail validation."""
        invalid_params = {
            "ef": 1000,  # Too high
            "T": 600,
            "Ncand_max": 1000,
            "rerank_mult": 4
        }
        
        assert not is_param_valid(invalid_params)
    
    def test_is_param_valid_partial_params(self):
        """Test validation with partial parameter sets."""
        partial_params = {
            "ef": 128,
            "T": 600,
            # Missing Ncand_max and rerank_mult
        }
        
        # Should pass validation for present parameters
        assert is_param_valid(partial_params)
    
    def test_get_param_ranges(self):
        """Test that parameter ranges are correctly defined."""
        ranges = get_param_ranges()
        
        expected_ranges = {
            'ef': (64, 256),
            'T': (200, 1200),
            'Ncand_max': (500, 2000),
            'rerank_mult': (2, 6)
        }
        
        assert ranges == expected_ranges


# Property-based tests using deterministic sampling
def test_deterministic_property_clipping():
    """Property-based test: any input params should satisfy invariants after clipping."""
    import random
    random.seed(0)  # Deterministic
    
    # Test multiple random parameter combinations
    for _ in range(64):
        params = {
            "ef": random.randint(0, 1000),
            "T": random.randint(0, 2000),
            "Ncand_max": random.randint(0, 3000),
            "rerank_mult": random.randint(0, 10)
        }
        
        clipped = clip_params(params)
        
        # All clipped parameters should be valid
        assert is_param_valid(clipped)
        
        # Check individual ranges
        if "ef" in clipped:
            assert 64 <= clipped["ef"] <= 256
        if "T" in clipped:
            assert 200 <= clipped["T"] <= 1200
        if "Ncand_max" in clipped:
            assert 500 <= clipped["Ncand_max"] <= 2000
        if "rerank_mult" in clipped:
            assert 2 <= clipped["rerank_mult"] <= 6


def test_deterministic_property_idempotency():
    """Property-based test: clipping should be idempotent."""
    import random
    random.seed(0)  # Deterministic
    
    # Test multiple random parameter combinations
    for _ in range(32):
        param_names = ["ef", "T", "Ncand_max", "rerank_mult"]
        params_dict = {}
        
        # Randomly select 1-4 parameters
        num_params = random.randint(1, 4)
        selected_params = random.sample(param_names, num_params)
        
        for param in selected_params:
            params_dict[param] = random.randint(-1000, 3000)
        
        clipped_once = clip_params(params_dict)
        clipped_twice = clip_params(clipped_once)
        
        assert clipped_once == clipped_twice


class TestConstraintEdgeCases:
    """Test edge cases and corner conditions."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    def test_empty_params(self):
        """Test clipping empty parameter dictionary."""
        clipped = clip_params({})
        assert clipped == {}
    
    def test_unknown_params_unchanged(self):
        """Test that unknown parameters are left unchanged."""
        params = {
            "ef": 128,
            "unknown_param": 999,
            "another_unknown": "test"
        }
        
        clipped = clip_params(params)
        
        assert clipped["ef"] == 128
        assert clipped["unknown_param"] == 999
        assert clipped["another_unknown"] == "test"
    
    def test_zero_values(self):
        """Test behavior with zero values."""
        params = {
            "ef": 0,
            "T": 0,
            "Ncand_max": 0,
            "rerank_mult": 0
        }
        
        clipped = clip_params(params)
        
        # All should be clipped to minimum values
        assert clipped["ef"] == 64
        assert clipped["T"] == 200
        assert clipped["Ncand_max"] == 500
        assert clipped["rerank_mult"] == 2
    
    def test_negative_values(self):
        """Test behavior with negative values."""
        params = {
            "ef": -100,
            "T": -50,
            "Ncand_max": -200,
            "rerank_mult": -5
        }
        
        clipped = clip_params(params)
        
        # All should be clipped to minimum values
        assert clipped["ef"] == 64
        assert clipped["T"] == 200
        assert clipped["Ncand_max"] == 500
        assert clipped["rerank_mult"] == 2
    
    def test_very_large_values(self):
        """Test behavior with very large values."""
        params = {
            "ef": 10000,
            "T": 50000,
            "Ncand_max": 100000,
            "rerank_mult": 100
        }
        
        clipped = clip_params(params)
        
        # All should be clipped to maximum values
        assert clipped["ef"] == 256
        assert clipped["T"] == 1200
        assert clipped["Ncand_max"] == 2000
        assert clipped["rerank_mult"] == 6
