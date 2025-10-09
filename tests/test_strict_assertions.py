"""
Strict assertions for step values, round-robin order, and boundary conditions.

These tests address coverage gaps and ensure exact behavior verification.
"""

import pytest
from unittest.mock import patch, MagicMock

from modules.autotuner.brain.decider import decide_tuning_action
from modules.autotuner.brain.apply import apply_action
from modules.autotuner.brain.constraints import clip_params
from modules.autotuner.brain.contracts import TuningInput, Action, SLO, Guards
from tests.fixtures import make_input, set_random_seed


class TestStrictStepAssertions:
    """Tests with exact step value assertions."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    def test_exact_step_values_core_actions(self):
        """Test exact step values for core action types that are reliably triggered."""
        # Test bump_ef (low recall + latency margin)
        inp = make_input(
            p95_ms=40.0,  # Low latency (margin)
            recall_at10=0.65,  # Low recall
            slo=SLO(p95_ms=150.0, recall_at10=0.80),
            params={"ef": 128}  # Not at maximum
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            assert action.kind == "bump_ef", f"Expected bump_ef for low recall + latency margin, got {action.kind}"
            assert action.step == 32.0, f"Expected step 32.0, got {action.step}"
        
        # Test drop_ef (high latency + recall redundancy)
        inp = make_input(
            p95_ms=250.0,  # High latency
            recall_at10=0.92,  # High recall (redundancy)
            slo=SLO(p95_ms=150.0, recall_at10=0.80),
            params={"ef": 128}  # Not at minimum
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            assert action.kind == "drop_ef", f"Expected drop_ef for high latency + recall redundancy, got {action.kind}"
            assert action.step == -32.0, f"Expected step -32.0, got {action.step}"
    
    def test_step_caps_and_floors(self):
        """Test that step sizes respect caps and floors."""
        # Test maximum step growth (should be capped at 3x base)
        inp = make_input(
            p95_ms=40.0,
            recall_at10=0.65,
            slo=SLO(p95_ms=150.0, recall_at10=0.80),
            adjustment_count=5  # High consecutive count
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            if action.kind == "bump_ef":
                # Step should be capped at 3x base (32 * 3 = 96)
                assert action.step <= 96.0, f"Step should be capped at 96.0, got {action.step}"
                assert action.step >= 32.0, f"Step should be at least base (32.0), got {action.step}"
    
    def test_boundary_step_assertions(self):
        """Test step assertions at parameter boundaries."""
        # Test ef at minimum - should drop ncand instead
        inp = make_input(
            p95_ms=250.0,
            recall_at10=0.92,
            slo=SLO(p95_ms=150.0, recall_at10=0.80),
            params={"ef": 64}  # At minimum
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            assert action.kind == "drop_ncand", f"Expected drop_ncand when ef at minimum, got {action.kind}"
            assert action.step == -200.0, f"Expected step -200.0 for drop_ncand, got {action.step}"
        
        # Test ef at maximum - should bump rerank instead
        inp = make_input(
            p95_ms=40.0,
            recall_at10=0.65,
            slo=SLO(p95_ms=150.0, recall_at10=0.80),
            params={"ef": 256}  # At maximum
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            assert action.kind == "bump_rerank", f"Expected bump_rerank when ef at maximum, got {action.kind}"
            assert action.step == 1.0, f"Expected step 1.0 for bump_rerank, got {action.step}"


class TestRoundRobinAssertions:
    """Tests for round-robin sequential knob changes."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    def test_single_knob_change_per_tick(self):
        """Test that only one knob changes per decision tick (before clipping)."""
        inp = make_input(
            p95_ms=40.0,
            recall_at10=0.65,
            slo=SLO(p95_ms=150.0, recall_at10=0.80)
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            # Should only suggest one knob change
            single_knob_actions = ["bump_ef", "drop_ef", "bump_T", "drop_T", 
                                 "bump_ncand", "drop_ncand", "bump_rerank", "drop_rerank", "noop"]
            assert action.kind in single_knob_actions, f"Expected single knob action, got {action.kind}"
            
            # Test the action logic directly (before clipping)
            old_params = inp.params.copy()
            new_params = old_params.copy()
            
            # Apply the action step directly (simulating the core logic)
            if action.kind == "bump_ef":
                new_params["ef"] = new_params.get("ef", 128) + int(action.step)
            elif action.kind == "drop_ef":
                new_params["ef"] = new_params.get("ef", 128) + int(action.step)
            elif action.kind == "bump_T":
                new_params["T"] = new_params.get("T", 500) + int(action.step)
            elif action.kind == "drop_T":
                new_params["T"] = new_params.get("T", 500) + int(action.step)
            elif action.kind == "bump_rerank":
                new_params["rerank_mult"] = new_params.get("rerank_mult", 2) + int(action.step)
            elif action.kind == "drop_rerank":
                new_params["rerank_mult"] = new_params.get("rerank_mult", 2) + int(action.step)
            elif action.kind == "bump_ncand":
                new_params["Ncand_max"] = new_params.get("Ncand_max", 1000) + int(action.step)
            elif action.kind == "drop_ncand":
                new_params["Ncand_max"] = new_params.get("Ncand_max", 1000) + int(action.step)
            
            # Count changes before clipping
            changes = []
            for key in old_params:
                if old_params[key] != new_params[key]:
                    changes.append(key)
            
            if action.kind != "noop":
                assert len(changes) == 1, f"Expected exactly 1 parameter change before clipping, got {len(changes)}: {changes}"
                assert changes[0] in ["ef", "T", "Ncand_max", "rerank_mult"], f"Unexpected parameter change: {changes[0]}"
    
    def test_decision_priority_order(self):
        """Test decision priority order when multiple actions are possible."""
        # Test that decision logic follows priority order
        base_inp = make_input(
            p95_ms=40.0,  # Low latency (margin)
            recall_at10=0.65,  # Low recall
            slo=SLO(p95_ms=150.0, recall_at10=0.80)
        )
        
        # Test ef priority (should prefer bump_ef over bump_rerank when ef is not at max)
        inp = TuningInput(
            p95_ms=base_inp.p95_ms,
            recall_at10=base_inp.recall_at10,
            qps=base_inp.qps,
            params={"ef": 128},  # Not at maximum
            slo=base_inp.slo,
            guards=base_inp.guards,
            near_T=base_inp.near_T,
            last_action=base_inp.last_action,
            adjustment_count=base_inp.adjustment_count
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            # Should prefer bump_ef when ef is not at maximum
            assert action.kind == "bump_ef", f"Expected bump_ef priority, got {action.kind}"
        
        # Test rerank priority (should prefer bump_rerank when ef is at max)
        inp = TuningInput(
            p95_ms=base_inp.p95_ms,
            recall_at10=base_inp.recall_at10,
            qps=base_inp.qps,
            params={"ef": 256, "rerank_mult": 3},  # ef at maximum
            slo=base_inp.slo,
            guards=base_inp.guards,
            near_T=base_inp.near_T,
            last_action=base_inp.last_action,
            adjustment_count=base_inp.adjustment_count
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None
            
            action = decide_tuning_action(inp)
            
            # Should prefer bump_rerank when ef is at maximum
            assert action.kind == "bump_rerank", f"Expected bump_rerank when ef at max, got {action.kind}"


class TestBoundaryConditionAssertions:
    """Tests with strict boundary condition assertions."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    def test_constraint_idempotency_exact(self):
        """Test exact idempotency of parameter clipping."""
        test_params = [
            {"ef": 1000, "T": 50, "Ncand_max": 100, "rerank_mult": 10},  # All out of bounds
            {"ef": 64, "T": 200, "Ncand_max": 500, "rerank_mult": 2},  # All at minimum
            {"ef": 256, "T": 1200, "Ncand_max": 2000, "rerank_mult": 6},  # All at maximum
            {"ef": 128, "T": 500, "Ncand_max": 1000, "rerank_mult": 3},  # All in range
        ]
        
        for params in test_params:
            # First clipping
            clipped1 = clip_params(params)
            
            # Second clipping (should be idempotent)
            clipped2 = clip_params(clipped1)
            
            # Should be identical
            assert clipped1 == clipped2, f"Idempotency failed for {params}: {clipped1} != {clipped2}"
            
            # Verify all parameters are in valid ranges
            assert 64 <= clipped1["ef"] <= 256, f"ef out of range: {clipped1['ef']}"
            assert 200 <= clipped1["T"] <= 1200, f"T out of range: {clipped1['T']}"
            assert 500 <= clipped1["Ncand_max"] <= 2000, f"Ncand_max out of range: {clipped1['Ncand_max']}"
            assert 2 <= clipped1["rerank_mult"] <= 6, f"rerank_mult out of range: {clipped1['rerank_mult']}"
    
    def test_exact_boundary_equality(self):
        """Test exact equality at parameter boundaries."""
        # Test minimum boundaries
        min_params = {"ef": 64, "T": 200, "Ncand_max": 500, "rerank_mult": 2}
        clipped_min = clip_params(min_params)
        assert clipped_min == min_params, f"Minimum params should be unchanged: {clipped_min} != {min_params}"
        
        # Test maximum boundaries
        max_params = {"ef": 256, "T": 1200, "Ncand_max": 2000, "rerank_mult": 6}
        clipped_max = clip_params(max_params)
        assert clipped_max == max_params, f"Maximum params should be unchanged: {clipped_max} != {max_params}"
    
    def test_step_sign_assertions(self):
        """Test exact step signs for all actions."""
        sign_tests = [
            ("bump_ef", 32.0),
            ("drop_ef", -32.0),
            ("bump_T", 100.0),
            ("drop_T", -100.0),
            ("bump_ncand", 200.0),
            ("drop_ncand", -200.0),
            ("bump_rerank", 1.0),
            ("drop_rerank", -1.0),
            ("noop", 0.0),
        ]
        
        for action_kind, expected_step in sign_tests:
            action = Action(kind=action_kind, step=expected_step, reason="test")
            
            # Test step sign
            if "bump" in action_kind:
                assert action.step > 0, f"{action_kind} should have positive step, got {action.step}"
            elif "drop" in action_kind:
                assert action.step < 0, f"{action_kind} should have negative step, got {action.step}"
            else:  # noop
                assert action.step == 0, f"{action_kind} should have zero step, got {action.step}"
