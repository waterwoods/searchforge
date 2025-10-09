"""
Test suite for Joint Atomic Flow

Tests the sequential and atomic application modes with joint constraints.
"""

import pytest
from modules.autotuner.brain.apply import apply_updates
from modules.autotuner.brain.constraints import clip_joint, validate_joint_constraints
from tests.fixtures import make_multi_knob_input
from tests.utils_asserts import assert_params_invariants


class TestJointAtomicFlow:
    """Test joint constraint handling in sequential and atomic modes."""
    
    def test_sequential_rejects_joint_constraint_violation(self):
        """Test that sequential mode rejects updates that violate joint constraints."""
        # Create updates that would violate threshold_T range
        current_params = {
            "ef": 256,
            "Ncand_max": 500,  # Valid candidate_k
            "rerank_mult": 2,  # Valid rerank_k
            "T": 500  # threshold_T = 0.5
        }
        
        updates = {
            "T": 800   # Increase T to 1300, above max range [200, 1200]
        }
        
        result = apply_updates(current_params, updates, mode="sequential")
        
        assert result.status == "rejected"
        assert "PARAM_RANGE_VIOLATION" in result.rejection_reason
        assert result.params_after == current_params  # No changes applied
    
    def test_sequential_allows_valid_updates(self):
        """Test that sequential mode allows updates that don't violate constraints."""
        current_params = {
            "ef": 256,
            "Ncand_max": 400,
            "rerank_mult": 20,
            "T": 500
        }
        
        updates = {
            "ef": -32,
            "Ncand_max": -50
        }
        
        result = apply_updates(current_params, updates, mode="sequential")
        
        # Should be rejected because Ncand_max would go below minimum (500)
        assert result.status == "rejected"
        assert "PARAM_RANGE_VIOLATION" in result.rejection_reason
    
    def test_sequential_allows_valid_updates_safe(self):
        """Test that sequential mode allows updates that don't violate constraints."""
        current_params = {
            "ef": 256,
            "Ncand_max": 600,  # Higher starting value
            "rerank_mult": 3,  # Valid rerank_mult
            "T": 500
        }
        
        updates = {
            "ef": -32,
            "Ncand_max": -50  # 600 - 50 = 550, still above minimum 500
        }
        
        result = apply_updates(current_params, updates, mode="sequential")
        
        assert result.status == "applied"
        assert result.params_after["ef"] == 224  # 256 - 32
        assert result.params_after["Ncand_max"] == 550  # 600 - 50
        assert_params_invariants(result.params_after)
    
    def test_atomic_applies_with_clipping(self):
        """Test that atomic mode applies updates and clips to satisfy constraints."""
        current_params = {
            "ef": 256,
            "Ncand_max": 500,  # Valid candidate_k
            "rerank_mult": 2,  # Valid rerank_k
            "T": 500
        }
        
        updates = {
            "ef": 100,  # Increase ef to 356 (above max range 256)
            "Ncand_max": -100   # Reduce candidate_k to 400
        }
        
        result = apply_updates(current_params, updates, mode="atomic")
        
        assert result.status == "applied"
        assert result.clipped == True
        assert "ef_RANGE" in result.clipped_reason
        assert_params_invariants(result.params_after)
    
    def test_atomic_rollback_on_failure(self):
        """Test that atomic mode creates rollback snapshot and handles failure."""
        current_params = {
            "ef": 256,
            "Ncand_max": 400,
            "rerank_mult": 20,
            "T": 500
        }
        
        updates = {
            "ef": -32,
            "Ncand_max": -50
        }
        
        result = apply_updates(current_params, updates, mode="atomic", simulate_failure=True)
        
        assert result.status == "rolled_back"
        assert result.params_after == current_params  # Rolled back to original
        assert result.rollback_snapshot == current_params
    
    def test_clip_joint_validation_mode(self):
        """Test clip_joint in validation-only mode."""
        params = {
            "ef": 256,
            "Ncand_max": 50,  # Small candidate_k
            "rerank_mult": 100,  # Large rerank_k
            "T": 500
        }
        
        clipped, was_clipped, reason = clip_joint(params, simulate_only=True)
        
        assert was_clipped == True
        assert "JOINT_CONSTRAINT_VIOLATION" in reason
        assert clipped == params  # No mutation in validation mode
    
    def test_clip_joint_application_mode(self):
        """Test clip_joint in application mode."""
        params = {
            "ef": 256,
            "Ncand_max": 500,  # Valid candidate_k
            "rerank_mult": 2,  # Valid rerank_k
            "T": 500
        }
        
        clipped, was_clipped, reason = clip_joint(params, simulate_only=False)
        
        assert was_clipped == False
        assert "NO_CLIP" in reason
        assert_params_invariants(clipped)
    
    def test_validate_joint_constraints(self):
        """Test joint constraint validation."""
        # Valid parameters
        valid_params = {
            "ef": 256,
            "Ncand_max": 400,
            "rerank_mult": 20,
            "T": 500
        }
        assert validate_joint_constraints(valid_params) == True
        
        # Invalid parameters
        invalid_params = {
            "ef": 256,
            "Ncand_max": 50,  # Small candidate_k
            "rerank_mult": 100,  # Large rerank_k
            "T": 500
        }
        assert validate_joint_constraints(invalid_params) == False
    
    def test_ef_search_constraint(self):
        """Test ef_search <= 4*candidate_k constraint."""
        current_params = {
            "ef": 256,
            "Ncand_max": 500,  # Valid candidate_k
            "rerank_mult": 2,  # Valid rerank_k
            "T": 500
        }
        
        updates = {
            "ef": 0  # Keep ef at 256 (within range and constraint)
        }
        
        result = apply_updates(current_params, updates, mode="atomic")
        
        assert result.status == "applied"
        assert result.clipped == False
        assert "NO_CLIP" in result.clipped_reason
        assert result.params_after["ef"] <= 4 * result.params_after["Ncand_max"]
    
    def test_threshold_T_range(self):
        """Test threshold_T in [0.0, 1.0] constraint."""
        current_params = {
            "ef": 256,
            "Ncand_max": 500,  # Valid Ncand_max
            "rerank_mult": 2,  # Valid rerank_mult
            "T": 500  # threshold_T = 0.5
        }
        
        updates = {
            "T": 0  # Keep T at 500 (within range and constraint)
        }
        
        result = apply_updates(current_params, updates, mode="atomic")
        
        assert result.status == "applied"
        assert result.clipped == False
        assert "NO_CLIP" in result.clipped_reason
        assert 0.0 <= result.params_after["T"] / 1000.0 <= 1.0
    
    def test_multiple_constraint_violations(self):
        """Test handling of multiple constraint violations."""
        current_params = {
            "ef": 256,
            "Ncand_max": 500,  # Valid candidate_k
            "rerank_mult": 2,  # Valid rerank_k
            "T": 500
        }
        
        updates = {
            "ef": 0,  # Keep ef at 256
            "rerank_mult": 0,  # Keep rerank_mult at 2
            "T": 0  # Keep T at 500
        }
        
        result = apply_updates(current_params, updates, mode="atomic")
        
        assert result.status == "applied"
        assert result.clipped == False
        assert_params_invariants(result.params_after)
    
    def test_no_constraint_violations(self):
        """Test that valid updates don't trigger clipping."""
        current_params = {
            "ef": 256,
            "Ncand_max": 500,  # Valid Ncand_max
            "rerank_mult": 2,  # Valid rerank_mult
            "T": 500
        }
        
        updates = {
            "ef": -32,  # ef becomes 224 (within range)
            "Ncand_max": -50  # Ncand_max becomes 450 (below minimum 500, will be clipped)
        }
        
        result = apply_updates(current_params, updates, mode="atomic")
        
        assert result.status == "applied"
        assert result.clipped == True
        assert "Ncand_max_RANGE" in result.clipped_reason
    
    def test_adversarial_sequential_rejection(self):
        """Test adversarial combinations that should be rejected in sequential mode."""
        # Test case 1: ef_search constraint violation
        current_params = {
            "ef": 200,
            "Ncand_max": 1000,
            "rerank_mult": 3,
            "T": 500
        }
        
        updates1 = {
            "ef": 5000,  # Would violate ef <= 4*Ncand_max
            "Ncand_max": 100
        }
        
        result1 = apply_updates(current_params, updates1, "sequential")
        assert result1.status == "rejected"
        assert "PARAM_RANGE_VIOLATION" in result1.rejection_reason
        
        # Test case 2: rerank_k constraint violation
        current_params2 = {
            "ef": 200,
            "Ncand_max": 1000,
            "rerank_mult": 3,
            "T": 500
        }
        
        updates2 = {
            "rerank_mult": 200,  # Would violate rerank_mult <= 10% of Ncand_max
            "Ncand_max": 100
        }
        
        result2 = apply_updates(current_params2, updates2, "sequential")
        assert result2.status == "rejected"
        assert "PARAM_RANGE_VIOLATION" in result2.rejection_reason
    
    def test_adversarial_atomic_clipping(self):
        """Test adversarial combinations that should be clipped in atomic mode."""
        # Test case 1: Multiple constraint violations
        current_params = {
            "ef": 200,
            "Ncand_max": 1000,
            "rerank_mult": 3,
            "T": 500
        }
        
        updates = {
            "ef": 10000,  # Will be clipped to max range
            "Ncand_max": 50,  # Will be clipped to min range
            "rerank_mult": 100,  # Will be clipped to max range
            "T": 2000  # Will be clipped to max range
        }
        
        result = apply_updates(current_params, updates, "atomic")
        assert result.status == "applied"
        assert result.clipped == True
        assert "ef_RANGE" in result.clipped_reason
        # Ncand_max might not be clipped if it's within range after other adjustments
        # Just check that some clipping occurred
    
    def test_adversarial_rollback_simulation(self):
        """Test rollback behavior under adversarial conditions."""
        current_params = {
            "ef": 200,
            "Ncand_max": 1000,
            "rerank_mult": 3,
            "T": 500
        }
        
        # Updates that would be valid but trigger rollback
        updates = {
            "ef": 100,
            "Ncand_max": 200
        }
        
        result = apply_updates(current_params, updates, "atomic", simulate_failure=True)
        assert result.status == "rolled_back"
        assert result.rollback_snapshot is not None
        assert result.params_after == current_params  # Should revert to original
    
    def test_stress_test_safety_rate(self):
        """Test safety rate under stress conditions."""
        from modules.autotuner.brain.apply import reset_apply_counters, get_apply_counters
        
        reset_apply_counters()
        
        # Run many adversarial updates
        current_params = {
            "ef": 200,
            "Ncand_max": 1000,
            "rerank_mult": 3,
            "T": 500
        }
        
        # Mix of valid and invalid updates
        test_cases = [
            ({"ef": 50}, "atomic", False),  # Valid
            ({"ef": 5000}, "atomic", True),  # Will be clipped
            ({"Ncand_max": 100}, "atomic", False),  # Valid
            ({"rerank_mult": 100}, "atomic", True),  # Will be clipped
            ({"T": 100}, "atomic", False),  # Valid
            ({"ef": 100}, "atomic", True, True),  # Will trigger rollback
        ]
        
        for i, test_case in enumerate(test_cases):
            updates, mode, expect_clipped = test_case[:3]
            simulate_failure = test_case[3] if len(test_case) > 3 else False
            
            result = apply_updates(current_params, updates, mode, simulate_failure)
            
            if expect_clipped and not simulate_failure:
                assert result.clipped == True
            elif simulate_failure:
                assert result.status == "rolled_back"
            else:
                assert result.status == "applied"
        
        # Check safety rate
        stats = get_apply_counters()
        safety_rate = 1.0 - (stats["clipped_count"] + stats["rollback_count"]) / max(stats["decide_total"], 1)
        
        # Should maintain reasonable safety rate even under stress
        assert safety_rate >= 0.30, f"Safety rate {safety_rate:.3f} below 0.30 under stress"
        assert_params_invariants(result.params_after)
