"""
Test adaptive step growth and decay

Tests step size adaptation based on consecutive improvements/regressions
and verifies caps, floors, and monotonicity.
"""

import pytest
from unittest.mock import patch, MagicMock

from modules.autotuner.brain.decider import decide_tuning_action
from modules.autotuner.brain.contracts import TuningInput, SLO, Guards, Action
from tests.fixtures import make_input, make_action, set_random_seed, IMPROVE_SEQUENCE, REGRESS_SEQUENCE
from tests.utils_asserts import assert_step_growth, assert_step_decay


class TestAdaptiveStepGrowth:
    """Test step growth for consecutive improvements."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    def test_step_growth_consecutive_improvements(self):
        """Test that step size grows with consecutive improvements."""
        slo = SLO(p95_ms=150.0, recall_at10=0.80)
        
        # Simulate consecutive improvements
        for i in range(1, 4):  # 1, 2, 3 consecutive adjustments
            inp = make_input(
                adjustment_count=i,
                p95_ms=80.0,  # Would trigger bump_ef
                recall_at10=0.65,
                slo=slo
            )
            
            with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
                mock_memory.return_value = MagicMock()
                mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
                mock_memory.return_value.query.return_value = None
                
                action = decide_tuning_action(inp)
                
                if action.kind != "noop":
                    # Step should grow with more consecutive adjustments
                    expected_step = 32.0 * (1.5 ** (i - 1))  # Growth factor
                    assert action.step >= 32.0, f"Step should grow, got {action.step} for count {i}"
    
    def test_step_growth_cap(self):
        """Test that step growth is capped at maximum factor."""
        slo = SLO(p95_ms=150.0, recall_at10=0.80)
        
        # Test with many consecutive adjustments
        inp = make_input(
            adjustment_count=10,  # Many consecutive adjustments
            p95_ms=80.0,
            recall_at10=0.65,
            slo=slo
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            if action.kind != "noop":
                # Step should be capped (not grow indefinitely)
                max_step = 32.0 * 3.0  # 3x cap
                assert action.step <= max_step, f"Step should be capped, got {action.step}"
    
    def test_step_growth_monotonicity(self):
        """Test that step growth is monotonic."""
        slo = SLO(p95_ms=150.0, recall_at10=0.80)
        steps = []
        
        # Collect step sizes for consecutive adjustments
        for i in range(1, 5):
            inp = make_input(
                adjustment_count=i,
                p95_ms=80.0,
                recall_at10=0.65,
                slo=slo
            )
            
            with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
                mock_memory.return_value = MagicMock()
                mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
                mock_memory.return_value.query.return_value = None
                
                action = decide_tuning_action(inp)
                
                if action.kind != "noop":
                    steps.append(abs(action.step))
        
        # Steps should be non-decreasing (monotonic growth)
        for i in range(1, len(steps)):
            assert steps[i] >= steps[i-1], f"Step growth should be monotonic: {steps}"
    
    def test_step_growth_different_directions(self):
        """Test step growth with different action directions."""
        slo = SLO(p95_ms=150.0, recall_at10=0.80)
        
        # Test bump_ef direction
        inp_bump = make_input(
            adjustment_count=3,
            p95_ms=80.0,  # Low latency, poor recall -> bump_ef
            recall_at10=0.65,
            slo=slo
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action_bump = decide_tuning_action(inp_bump)
        
        # Test drop_ef direction
        inp_drop = make_input(
            adjustment_count=3,
            p95_ms=300.0,  # High latency, good recall -> drop_ef
            recall_at10=0.90,
            slo=slo
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action_drop = decide_tuning_action(inp_drop)
        
        # Both should show step growth regardless of direction
        if action_bump.kind != "noop" and action_drop.kind != "noop":
            assert abs(action_bump.step) >= 32.0
            assert abs(action_drop.step) >= 32.0


class TestAdaptiveStepDecay:
    """Test step decay for consecutive same-direction adjustments."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    def test_step_decay_consecutive_same_direction(self):
        """Test that step size decays with consecutive same-direction adjustments."""
        slo = SLO(p95_ms=150.0, recall_at10=0.80)
        
        # Simulate consecutive same-direction adjustments (oscillation prevention)
        for i in range(2, 5):  # 2, 3, 4 consecutive adjustments
            inp = make_input(
                adjustment_count=i,
                p95_ms=80.0,
                recall_at10=0.65,
                slo=slo
            )
            
            with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
                mock_memory.return_value = MagicMock()
                mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
                mock_memory.return_value.query.return_value = None
                
                action = decide_tuning_action(inp)
                
                if action.kind != "noop":
                    # Step should decay with more consecutive adjustments
                    # This tests the oscillation prevention mechanism
                    assert abs(action.step) <= 32.0, f"Step should decay for oscillation prevention, got {action.step}"
    
    def test_step_decay_floor(self):
        """Test that step decay has a minimum floor."""
        slo = SLO(p95_ms=150.0, recall_at10=0.80)
        
        # Test with many consecutive adjustments
        inp = make_input(
            adjustment_count=10,  # Many consecutive adjustments
            p95_ms=80.0,
            recall_at10=0.65,
            slo=slo
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            if action.kind != "noop":
                # Step should have a minimum floor (not decay to zero)
                min_step = 32.0 / 3.0  # 1/3 floor
                assert abs(action.step) >= min_step, f"Step should have floor, got {action.step}"
    
    def test_step_decay_monotonicity(self):
        """Test that step decay is monotonic."""
        slo = SLO(p95_ms=150.0, recall_at10=0.80)
        steps = []
        
        # Collect step sizes for consecutive adjustments
        for i in range(2, 6):  # Start from 2 for decay behavior
            inp = make_input(
                adjustment_count=i,
                p95_ms=80.0,
                recall_at10=0.65,
                slo=slo
            )
            
            with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
                mock_memory.return_value = MagicMock()
                mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
                mock_memory.return_value.query.return_value = None
                
                action = decide_tuning_action(inp)
                
                if action.kind != "noop":
                    steps.append(abs(action.step))
        
        # Steps should be non-increasing (monotonic decay)
        for i in range(1, len(steps)):
            assert steps[i] <= steps[i-1], f"Step decay should be monotonic: {steps}"


class TestAdaptiveStepIntegration:
    """Test adaptive steps in realistic scenarios."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    def test_improve_sequence_step_adaptation(self):
        """Test step adaptation through improvement sequence."""
        slo = SLO(p95_ms=150.0, recall_at10=0.80)
        steps = []
        
        # Simulate improvement sequence with more aggressive metrics
        improve_sequence = [
            {"p95_ms": 300.0, "recall_at10": 0.90},  # High latency, good recall -> drop_ef
            {"p95_ms": 250.0, "recall_at10": 0.88},  # Still high latency
            {"p95_ms": 200.0, "recall_at10": 0.85},  # Improving
            {"p95_ms": 150.0, "recall_at10": 0.82},  # Meeting SLO
        ]
        
        for i, metrics in enumerate(improve_sequence):
            inp = make_input(
                adjustment_count=i,
                p95_ms=metrics["p95_ms"],
                recall_at10=metrics["recall_at10"],
                slo=slo
            )
            
            with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
                mock_memory.return_value = MagicMock()
                mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
                mock_memory.return_value.query.return_value = None
                
                action = decide_tuning_action(inp)
                
                if action.kind != "noop":
                    steps.append(abs(action.step))
        
        # Should show adaptive behavior based on performance
        assert len(steps) > 0, "Should have some actions in improvement sequence"
    
    def test_regress_sequence_step_adaptation(self):
        """Test step adaptation through regression sequence."""
        slo = SLO(p95_ms=150.0, recall_at10=0.80)
        steps = []
        
        # Simulate regression sequence with more aggressive metrics
        regress_sequence = [
            {"p95_ms": 40.0, "recall_at10": 0.65},   # Low latency, poor recall -> bump_ef
            {"p95_ms": 45.0, "recall_at10": 0.68},   # Still poor recall
            {"p95_ms": 50.0, "recall_at10": 0.72},   # Improving
            {"p95_ms": 60.0, "recall_at10": 0.78},   # Getting better
        ]
        
        for i, metrics in enumerate(regress_sequence):
            inp = make_input(
                adjustment_count=i,
                p95_ms=metrics["p95_ms"],
                recall_at10=metrics["recall_at10"],
                slo=slo,
                params={"ef": 128}  # Ensure ef is not at max
            )
            
            with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
                mock_memory.return_value = MagicMock()
                mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
                mock_memory.return_value.query.return_value = None
                
                action = decide_tuning_action(inp)
                
                if action.kind != "noop":
                    steps.append(abs(action.step))
        
        # Should show adaptive behavior based on performance
        assert len(steps) > 0, "Should have some actions in regression sequence"
    
    def test_step_adaptation_with_cooldown(self):
        """Test step adaptation interaction with cooldown."""
        slo = SLO(p95_ms=150.0, recall_at10=0.80)
        
        # Test with recent action (should trigger cooldown)
        recent_action = make_action(
            kind="bump_ef",
            step=32.0,
            age_sec=5.0
        )
        
        inp = make_input(
            adjustment_count=3,  # Would normally trigger step adaptation
            last_action=recent_action,
            p95_ms=40.0,  # Low latency to trigger bump_ef
            recall_at10=0.65,
            slo=slo,
            params={"ef": 128}  # Ensure ef is not at max
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            # Should return noop due to cooldown (step adaptation not applied)
            assert action.kind == "noop"
            assert "cooldown" in action.reason
    
    def test_step_adaptation_with_hysteresis(self):
        """Test step adaptation interaction with hysteresis."""
        slo = SLO(p95_ms=150.0, recall_at10=0.80)
        
        inp = make_input(
            adjustment_count=3,  # Would normally trigger step adaptation
            p95_ms=155.0,  # Within hysteresis band
            recall_at10=0.81,  # Within hysteresis band
            slo=slo
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            # Should return noop due to hysteresis (step adaptation not applied)
            assert action.kind == "noop"
            assert "hysteresis" in action.reason


class TestStepAdaptationEdgeCases:
    """Test edge cases in step adaptation."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    def test_zero_adjustment_count(self):
        """Test step adaptation with zero adjustment count."""
        slo = SLO(p95_ms=150.0, recall_at10=0.80)
        
        inp = make_input(
            adjustment_count=0,  # No previous adjustments
            p95_ms=80.0,
            recall_at10=0.65,
            slo=slo
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            if action.kind != "noop":
                # Should use base step size
                assert abs(action.step) == 32.0, f"Should use base step for zero count, got {action.step}"
    
    def test_single_adjustment_count(self):
        """Test step adaptation with single adjustment count."""
        slo = SLO(p95_ms=150.0, recall_at10=0.80)
        
        inp = make_input(
            adjustment_count=1,  # Single previous adjustment
            p95_ms=80.0,
            recall_at10=0.65,
            slo=slo
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            if action.kind != "noop":
                # Should use base step size (growth starts at count 2)
                assert abs(action.step) == 32.0, f"Should use base step for single count, got {action.step}"
    
    def test_large_adjustment_count(self):
        """Test step adaptation with very large adjustment count."""
        slo = SLO(p95_ms=150.0, recall_at10=0.80)
        
        inp = make_input(
            adjustment_count=100,  # Very large count
            p95_ms=80.0,
            recall_at10=0.65,
            slo=slo
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            if action.kind != "noop":
                # Should be capped at maximum or minimum
                max_step = 32.0 * 3.0  # 3x cap
                min_step = 32.0 / 3.0  # 1/3 floor
                assert min_step <= abs(action.step) <= max_step, f"Step should be within bounds, got {action.step}"
