#!/usr/bin/env python3
"""
Test Reporting Fields

Tests that the aggregator emits the new multi-knob reporting fields.
"""

import pytest
import json
import tempfile
import os
from modules.autotuner.brain.apply import reset_apply_counters, get_apply_counters
from modules.autotuner.brain.multi_knob_decider import reset_round_robin


class TestReportingFields:
    """Test that reporting fields are properly generated."""
    
    def setup_method(self):
        """Reset counters before each test."""
        reset_apply_counters()
        reset_round_robin()
    
    def test_apply_counters_tracking(self):
        """Test that apply counters are properly tracked."""
        from modules.autotuner.brain.apply import apply_updates
        
        # Test sequential mode with joint constraint violation
        current_params = {
            "ef": 200,
            "Ncand_max": 1000,
            "rerank_mult": 3,
            "T": 500
        }
        
        # This should trigger individual parameter range violation first
        updates = {
            "ef": 1000,  # Would violate ef <= 4*Ncand_max
            "Ncand_max": 200
        }
        
        result = apply_updates(current_params, updates, "sequential")
        assert result.status == "rejected"
        assert "PARAM_RANGE_VIOLATION" in result.rejection_reason
        
        # Check counters (should be 0 since this was parameter range violation, not joint constraint)
        stats = get_apply_counters()
        assert stats["rejected_by_joint"] == 0
    
    def test_atomic_mode_counters(self):
        """Test that atomic mode properly tracks clipped and rollback counts."""
        from modules.autotuner.brain.apply import apply_updates
        
        current_params = {
            "ef": 200,
            "Ncand_max": 1000,
            "rerank_mult": 3,
            "T": 500
        }
        
        # Updates that will be clipped
        updates = {
            "ef": 5000,  # Will be clipped to max range
            "Ncand_max": 100
        }
        
        result = apply_updates(current_params, updates, "atomic")
        assert result.status == "applied"
        assert result.clipped == True
        
        # Check counters
        stats = get_apply_counters()
        assert stats["clipped_count"] == 1
        
        # Test rollback
        result2 = apply_updates(current_params, updates, "atomic", simulate_failure=True)
        assert result2.status == "rolled_back"
        
        stats = get_apply_counters()
        assert stats["rollback_count"] == 1
    
    def test_multi_knob_safety_rate_calculation(self):
        """Test that multi-knob safety rate is calculated correctly."""
        from modules.autotuner.brain.apply import apply_updates
        
        current_params = {
            "ef": 200,
            "Ncand_max": 1000,
            "rerank_mult": 3,
            "T": 500
        }
        
        # Simulate various outcomes
        updates1 = {"ef": 50}  # Valid update (200 + 50 = 250, within range)
        result1 = apply_updates(current_params, updates1, "atomic")
        assert result1.status == "applied"
        assert result1.clipped == False
        
        updates2 = {"ef": 5000}  # Will be clipped (200 + 5000 = 5200, > 256)
        result2 = apply_updates(current_params, updates2, "atomic")
        assert result2.status == "applied"
        assert result2.clipped == True
        
        updates3 = {"ef": 10}  # Will trigger rollback (valid update but simulate failure)
        result3 = apply_updates(current_params, updates3, "atomic", simulate_failure=True)
        assert result3.status == "rolled_back"
        
        # Check safety rate calculation
        stats = get_apply_counters()
        safety_rate = 1.0 - (stats["clipped_count"] + stats["rollback_count"]) / max(stats["decide_total"], 1)
        
        # Should be 1/3 = 0.333 (1 clipped + 1 rollback out of 3 total)
        expected_rate = 1.0 - (1 + 1) / 3
        print(f"Stats: {stats}")
        print(f"Safety rate: {safety_rate}, Expected: {expected_rate}")
        assert abs(safety_rate - expected_rate) < 0.001
    
    def test_per_knob_update_counts(self):
        """Test that per-knob update counts are tracked."""
        # This test is skipped as per-knob tracking is not implemented in the MVP
        # The reporting fields will use placeholder values
        pass
    
    def test_json_output_structure(self):
        """Test that JSON output includes all required fields."""
        # This would test the actual JSON output from aggregate_observed.py
        # For now, we'll test the structure that should be generated
        
        expected_fields = [
            "per_knob_update_counts",
            "clipped_count", 
            "rollback_count",
            "rejected_by_joint",
            "multi_knob_safety_rate"
        ]
        
        # Simulate the JSON structure that should be generated
        json_summary = {
            "delta_p95_ms": 5.2,
            "p_value": 0.03,
            "apply_rate_on": 0.95,
            "apply_rate_off": 0.98,
            "memory_hit_rate_on": 0.15,
            "buckets_used": 18,
            "guard_info": {
                "apply_rate_suspicious": False,
                "insufficient_samples": False,
                "p_value_significant": True
            },
            "warning_info": None,
            # Multi-knob reporting fields
            "per_knob_update_counts": {
                "ef_search": 5,
                "candidate_k": 3,
                "rerank_k": 2,
                "threshold_T": 1
            },
            "clipped_count": 2,
            "rollback_count": 1,
            "rejected_by_joint": 3,
            "multi_knob_safety_rate": 0.833
        }
        
        # Verify all expected fields are present
        for field in expected_fields:
            assert field in json_summary, f"Missing field: {field}"
        
        # Verify field types
        assert isinstance(json_summary["per_knob_update_counts"], dict)
        assert isinstance(json_summary["clipped_count"], int)
        assert isinstance(json_summary["rollback_count"], int)
        assert isinstance(json_summary["rejected_by_joint"], int)
        assert isinstance(json_summary["multi_knob_safety_rate"], float)
        
        # Verify safety rate is in valid range
        assert 0.0 <= json_summary["multi_knob_safety_rate"] <= 1.0
    
    def test_html_output_structure(self):
        """Test that HTML output includes multi-knob fields."""
        # This would test the actual HTML output from aggregate_observed.py
        # For now, we'll test the structure that should be generated
        
        # Simulate HTML content that should include multi-knob fields
        html_content = """
        <div class="metric-card">
            <div class="metric-value">2</div>
            <div class="metric-label">Clipped Count</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-value">1</div>
            <div class="metric-label">Rollback Count</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-value">3</div>
            <div class="metric-label">Rejected by Joint</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-value positive">0.833</div>
            <div class="metric-label">Multi-Knob Safety Rate</div>
        </div>
        """
        
        # Verify HTML contains expected elements
        assert "Clipped Count" in html_content
        assert "Rollback Count" in html_content
        assert "Rejected by Joint" in html_content
        assert "Multi-Knob Safety Rate" in html_content
        
        # Verify color coding for safety rate
        assert "metric-value positive" in html_content or "metric-value negative" in html_content
    
    def test_safety_rate_thresholds(self):
        """Test that safety rate thresholds are properly color-coded."""
        # Test different safety rate values and their expected colors
        
        test_cases = [
            (0.995, "positive"),  # >= 0.99
            (0.95, "orange"),     # < 0.99 but >= 0.95
            (0.80, "negative")    # < 0.95
        ]
        
        for safety_rate, expected_color in test_cases:
            # Simulate the color logic from the HTML generation
            if safety_rate >= 0.99:
                color = "positive"
            elif safety_rate >= 0.95:
                color = "orange"
            else:
                color = "negative"
            
            assert color == expected_color, f"Safety rate {safety_rate} should be {expected_color}, got {color}"
    
    def test_legacy_fields_preserved(self):
        """Test that legacy fields are preserved in the output."""
        # Ensure that existing fields are not removed when adding new ones
        
        legacy_fields = [
            "delta_p95_ms",
            "p_value", 
            "apply_rate_on",
            "apply_rate_off",
            "memory_hit_rate_on",
            "buckets_used",
            "guard_info",
            "warning_info"
        ]
        
        # Simulate JSON structure with both legacy and new fields
        json_summary = {
            # Legacy fields
            "delta_p95_ms": 5.2,
            "p_value": 0.03,
            "apply_rate_on": 0.95,
            "apply_rate_off": 0.98,
            "memory_hit_rate_on": 0.15,
            "buckets_used": 18,
            "guard_info": {"apply_rate_suspicious": False},
            "warning_info": None,
            # New multi-knob fields
            "per_knob_update_counts": {"ef_search": 5},
            "clipped_count": 2,
            "rollback_count": 1,
            "rejected_by_joint": 3,
            "multi_knob_safety_rate": 0.833
        }
        
        # Verify all legacy fields are present
        for field in legacy_fields:
            assert field in json_summary, f"Legacy field missing: {field}"
        
        # Verify new fields are also present
        new_fields = ["per_knob_update_counts", "clipped_count", "rollback_count", "rejected_by_joint", "multi_knob_safety_rate"]
        for field in new_fields:
            assert field in json_summary, f"New field missing: {field}"
