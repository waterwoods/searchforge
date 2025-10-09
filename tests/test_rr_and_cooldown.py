#!/usr/bin/env python3
"""
Test Round-Robin and Cooldown Behavior

Tests the round-robin cycling and cooldown gates for multi-knob decider.
"""

import pytest
from modules.autotuner.brain.multi_knob_decider import (
    decide_multi_knob, reset_round_robin, get_round_robin_state
)
from modules.autotuner.brain.contracts import TuningInput, SLO
from tests.fixtures import make_multi_knob_input


class TestRoundRobinAndCooldown:
    """Test round-robin cycling and cooldown behavior."""
    
    def setup_method(self):
        """Reset state before each test."""
        reset_round_robin()
    
    def test_round_robin_cycling(self):
        """Test that bundles cycle in round-robin order."""
        # Create input that triggers round-robin fallback (far from SLO to avoid memory hit)
        inp = make_multi_knob_input(
            p95_ms=100.0,  # Well below SLO
            recall_at10=0.90  # Well above SLO
        )
        
        # First call should get latency_drop (index 0)
        action1 = decide_multi_knob(inp)
        assert action1.kind == "multi_knob"
        assert "LATENCY_DROP" in action1.reason
        
        # Second call should be blocked by cooldown
        action2 = decide_multi_knob(inp)
        assert action2.kind == "noop"
        assert "BUNDLE_COOLDOWN_REMAINING_1" in action2.reason
        
        # Third call should still be blocked by cooldown
        action3 = decide_multi_knob(inp)
        assert action3.kind == "noop"
        assert "BUNDLE_COOLDOWN_REMAINING_0" in action3.reason
        
        # Fourth call should get recall_gain (index 1, next in round-robin)
        action4 = decide_multi_knob(inp)
        assert action4.kind == "multi_knob"
        assert "RECALL_GAIN" in action4.reason
        
        # Fifth call should be blocked by cooldown again
        action5 = decide_multi_knob(inp)
        assert action5.kind == "noop"
        assert "BUNDLE_COOLDOWN_REMAINING_1" in action5.reason
        
        # Sixth call should still be blocked
        action6 = decide_multi_knob(inp)
        assert action6.kind == "noop"
        assert "BUNDLE_COOLDOWN_REMAINING_0" in action6.reason
        
        # Seventh call should cycle back to latency_drop (index 0)
        action7 = decide_multi_knob(inp)
        assert action7.kind == "multi_knob"
        assert "LATENCY_DROP" in action7.reason
    
    def test_cooldown_enforcement(self):
        """Test that cooldown prevents immediate bundle triggering."""
        # Create input that would trigger a bundle (far from SLO to avoid memory hit)
        inp = make_multi_knob_input(
            p95_ms=200.0,  # Well above SLO
            recall_at10=0.90  # Well above SLO
        )
        
        # First call should trigger latency_drop and set cooldown
        action1 = decide_multi_knob(inp)
        assert action1.kind == "multi_knob"
        assert "LATENCY_DROP" in action1.reason
        
        # Second call should be blocked by cooldown
        action2 = decide_multi_knob(inp)
        assert action2.kind == "noop"
        assert "BUNDLE_COOLDOWN_REMAINING_1" in action2.reason
        
        # Third call should still be blocked
        action3 = decide_multi_knob(inp)
        assert action3.kind == "noop"
        assert "BUNDLE_COOLDOWN_REMAINING_0" in action3.reason
        
        # Fourth call should allow bundle again
        action4 = decide_multi_knob(inp)
        assert action4.kind == "multi_knob"
        assert "LATENCY_DROP" in action4.reason
    
    def test_cooldown_with_round_robin(self):
        """Test cooldown behavior with round-robin cycling."""
        # Create input that triggers round-robin (far from SLO to avoid memory hit)
        inp = make_multi_knob_input(
            p95_ms=100.0,  # Well below SLO
            recall_at10=0.90  # Well above SLO
        )
        
        # First call: latency_drop, cooldown=2
        action1 = decide_multi_knob(inp)
        assert action1.kind == "multi_knob"
        assert "LATENCY_DROP" in action1.reason
        
        # Second call: cooldown=1
        action2 = decide_multi_knob(inp)
        assert action2.kind == "noop"
        assert "BUNDLE_COOLDOWN_REMAINING_1" in action2.reason
        
        # Third call: cooldown=0
        action3 = decide_multi_knob(inp)
        assert action3.kind == "noop"
        assert "BUNDLE_COOLDOWN_REMAINING_0" in action3.reason
        
        # Fourth call: recall_gain (next in round-robin), cooldown=2
        action4 = decide_multi_knob(inp)
        assert action4.kind == "multi_knob"
        assert "RECALL_GAIN" in action4.reason
    
    def test_round_robin_state_tracking(self):
        """Test that round-robin state is properly tracked."""
        inp = make_multi_knob_input(
            p95_ms=100.0,  # Well below SLO
            recall_at10=0.90  # Well above SLO
        )
        
        # Check initial state
        state = get_round_robin_state()
        assert state["bundle_index"] == 0
        assert state["cooldown_remaining"] == 0
        
        # After first bundle
        decide_multi_knob(inp)
        state = get_round_robin_state()
        assert state["bundle_index"] == 1  # Advanced to next
        assert state["cooldown_remaining"] == 2  # Set cooldown
        
        # After cooldown period
        decide_multi_knob(inp)  # cooldown=1
        decide_multi_knob(inp)  # cooldown=0
        decide_multi_knob(inp)  # New bundle
        
        state = get_round_robin_state()
        assert state["bundle_index"] == 0  # Cycled back
        assert state["cooldown_remaining"] == 2  # New cooldown
    
    def test_memory_hit_bypasses_cooldown(self):
        """Test that memory hits can bypass cooldown for steady_nudge."""
        # Create input that triggers memory hit (close to SLO)
        inp = make_multi_knob_input(
            p95_ms=155.0,  # Close to SLO
            recall_at10=0.81  # Close to SLO
        )
        
        # First call: should trigger steady_nudge even if cooldown active
        action1 = decide_multi_knob(inp)
        assert action1.kind == "multi_knob"
        assert "STEADY_NUDGE" in action1.reason
        assert "MEMORY_HIT" in action1.reason
    
    def test_performance_triggers_override_round_robin(self):
        """Test that performance-based triggers override round-robin."""
        # High p95, good recall -> should trigger latency_drop regardless of round-robin
        inp1 = make_multi_knob_input(
            p95_ms=200.0,  # Well above SLO
            recall_at10=0.90  # Well above SLO
        )
        
        action1 = decide_multi_knob(inp1)
        assert action1.kind == "multi_knob"
        assert "LATENCY_DROP" in action1.reason
        
        # Reset state for second test
        reset_round_robin()
        
        # Low recall, good latency -> should trigger recall_gain regardless of round-robin
        inp2 = make_multi_knob_input(
            p95_ms=100.0,  # Good latency
            recall_at10=0.70  # Well below SLO
        )
        
        action2 = decide_multi_knob(inp2)
        assert action2.kind == "multi_knob"
        assert "RECALL_GAIN" in action2.reason
    
    def test_macro_bias_overrides_round_robin(self):
        """Test that macro bias overrides round-robin selection."""
        # L bias should always trigger latency_drop (far from SLO to avoid memory hit)
        inp = make_multi_knob_input(
            p95_ms=100.0,  # Well below SLO
            recall_at10=0.90  # Well above SLO
        )
        macros = {"L": 0.8, "R": 0.0}
        
        # Multiple calls should all get latency_drop due to L bias
        for i in range(3):
            if i > 0:
                reset_round_robin()  # Reset cooldown for each call
            action = decide_multi_knob(inp, macros)
            assert action.kind == "multi_knob"
            assert "LATENCY_DROP" in action.reason
    
    def test_safety_rate_under_round_robin(self):
        """Test that safety rate remains high under round-robin stress."""
        from modules.autotuner.brain.apply import reset_apply_counters, get_apply_counters
        
        reset_apply_counters()
        
        # Run many round-robin cycles (far from SLO to avoid memory hit)
        inp = make_multi_knob_input(
            p95_ms=100.0,  # Well below SLO
            recall_at10=0.90  # Well above SLO
        )
        
        for _ in range(20):  # 20 ticks
            decide_multi_knob(inp)
        
        # Check safety rate
        stats = get_apply_counters()
        safety_rate = 1.0 - (stats["clipped_count"] + stats["rollback_count"]) / max(stats["decide_total"], 1)
        
        assert safety_rate >= 0.99, f"Safety rate {safety_rate:.3f} below 0.99"
    
    def test_cooldown_reset_functionality(self):
        """Test that reset_round_robin properly resets state."""
        inp = make_multi_knob_input(
            p95_ms=160.0,
            recall_at10=0.81
        )
        
        # Trigger a bundle and cooldown
        decide_multi_knob(inp)
        
        # Check cooldown is active
        state = get_round_robin_state()
        assert state["cooldown_remaining"] > 0
        
        # Reset
        reset_round_robin()
        
        # Check state is reset
        state = get_round_robin_state()
        assert state["bundle_index"] == 0
        assert state["cooldown_remaining"] == 0
        
        # Should be able to trigger bundle immediately
        action = decide_multi_knob(inp)
        assert action.kind == "multi_knob"
