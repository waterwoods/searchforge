#!/usr/bin/env python3
"""
Test suite for AutoTuner Demo Pack UI functionality.

Tests tab controller, data presence detection, inline JSON data sourcing,
and DOM interactions for reliable offline file:// viewing.
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.aggregate_observed import generate_demo_pack_index, generate_global_comparison_content
from scripts.run_demo_pack import DemoPackOrchestrator


class TestDemoPackUI(unittest.TestCase):
    """Test UI functionality for demo pack HTML generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_single_scenario_tab_generation(self):
        """Test that only Scenario A tab is generated when only Scenario A exists."""
        
        # Create scenario A directory and data
        scenario_a_dir = self.temp_path / "scenario_A"
        scenario_a_dir.mkdir()
        
        # Create one_pager.json for scenario A
        scenario_a_data = {
            "scenario": "A",
            "comparison": {
                "delta_p95_ms": 10.5,
                "p_value": 0.012,
                "delta_recall": 0.028,
                "safety_rate": 0.995,
                "apply_rate": 0.957
            }
        }
        
        with open(scenario_a_dir / "one_pager.json", "w") as f:
            json.dump(scenario_a_data, f)
        
        # Create metadata
        metadata = {
            "created_at": "2025-01-06T09:00:00",
            "git_sha": "abc123",
            "notes": "Test single scenario",
            "scenarios_run": ["A"],
            "summary": {
                "scenarios_passed": 1,
                "scenarios_total": 1,
                "pass_rate": 1.0
            }
        }
        
        with open(self.temp_path / "metadata.json", "w") as f:
            json.dump(metadata, f)
        
        # Generate HTML
        html = generate_demo_pack_index(str(self.temp_path))
        
        # Verify HTML content
        self.assertIn('Scenario A', html)
        self.assertIn('data-tab="scenario-a"', html)
        self.assertNotIn('data-tab="scenario-b"', html)
        self.assertNotIn('data-tab="scenario-c"', html)
        
        # Verify Global tab is NOT present (only one scenario)
        self.assertNotIn('Global Comparison', html)
        self.assertNotIn('data-tab="global"', html)
        
        # Verify inline JSON data is present
        self.assertIn('id="data-scenario-a"', html)
        self.assertIn('"scenario": "A"', html)
        
        # Verify tab content sections
        self.assertIn('id="tab-scenario-a"', html)
        self.assertIn('class="tab-content hidden"', html)
    
    def test_multiple_scenarios_with_global_tab(self):
        """Test that Global tab is generated when multiple scenarios exist."""
        
        # Create scenario A and B directories
        for scenario in ["A", "B"]:
            scenario_dir = self.temp_path / f"scenario_{scenario}"
            scenario_dir.mkdir()
            
            scenario_data = {
                "scenario": scenario,
                "comparison": {
                    "delta_p95_ms": 10.5 if scenario == "A" else 8.2,
                    "p_value": 0.012 if scenario == "A" else 0.023,
                    "delta_recall": 0.028 if scenario == "A" else 0.031,
                    "safety_rate": 0.995,
                    "apply_rate": 0.957
                }
            }
            
            with open(scenario_dir / "one_pager.json", "w") as f:
                json.dump(scenario_data, f)
        
        # Create metadata
        metadata = {
            "created_at": "2025-01-06T09:00:00",
            "git_sha": "abc123",
            "notes": "Test multiple scenarios",
            "scenarios_run": ["A", "B"],
            "summary": {
                "scenarios_passed": 2,
                "scenarios_total": 2,
                "pass_rate": 1.0
            }
        }
        
        with open(self.temp_path / "metadata.json", "w") as f:
            json.dump(metadata, f)
        
        # Generate HTML
        html = generate_demo_pack_index(str(self.temp_path))
        
        # Verify both scenario tabs are present
        self.assertIn('Scenario A', html)
        self.assertIn('Scenario B', html)
        self.assertIn('data-tab="scenario-a"', html)
        self.assertIn('data-tab="scenario-b"', html)
        
        # Verify Global tab is present (multiple scenarios)
        self.assertIn('Global Comparison', html)
        self.assertIn('data-tab="global"', html)
        
        # Verify inline JSON data for both scenarios
        self.assertIn('id="data-scenario-a"', html)
        self.assertIn('id="data-scenario-b"', html)
        
        # Verify tab content sections
        self.assertIn('id="tab-scenario-a"', html)
        self.assertIn('id="tab-scenario-b"', html)
        self.assertIn('id="tab-global"', html)
    
    def test_tab_controller_javascript(self):
        """Test that tab controller JavaScript is properly generated."""
        
        # Create minimal scenario
        scenario_a_dir = self.temp_path / "scenario_A"
        scenario_a_dir.mkdir()
        
        scenario_a_data = {
            "scenario": "A",
            "comparison": {"delta_p95_ms": 10.5, "p_value": 0.012}
        }
        
        with open(scenario_a_dir / "one_pager.json", "w") as f:
            json.dump(scenario_a_data, f)
        
        # Generate HTML
        html = generate_demo_pack_index(str(self.temp_path))
        
        # Verify JavaScript functions
        self.assertIn('function showTab(tabId)', html)
        self.assertIn('function getScenarioData(scenarioName)', html)
        self.assertIn('function renderGlobalComparison()', html)
        
        # Verify keyboard navigation
        self.assertIn('ArrowLeft', html)
        self.assertIn('ArrowRight', html)
        
        # Verify URL hash handling
        self.assertIn('window.location.hash', html)
        
        # Verify ARIA attributes
        self.assertIn('aria-selected', html)
        self.assertIn('aria-hidden', html)
        self.assertIn('role="tab"', html)
        self.assertIn('role="tabpanel"', html)
    
    def test_global_comparison_content_generation(self):
        """Test global comparison content generation."""
        
        scenario_data = {
            "A": {
                "scenario": "A",
                "comparison": {
                    "delta_p95_ms": 10.5,
                    "p_value": 0.012,
                    "delta_recall": 0.028,
                    "safety_rate": 0.995,
                    "apply_rate": 0.957
                }
            },
            "B": {
                "scenario": "B",
                "comparison": {
                    "delta_p95_ms": 8.2,
                    "p_value": 0.023,
                    "delta_recall": 0.031,
                    "safety_rate": 0.992,
                    "apply_rate": 0.956
                }
            }
        }
        
        metadata = {
            "summary": {
                "scenarios_passed": 2,
                "scenarios_total": 2,
                "pass_rate": 1.0,
                "duration_per_side": 900,
                "buckets_per_side": 90,
                "perm_trials": 5000
            }
        }
        
        content = generate_global_comparison_content(scenario_data, metadata)
        
        # Verify summary content
        self.assertIn('Global Comparison', content)
        self.assertIn('Scenario Pass Rate', content)
        self.assertIn('2/2', content)
        self.assertIn('100.0% Success Rate', content)
        
        # Verify enhanced parameters
        self.assertIn('Duration per side:</strong> 900s', content)
        self.assertIn('Buckets per side:</strong> 90', content)
        self.assertIn('Permutation trials:</strong> 5000', content)
    
    def test_no_data_scenario_handling(self):
        """Test handling of scenarios with no data."""
        
        # Create scenario directory but no JSON file
        scenario_a_dir = self.temp_path / "scenario_A"
        scenario_a_dir.mkdir()
        
        # Generate HTML
        html = generate_demo_pack_index(str(self.temp_path))
        
        # Verify scenario tab is still generated
        self.assertIn('Scenario A', html)
        self.assertIn('data-tab="scenario-a"', html)
        
        # Verify no inline JSON data (no JSON file)
        self.assertNotIn('id="data-scenario-a"', html)
        
        # Verify Global tab is not present (no data)
        self.assertNotIn('Global Comparison', html)
    
    def test_accessibility_features(self):
        """Test accessibility features in generated HTML."""
        
        # Create scenario
        scenario_a_dir = self.temp_path / "scenario_A"
        scenario_a_dir.mkdir()
        
        scenario_a_data = {
            "scenario": "A",
            "comparison": {"delta_p95_ms": 10.5, "p_value": 0.012}
        }
        
        with open(scenario_a_dir / "one_pager.json", "w") as f:
            json.dump(scenario_a_data, f)
        
        # Generate HTML
        html = generate_demo_pack_index(str(self.temp_path))
        
        # Verify accessibility attributes
        self.assertIn('role="tablist"', html)
        self.assertIn('aria-label="Demo Pack Scenarios"', html)
        self.assertIn('role="tab"', html)
        self.assertIn('role="tabpanel"', html)
        self.assertIn('tabindex="0"', html)
        
        # Verify focus management
        self.assertIn('.tab:focus', html)
        self.assertIn('border-color: #007bff', html)
        
        # Verify keyboard navigation
        self.assertIn('keydown', html)
        self.assertIn('preventDefault()', html)
    
    def test_css_styles_for_offline_viewing(self):
        """Test CSS styles are properly embedded for offline viewing."""
        
        # Create minimal scenario
        scenario_a_dir = self.temp_path / "scenario_A"
        scenario_a_dir.mkdir()
        
        scenario_a_data = {
            "scenario": "A",
            "comparison": {"delta_p95_ms": 10.5, "p_value": 0.012}
        }
        
        with open(scenario_a_dir / "one_pager.json", "w") as f:
            json.dump(scenario_a_data, f)
        
        # Generate HTML
        html = generate_demo_pack_index(str(self.temp_path))
        
        # Verify CSS is embedded (not linked)
        self.assertIn('<style>', html)
        self.assertNotIn('<link rel="stylesheet"', html)
        
        # Verify essential CSS classes
        self.assertIn('.tab-content.hidden', html)
        self.assertIn('display: none', html)
        self.assertIn('.tab.disabled', html)
        self.assertIn('pointer-events: none', html)
        
        # Verify color classes
        self.assertIn('.pass', html)
        self.assertIn('.fail', html)
        self.assertIn('.warning', html)
        
        # Verify responsive design
        self.assertIn('grid-template-columns: repeat(auto-fit', html)
        self.assertIn('flex-wrap: wrap', html)


