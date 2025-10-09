"""
Test memory hook contract and interface

Tests memory hook integration with stub/mock memory behavior,
verifying that the decider correctly scales steps and sets reasons
without needing real memory state.
"""

import pytest
from unittest.mock import patch, MagicMock
import os

from modules.autotuner.brain.decider import decide_tuning_action
from modules.autotuner.brain.hook import pre_decide_with_memory
from modules.autotuner.brain.contracts import TuningInput, SLO, Guards, Action, SweetSpot
from tests.fixtures import make_input, make_action, set_random_seed, MockMemory
from tests.utils_asserts import assert_action_properties


class TestMemoryHookContract:
    """Test memory hook interface and contract behavior."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    def _create_mock_memory_with_sweet_spot(self, inp, ef, meets_slo=True, age_s=100.0):
        """Helper to create mock memory with sweet spot using correct bucket ID."""
        mock_memory = MockMemory()
        bucket_id = mock_memory.default_bucket_of(inp)
        mock_memory.add_sweet_spot(bucket_id, ef=ef, meets_slo=meets_slo, age_s=age_s)
        return mock_memory
    
    def test_memory_hook_micro_step(self):
        """Test that memory hook returns micro step with correct scaling."""
        inp = make_input(
            params={"ef": 160, "Ncand_max": 400, "rerank_mult": 20, "T": 500}
        )
        
        # Create mock memory with sweet spot
        mock_memory = self._create_mock_memory_with_sweet_spot(inp, ef=200)
        
        # Test memory hook directly
        action = pre_decide_with_memory(inp, mock_memory)
        
        assert action is not None
        assert action.kind == "bump_ef"
        assert action.step == 16.0  # Micro step (smaller than normal 32)
        assert "memory" in action.reason.lower() or "follow" in action.reason.lower()
    
    def test_memory_hook_at_sweet_spot_noop(self):
        """Test that memory hook returns noop when at sweet spot."""
        inp = make_input(
            params={"ef": 160, "Ncand_max": 400, "rerank_mult": 20, "T": 500}  # Already at sweet spot
        )
        
        # Create mock memory with sweet spot
        mock_memory = self._create_mock_memory_with_sweet_spot(inp, ef=160)
        
        action = pre_decide_with_memory(inp, mock_memory)
        
        assert action is not None
        assert action.kind == "noop"
        assert "sweet_spot" in action.reason.lower() or "memory" in action.reason.lower()
    
    def test_memory_hook_miss_returns_none(self):
        """Test that memory hook returns None on miss."""
        mock_memory = MockMemory()  # No sweet spot added
        
        inp = make_input(
            params={"ef": 160, "Ncand_max": 400, "rerank_mult": 20, "T": 500}
        )
        
        action = pre_decide_with_memory(inp, mock_memory)
        
        assert action is None
    
    def test_memory_hook_stale_sweet_spot(self):
        """Test that memory hook works with sweet spots regardless of age (staleness is handled by memory system)."""
        inp = make_input(
            params={"ef": 160, "Ncand_max": 400, "rerank_mult": 20, "T": 500}
        )
        
        # Create mock memory with old sweet spot
        mock_memory = self._create_mock_memory_with_sweet_spot(inp, ef=200, age_s=1000.0)  # Old but still valid
        
        action = pre_decide_with_memory(inp, mock_memory)
        # Memory hook should still work - staleness is handled by memory system, not hook
        assert action is not None
        assert action.kind == "bump_ef"
        assert action.step == 16.0
    
    def test_memory_hook_invalid_sweet_spot(self):
        """Test that memory hook ignores sweet spots that don't meet SLO."""
        inp = make_input(
            params={"ef": 160, "Ncand_max": 400, "rerank_mult": 20, "T": 500}
        )
        
        mock_memory = self._create_mock_memory_with_sweet_spot(inp, ef=200, meets_slo=False)
        
        action = pre_decide_with_memory(inp, mock_memory)
        
        assert action is None
    
    def test_memory_hook_disabled_returns_none(self):
        """Test that memory hook returns None when memory is disabled."""
        mock_memory = MockMemory(enabled=False)
        bucket_id = "test_bucket"
        mock_memory.add_sweet_spot(bucket_id, ef=200, meets_slo=True, age_s=100.0)
        
        inp = make_input(
            params={"ef": 160, "Ncand_max": 400, "rerank_mult": 20, "T": 500}
        )
        
        with patch.dict(os.environ, {'MEMORY_ENABLED': '0'}):
            action = pre_decide_with_memory(inp, mock_memory)
            assert action is None
    
    def test_memory_hook_step_scaling(self):
        """Test that memory hook uses smaller step sizes."""
        # Test different ef gaps
        test_cases = [
            {"current_ef": 160, "sweet_ef": 200, "expected_step": 16.0, "expected_kind": "bump_ef"},
            {"current_ef": 200, "sweet_ef": 160, "expected_step": -16.0, "expected_kind": "drop_ef"},
            {"current_ef": 160, "sweet_ef": 180, "expected_step": 16.0, "expected_kind": "bump_ef"},
        ]
        
        for case in test_cases:
            inp = make_input(
                params={"ef": case["current_ef"], "Ncand_max": 400, "rerank_mult": 20, "T": 500}
            )
            
            mock_memory = self._create_mock_memory_with_sweet_spot(inp, ef=case["sweet_ef"])
            
            action = pre_decide_with_memory(inp, mock_memory)
            
            assert action is not None
            assert action.kind == case["expected_kind"]
            assert action.step == case["expected_step"]
            assert abs(action.step) == 16.0  # Always micro step


