"""
Test hysteresis and cooldown mechanisms

Tests oscillation prevention through hysteresis bands and cooldown windows.
"""

import pytest
import time
from unittest.mock import patch, MagicMock

from modules.autotuner.brain.decider import decide_tuning_action
from modules.autotuner.brain.constraints import hysteresis
from modules.autotuner.brain.contracts import TuningInput, SLO, Guards, Action
from tests.fixtures import make_input, make_action, set_random_seed
from tests.utils_asserts import assert_action_properties


class TestHysteresis:
    """Test hysteresis band behavior."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    def test_hysteresis_function_basic(self):
        """Test basic hysteresis function behavior."""
        # Test within band
        assert hysteresis(150.0, 150.0, 100.0) == True
        assert hysteresis(200.0, 150.0, 100.0) == True   # Within band
        assert hysteresis(100.0, 150.0, 100.0) == True   # Within band
        
        # Test outside band
        assert hysteresis(260.0, 150.0, 100.0) == False  # Outside band
        assert hysteresis(40.0, 150.0, 100.0) == False   # Outside band
    
    def test_hysteresis_band_noop(self):
        """Test that hysteresis band triggers noop actions."""
        slo = SLO(p95_ms=150.0, recall_at10=0.80)
        
        # Test cases within hysteresis band
        test_cases = [
            {"p95_ms": 155.0, "recall_at10": 0.81},  # Both within band
            {"p95_ms": 145.0, "recall_at10": 0.79},  # Both within band
            {"p95_ms": 200.0, "recall_at10": 0.81},  # P95 outside, recall within
            {"p95_ms": 155.0, "recall_at10": 0.85},  # P95 within, recall outside
        ]
        
        for case in test_cases:
            inp = make_input(
                p95_ms=case["p95_ms"],
                recall_at10=case["recall_at10"],
                slo=slo
            )
            
            with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
                mock_memory.return_value = MagicMock()
                mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
                mock_memory.return_value.query.return_value = None
                
                action = decide_tuning_action(inp)
                
                # Should return noop if both metrics are within hysteresis band
                if (abs(case["p95_ms"] - slo.p95_ms) < 100 and 
                    abs(case["recall_at10"] - slo.recall_at10) < 0.02):
                    assert_action_properties(
                        action,
                        expected_kind="noop",
                        expected_reason_contains="hysteresis"
                    )
    
    def test_hysteresis_band_allows_action(self):
        """Test that metrics outside hysteresis band allow actions."""
        slo = SLO(p95_ms=150.0, recall_at10=0.80)
        
        # Test cases outside hysteresis band
        test_cases = [
            {"p95_ms": 300.0, "recall_at10": 0.90},  # High latency, good recall
            {"p95_ms": 80.0, "recall_at10": 0.65},   # Low latency, poor recall
        ]
        
        for case in test_cases:
            inp = make_input(
                p95_ms=case["p95_ms"],
                recall_at10=case["recall_at10"],
                slo=slo
            )
            
            with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
                mock_memory.return_value = MagicMock()
                mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
                mock_memory.return_value.query.return_value = None
                
                action = decide_tuning_action(inp)
                
                # Should not return noop with hysteresis reason
                assert action.kind != "noop" or "hysteresis" not in action.reason
    
    def test_hysteresis_edge_cases(self):
        """Test hysteresis behavior at exact band boundaries."""
        slo = SLO(p95_ms=150.0, recall_at10=0.80)
        
        # Exact boundary cases
        boundary_cases = [
            {"p95_ms": 250.0, "recall_at10": 0.82},  # Exactly at P95 band edge
            {"p95_ms": 50.0, "recall_at10": 0.78},   # Exactly at P95 band edge
            {"p95_ms": 155.0, "recall_at10": 0.82},  # Exactly at recall band edge
            {"p95_ms": 145.0, "recall_at10": 0.78},  # Exactly at recall band edge
        ]
        
        for case in boundary_cases:
            inp = make_input(
                p95_ms=case["p95_ms"],
                recall_at10=case["recall_at10"],
                slo=slo
            )
            
            with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
                mock_memory.return_value = MagicMock()
                mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
                mock_memory.return_value.query.return_value = None
                
                action = decide_tuning_action(inp)
                
                # Boundary behavior should be deterministic
                assert action is not None


class TestCooldown:
    """Test cooldown mechanism behavior."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    def test_cooldown_blocks_repeat_action(self):
        """Test that cooldown blocks repeated actions within time window."""
        # Create recent action
        recent_action = make_action(
            kind="bump_ef",
            step=32.0,
            age_sec=5.0  # Recent action (less than 10s)
        )
        
        inp = make_input(
            last_action=recent_action,
            guards=Guards(cooldown=False, stable=False),  # Not in cooldown guard
            p95_ms=40.0,  # Low latency to trigger bump_ef
            recall_at10=0.65,
            slo=SLO(p95_ms=150.0, recall_at10=0.80),
            params={"ef": 128}  # Ensure ef is not at max
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            assert_action_properties(
                action,
                expected_kind="noop",
                expected_reason_contains="cooldown"
            )
    
    def test_cooldown_expires_after_window(self):
        """Test that cooldown expires after time window."""
        # Create old action
        old_action = make_action(
            kind="bump_ef",
            step=32.0,
            age_sec=15.0  # Old action (more than 10s)
        )
        
        inp = make_input(
            last_action=old_action,
            guards=Guards(cooldown=False, stable=False),
            p95_ms=80.0,  # Would normally trigger bump_ef
            recall_at10=0.65,
            slo=SLO(p95_ms=150.0, recall_at10=0.80)
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            # Should allow action after cooldown expires
            assert action.kind != "noop" or "cooldown" not in action.reason
    
    def test_cooldown_different_action_allowed(self):
        """Test that different actions are allowed even with recent action."""
        # Create recent action
        recent_action = make_action(
            kind="bump_ef",
            step=32.0,
            age_sec=5.0  # Recent action
        )
        
        inp = make_input(
            last_action=recent_action,
            guards=Guards(cooldown=False, stable=False),
            p95_ms=300.0,  # Would trigger drop_ef (different from bump_ef)
            recall_at10=0.90,
            slo=SLO(p95_ms=150.0, recall_at10=0.80)
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            # Different action should be allowed
            assert action.kind != "noop" or "cooldown" not in action.reason
    
    def test_cooldown_guard_takes_precedence(self):
        """Test that cooldown guard takes precedence over action-based cooldown."""
        inp = make_input(
            guards=Guards(cooldown=True, stable=False),  # Explicit cooldown guard
            p95_ms=80.0,
            recall_at10=0.65,
            slo=SLO(p95_ms=150.0, recall_at10=0.80)
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            assert_action_properties(
                action,
                expected_kind="noop",
                expected_reason_contains="cooldown"
            )
    
    def test_cooldown_window_boundary(self):
        """Test cooldown behavior at exact time boundary."""
        # Test exactly at 10 second boundary
        boundary_action = make_action(
            kind="bump_ef",
            step=32.0,
            age_sec=10.0  # Exactly at boundary
        )
        
        inp = make_input(
            last_action=boundary_action,
            guards=Guards(cooldown=False, stable=False),
            p95_ms=80.0,
            recall_at10=0.65,
            slo=SLO(p95_ms=150.0, recall_at10=0.80)
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            # Boundary behavior should be deterministic
            assert action is not None
    
    def test_cooldown_no_last_action(self):
        """Test cooldown behavior when no last action exists."""
        inp = make_input(
            last_action=None,  # No previous action
            guards=Guards(cooldown=False, stable=False),
            p95_ms=80.0,
            recall_at10=0.65,
            slo=SLO(p95_ms=150.0, recall_at10=0.80)
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            # Should allow action when no previous action
            assert action.kind != "noop" or "cooldown" not in action.reason


class TestHysteresisCooldownInteraction:
    """Test interaction between hysteresis and cooldown mechanisms."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    def test_hysteresis_and_cooldown_both_active(self):
        """Test behavior when both hysteresis and cooldown are active."""
        recent_action = make_action(
            kind="bump_ef",
            step=32.0,
            age_sec=5.0  # Recent action
        )
        
        inp = make_input(
            last_action=recent_action,
            guards=Guards(cooldown=False, stable=False),
            p95_ms=155.0,  # Within hysteresis band
            recall_at10=0.81,  # Within hysteresis band
            slo=SLO(p95_ms=150.0, recall_at10=0.80)
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            # Should return noop due to hysteresis (cooldown should not be checked)
            assert_action_properties(
                action,
                expected_kind="noop",
                expected_reason_contains="hysteresis"
            )
    
    def test_cooldown_takes_precedence_over_hysteresis(self):
        """Test that cooldown guard takes precedence over hysteresis."""
        inp = make_input(
            guards=Guards(cooldown=True, stable=False),  # Explicit cooldown
            p95_ms=155.0,  # Within hysteresis band
            recall_at10=0.81,  # Within hysteresis band
            slo=SLO(p95_ms=150.0, recall_at10=0.80)
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            # Should return noop due to cooldown guard (not hysteresis)
            assert_action_properties(
                action,
                expected_kind="noop",
                expected_reason_contains="cooldown"
            )
    
    def test_oscillation_prevention(self):
        """Test that hysteresis and cooldown work together to prevent oscillation."""
        # Simulate oscillation scenario
        oscillation_sequence = [
            {"p95_ms": 160.0, "recall_at10": 0.80, "last_action": None},
            {"p95_ms": 140.0, "recall_at10": 0.82, "last_action": "bump_ef"},
            {"p95_ms": 160.0, "recall_at10": 0.80, "last_action": "drop_ef"},
            {"p95_ms": 140.0, "recall_at10": 0.82, "last_action": "bump_ef"},
        ]
        
        slo = SLO(p95_ms=150.0, recall_at10=0.80)
        
        for i, case in enumerate(oscillation_sequence):
            last_action = None
            if case["last_action"]:
                last_action = make_action(
                    kind=case["last_action"],
                    step=32.0,
                    age_sec=2.0  # Recent action
                )
            
            inp = make_input(
                p95_ms=case["p95_ms"],
                recall_at10=case["recall_at10"],
                slo=slo,
                last_action=last_action,
                guards=Guards(cooldown=False, stable=False)
            )
            
            with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
                mock_memory.return_value = MagicMock()
                mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
                mock_memory.return_value.query.return_value = None
                
                action = decide_tuning_action(inp)
                
                # Should prevent oscillation through hysteresis or cooldown
                if i > 0:  # After first iteration
                    assert action.kind == "noop", f"Expected noop to prevent oscillation, got {action.kind}"
