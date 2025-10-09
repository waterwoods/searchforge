#!/usr/bin/env python3
"""
Test Report Gateways

Tests that the A/B report generation includes all required fields and applies color rules correctly.
"""

import pytest
import os
import json
import tempfile
import subprocess
import sys
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class TestReportGateways:
    """Test report generation and gateway logic."""
    
    def test_summary_includes_required_fields(self):
        """Test that summary includes apply_rate_on/off, multi_knob_safety_rate, buckets, duration."""
        from scripts.run_brain_ab_experiment import run_ab_simulation, calculate_ab_metrics
        
        # Run simulation
        events_a, events_b = run_ab_simulation(duration_sec=60, bucket_sec=3)
        metrics = calculate_ab_metrics(events_a, events_b, bucket_sec=3)
        
        # Check required fields are present
        required_fields = [
            "apply_rate_a", "apply_rate_b", "multi_knob_safety_rate"
        ]
        
        for field in required_fields:
            assert field in metrics, f"Missing field: {field}"
        
        # Check that metrics have reasonable values
        assert 0 <= metrics["apply_rate_a"] <= 1
        assert 0 <= metrics["apply_rate_b"] <= 1
        assert 0 <= metrics["multi_knob_safety_rate"] <= 1
    
    def test_color_rules_green_yellow_red(self):
        """Test that color rules for GREEN/YELLOW/RED are applied correctly."""
        from scripts.aggregate_observed import generate_simulator_ab_html
        
        # Test GREEN case: delta_p95 > 0 and p_value < 0.05
        events_a = [{"event": "RESPONSE", "cost_ms": 100.0, "stats": {"recall_at10": 0.8}, "ts": "2024-01-01T00:00:00Z"}]
        events_b = [{"event": "RESPONSE", "cost_ms": 90.0, "stats": {"recall_at10": 0.85}, "ts": "2024-01-01T00:00:00Z"}]
        
        metrics = {
            "p_value": 0.03,  # < 0.05
            "apply_rate_a": 0.1,
            "apply_rate_b": 0.15,
            "multi_knob_safety_rate": 0.99,
            "run_params": {"duration_sec": 120, "bucket_sec": 5, "qps": 10.0, "buckets_generated": 24}
        }
        
        html_content = generate_simulator_ab_html(events_a, events_b, metrics, {}, "test_off", "test_on")
        
        # Should contain GREEN indicators
        assert "positive" in html_content  # GREEN color class
        
        # Test YELLOW case: p in [0.05, 0.1] or |delta| < 1ms
        metrics_yellow = metrics.copy()
        metrics_yellow["p_value"] = 0.08  # In [0.05, 0.1]
        
        html_yellow = generate_simulator_ab_html(events_a, events_b, metrics_yellow, {}, "test_off", "test_on")
        
        # Should contain YELLOW indicators
        assert "orange" in html_yellow  # YELLOW color class
        
        # Test RED case: p > 0.1 and |delta| >= 1ms
        metrics_red = metrics.copy()
        metrics_red["p_value"] = 0.15  # > 0.1
        
        html_red = generate_simulator_ab_html(events_a, events_b, metrics_red, {}, "test_off", "test_on")
        
        # Should contain RED indicators
        assert "negative" in html_red  # RED color class
    
    def test_low_sample_warning_triggers(self):
        """Test that warning triggers when buckets < 10."""
        from scripts.aggregate_observed import generate_simulator_ab_html
        
        events_a = [{"event": "RESPONSE", "cost_ms": 100.0, "stats": {"recall_at10": 0.8}, "ts": "2024-01-01T00:00:00Z"}]
        events_b = [{"event": "RESPONSE", "cost_ms": 90.0, "stats": {"recall_at10": 0.85}, "ts": "2024-01-01T00:00:00Z"}]
        
        # Low sample case
        metrics_low = {
            "p_value": 0.03,
            "apply_rate_a": 0.1,
            "apply_rate_b": 0.15,
            "multi_knob_safety_rate": 0.99,
            "run_params": {"duration_sec": 30, "bucket_sec": 5, "qps": 10.0, "buckets_generated": 6}  # < 10
        }
        
        html_low = generate_simulator_ab_html(events_a, events_b, metrics_low, {}, "test_off", "test_on")
        
        # Should contain warning
        assert "WARNING" in html_low
        assert "Low sample regime" in html_low
        assert "buckets < 10" in html_low
        
        # High sample case
        metrics_high = metrics_low.copy()
        metrics_high["run_params"]["buckets_generated"] = 24  # >= 10
        
        html_high = generate_simulator_ab_html(events_a, events_b, metrics_high, {}, "test_off", "test_on")
        
        # Should not contain warning
        assert "WARNING" not in html_high
        assert "Low sample regime" not in html_high
    
    def test_delta_p95_formula_displayed(self):
        """Test that the ΔP95 formula is displayed in the HTML header."""
        from scripts.aggregate_observed import generate_simulator_ab_html
        
        events_a = [{"event": "RESPONSE", "cost_ms": 100.0, "stats": {"recall_at10": 0.8}, "ts": "2024-01-01T00:00:00Z"}]
        events_b = [{"event": "RESPONSE", "cost_ms": 90.0, "stats": {"recall_at10": 0.85}, "ts": "2024-01-01T00:00:00Z"}]
        
        metrics = {
            "p_value": 0.03,
            "apply_rate_a": 0.1,
            "apply_rate_b": 0.15,
            "multi_knob_safety_rate": 0.99,
            "run_params": {"duration_sec": 120, "bucket_sec": 5, "qps": 10.0, "buckets_generated": 24}
        }
        
        html_content = generate_simulator_ab_html(events_a, events_b, metrics, {}, "test_off", "test_on")
        
        # Should contain formula
        assert "ΔP95 = mean(p95_single) - mean(p95_multi)" in html_content
        assert "GREEN if ΔP95 > 0 and p < 0.05" in html_content
        assert "YELLOW if p ∈ [0.05,0.1] or |ΔP95| < 1ms" in html_content
        assert "RED otherwise" in html_content
    
    def test_per_knob_counts_displayed(self):
        """Test that per-knob update counts are displayed with percentages."""
        from scripts.aggregate_observed import generate_simulator_ab_html
        
        events_a = [{"event": "RESPONSE", "cost_ms": 100.0, "stats": {"recall_at10": 0.8}, "ts": "2024-01-01T00:00:00Z"}]
        events_b = [{"event": "RESPONSE", "cost_ms": 90.0, "stats": {"recall_at10": 0.85}, "ts": "2024-01-01T00:00:00Z"}]
        
        metrics = {
            "p_value": 0.03,
            "apply_rate_a": 0.1,
            "apply_rate_b": 0.15,
            "multi_knob_safety_rate": 0.99,
            "ef_search_updates": 10,
            "candidate_k_updates": 8,
            "rerank_k_updates": 5,
            "threshold_T_updates": 3,
            "decide_total": 20,
            "run_params": {"duration_sec": 120, "bucket_sec": 5, "qps": 10.0, "buckets_generated": 24}
        }
        
        html_content = generate_simulator_ab_html(events_a, events_b, metrics, {}, "test_off", "test_on")
        
        # Should contain per-knob table
        assert "Per-Knob Update Counts" in html_content
        assert "EF Search" in html_content
        assert "Candidate K" in html_content
        assert "Rerank K" in html_content
        assert "Threshold T" in html_content
        
        # Should contain percentages
        assert "50.0%" in html_content  # 10/20 * 100
        assert "40.0%" in html_content  # 8/20 * 100
        assert "25.0%" in html_content  # 5/20 * 100
        assert "15.0%" in html_content  # 3/20 * 100
    
    def test_top_3_reasons_displayed(self):
        """Test that top-3 rejection/clip reasons are displayed."""
        from scripts.aggregate_observed import generate_simulator_ab_html
        
        events_a = [{"event": "RESPONSE", "cost_ms": 100.0, "stats": {"recall_at10": 0.8}, "ts": "2024-01-01T00:00:00Z"}]
        events_b = [{"event": "RESPONSE", "cost_ms": 90.0, "stats": {"recall_at10": 0.85}, "ts": "2024-01-01T00:00:00Z"}]
        
        metrics = {
            "p_value": 0.03,
            "apply_rate_a": 0.1,
            "apply_rate_b": 0.15,
            "multi_knob_safety_rate": 0.99,
            "rejected_by_joint": 5,
            "clipped_count": 3,
            "rollback_count": 1,
            "run_params": {"duration_sec": 120, "bucket_sec": 5, "qps": 10.0, "buckets_generated": 24}
        }
        
        html_content = generate_simulator_ab_html(events_a, events_b, metrics, {}, "test_off", "test_on")
        
        # Should contain top-3 reasons table
        assert "Top-3 Rejection/Clip Reasons" in html_content
        assert "Rejected by Joint" in html_content
        assert "Clipped Count" in html_content
        assert "Rollback Count" in html_content
        
        # Should contain the counts
        assert "5" in html_content  # rejected_by_joint
        assert "3" in html_content  # clipped_count
        assert "1" in html_content  # rollback_count
    
    def test_safety_rate_color_thresholds(self):
        """Test that safety rate color thresholds are applied correctly."""
        from scripts.aggregate_observed import generate_simulator_ab_html
        
        events_a = [{"event": "RESPONSE", "cost_ms": 100.0, "stats": {"recall_at10": 0.8}, "ts": "2024-01-01T00:00:00Z"}]
        events_b = [{"event": "RESPONSE", "cost_ms": 90.0, "stats": {"recall_at10": 0.85}, "ts": "2024-01-01T00:00:00Z"}]
        
        # Test GREEN case: safety_rate >= 0.99
        metrics_green = {
            "p_value": 0.03,
            "apply_rate_a": 0.1,
            "apply_rate_b": 0.15,
            "multi_knob_safety_rate": 0.995,  # >= 0.99
            "run_params": {"duration_sec": 120, "bucket_sec": 5, "qps": 10.0, "buckets_generated": 24}
        }
        
        html_green = generate_simulator_ab_html(events_a, events_b, metrics_green, {}, "test_off", "test_on")
        assert "positive" in html_green  # GREEN
        
        # Test ORANGE case: 0.95 <= safety_rate < 0.99
        metrics_orange = metrics_green.copy()
        metrics_orange["multi_knob_safety_rate"] = 0.97  # In [0.95, 0.99)
        
        html_orange = generate_simulator_ab_html(events_a, events_b, metrics_orange, {}, "test_off", "test_on")
        assert "orange" in html_orange  # YELLOW
        
        # Test RED case: safety_rate < 0.95
        metrics_red = metrics_green.copy()
        metrics_red["multi_knob_safety_rate"] = 0.90  # < 0.95
        
        html_red = generate_simulator_ab_html(events_a, events_b, metrics_red, {}, "test_off", "test_on")
        assert "negative" in html_red  # RED
    
    def test_apply_rate_color_thresholds(self):
        """Test that apply rate color thresholds are applied correctly."""
        from scripts.aggregate_observed import generate_simulator_ab_html
        
        events_a = [{"event": "RESPONSE", "cost_ms": 100.0, "stats": {"recall_at10": 0.8}, "ts": "2024-01-01T00:00:00Z"}]
        events_b = [{"event": "RESPONSE", "cost_ms": 90.0, "stats": {"recall_at10": 0.85}, "ts": "2024-01-01T00:00:00Z"}]
        
        # Test GREEN case: apply_rate >= 0.95
        metrics_green = {
            "p_value": 0.03,
            "apply_rate_a": 0.96,  # >= 0.95
            "apply_rate_b": 0.98,  # >= 0.95
            "multi_knob_safety_rate": 0.99,
            "run_params": {"duration_sec": 120, "bucket_sec": 5, "qps": 10.0, "buckets_generated": 24}
        }
        
        html_green = generate_simulator_ab_html(events_a, events_b, metrics_green, {}, "test_off", "test_on")
        assert "positive" in html_green  # GREEN
        
        # Test ORANGE case: 0.90 <= apply_rate < 0.95
        metrics_orange = metrics_green.copy()
        metrics_orange["apply_rate_a"] = 0.92  # In [0.90, 0.95)
        metrics_orange["apply_rate_b"] = 0.93
        
        html_orange = generate_simulator_ab_html(events_a, events_b, metrics_orange, {}, "test_off", "test_on")
        assert "orange" in html_orange  # YELLOW
        
        # Test RED case: apply_rate < 0.90
        metrics_red = metrics_green.copy()
        metrics_red["apply_rate_a"] = 0.85  # < 0.90
        metrics_red["apply_rate_b"] = 0.88
        
        html_red = generate_simulator_ab_html(events_a, events_b, metrics_red, {}, "test_off", "test_on")
        assert "negative" in html_red  # RED
    
    def test_pass_fail_verdict_card(self):
        """Test that PASS/FAIL verdict card works correctly."""
        from scripts.aggregate_observed import generate_simulator_ab_html
        
        events_a = [{"event": "RESPONSE", "cost_ms": 100.0, "stats": {"recall_at10": 0.8}, "ts": "2024-01-01T00:00:00Z"}]
        events_b = [{"event": "RESPONSE", "cost_ms": 90.0, "stats": {"recall_at10": 0.85}, "ts": "2024-01-01T00:00:00Z"}]
        
        # Test PASS case: delta_p95 > 0, p_value < 0.05, delta_recall >= -0.01
        metrics_pass = {
            "p_value": 0.03,  # < 0.05
            "apply_rate_a": 0.1,
            "apply_rate_b": 0.15,
            "multi_knob_safety_rate": 0.99,
            "run_params": {"duration_sec": 120, "bucket_sec": 5, "qps": 10.0, "buckets_generated": 24}
        }
        
        html_pass = generate_simulator_ab_html(events_a, events_b, metrics_pass, {}, "test_off", "test_on")
        assert "PASS" in html_pass
        assert "VERDICT" in html_pass
        assert "PASS if: ΔP95 > 0 AND p < 0.05 AND ΔRecall ≥ -0.01" in html_pass
        
        # Test FAIL case: flip delta_p95 sign
        events_a_fail = [{"event": "RESPONSE", "cost_ms": 90.0, "stats": {"recall_at10": 0.8}, "ts": "2024-01-01T00:00:00Z"}]
        events_b_fail = [{"event": "RESPONSE", "cost_ms": 100.0, "stats": {"recall_at10": 0.85}, "ts": "2024-01-01T00:00:00Z"}]
        
        html_fail = generate_simulator_ab_html(events_a_fail, events_b_fail, metrics_pass, {}, "test_off", "test_on")
        assert "FAIL" in html_fail
    
    def test_reproducibility_fields_present(self):
        """Test that reproducibility fields are present in JSON/HTML."""
        from scripts.run_brain_ab_experiment import run_ab_simulation, calculate_ab_metrics
        import tempfile
        import subprocess
        import sys
        
        # Run simulation through main function to get run_params
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = os.path.join(temp_dir, "test.csv")
            
            # Run the main function with simulator mode
            result = subprocess.run([
                sys.executable, "scripts/run_brain_ab_experiment.py",
                "--mode", "simulator",
                "--duration-sec", "60",
                "--bucket-sec", "3",
                "--seed", "42",
                "--perm-trials", "500",
                "--csv-out", csv_path
            ], capture_output=True, text=True, cwd="/Users/nanxinli/Documents/dev/searchforge")
            
            assert result.returncode == 0, f"Simulation failed: {result.stderr}"
            
            # Find the generated directories
            import glob
            off_dirs = glob.glob(os.path.join("/Users/nanxinli/Documents/dev/searchforge", "reports/observed/ab_effectiveness/single_knob_*"))
            on_dirs = glob.glob(os.path.join("/Users/nanxinli/Documents/dev/searchforge", "reports/observed/ab_effectiveness/multi_knob_*"))
            
            if off_dirs and on_dirs:
                # Load metrics from the most recent run
                off_dir = max(off_dirs, key=os.path.getctime)
                on_dir = max(on_dirs, key=os.path.getctime)
                
                with open(os.path.join(off_dir, "metrics.json"), 'r') as f:
                    metrics = json.load(f)
                
                # Check that run_params contains reproducibility fields
                assert "run_params" in metrics
                run_params = metrics["run_params"]
                
                required_fields = ["seed", "perm_trials", "duration_sec", "bucket_sec", "qps"]
                for field in required_fields:
                    assert field in run_params, f"Missing reproducibility field: {field}"
                
                # Check values match what we passed
                assert run_params["seed"] == 42
                assert run_params["perm_trials"] == 500
                assert run_params["duration_sec"] == 60
                assert run_params["bucket_sec"] == 3
                assert run_params["qps"] == 10.0
                
                # Check CSV was created
                assert os.path.exists(csv_path)
                
                # Clean up
                import shutil
                shutil.rmtree(off_dir, ignore_errors=True)
                shutil.rmtree(on_dir, ignore_errors=True)
    
    def test_csv_export_functionality(self):
        """Test that CSV export works correctly."""
        from scripts.run_brain_ab_experiment import run_ab_simulation, export_csv_data
        import csv
        import tempfile
        
        # Run simulation
        events_a, events_b = run_ab_simulation(duration_sec=30, bucket_sec=3)
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            csv_path = tmp_file.name
        
        try:
            # Export CSV
            export_csv_data(events_a, events_b, csv_path, bucket_sec=3)
            
            # Check file exists
            assert os.path.exists(csv_path)
            
            # Check CSV content
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            # Check header
            assert rows[0] == ['t_start', 'p95_single', 'p95_multi', 'recall_single', 'recall_multi', 'delta_p95']
            
            # Check row count matches buckets
            assert len(rows) - 1 == len(events_a)  # -1 for header
            
            # Check data rows have correct format
            for i, row in enumerate(rows[1:], 1):
                assert len(row) == 6  # 6 columns
                assert row[0] == str((i-1) * 3)  # t_start = (i-1) * bucket_sec
                assert float(row[1]) > 0  # p95_single > 0
                assert float(row[2]) > 0  # p95_multi > 0
                assert 0 <= float(row[3]) <= 1  # recall_single in [0,1]
                assert 0 <= float(row[4]) <= 1  # recall_multi in [0,1]
                assert float(row[5]) == float(row[1]) - float(row[2])  # delta_p95 = p95_single - p95_multi
        
        finally:
            # Clean up
            if os.path.exists(csv_path):
                os.unlink(csv_path)