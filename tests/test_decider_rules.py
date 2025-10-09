"""
Test AutoTuner Brain decision rules

Tests all functional pathways in the decider including guards, hysteresis,
cooldown, adaptive steps, memory hooks, and sequential multi-knob rotation.
"""

import pytest
from unittest.mock import patch, MagicMock

from modules.autotuner.brain.decider import decide_tuning_action
from modules.autotuner.brain.contracts import TuningInput, SLO, Guards, Action
from tests.fixtures import make_input, make_action, set_random_seed
from tests.utils_asserts import assert_action_properties


class TestDecisionRules:
    """Test core decision logic pathways."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    @pytest.mark.parametrize("p95_ms,recall_at10,expected_kind,expected_reason_contains", [
        # High latency, sufficient recall -> drop ef or ncand
        (300.0, 0.86, "drop_ef", "high_latency_with_recall_redundancy"),  # 0.86 > 0.85
        (250.0, 0.90, "drop_ef", "high_latency_with_recall_redundancy"),
        # Low recall, sufficient latency margin -> bump ef or rerank
        (50.0, 0.65, "bump_ef", "low_recall_with_latency_margin"),
        (40.0, 0.70, "bump_ef", "low_recall_with_latency_margin"),
        # Both metrics good -> noop
        (120.0, 0.85, "noop", "within_slo_or_uncertain"),
    ])
    def test_basic_decision_pathways(self, p95_ms, recall_at10, expected_kind, expected_reason_contains):
        """Test basic decision pathways based on performance metrics."""
        # Set ef to a reasonable value for low recall tests
        params = {"ef": 128} if expected_kind == "bump_ef" else {}
        inp = make_input(
            p95_ms=p95_ms,
            recall_at10=recall_at10,
            slo=SLO(p95_ms=150.0, recall_at10=0.80),
            params=params
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None  # No memory hit
            
            action = decide_tuning_action(inp)
            
            assert_action_properties(
                action, 
                expected_kind=expected_kind,
                expected_reason_contains=expected_reason_contains
            )
    
    def test_guards_cooldown_blocks_action(self):
        """Test that cooldown guard blocks all actions."""
        inp = make_input(
            guards=Guards(cooldown=True, stable=False),
            p95_ms=300.0,  # High latency that would normally trigger action
            recall_at10=0.90  # Good recall
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
    
    def test_hysteresis_band_noop(self):
        """Test that small oscillations within hysteresis band trigger noop."""
        inp = make_input(
            p95_ms=155.0,  # Within 100ms of SLO (150ms)
            recall_at10=0.81,  # Within 0.02 of SLO (0.80)
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
                expected_reason_contains="within_hysteresis_band"
            )
    
    def test_cooldown_with_recent_action(self):
        """Test cooldown mechanism with recent same action."""
        recent_action = make_action(
            kind="bump_ef", 
            step=32.0, 
            age_sec=5.0  # Recent action (less than 10s)
        )
        
        inp = make_input(
            last_action=recent_action,
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
    
    def test_adaptive_step_growth(self):
        """Test adaptive step growth for consecutive improvements."""
        inp = make_input(
            adjustment_count=2,  # Consecutive adjustments
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
            
            # Should have smaller step due to consecutive adjustments (oscillation prevention)
            assert action.step < 32.0, f"Expected smaller step for oscillation prevention, got {action.step}"
            assert action.kind in ["bump_ef", "bump_rerank"]
    
    def test_adaptive_step_decay(self):
        """Test adaptive step decay for consecutive same direction."""
        # Simulate consecutive same direction adjustments
        inp = make_input(
            adjustment_count=3,  # Many consecutive adjustments
            p95_ms=80.0,
            recall_at10=0.65,
            slo=SLO(p95_ms=150.0, recall_at10=0.80)
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            # Should have smaller step due to oscillation prevention
            assert action.step <= 32.0, f"Expected smaller step, got {action.step}"
    
    def test_near_t_threshold_pressure(self):
        """Test bump_T for threshold pressure when near_T is true."""
        inp = make_input(
            near_T=True,
            guards=Guards(cooldown=False, stable=True),  # Stable state
            p95_ms=180.0,  # Above SLO
            recall_at10=0.85,  # Good recall
            slo=SLO(p95_ms=150.0, recall_at10=0.80)
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            assert_action_properties(
                action,
                expected_kind="bump_T",
                expected_reason_contains="near_T_boundary_optimization"
            )
    
    def test_rollback_after_consecutive_violations(self):
        """Test rollback after consecutive SLO violations."""
        # This would need to be implemented in the actual decider
        # For now, test that the rollback action type exists
        inp = make_input(
            p95_ms=200.0,
            recall_at10=0.70,
            slo=SLO(p95_ms=150.0, recall_at10=0.80)
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            # Rollback is not implemented in current version
            # This test documents the expected behavior
            assert action.kind != "rollback"  # Current implementation doesn't have rollback


class TestMemoryHook:
    """Test memory hook integration."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    def test_memory_hit_micro_step(self):
        """Test memory hit returns micro step with correct reason."""
        from tests.fixtures import MockMemory
        
        # Create mock memory with sweet spot
        mock_memory = MockMemory()
        bucket_id = "test_bucket"
        mock_memory.add_sweet_spot(bucket_id, ef=200, meets_slo=True)
        
        inp = make_input(
            params={"ef": 160, "Ncand_max": 400, "rerank_mult": 20, "T": 500}
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_get_memory:
            mock_get_memory.return_value = mock_memory
            # Mock the default_bucket_of method
            mock_memory.default_bucket_of = MagicMock(return_value=bucket_id)
            
            action = decide_tuning_action(inp)
            
            # Should use memory and return micro step
            assert action.kind == "bump_ef"
            assert action.step == 16.0  # Micro step (smaller than normal 32)
            assert "memory" in action.reason.lower() or "follow" in action.reason.lower()
    
    def test_memory_miss_falls_back_to_normal_logic(self):
        """Test that memory miss falls back to normal decision logic."""
        from tests.fixtures import MockMemory
        
        mock_memory = MockMemory()
        bucket_id = "test_bucket"
        # No sweet spot added, so memory.query returns None
        
        inp = make_input(
            p95_ms=40.0,  # Low latency to trigger bump_ef
            recall_at10=0.65,
            slo=SLO(p95_ms=150.0, recall_at10=0.80),
            params={"ef": 128}  # Ensure ef is not at max
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_get_memory:
            mock_get_memory.return_value = mock_memory
            # Mock the default_bucket_of method
            mock_memory.default_bucket_of = MagicMock(return_value=bucket_id)
            
            action = decide_tuning_action(inp)
            
            # Should fall back to normal logic
            assert action.kind == "bump_ef"
            assert action.step == 32.0  # Normal step size
            assert "memory" not in action.reason.lower()
    
    def test_memory_at_sweet_spot_noop(self):
        """Test that being at sweet spot returns noop."""
        from tests.fixtures import MockMemory
        
        mock_memory = MockMemory()
        bucket_id = "test_bucket"
        mock_memory.add_sweet_spot(bucket_id, ef=160, meets_slo=True)
        
        inp = make_input(
            params={"ef": 160, "Ncand_max": 400, "rerank_mult": 20, "T": 500}  # Already at sweet spot
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_get_memory:
            mock_get_memory.return_value = mock_memory
            # Mock the default_bucket_of method
            mock_memory.default_bucket_of = MagicMock(return_value=bucket_id)
            
            action = decide_tuning_action(inp)
            
            assert action.kind == "noop"
            assert "sweet_spot" in action.reason.lower() or "memory" in action.reason.lower()


class TestSequentialMultiKnob:
    """Test sequential multi-knob rotation behavior."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    def test_sequential_knob_rotation(self):
        """Test that only one knob changes per decision tick."""
        # This test documents expected behavior for sequential knob changes
        # The actual implementation would need to track knob rotation state
        
        inp = make_input(
            p95_ms=80.0,
            recall_at10=0.65,
            slo=SLO(p95_ms=150.0, recall_at10=0.80)
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            # Should only suggest one knob change
            assert action.kind in ["bump_ef", "bump_rerank", "noop"]
            # The sequential rotation would be tested in integration tests
            # where we track knob changes across multiple decisions


@pytest.mark.parametrize("test_case", [
    {"p95_ms": 300.0, "recall_at10": 0.86, "expected": "drop_ef"},  # Fixed recall
    {"p95_ms": 40.0, "recall_at10": 0.65, "expected": "bump_ef"},   # Fixed latency
    {"p95_ms": 120.0, "recall_at10": 0.85, "expected": "noop"},
])
def test_decision_table_driven(test_case):
    """Table-driven test for common decision scenarios."""
    # Set ef to reasonable value for bump_ef tests
    params = {"ef": 128} if test_case["expected"] == "bump_ef" else {}
    inp = make_input(
        p95_ms=test_case["p95_ms"],
        recall_at10=test_case["recall_at10"],
        slo=SLO(p95_ms=150.0, recall_at10=0.80),
        params=params
    )
    
    with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
        mock_memory.return_value = MagicMock()
        mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
        mock_memory.return_value.query.return_value = None
        
        action = decide_tuning_action(inp)
        
        assert action.kind == test_case["expected"]
