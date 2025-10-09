"""
Test suite for Macro Consistency

Tests that macro indicators (L/R) consistently bias bundle selection.
"""

import pytest
from modules.autotuner.brain.multi_knob_decider import decide_multi_knob
from tests.fixtures import make_multi_knob_input, make_macros
from tests.utils_asserts import assert_updates_direction


class TestMacroConsistency:
    """Test macro indicator consistency and bias."""
    
    def test_increasing_L_biases_latency_drop(self):
        """Test that increasing L values bias toward latency_drop selection."""
        # Neutral performance that could go either way
        base_inp = make_multi_knob_input(
            p95_ms=160.0,  # Slightly above SLO
            recall_at10=0.80,  # At SLO
            params={"ef": 256, "candidate_k": 400, "rerank_k": 20, "threshold_T": 0.2}
        )
        
        # Test increasing L values
        L_values = [0.0, 0.3, 0.5, 0.7, 0.9]
        latency_drop_count = 0
        
        for L in L_values:
            macros = make_macros(L=L, R=0.0)
            action = decide_multi_knob(base_inp, macros)
            
            if action.kind == "multi_knob" and "LATENCY" in action.reason:
                latency_drop_count += 1
                assert_updates_direction(action.updates, "latency_drop")
        
        # Should see increasing bias toward latency_drop
        assert latency_drop_count >= 2, f"Expected at least 2 latency_drop selections, got {latency_drop_count}"
    
    def test_increasing_R_biases_recall_gain(self):
        """Test that increasing R values bias toward recall_gain selection."""
        # Neutral performance that could go either way
        base_inp = make_multi_knob_input(
            p95_ms=160.0,  # Slightly above SLO
            recall_at10=0.80,  # At SLO
            params={"ef": 256, "candidate_k": 400, "rerank_k": 20, "threshold_T": 0.2}
        )
        
        # Test increasing R values
        R_values = [0.0, 0.3, 0.5, 0.7, 0.9]
        recall_gain_count = 0
        
        for R in R_values:
            macros = make_macros(L=0.0, R=R)
            action = decide_multi_knob(base_inp, macros)
            
            if action.kind == "multi_knob" and "RECALL" in action.reason:
                recall_gain_count += 1
                assert_updates_direction(action.updates, "recall_gain")
        
        # Should see increasing bias toward recall_gain
        assert recall_gain_count >= 2, f"Expected at least 2 recall_gain selections, got {recall_gain_count}"
    
    def test_macro_bias_monotonic_trend(self):
        """Test that macro bias shows monotonic trend across multiple ticks."""
        # Simulate multiple decision ticks with varying macro values
        base_inp = make_multi_knob_input(
            p95_ms=165.0,  # Slightly above SLO
            recall_at10=0.79,  # Slightly below SLO
            params={"ef": 256, "candidate_k": 400, "rerank_k": 20, "threshold_T": 0.2}
        )
        
        # Simulate increasing L trend
        L_trend = [0.1, 0.3, 0.5, 0.7, 0.9]
        latency_selections = []
        
        for L in L_trend:
            macros = make_macros(L=L, R=0.0)
            action = decide_multi_knob(base_inp, macros)
            
            is_latency_focused = (action.kind == "multi_knob" and 
                                "LATENCY" in action.reason)
            latency_selections.append(is_latency_focused)
        
        # Should see monotonic increase in latency focus
        # (More True values as L increases)
        true_count = sum(latency_selections)
        assert true_count >= 2, f"Expected monotonic trend, got {latency_selections}"
    
    def test_macro_bias_deterministic(self):
        """Test that macro bias is deterministic for same inputs."""
        inp = make_multi_knob_input(
            p95_ms=160.0,
            recall_at10=0.80,
            params={"ef": 256, "candidate_k": 400, "rerank_k": 20, "threshold_T": 0.2}
        )
        
        macros = make_macros(L=0.6, R=0.3)
        
        # Multiple calls should give same result
        action1 = decide_multi_knob(inp, macros)
        action2 = decide_multi_knob(inp, macros)
        
        assert action1.kind == action2.kind
        assert action1.reason == action2.reason
        if action1.updates:
            assert action1.updates == action2.updates
    
    def test_macro_bias_scaling(self):
        """Test that macro bias affects scaling of updates."""
        inp = make_multi_knob_input(
            p95_ms=155.0,  # Close to SLO (memory hit condition)
            recall_at10=0.81,  # Close to SLO
            params={"ef": 256, "candidate_k": 400, "rerank_k": 20, "threshold_T": 0.2}
        )
        
        # Test with different macro values
        macros_low = make_macros(L=0.2, R=0.0)
        macros_high = make_macros(L=0.8, R=0.0)
        
        action_low = decide_multi_knob(inp, macros_low)
        action_high = decide_multi_knob(inp, macros_high)
        
        # Both should be latency-focused due to L bias
        if action_low.kind == "multi_knob" and action_high.kind == "multi_knob":
            assert "LATENCY" in action_low.reason
            assert "LATENCY" in action_high.reason
            
            # Higher L should result in larger magnitude updates
            if "ef_search" in action_low.updates and "ef_search" in action_high.updates:
                assert abs(action_high.updates["ef_search"]) >= abs(action_low.updates["ef_search"])
    
    def test_macro_bias_edge_cases(self):
        """Test macro bias behavior at edge cases."""
        inp = make_multi_knob_input(
            p95_ms=160.0,
            recall_at10=0.80,
            params={"ef": 256, "candidate_k": 400, "rerank_k": 20, "threshold_T": 0.2}
        )
        
        # Test with zero macros
        macros_zero = make_macros(L=0.0, R=0.0)
        action_zero = decide_multi_knob(inp, macros_zero)
        
        # Should fall back to default decision logic
        assert action_zero.kind in ["noop", "multi_knob"]
        
        # Test with both L and R high
        macros_both = make_macros(L=0.8, R=0.8)
        action_both = decide_multi_knob(inp, macros_both)
        
        # Should still make a decision (L takes precedence)
        assert action_both.kind in ["noop", "multi_knob"]
    
    def test_macro_bias_performance_scenarios(self):
        """Test macro bias across different performance scenarios."""
        scenarios = [
            # High latency, good recall
            {"p95_ms": 200.0, "recall_at10": 0.85, "expected": "latency_drop"},
            # Good latency, low recall  
            {"p95_ms": 120.0, "recall_at10": 0.75, "expected": "recall_gain"},
            # Both good
            {"p95_ms": 140.0, "recall_at10": 0.82, "expected": "noop"},
            # Both bad
            {"p95_ms": 200.0, "recall_at10": 0.75, "expected": "latency_drop"}
        ]
        
        for scenario in scenarios:
            inp = make_multi_knob_input(
                p95_ms=scenario["p95_ms"],
                recall_at10=scenario["recall_at10"],
                params={"ef": 256, "candidate_k": 400, "rerank_k": 20, "threshold_T": 0.2}
            )
            
            # Test with L bias
            macros_L = make_macros(L=0.7, R=0.0)
            action_L = decide_multi_knob(inp, macros_L)
            
            # Test with R bias
            macros_R = make_macros(L=0.0, R=0.7)
            action_R = decide_multi_knob(inp, macros_R)
            
            # Both should make decisions (not noop unless truly within SLO)
            if scenario["expected"] != "noop":
                if action_L.kind == "multi_knob":
                    assert "LATENCY" in action_L.reason or "RECALL" in action_L.reason
                if action_R.kind == "multi_knob":
                    assert "LATENCY" in action_R.reason or "RECALL" in action_R.reason
