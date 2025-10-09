#!/usr/bin/env python3
"""
Tests for plot_time_series.py functionality.

Tests the new CLI interface and batch rendering capabilities without requiring
actual image generation or complex file dependencies.
"""

import os
import sys
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from scripts.plot_time_series import (
    generate_plots_from_pack_root,
    embed_charts_in_html,
    create_scenario_charts_html,
    insert_charts_into_html,
    apply_ewma_smoothing
)


class TestPlotTimeSeries:
    """Test cases for plot_time_series.py functionality."""
    
    def setup_method(self):
        """Set up test environment with temporary directories and mock data."""
        self.test_dir = tempfile.mkdtemp()
        self.pack_root = Path(self.test_dir) / "test_pack"
        self.pack_root.mkdir()
        
        # Create mock CSV data for scenario A
        self.create_mock_csv_data()
        
        # Create mock HTML file
        self.create_mock_html()
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    def create_mock_csv_data(self):
        """Create synthetic CSV data for testing."""
        # Create scenario A directory and CSV
        scenario_a_dir = self.pack_root / "scenario_A"
        scenario_a_dir.mkdir()
        
        # Generate 8 time buckets of synthetic data
        data = {
            't_start': [0, 10, 20, 30, 40, 50, 60, 70],
            'p95_single': [120.5, 119.8, 118.9, 117.5, 116.8, 115.2, 114.1, 113.5],
            'p95_multi': [118.2, 117.1, 116.5, 115.8, 114.9, 113.8, 112.5, 111.9],
            'recall_single': [0.75, 0.76, 0.77, 0.78, 0.79, 0.80, 0.81, 0.82],
            'recall_multi': [0.78, 0.79, 0.80, 0.81, 0.82, 0.83, 0.84, 0.85],
            'delta_p95': [2.3, 2.7, 2.4, 1.7, 1.9, 1.4, 1.6, 1.6],
            'delta_recall': [0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03]
        }
        
        df = pd.DataFrame(data)
        csv_path = scenario_a_dir / "one_pager.csv"
        df.to_csv(csv_path, index=False)
    
    def create_mock_html(self):
        """Create mock HTML file for testing embedding."""
        html_content = '''<!DOCTYPE html>
<html>
<head><title>Test Demo Pack</title></head>
<body>
    <section id="tab-scenario-a" class="tab-content">
        <div class="metric-grid">
            <div class="metric-card">
                <h3>Hero KPIs</h3>
                <div class="metric-value pass">PASS</div>
            </div>
        </div>
    </section>
</body>
</html>'''
        
        html_path = self.pack_root / "index.html"
        with open(html_path, 'w') as f:
            f.write(html_content)
    
    @patch('scripts.plot_time_series.create_scenario_plots')
    def test_generate_plots_from_pack_root_success(self, mock_create_plots):
        """Test successful plot generation from pack root."""
        # Mock the plot creation function
        mock_create_plots.return_value = [
            str(self.pack_root / "plots" / "scenario_a_p95.png"),
            str(self.pack_root / "plots" / "scenario_a_recall.png")
        ]
        
        # Test with auto-detected scenarios
        result = generate_plots_from_pack_root(str(self.pack_root))
        
        # Verify results
        assert len(result) == 2
        assert "scenario_a_p95.png" in result[0]
        assert "scenario_a_recall.png" in result[1]
        
        # Verify plots directory was created
        plots_dir = self.pack_root / "plots"
        assert plots_dir.exists()
        
        # Verify create_scenario_plots was called with correct data
        mock_create_plots.assert_called_once()
        call_args = mock_create_plots.call_args
        assert call_args[0][0] == "A"  # scenario name
        
        # Verify DataFrames were passed (new format)
        single_df = call_args[0][1]
        multi_df = call_args[0][2]
        assert 'time_bucket' in single_df.columns
        assert 'p95_ms' in single_df.columns
        assert 'recall_at10' in single_df.columns
        assert 'mode' in single_df.columns
        assert single_df['mode'].iloc[0] == 'single'
        assert multi_df['mode'].iloc[0] == 'multi'
    
    def test_generate_plots_from_pack_root_missing_scenario(self):
        """Test handling of missing scenario data."""
        # Test with non-existent scenario
        result = generate_plots_from_pack_root(str(self.pack_root), scenarios=["B"])
        
        # Should return empty list
        assert result == []
    
    def test_generate_plots_from_pack_root_invalid_pack_root(self):
        """Test handling of invalid pack root directory."""
        result = generate_plots_from_pack_root("/nonexistent/path")
        
        # Should return empty list
        assert result == []
    
    def test_apply_ewma_smoothing(self):
        """Test EWMA smoothing function."""
        # Create test series
        series = pd.Series([1, 2, 3, 4, 5, 6, 7, 8])
        
        # Apply smoothing
        smoothed = apply_ewma_smoothing(series, alpha=0.3)
        
        # Verify output
        assert len(smoothed) == len(series)
        assert smoothed.iloc[0] == series.iloc[0]  # First value unchanged
        assert smoothed.iloc[-1] != series.iloc[-1]  # Last value should be different
    
    def test_embed_charts_in_html_success(self):
        """Test successful chart embedding in HTML."""
        # Create mock plots directory with fake PNG files
        plots_dir = self.pack_root / "plots"
        plots_dir.mkdir()
        
        # Create fake PNG files
        (plots_dir / "scenario_a_p95.png").touch()
        (plots_dir / "scenario_a_recall.png").touch()
        
        # Test embedding
        result = embed_charts_in_html(str(self.pack_root / "index.html"), str(self.pack_root))
        
        # Verify success
        assert result is True
        
        # Verify HTML was modified
        html_content = (self.pack_root / "index.html").read_text()
        assert "scenario-charts" in html_content
        assert "P95 Latency (ms) vs Time" in html_content
        assert "Recall@10 vs Time" in html_content
    
    def test_embed_charts_in_html_missing_plots(self):
        """Test handling when no plots exist."""
        # Test with no plots directory
        result = embed_charts_in_html(str(self.pack_root / "index.html"), str(self.pack_root))
        
        # Should return False
        assert result is False
    
    def test_embed_charts_in_html_already_embedded(self):
        """Test handling when charts are already embedded."""
        # Create plots directory and fake files
        plots_dir = self.pack_root / "plots"
        plots_dir.mkdir()
        (plots_dir / "scenario_a_p95.png").touch()
        
        # First embedding
        result1 = embed_charts_in_html(str(self.pack_root / "index.html"), str(self.pack_root))
        assert result1 is True
        
        # Second embedding should skip
        result2 = embed_charts_in_html(str(self.pack_root / "index.html"), str(self.pack_root))
        assert result2 is True  # Should return True but skip actual embedding
    
    def test_create_scenario_charts_html(self):
        """Test HTML generation for scenario charts."""
        plots_dir = self.pack_root / "plots"
        plots_dir.mkdir()
        
        # Create fake PNG files
        (plots_dir / "scenario_a_p95.png").touch()
        (plots_dir / "scenario_a_recall.png").touch()
        
        # Generate HTML
        charts_html = create_scenario_charts_html({"A"}, plots_dir, self.pack_root)
        
        # Verify HTML structure
        assert "A" in charts_html
        assert "P95 Latency (ms) vs Time" in charts_html["A"]
        assert "Recall@10 vs Time" in charts_html["A"]
        assert "scenario-charts" in charts_html["A"]
    
    def test_create_scenario_charts_html_no_data(self):
        """Test HTML generation when no charts exist."""
        plots_dir = self.pack_root / "plots"
        plots_dir.mkdir()
        
        # Generate HTML without any PNG files
        charts_html = create_scenario_charts_html({"A"}, plots_dir, self.pack_root)
        
        # Verify "No data available" message
        assert "No data available" in charts_html["A"]
    
    def test_insert_charts_into_html(self):
        """Test HTML insertion logic."""
        # Create mock HTML content
        html_content = '''<section id="tab-scenario-a" class="tab-content">
            <div class="metric-grid">
                <div class="metric-card">Hero KPIs</div>
            </div>
        </section>'''
        
        # Create charts HTML
        charts_html = {
            "A": '<div class="scenario-charts">Test Charts</div>'
        }
        
        # Insert charts
        result = insert_charts_into_html(html_content, charts_html)
        
        # Verify charts were inserted
        assert "scenario-charts" in result
        assert "Test Charts" in result
    
    @patch('scripts.plot_time_series.plt.savefig')
    @patch('scripts.plot_time_series.plt.figure')
    def test_create_scenario_plots_mock(self, mock_figure, mock_savefig):
        """Test plot creation with mocked matplotlib."""
        # Import the function we need to test
        from scripts.plot_time_series import create_scenario_plots
        
        # Create test DataFrames (new format)
        single_df = pd.DataFrame({
            'time_bucket': [0, 10, 20, 30, 40],
            'p95_ms': [120, 119, 118, 117, 116],
            'recall_at10': [0.75, 0.76, 0.77, 0.78, 0.79],
            'mode': 'single'
        })
        
        multi_df = pd.DataFrame({
            'time_bucket': [0, 10, 20, 30, 40],
            'p95_ms': [118, 117, 116, 115, 114],
            'recall_at10': [0.78, 0.79, 0.80, 0.81, 0.82],
            'mode': 'multi'
        })
        
        # Test plot creation
        plots_dir = self.pack_root / "plots"
        plots_dir.mkdir()
        
        result = create_scenario_plots("A", single_df, multi_df, plots_dir)
        
        # Verify results
        assert len(result) == 2
        assert "scenario_a_p95.png" in result[0]
        assert "scenario_a_recall.png" in result[1]
        
        # Verify matplotlib functions were called
        assert mock_figure.called
        assert mock_savefig.call_count == 2


def test_cli_interface():
    """Test the new CLI interface with mock arguments."""
    from scripts.plot_time_series import main
    
    # Test with mock arguments
    test_args = [
        '--pack-root', '/tmp/test_pack',
        '--scenarios', 'A,B,C',
        '--alpha', '0.5'
    ]
    
    with patch('sys.argv', ['plot_time_series.py'] + test_args):
        with patch('scripts.plot_time_series.generate_plots_from_pack_root') as mock_generate:
            with patch('scripts.plot_time_series.embed_charts_in_html') as mock_embed:
                mock_generate.return_value = ['plot1.png', 'plot2.png']
                mock_embed.return_value = True
                
                # This should not raise an exception
                try:
                    main()
                except SystemExit:
                    pass  # Expected when argparse exits
    
    # Verify the functions were called with correct arguments
    mock_generate.assert_called_once_with('/tmp/test_pack', ['A', 'B', 'C'], 0.5)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
