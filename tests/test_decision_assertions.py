"""
Strengthened decision logic tests with exact action and step assertions.

These tests address coverage gaps identified by mutation probes P1 and P2.
"""

import pytest
from unittest.mock import patch, MagicMock

from modules.autotuner.brain.decider import decide_tuning_action
from modules.autotuner.brain.contracts import TuningInput, SLO, Guards, Action
from tests.fixtures import make_input, set_random_seed


class TestDecisionLogicAssertions:
    """Tests with strict assertions for decision logic."""
    
    def setup_method(self):
        """Set up deterministic random state for each test."""
        set_random_seed(0)
    
    def test_high_latency_recall_redundancy_exact_assertions(self):
        """Test high latency with recall redundancy - assert exact action and step."""
        inp = make_input(
            p95_ms=250.0,  # High latency (250 > 150)
            recall_at10=0.92,  # High recall (0.92 > 0.80 + 0.05)
            slo=SLO(p95_ms=150.0, recall_at10=0.80),
            params={"ef": 128}  # Not at minimum
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None  # No memory hit
            
            action = decide_tuning_action(inp)
            
            # Exact assertions
            assert action.kind == "drop_ef", f"Expected drop_ef for high latency + recall redundancy, got {action.kind}"
            assert action.step == -32.0, f"Expected step -32.0, got {action.step}"
            assert "high_latency_with_recall_redundancy" in action.reason, f"Expected reason containing 'high_latency_with_recall_redundancy', got {action.reason}"
    
    def test_low_recall_latency_margin_exact_assertions(self):
        """Test low recall with latency margin - assert exact action and step."""
        inp = make_input(
            p95_ms=40.0,  # Low latency (40 < 150 - 100)
            recall_at10=0.65,  # Low recall (0.65 < 0.80)
            slo=SLO(p95_ms=150.0, recall_at10=0.80),
            params={"ef": 128}  # Not at maximum
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None  # No memory hit
            
            action = decide_tuning_action(inp)
            
            # Exact assertions
            assert action.kind == "bump_ef", f"Expected bump_ef for low recall + latency margin, got {action.kind}"
            assert action.step == 32.0, f"Expected step 32.0, got {action.step}"
            assert "low_recall_with_latency_margin" in action.reason, f"Expected reason containing 'low_recall_with_latency_margin', got {action.reason}"
    
    def test_ef_at_minimum_drop_ncand_exact_assertions(self):
        """Test ef at minimum - should drop ncand instead of ef."""
        inp = make_input(
            p95_ms=250.0,  # High latency
            recall_at10=0.92,  # High recall
            slo=SLO(p95_ms=150.0, recall_at10=0.80),
            params={"ef": 64}  # At minimum
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None  # No memory hit
            
            action = decide_tuning_action(inp)
            
            # Exact assertions
            assert action.kind == "drop_ncand", f"Expected drop_ncand when ef at minimum, got {action.kind}"
            assert action.step == -200.0, f"Expected step -200.0, got {action.step}"
            assert "high_latency_ef_at_min_drop_ncand" in action.reason, f"Expected reason containing 'high_latency_ef_at_min_drop_ncand', got {action.reason}"
    
    def test_ef_at_maximum_bump_rerank_exact_assertions(self):
        """Test ef at maximum - should bump rerank instead of ef."""
        inp = make_input(
            p95_ms=40.0,  # Low latency
            recall_at10=0.65,  # Low recall
            slo=SLO(p95_ms=150.0, recall_at10=0.80),
            params={"ef": 256}  # At maximum
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None  # No memory hit
            
            action = decide_tuning_action(inp)
            
            # Exact assertions
            assert action.kind == "bump_rerank", f"Expected bump_rerank when ef at maximum, got {action.kind}"
            assert action.step == 1.0, f"Expected step 1.0, got {action.step}"
            assert "low_recall_ef_at_max_bump_rerank" in action.reason, f"Expected reason containing 'low_recall_ef_at_max_bump_rerank', got {action.reason}"
    
    def test_within_slo_exact_assertions(self):
        """Test within SLO - should be noop."""
        inp = make_input(
            p95_ms=140.0,  # Within SLO (140 < 150)
            recall_at10=0.85,  # Within SLO (0.85 >= 0.80)
            slo=SLO(p95_ms=150.0, recall_at10=0.80)
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None  # No memory hit
            
            action = decide_tuning_action(inp)
            
            # Exact assertions
            assert action.kind == "noop", f"Expected noop when within SLO, got {action.kind}"
            assert action.step == 0.0, f"Expected step 0.0, got {action.step}"
            assert "within_slo_or_uncertain" in action.reason, f"Expected reason containing 'within_slo_or_uncertain', got {action.reason}"
    
    def test_hysteresis_band_exact_assertions(self):
        """Test hysteresis band - should be noop even if slightly outside SLO."""
        inp = make_input(
            p95_ms=155.0,  # Slightly above SLO (155 > 150) but within hysteresis band (155 < 150 + 100)
            recall_at10=0.81,  # Slightly above SLO (0.81 > 0.80) but within hysteresis band (0.81 < 0.80 + 0.02)
            slo=SLO(p95_ms=150.0, recall_at10=0.80),
            guards=Guards(cooldown=False, stable=True)  # Stable state for hysteresis
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None  # No memory hit
            
            action = decide_tuning_action(inp)
            
            # Exact assertions
            assert action.kind == "noop", f"Expected noop within hysteresis band, got {action.kind}"
            assert action.step == 0.0, f"Expected step 0.0, got {action.step}"
            assert "within_hysteresis_band" in action.reason, f"Expected reason containing 'within_hysteresis_band', got {action.reason}"
    
    def test_cooldown_exact_assertions(self):
        """Test cooldown - should be noop even if action would be taken."""
        inp = make_input(
            p95_ms=40.0,  # Low latency that would trigger bump_ef
            recall_at10=0.65,  # Low recall that would trigger bump_ef
            slo=SLO(p95_ms=150.0, recall_at10=0.80),
            guards=Guards(cooldown=True, stable=True),  # Cooldown active
            last_action=Action(kind="bump_ef", step=32.0, reason="previous", age_sec=5.0)  # Recent action
        )
        
        with patch('modules.autotuner.brain.decider.get_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.default_bucket_of.return_value = "test_bucket"
            mock_memory.return_value.query.return_value = None  # No memory hit
            
            action = decide_tuning_action(inp)
            
            # Exact assertions
            assert action.kind == "noop", f"Expected noop due to cooldown, got {action.kind}"
            assert action.step == 0.0, f"Expected step 0.0, got {action.step}"
            assert "cooldown" in action.reason.lower(), f"Expected reason containing 'cooldown', got {action.reason}"
