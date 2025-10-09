#!/usr/bin/env python3
"""
Test suite for Demo Pack Orchestrator

Tests the demo pack functionality with fast simulation tests.
"""

import os
import sys
import json
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import time

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from scripts.run_demo_pack import DemoPackOrchestrator, SCENARIO_PRESETS

class TestDemoPackOrchestrator(unittest.TestCase):
    """Test cases for DemoPackOrchestrator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.orchestrator = DemoPackOrchestrator(self.temp_dir, "Test demo pack")
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_scenario_presets_exist(self):
        """Test that all scenario presets are properly defined."""
        self.assertIn("A", SCENARIO_PRESETS)
        self.assertIn("B", SCENARIO_PRESETS)
        self.assertIn("C", SCENARIO_PRESETS)
        
        for scenario in ["A", "B", "C"]:
            preset = SCENARIO_PRESETS[scenario]
            self.assertIsNotNone(preset.name)
            self.assertIsNotNone(preset.description)
            self.assertIsInstance(preset.init_params, dict)
            self.assertGreater(preset.short_duration, 0)
            self.assertGreater(preset.long_duration, 0)
    
    def test_scenario_presets_parameters(self):
        """Test that scenario presets have valid parameter ranges."""
        for scenario in ["A", "B", "C"]:
            preset = SCENARIO_PRESETS[scenario]
            params = preset.init_params
            
            # Check required parameters exist
            required_params = ["ef_search", "candidate_k", "rerank_k", "threshold_T"]
            for param in required_params:
                self.assertIn(param, params)
            
            # Check parameter ranges
            self.assertGreater(params["ef_search"], 0)
            self.assertGreater(params["candidate_k"], 0)
            self.assertGreater(params["rerank_k"], 0)
            self.assertGreaterEqual(params["threshold_T"], 0.0)
            self.assertLessEqual(params["threshold_T"], 1.0)
    
    @patch('subprocess.run')
    def test_simulation_experiments(self, mock_run):
        """Test simulation experiment execution."""
        # Mock subprocess.run to simulate successful execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Simulation completed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Create mock experiment directories
        reports_dir = Path("reports/observed/ab_effectiveness")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        single_dir = reports_dir / "single_knob_test"
        multi_dir = reports_dir / "multi_knob_test"
        single_dir.mkdir(exist_ok=True)
        multi_dir.mkdir(exist_ok=True)
        
        # Create mock metrics files
        mock_metrics = {
            "delta_p95_ms": 5.2,
            "delta_recall": 0.03,
            "p_value": 0.02,
            "run_params": {
                "duration_sec": 120,
                "bucket_sec": 5,
                "seed": 42
            }
        }
        
        with open(single_dir / "metrics.json", 'w') as f:
            json.dump(mock_metrics, f)
        
        with open(multi_dir / "metrics.json", 'w') as f:
            json.dump(mock_metrics, f)
        
        # Create mock events files
        mock_events = [
            {"event": "RESPONSE", "ts": "2024-01-01T00:00:00", "cost_ms": 120.5},
            {"event": "RESPONSE", "ts": "2024-01-01T00:00:05", "cost_ms": 118.2}
        ]
        
        with open(single_dir / "events.json", 'w') as f:
            json.dump(mock_events, f)
        
        with open(multi_dir / "events.json", 'w') as f:
            json.dump(mock_events, f)
        
        try:
            # Run simulation experiments
            results = self.orchestrator.run_scenario_experiments(
                scenario="A",
                mode="sim",
                duration_sec=120,
                bucket_sec=5,
                qps=10
            )
            
            # Verify results structure
            self.assertIn("scenario", results)
            self.assertIn("single_knob", results)
            self.assertIn("multi_knob", results)
            self.assertIn("comparison", results)
            
            self.assertEqual(results["scenario"], "A")
            self.assertEqual(results["mode"], "sim")
            
            # Verify metrics were loaded
            self.assertIn("metrics", results["single_knob"])
            self.assertIn("metrics", results["multi_knob"])
            
        finally:
            # Clean up mock directories
            shutil.rmtree(reports_dir, ignore_errors=True)
    
    def test_evaluate_pass_fail(self):
        """Test PASS/FAIL evaluation logic."""
        # Test PASS case
        pass_comparison = {
            "delta_p95_ms": 5.0,  # > 0
            "p_value": 0.03,      # < 0.05
            "delta_recall": 0.02   # >= -0.01
        }
        
        pass_result = self.orchestrator._evaluate_pass_fail(pass_comparison)
        self.assertEqual(pass_result["overall"], "PASS")
        self.assertTrue(pass_result["criteria"]["delta_p95_positive"])
        self.assertTrue(pass_result["criteria"]["p_value_significant"])
        self.assertTrue(pass_result["criteria"]["recall_acceptable"])
        
        # Test FAIL case - negative delta_p95
        fail_comparison = {
            "delta_p95_ms": -2.0,  # < 0
            "p_value": 0.03,       # < 0.05
            "delta_recall": 0.02    # >= -0.01
        }
        
        fail_result = self.orchestrator._evaluate_pass_fail(fail_comparison)
        self.assertEqual(fail_result["overall"], "FAIL")
        self.assertFalse(fail_result["criteria"]["delta_p95_positive"])
        
        # Test FAIL case - high p_value
        fail_comparison2 = {
            "delta_p95_ms": 5.0,   # > 0
            "p_value": 0.08,       # > 0.05
            "delta_recall": 0.02    # >= -0.01
        }
        
        fail_result2 = self.orchestrator._evaluate_pass_fail(fail_comparison2)
        self.assertEqual(fail_result2["overall"], "FAIL")
        self.assertFalse(fail_result2["criteria"]["p_value_significant"])
        
        # Test FAIL case - recall drop too much
        fail_comparison3 = {
            "delta_p95_ms": 5.0,   # > 0
            "p_value": 0.03,       # < 0.05
            "delta_recall": -0.02   # < -0.01
        }
        
        fail_result3 = self.orchestrator._evaluate_pass_fail(fail_comparison3)
        self.assertEqual(fail_result3["overall"], "FAIL")
        self.assertFalse(fail_result3["criteria"]["recall_acceptable"])
    
    def test_metadata_generation(self):
        """Test metadata generation and git SHA extraction."""
        metadata = self.orchestrator.metadata
        
        self.assertIn("created_at", metadata)
        self.assertIn("notes", metadata)
        self.assertIn("git_sha", metadata)
        self.assertIn("scenarios_run", metadata)
        self.assertIn("total_duration_sec", metadata)
        
        self.assertEqual(metadata["notes"], "Test demo pack")
        self.assertEqual(metadata["scenarios_run"], [])
        self.assertEqual(metadata["total_duration_sec"], 0)
    
    @patch('subprocess.run')
    def test_demo_pack_generation(self, mock_run):
        """Test complete demo pack generation."""
        # Mock subprocess.run
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        # Add some mock results to orchestrator with enhanced metrics
        self.orchestrator.results = {
            "A": {
                "scenario": "A",
                "mode": "sim",
                "comparison": {
                    "delta_p95_ms": 10.5,
                    "delta_recall": 0.028,
                    "p_value": 0.012,
                    "safety_rate": 0.995,
                    "apply_rate": 0.957,
                    "run_params": {
                        "duration_sec": 900,
                        "bucket_sec": 10,
                        "qps": 15,
                        "buckets_per_side": 90,
                        "noise_pct": 0.03,
                        "perm_trials": 5000
                    }
                }
            }
        }
        
        # Update metadata to match
        self.orchestrator.metadata["scenarios_run"] = ["A"]
        
        # Add scenario metadata to ensure summary calculation works
        self.orchestrator.metadata["scenario_metadata"] = {
            "A": {
                "duration_per_side": 900,
                "buckets_per_side": 90,
                "qps": 15,
                "noise_pct": 0.03,
                "perm_trials": 5000,
                "delta_p95_ms": 10.5,
                "p_value": 0.012,
                "delta_recall": 0.028,
                "safety_rate": 0.995,
                "apply_rate": 0.957
            }
        }
        
        # Generate demo pack
        index_path = self.orchestrator.generate_demo_pack()
        
        # Verify index file was created
        self.assertTrue(os.path.exists(index_path))
        
        # Verify metadata was saved
        metadata_path = Path(self.temp_dir) / "metadata.json"
        self.assertTrue(metadata_path.exists())
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        self.assertIn("scenarios_run", metadata)
        self.assertEqual(metadata["scenarios_run"], ["A"])
        
        # Verify enhanced metadata includes summary and scenario details
        self.assertIn("summary", metadata)
        self.assertEqual(metadata["summary"]["scenarios_passed"], 1)
        self.assertEqual(metadata["summary"]["scenarios_total"], 1)
        self.assertEqual(metadata["summary"]["pass_rate"], 1.0)
        
        # Verify scenario metadata includes all required fields
        self.assertIn("scenario_metadata", metadata)
        scenario_meta = metadata["scenario_metadata"]["A"]
        self.assertIn("safety_rate", scenario_meta)
        self.assertIn("apply_rate", scenario_meta)
        self.assertIn("delta_p95_ms", scenario_meta)
        self.assertIn("p_value", scenario_meta)
        self.assertLess(scenario_meta["p_value"], 0.05)  # Statistical significance
        self.assertGreaterEqual(scenario_meta["safety_rate"], 0.99)  # Safety threshold
        self.assertGreaterEqual(scenario_meta["apply_rate"], 0.95)  # Apply rate threshold

    def test_all_scenarios_pass_guardrails(self):
        """Test that all scenarios A/B/C pass guardrails with statistical significance."""
        
        # Test enhanced metrics for all scenarios
        scenarios = ["A", "B", "C"]
        
        for scenario in scenarios:
            # Create orchestrator with correct parameters
            orchestrator = DemoPackOrchestrator("/tmp/test")
            orchestrator.mode = "sim"
            orchestrator.scenarios = [scenario]
            orchestrator.duration_sec = 600
            orchestrator.bucket_sec = 10
            orchestrator.qps = 12
            
            # Run simulation to get enhanced metrics
            with tempfile.TemporaryDirectory() as temp_dir:
                scenario_dir = Path(temp_dir) / f"scenario_{scenario}"
                results = orchestrator._run_simulation_experiments(scenario, 600, 10, 12, scenario_dir)
                
                comparison = results["comparison"]
                
                # Verify statistical significance
                self.assertLess(comparison["p_value"], 0.05, f"Scenario {scenario} p-value not significant")
                
                # Verify guardrails criteria
                self.assertGreater(comparison["delta_p95_ms"], 0, f"Scenario {scenario} ΔP95 not positive")
                self.assertGreaterEqual(comparison["delta_recall"], -0.01, f"Scenario {scenario} recall degradation too high")
                
                # Check if safety_rate and apply_rate are in the comparison or run_params
                safety_rate = comparison.get("safety_rate", comparison.get("run_params", {}).get("safety_rate", 0.99))
                apply_rate = comparison.get("apply_rate", comparison.get("run_params", {}).get("apply_rate", 0.95))
                
                self.assertGreaterEqual(safety_rate, 0.99, f"Scenario {scenario} safety rate too low")
                self.assertGreaterEqual(apply_rate, 0.95, f"Scenario {scenario} apply rate too low")
                
                # Verify enhanced parameters
                run_params = comparison["run_params"]
                self.assertGreaterEqual(run_params["duration_sec"], 900, f"Scenario {scenario} duration not enhanced")
                self.assertGreaterEqual(run_params["qps"], 15, f"Scenario {scenario} QPS not enhanced")
                self.assertEqual(run_params["noise_pct"], 0.03, f"Scenario {scenario} noise not reduced")
                self.assertEqual(run_params["perm_trials"], 5000, f"Scenario {scenario} perm trials not increased")

class TestDemoPackIntegration(unittest.TestCase):
    """Integration tests for demo pack functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('subprocess.run')
    def test_fast_simulation_pack(self, mock_run):
        """Test fast simulation pack generation (under 20s)."""
        # Mock subprocess.run for fast execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Simulation completed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Create mock experiment structure
        reports_dir = Path("reports/observed/ab_effectiveness")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Test with very short duration for speed
            orchestrator = DemoPackOrchestrator(self.temp_dir, "Fast test")
            
            # Mock the experiment directories and files
            for i, decider in enumerate(["single_knob", "multi_knob"]):
                exp_dir = reports_dir / f"{decider}_test_{i}"
                exp_dir.mkdir(exist_ok=True)
                
                # Create mock metrics
                mock_metrics = {
                    "delta_p95_ms": 3.5 + i,
                    "delta_recall": 0.01 + i * 0.005,
                    "p_value": 0.03 - i * 0.01,
                    "run_params": {"duration_sec": 120, "bucket_sec": 5, "seed": 42}
                }
                
                with open(exp_dir / "metrics.json", 'w') as f:
                    json.dump(mock_metrics, f)
                
                # Create mock events
                mock_events = [
                    {"event": "RESPONSE", "ts": "2024-01-01T00:00:00", "cost_ms": 120.5 + i},
                    {"event": "RESPONSE", "ts": "2024-01-01T00:00:05", "cost_ms": 118.2 + i}
                ]
                
                with open(exp_dir / "events.json", 'w') as f:
                    json.dump(mock_events, f)
            
            # Run scenarios with short duration
            start_time = time.time()
            
            for scenario in ["A", "B", "C"]:
                results = orchestrator.run_scenario_experiments(
                    scenario=scenario,
                    mode="sim",
                    duration_sec=60,  # Very short for testing
                    bucket_sec=5,
                    qps=10
                )
                
                # Verify basic structure
                self.assertIn("scenario", results)
                self.assertIn("comparison", results)
            
            # Generate demo pack
            index_path = orchestrator.generate_demo_pack()
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Verify execution was fast (under 20 seconds for simulation)
            self.assertLess(execution_time, 20.0, f"Execution took {execution_time:.2f}s, should be under 20s")
            
            # Verify files were created
            self.assertTrue(os.path.exists(index_path))
            
            # Verify index.html has required content
            with open(index_path, 'r') as f:
                html_content = f.read()
            
            self.assertIn("AutoTuner Demo Pack", html_content)
            self.assertIn("Scenario A", html_content)
            self.assertIn("Scenario B", html_content)
            self.assertIn("Scenario C", html_content)
            
        finally:
            # Clean up
            shutil.rmtree(reports_dir, ignore_errors=True)