class TestDemoPackUITabInteraction(unittest.TestCase):
    """Test tab interaction functionality using DOM simulation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_tab_switching_logic(self):
        """Test that tab switching logic works correctly."""
        
        # Create multiple scenarios
        for scenario in ["A", "B"]:
            scenario_dir = self.temp_path / f"scenario_{scenario}"
            scenario_dir.mkdir()
            
            scenario_data = {
                "scenario": scenario,
                "comparison": {
                    "delta_p95_ms": 10.5 if scenario == "A" else 8.2,
                    "p_value": 0.012 if scenario == "A" else 0.023,
                    "delta_recall": 0.028,
                    "safety_rate": 0.995,
                    "apply_rate": 0.957
                }
            }
            
            with open(scenario_dir / "one_pager.json", "w") as f:
                json.dump(scenario_data, f)
        
        # Generate HTML
        html = generate_demo_pack_index(str(self.temp_path))
        
        # Simulate DOM interaction by checking JavaScript logic
        # This tests the logic without actually running JavaScript
        
        # Verify showTab function exists and handles tab switching
        self.assertIn('showTab(tabId)', html)
        self.assertIn('classList.add(\'hidden\')', html)
        self.assertIn('classList.remove(\'hidden\')', html)
        self.assertIn('setAttribute(\'aria-selected\', \'true\')', html)
        self.assertIn('setAttribute(\'aria-hidden\', \'false\')', html)
        
        # Verify URL hash updating
        self.assertIn('window.location.hash = tabId', html)
        
        # Verify keyboard navigation logic
        self.assertIn('tabs[activeIndex - 1].click()', html)
        self.assertIn('tabs[activeIndex + 1].click()', html)
    
    def test_global_comparison_rendering(self):
        """Test global comparison rendering logic."""
        
        # Create scenarios for global comparison
        for scenario in ["A", "B", "C"]:
            scenario_dir = self.temp_path / f"scenario_{scenario}"
            scenario_dir.mkdir()
            
            scenario_data = {
                "scenario": scenario,
                "comparison": {
                    "delta_p95_ms": 10.5 + (hash(scenario) % 5),
                    "p_value": 0.012 + (hash(scenario) % 10) * 0.001,
                    "delta_recall": 0.028 + (hash(scenario) % 5) * 0.001,
                    "safety_rate": 0.995,
                    "apply_rate": 0.957
                }
            }
            
            with open(scenario_dir / "one_pager.json", "w") as f:
                json.dump(scenario_data, f)
        
        # Generate HTML
        html = generate_demo_pack_index(str(self.temp_path))
        
        # Verify global comparison rendering function
        self.assertIn('renderGlobalComparison()', html)
        self.assertIn('getScenarioData(name)', html)
        self.assertIn('无数据 - No global comparison data available', html)
        
        # Verify comparison data processing
        self.assertIn('comparisonData.map', html)
        self.assertIn('item.deltaP95', html)
        self.assertIn('item.pValue', html)
        self.assertIn('item.safetyRate', html)
        
        # Verify dynamic content generation
        self.assertIn('innerHTML = renderGlobalComparison()', html)


def run_fast_tests():
    """Run fast UI tests."""
    print("Running fast UI tests...")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add fast tests
    fast_tests = [
        TestDemoPackUI('test_single_scenario_tab_generation'),
        TestDemoPackUI('test_multiple_scenarios_with_global_tab'),
        TestDemoPackUI('test_tab_controller_javascript'),
        TestDemoPackUI('test_css_styles_for_offline_viewing'),
        TestDemoPackUITabInteraction('test_tab_switching_logic'),
    ]
    
    for test in fast_tests:
        suite.addTest(test)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    
    if '--fast' in sys.argv:
        success = run_fast_tests()
        sys.exit(0 if success else 1)
    else:
        # Run all tests
        unittest.main(verbosity=2)