class TestMemoryHookIntegration:
    """Test memory hook integration with decider."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    def _create_mock_memory_with_sweet_spot(self, inp, ef, meets_slo=True, age_s=100.0):
        """Helper to create mock memory with sweet spot using correct bucket ID."""
        mock_memory = MockMemory()
        bucket_id = mock_memory.default_bucket_of(inp)
        mock_memory.add_sweet_spot(bucket_id, ef=ef, meets_slo=meets_slo, age_s=age_s)
        return mock_memory
    
    def test_memory_hook_takes_precedence(self):
        """Test that memory hook takes precedence over normal decision logic."""
        inp = make_input(
            params={"ef": 160, "Ncand_max": 400, "rerank_mult": 20, "T": 500},
            p95_ms=40.0,  # Low latency to trigger bump_ef
            recall_at10=0.65,
            slo=SLO(p95_ms=150.0, recall_at10=0.80)
        )
        
        mock_memory = self._create_mock_memory_with_sweet_spot(inp, ef=200)
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_get_memory:
            mock_get_memory.return_value = mock_memory
            # Mock the default_bucket_of method
            mock_memory.default_bucket_of = MagicMock(return_value=mock_memory.default_bucket_of(inp))
            
            action = decide_tuning_action(inp)
            
            # Should use memory hook (micro step) instead of normal logic
            assert action.kind == "bump_ef"
            assert action.step == 16.0  # Micro step from memory
            assert "memory" in action.reason.lower() or "follow" in action.reason.lower()
    
    def test_memory_hook_fallback_to_normal_logic(self):
        """Test that normal logic is used when memory hook returns None."""
        mock_memory = MockMemory()  # No sweet spot added
        
        inp = make_input(
            params={"ef": 160, "Ncand_max": 400, "rerank_mult": 20, "T": 500},
            p95_ms=40.0,  # Low latency to trigger bump_ef
            recall_at10=0.65,
            slo=SLO(p95_ms=150.0, recall_at10=0.80)
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_get_memory:
            mock_get_memory.return_value = mock_memory
            # Mock the default_bucket_of method
            mock_memory.default_bucket_of = MagicMock(return_value=mock_memory.default_bucket_of(inp))
            
            action = decide_tuning_action(inp)
            
            # Should use normal logic (larger step)
            assert action.kind == "bump_ef"
            assert action.step == 32.0  # Normal step
            assert "memory" not in action.reason.lower()
    
    def test_memory_hook_with_cooldown_guard(self):
        """Test memory hook behavior with cooldown guard."""
        inp = make_input(
            params={"ef": 160, "Ncand_max": 400, "rerank_mult": 20, "T": 500},
            guards=Guards(cooldown=True, stable=False),  # Explicit cooldown
            p95_ms=40.0,  # Low latency to trigger bump_ef
            recall_at10=0.65,
            slo=SLO(p95_ms=150.0, recall_at10=0.80)
        )
        
        mock_memory = self._create_mock_memory_with_sweet_spot(inp, ef=200)
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_get_memory:
            mock_get_memory.return_value = mock_memory
            # Mock the default_bucket_of method
            mock_memory.default_bucket_of = MagicMock(return_value=mock_memory.default_bucket_of(inp))
            
            action = decide_tuning_action(inp)
            
            # Memory hook takes precedence over cooldown guard (memory hook is checked first)
            assert action.kind == "bump_ef"
            assert action.step == 16.0  # Micro step from memory
            assert "memory" in action.reason.lower() or "follow" in action.reason.lower()
    
    def test_memory_hook_with_hysteresis(self):
        """Test memory hook behavior with hysteresis."""
        inp = make_input(
            params={"ef": 160, "Ncand_max": 400, "rerank_mult": 20, "T": 500},
            p95_ms=155.0,  # Within hysteresis band
            recall_at10=0.81,  # Within hysteresis band
            slo=SLO(p95_ms=150.0, recall_at10=0.80)
        )
        
        mock_memory = self._create_mock_memory_with_sweet_spot(inp, ef=200)
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_get_memory:
            mock_get_memory.return_value = mock_memory
            # Mock the default_bucket_of method
            mock_memory.default_bucket_of = MagicMock(return_value=mock_memory.default_bucket_of(inp))
            
            action = decide_tuning_action(inp)
            
            # Memory hook should take precedence over hysteresis
            assert action.kind == "bump_ef"
            assert action.step == 16.0  # Micro step from memory
            assert "memory" in action.reason.lower() or "follow" in action.reason.lower()


class TestMemoryHookEdgeCases:
    """Test edge cases in memory hook behavior."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    def test_memory_hook_small_ef_gap(self):
        """Test memory hook with small ef gap (within step_min)."""
        mock_memory = MockMemory()
        
        inp = make_input(
            params={"ef": 160, "Ncand_max": 400, "rerank_mult": 20, "T": 500}  # Gap = 10 < 16
        )
        
        # Get the bucket_id that will be used by the memory hook
        bucket_id = mock_memory.default_bucket_of(inp)
        mock_memory.add_sweet_spot(bucket_id, ef=170, meets_slo=True, age_s=100.0)  # Small gap
        
        action = pre_decide_with_memory(inp, mock_memory)
        
        # Should return noop when gap is too small
        assert action.kind == "noop"
        assert action.reason == "at_sweet_spot"
    
    def test_memory_hook_zero_ef_gap(self):
        """Test memory hook with zero ef gap."""
        mock_memory = MockMemory()
        
        inp = make_input(
            params={"ef": 160, "Ncand_max": 400, "rerank_mult": 20, "T": 500}
        )
        
        # Get the bucket_id that will be used by the memory hook
        bucket_id = mock_memory.default_bucket_of(inp)
        mock_memory.add_sweet_spot(bucket_id, ef=160, meets_slo=True, age_s=100.0)  # No gap
        
        action = pre_decide_with_memory(inp, mock_memory)
        
        # Should return noop when already at sweet spot
        assert action.kind == "noop"
        assert action.reason == "at_sweet_spot"
    
    def test_memory_hook_large_ef_gap(self):
        """Test memory hook with large ef gap."""
        mock_memory = MockMemory()
        
        inp = make_input(
            params={"ef": 160, "Ncand_max": 400, "rerank_mult": 20, "T": 500}  # Gap = 140 > 16
        )
        
        # Get the bucket_id that will be used by the memory hook
        bucket_id = mock_memory.default_bucket_of(inp)
        mock_memory.add_sweet_spot(bucket_id, ef=300, meets_slo=True, age_s=100.0)  # Large gap
        
        action = pre_decide_with_memory(inp, mock_memory)
        
        # Should return micro step towards sweet spot
        assert action.kind == "bump_ef"
        assert action.step == 16.0  # Micro step, not full gap
    
    def test_memory_hook_missing_ef_param(self):
        """Test memory hook when ef parameter is missing."""
        mock_memory = MockMemory()
        
        inp = make_input(
            params={"Ncand_max": 400, "rerank_mult": 20, "T": 500}  # Missing ef
        )
        
        # Get the bucket_id that will be used by the memory hook
        bucket_id = mock_memory.default_bucket_of(inp)
        mock_memory.add_sweet_spot(bucket_id, ef=200, meets_slo=True, age_s=100.0)
        
        action = pre_decide_with_memory(inp, mock_memory)
        
        # Should handle missing ef gracefully
        # The hook should use default ef value (128) and proceed
        assert action is not None
        assert action.kind in ["bump_ef", "drop_ef", "noop"]
    
    def test_memory_hook_query_returns_none(self):
        """Test memory hook when memory query returns None."""
        mock_memory = MockMemory()  # No sweet spot added, so query returns None
        
        inp = make_input(
            params={"ef": 160, "Ncand_max": 400, "rerank_mult": 20, "T": 500}
        )
        
        # Mock query to return None explicitly
        mock_memory.query = MagicMock(return_value=None)
        
        action = pre_decide_with_memory(inp, mock_memory)
        
        assert action is None


