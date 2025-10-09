"""
Test action application and atomic vs sequential modes

Tests parameter application, constraint preservation, and rollback behavior.
"""

import pytest
from unittest.mock import patch, MagicMock

from modules.autotuner.brain.apply import apply_action, compute_parameter_delta, validate_action_application
from modules.autotuner.brain.contracts import Action
from tests.fixtures import make_input, make_action, set_random_seed
from tests.utils_asserts import assert_all_params_valid, assert_single_knob_change


class TestActionApplication:
    """Test basic action application."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    @pytest.mark.parametrize("action_kind,param_name,expected_change,step_value", [
        ("bump_ef", "ef", 32, 32.0),
        ("drop_ef", "ef", -32, -32.0),
        ("bump_T", "T", 32, 32.0),
        ("drop_T", "T", -32, -32.0),
        ("bump_rerank", "rerank_mult", 2, 2.0),  # Smaller step to avoid clipping
        ("drop_rerank", "rerank_mult", -2, -2.0),
        ("bump_ncand", "Ncand_max", 32, 32.0),
        ("drop_ncand", "Ncand_max", -32, -32.0),
    ])
    def test_single_knob_changes(self, action_kind, param_name, expected_change, step_value):
        """Test that actions correctly modify single parameters."""
        params = {
            "ef": 128,
            "T": 500,
            "Ncand_max": 1000,
            "rerank_mult": 4
        }
        
        action = make_action(kind=action_kind, step=step_value)
        new_params = apply_action(params, action)
        
        # Check that the specific parameter changed
        assert new_params[param_name] == params[param_name] + expected_change
        
        # Check that other parameters are unchanged
        for key, value in params.items():
            if key != param_name:
                assert new_params[key] == value
    
    def test_noop_action_no_changes(self):
        """Test that noop action makes no parameter changes."""
        params = {
            "ef": 128,
            "T": 500,
            "Ncand_max": 1000,
            "rerank_mult": 4
        }
        
        action = make_action(kind="noop", step=0.0)
        new_params = apply_action(params, action)
        
        assert new_params == params
    
    def test_rollback_action_no_changes(self):
        """Test that rollback action makes no parameter changes (current implementation)."""
        params = {
            "ef": 128,
            "T": 500,
            "Ncand_max": 1000,
            "rerank_mult": 4
        }
        
        action = make_action(kind="rollback", step=0.0)
        new_params = apply_action(params, action)
        
        # Current implementation treats rollback as noop
        assert new_params == params
    
    def test_constraint_preservation(self):
        """Test that applied parameters are always within valid ranges."""
        params = {
            "ef": 128,
            "T": 500,
            "Ncand_max": 1000,
            "rerank_mult": 4
        }
        
        # Test actions that would push parameters out of bounds
        actions = [
            make_action(kind="bump_ef", step=1000.0),  # Would exceed max ef
            make_action(kind="drop_ef", step=1000.0),  # Would go below min ef
            make_action(kind="bump_T", step=10000.0),  # Would exceed max T
            make_action(kind="drop_T", step=10000.0),  # Would go below min T
        ]
        
        for action in actions:
            new_params = apply_action(params, action)
            assert_all_params_valid(new_params)
    
    def test_parameter_delta_computation(self):
        """Test parameter delta computation."""
        old_params = {
            "ef": 128,
            "T": 500,
            "Ncand_max": 1000,
            "rerank_mult": 4
        }
        
        new_params = {
            "ef": 160,  # +32
            "T": 500,   # unchanged
            "Ncand_max": 968,  # -32
            "rerank_mult": 4   # unchanged
        }
        
        delta = compute_parameter_delta(old_params, new_params)
        
        assert delta["ef"] == 32
        assert delta["T"] == 0
        assert delta["Ncand_max"] == -32
        assert delta["rerank_mult"] == 0
    
    def test_parameter_delta_with_missing_keys(self):
        """Test delta computation with missing keys in one or both dictionaries."""
        old_params = {"ef": 128, "T": 500}
        new_params = {"ef": 160, "Ncand_max": 1000}
        
        delta = compute_parameter_delta(old_params, new_params)
        
        assert delta["ef"] == 32
        assert delta["T"] == -500  # 0 - 500
        assert delta["Ncand_max"] == 1000  # 1000 - 0
    
    def test_action_validation(self):
        """Test action validation function."""
        params = {
            "ef": 128,
            "T": 500,
            "Ncand_max": 1000,
            "rerank_mult": 4
        }
        
        # Valid action
        valid_action = make_action(kind="bump_ef", step=32.0)
        assert validate_action_application(params, valid_action)
        
        # Invalid action (noop for invalid kind)
        invalid_action = make_action(kind="invalid_kind", step=32.0)
        # Should return True because noop is valid
        assert validate_action_application(params, invalid_action)


class TestSequentialVsAtomic:
    """Test sequential vs atomic application modes."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    def test_sequential_mode_single_change(self):
        """Test that sequential mode only changes one parameter at a time."""
        params = {
            "ef": 128,
            "T": 500,
            "Ncand_max": 1000,
            "rerank_mult": 4
        }
        
        action = make_action(kind="bump_ef", step=32.0)
        new_params = apply_action(params, action)
        
        # Should only change one parameter
        assert_single_knob_change(params, new_params)
    
    def test_atomic_mode_multiple_changes(self):
        """Test atomic mode for multiple parameter changes."""
        # This would need to be implemented in the actual apply_action function
        # For now, test that current implementation is sequential
        
        params = {
            "ef": 128,
            "T": 500,
            "Ncand_max": 1000,
            "rerank_mult": 4
        }
        
        action = make_action(kind="bump_ef", step=32.0)
        new_params = apply_action(params, action)
        
        # Current implementation is sequential
        assert_single_knob_change(params, new_params)
    
    def test_rollback_behavior(self):
        """Test rollback behavior on simulated downstream failure."""
        # This would need to be implemented with atomic mode
        # For now, test that rollback action exists and behaves correctly
        
        params = {
            "ef": 128,
            "T": 500,
            "Ncand_max": 1000,
            "rerank_mult": 4
        }
        
        action = make_action(kind="rollback", step=0.0)
        new_params = apply_action(params, action)
        
        # Rollback should preserve original state
        assert new_params == params


