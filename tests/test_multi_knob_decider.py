"""
Test suite for Multi-Knob Decider

Tests the multi-parameter tuning decision logic with bundles and selection rules.
"""

import pytest
from modules.autotuner.brain.multi_knob_decider import (
    decide_multi_knob, 
    get_adaptive_step_factor,
    analyze_multi_knob_input
)
from modules.autotuner.brain.contracts import Action
from tests.fixtures import make_multi_knob_input, make_macros
from tests.utils_asserts import assert_updates_direction, assert_action_properties


class TestMultiKnobDecider:
    """Test multi-knob decision logic."""
    
    def test_latency_drop_selection(self):
        """Test that high p95 with recall margin selects latency_drop bundle."""
        # High latency with recall margin
        inp = make_multi_knob_input(
            p95_ms=200.0,  # Above SLO (150)
            recall_at10=0.85,  # Above SLO (0.80) with margin
            params={"ef": 256, "candidate_k": 400, "rerank_k": 20, "threshold_T": 0.2}
        )
        
        action = decide_multi_knob(inp)
        
        assert action.kind == "multi_knob"
        assert action.updates is not None
        assert "LATENCY" in action.reason
        assert_updates_direction(action.updates, "latency_drop")
        
        # Check specific bundle values
        assert action.updates["ef_search"] == -64
        assert action.updates["candidate_k"] == -50
        assert action.updates["threshold_T"] == 0.02
    
    def test_recall_gain_selection(self):
        """Test that low recall with latency margin selects recall_gain bundle."""
        # Low recall with latency margin
        inp = make_multi_knob_input(
            p95_ms=120.0,  # Below SLO (150) with margin
            recall_at10=0.75,  # Below SLO (0.80)
            params={"ef": 256, "candidate_k": 400, "rerank_k": 20, "threshold_T": 0.2}
        )
        
        action = decide_multi_knob(inp)
        
        assert action.kind == "multi_knob"
        assert action.updates is not None
        assert "RECALL" in action.reason
        assert_updates_direction(action.updates, "recall_gain")
        
        # Check specific bundle values
        assert action.updates["ef_search"] == 64
        assert action.updates["rerank_k"] == 10
        assert action.updates["threshold_T"] == -0.02
    
    def test_memory_hit_steady_nudge(self):
        """Test that memory hit triggers steady_nudge with scaling."""
        # Close to SLO on both metrics (memory hit condition)
        # Need to be within SLO to avoid latency_drop selection
        inp = make_multi_knob_input(
            p95_ms=145.0,  # Below SLO (150)
            recall_at10=0.81,  # Above SLO (0.80)
            params={"ef": 256, "candidate_k": 400, "rerank_k": 20, "threshold_T": 0.2}
        )
        
        action = decide_multi_knob(inp)
        
        assert action.kind == "multi_knob"
        assert action.updates is not None
        assert "MEMORY_HIT" in action.reason
        
        # Should be steady_nudge bundle with 0.5 scaling
        assert action.updates["ef_search"] == -16  # -32 * 0.5
        assert action.updates["candidate_k"] == -12.5  # -25 * 0.5
        assert action.updates["threshold_T"] == 0.005  # 0.01 * 0.5
    
    def test_noop_when_within_slo(self):
        """Test that no action is taken when within SLO."""
        # Within SLO on both metrics, but not close enough to trigger memory hit
        inp = make_multi_knob_input(
            p95_ms=120.0,  # Well below SLO (150)
            recall_at10=0.85,  # Well above SLO (0.80)
            params={"ef": 256, "candidate_k": 400, "rerank_k": 20, "threshold_T": 0.2}
        )
        
        action = decide_multi_knob(inp)
        
        assert action.kind == "noop"
        assert action.updates is None
        assert "within_slo" in action.reason.lower()
    
    def test_macro_bias_selection(self):
        """Test that macro indicators bias bundle selection."""
        # Neutral performance
        inp = make_multi_knob_input(
            p95_ms=160.0,  # Slightly above SLO
            recall_at10=0.80,  # At SLO
            params={"ef": 256, "candidate_k": 400, "rerank_k": 20, "threshold_T": 0.2}
        )
        
        # Test L bias (latency focus)
        macros_L = make_macros(L=0.8, R=0.0)
        action_L = decide_multi_knob(inp, macros_L)
        
        assert action_L.kind == "multi_knob"
        assert "LATENCY" in action_L.reason
        assert_updates_direction(action_L.updates, "latency_drop")
        
        # Test R bias (recall focus)
        macros_R = make_macros(L=0.0, R=0.8)
        action_R = decide_multi_knob(inp, macros_R)
        
        assert action_R.kind == "multi_knob"
        assert "RECALL" in action_R.reason
        assert_updates_direction(action_R.updates, "recall_gain")
    
    def test_adaptive_step_factor(self):
        """Test adaptive step factor calculation."""
        # Two consecutive improvements -> increase step size
        factor = get_adaptive_step_factor(consecutive_improvements=2, consecutive_regressions=0)
        assert factor == 1.5
        
        # More improvements -> higher factor (capped at 1.5)
        factor = get_adaptive_step_factor(consecutive_improvements=5, consecutive_regressions=0)
        assert factor == 1.5
        
        # Regression -> decrease step size
        factor = get_adaptive_step_factor(consecutive_improvements=0, consecutive_regressions=1)
        assert factor == 0.5
        
        # More regressions -> lower factor (floored at 0.33)
        factor = get_adaptive_step_factor(consecutive_improvements=0, consecutive_regressions=3)
        assert factor == 0.33
        
        # No changes -> no adjustment
        factor = get_adaptive_step_factor(consecutive_improvements=0, consecutive_regressions=0)
        assert factor == 1.0
    
    def test_analyze_multi_knob_input(self):
        """Test input analysis for multi-knob decisions."""
        inp = make_multi_knob_input(
            p95_ms=200.0,
            recall_at10=0.75,
            params={"ef": 256, "candidate_k": 400, "rerank_k": 20, "threshold_T": 0.2}
        )
        
        analysis = analyze_multi_knob_input(inp)
        
        assert analysis['latency_violation'] == True
        assert analysis['recall_violation'] == True
        assert abs(analysis['recall_margin'] - (-0.05)) < 1e-10
        assert analysis['latency_margin'] == -50.0
        assert analysis['memory_hit'] == False
        assert 'current_params' in analysis
    
    def test_bundle_magnitudes(self):
        """Test that bundle magnitudes are reasonable."""
        inp = make_multi_knob_input(
            p95_ms=200.0,
            recall_at10=0.85,
            params={"ef": 256, "candidate_k": 400, "rerank_k": 20, "threshold_T": 0.2}
        )
        
        action = decide_multi_knob(inp)
        
        # Check that magnitudes are reasonable (not too large)
        for key, value in action.updates.items():
            assert abs(value) <= 100, f"Update magnitude too large: {key}={value}"
    
    def test_deterministic_behavior(self):
        """Test that decisions are deterministic for same inputs."""
        inp = make_multi_knob_input(
            p95_ms=180.0,
            recall_at10=0.80,
            params={"ef": 256, "candidate_k": 400, "rerank_k": 20, "threshold_T": 0.2}
        )
        
        action1 = decide_multi_knob(inp)
        action2 = decide_multi_knob(inp)
        
        assert action1.kind == action2.kind
        assert action1.reason == action2.reason
        if action1.updates:
            assert action1.updates == action2.updates