class TestMemoryHookContractCompliance:
    """Test compliance with memory hook contract."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    def test_memory_hook_always_returns_action_or_none(self):
        """Test that memory hook always returns Action or None."""
        mock_memory = MockMemory()
        
        test_cases = [
            # Valid sweet spot
            {"sweet_ef": 200, "meets_slo": True, "age_s": 100.0},
            # Invalid sweet spot
            {"sweet_ef": 200, "meets_slo": False, "age_s": 100.0},
            # Stale sweet spot
            {"sweet_ef": 200, "meets_slo": True, "age_s": 1000.0},
            # No sweet spot
            None,
        ]
        
        for case in test_cases:
            if case:
                mock_memory.add_sweet_spot("test_bucket", ef=case["sweet_ef"], 
                                         meets_slo=case["meets_slo"], age_s=case["age_s"])
            
            inp = make_input(
                params={"ef": 160, "Ncand_max": 400, "rerank_mult": 20, "T": 500}
            )
            
            action = pre_decide_with_memory(inp, mock_memory)
            
            # Should always return Action or None
            assert action is None or isinstance(action, Action)
    
    def test_memory_hook_reason_consistency(self):
        """Test that memory hook reasons are consistent."""
        mock_memory = MockMemory()
        
        # Test different scenarios and their expected reasons
        scenarios = [
            {"gap": 50, "expected_reason_contains": ["follow", "memory"]},
            {"gap": 5, "expected_reason_contains": ["sweet_spot", "memory"]},
        ]
        
        for scenario in scenarios:
            mock_memory.add_sweet_spot("test_bucket", ef=160 + scenario["gap"], 
                                     meets_slo=True, age_s=100.0)
            
            inp = make_input(
                params={"ef": 160, "Ncand_max": 400, "rerank_mult": 20, "T": 500}
            )
            
            action = pre_decide_with_memory(inp, mock_memory)
            
            if action is not None:
                # Reason should contain expected keywords
                reason_lower = action.reason.lower()
                for expected in scenario["expected_reason_contains"]:
                    assert expected in reason_lower, f"Reason '{action.reason}' should contain '{expected}'"