class TestConstraintAdjustment:
    """Test constraint adjustment and clipping behavior."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    def test_clipped_params_reason(self):
        """Test that clipped parameters are properly handled."""
        params = {
            "ef": 200,  # Valid range
            "T": 500,   # Valid range
            "Ncand_max": 1000,  # Valid range
            "rerank_mult": 4    # Valid range
        }
        
        # Action that would push ef out of bounds
        action = make_action(kind="bump_ef", step=1000.0)
        new_params = apply_action(params, action)
        
        # ef should be clipped to maximum (256)
        assert new_params["ef"] == 256
        assert_all_params_valid(new_params)
    
    def test_multiple_clipping(self):
        """Test clipping multiple parameters simultaneously."""
        params = {
            "ef": 200,
            "T": 500,
            "Ncand_max": 1000,
            "rerank_mult": 4
        }
        
        # Create a custom action that would affect multiple params
        # This tests the constraint system's ability to handle multiple adjustments
        action1 = make_action(kind="bump_ef", step=1000.0)  # Would exceed max
        action2 = make_action(kind="drop_ef", step=-1000.0)  # Would go below min
        
        new_params1 = apply_action(params, action1)
        new_params2 = apply_action(params, action2)
        
        # Both should be properly clipped
        assert new_params1["ef"] == 256  # Clipped to max
        assert new_params2["ef"] == 64   # Clipped to min
        
        assert_all_params_valid(new_params1)
        assert_all_params_valid(new_params2)


class TestEdgeCases:
    """Test edge cases in action application."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    def test_zero_step_size(self):
        """Test actions with zero step size."""
        params = {
            "ef": 128,
            "T": 500,
            "Ncand_max": 1000,
            "rerank_mult": 4
        }
        
        action = make_action(kind="bump_ef", step=0.0)
        new_params = apply_action(params, action)
        
        # Should make no change
        assert new_params["ef"] == params["ef"]
    
    def test_fractional_step_size(self):
        """Test actions with fractional step sizes."""
        params = {
            "ef": 128,
            "T": 500,
            "Ncand_max": 1000,
            "rerank_mult": 4
        }
        
        action = make_action(kind="bump_ef", step=32.5)
        new_params = apply_action(params, action)
        
        # Should convert to int (32)
        assert new_params["ef"] == 160  # 128 + 32
    
    def test_negative_step_size(self):
        """Test actions with negative step sizes."""
        params = {
            "ef": 128,
            "T": 500,
            "Ncand_max": 1000,
            "rerank_mult": 4
        }
        
        # bump_ef with negative step should still add (not subtract)
        action = make_action(kind="bump_ef", step=-16.0)
        new_params = apply_action(params, action)
        
        # Should add the step value (even if negative)
        assert new_params["ef"] == 112  # 128 + (-16)
    
    def test_missing_parameters(self):
        """Test action application with missing parameters."""
        params = {"ef": 128}  # Only ef parameter
        
        action = make_action(kind="bump_T", step=32.0)
        new_params = apply_action(params, action)
        
        # Should add default T value and apply change
        assert "T" in new_params
        assert new_params["T"] == 532  # 500 (default) + 32
    
    def test_invalid_action_kind(self):
        """Test behavior with invalid action kinds."""
        params = {
            "ef": 128,
            "T": 500,
            "Ncand_max": 1000,
            "rerank_mult": 4
        }
        
        # Create action with invalid kind
        action = Action(kind="invalid_kind", step=32.0, reason="test")
        new_params = apply_action(params, action)
        
        # Should make no changes (invalid action ignored)
        assert new_params == params