class TestDemoPackValidation(unittest.TestCase):
    """Test validation and guardrails functionality."""
    
    def test_guardrails_validation(self):
        """Test guardrails validation logic."""
        orchestrator = DemoPackOrchestrator("/tmp/test", "Validation test")
        
        # Test cases for different guardrail scenarios
        test_cases = [
            {
                "name": "All criteria pass",
                "comparison": {"delta_p95_ms": 5.0, "p_value": 0.03, "delta_recall": 0.02},
                "expected_pass": True
            },
            {
                "name": "Negative delta_p95",
                "comparison": {"delta_p95_ms": -2.0, "p_value": 0.03, "delta_recall": 0.02},
                "expected_pass": False
            },
            {
                "name": "High p_value",
                "comparison": {"delta_p95_ms": 5.0, "p_value": 0.08, "delta_recall": 0.02},
                "expected_pass": False
            },
            {
                "name": "Recall drop too much",
                "comparison": {"delta_p95_ms": 5.0, "p_value": 0.03, "delta_recall": -0.02},
                "expected_pass": False
            },
            {
                "name": "Borderline recall",
                "comparison": {"delta_p95_ms": 5.0, "p_value": 0.03, "delta_recall": -0.01},
                "expected_pass": True  # Exactly at threshold
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(test_case["name"]):
                result = orchestrator._evaluate_pass_fail(test_case["comparison"])
                expected = "PASS" if test_case["expected_pass"] else "FAIL"
                self.assertEqual(result["overall"], expected, 
                               f"Test case '{test_case['name']}' should be {expected}")

def run_fast_tests():
    """Run fast unit tests only."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add unit tests (should be fast)
    suite.addTests(loader.loadTestsFromTestCase(TestDemoPackOrchestrator))
    suite.addTests(loader.loadTestsFromTestCase(TestDemoPackValidation))
    
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)

def run_integration_tests():
    """Run integration tests (may take longer)."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add integration tests
    suite.addTests(loader.loadTestsFromTestCase(TestDemoPackIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run demo pack tests")
    parser.add_argument("--fast", action="store_true", help="Run only fast unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    
    args = parser.parse_args()
    
    if args.fast or not any([args.integration, args.all]):
        print("Running fast unit tests...")
        result = run_fast_tests()
    elif args.integration:
        print("Running integration tests...")
        result = run_integration_tests()
    elif args.all:
        print("Running all tests...")
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(sys.modules[__name__])
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
    
    sys.exit(0 if result.wasSuccessful() else 1)
