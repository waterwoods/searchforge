"""
Report Generator for Canary Deployments

This module generates HTML reports with charts and KPI tables for A/B testing results.
"""

import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

from .ab_evaluator import ABEvaluator, get_ab_evaluator

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates HTML reports for canary deployment results.
    
    Features:
    - Interactive charts with Chart.js
    - KPI tables with comparison metrics
    - Responsive design
    - Export functionality
    """
    
    def __init__(self, ab_evaluator: Optional[ABEvaluator] = None):
        """
        Initialize the report generator.
        
        Args:
            ab_evaluator: A/B evaluator instance
        """
        self.ab_evaluator = ab_evaluator or get_ab_evaluator()
    
    def generate_html_report(self, output_file: str, window_minutes: int = 10) -> None:
        """
        Generate a comprehensive HTML report.
        
        Args:
            output_file: Output HTML file path
            window_minutes: Time window for analysis
        """
        # Get A/B comparison data
        report_data = self.ab_evaluator.generate_kpi_report(window_minutes)
        bucket_distribution = self.ab_evaluator.get_bucket_distribution()
        
        # Generate HTML content
        html_content = self._create_html_template(report_data, bucket_distribution, window_minutes)
        
        # Write to file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"Generated HTML report: {output_file}")
        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")
            raise
    
    def _create_html_template(self, report_data: Dict[str, Any], 
                            bucket_distribution: Dict[str, Any], 
                            window_minutes: int = 10) -> str:
        """Create HTML template with embedded data."""
        
        # Extract key metrics for charts
        config_a_p95 = report_data['performance_comparison']['config_a'].get('avg_p95_ms', 0)
        config_b_p95 = report_data['performance_comparison']['config_b'].get('avg_p95_ms', 0)
        config_a_recall = report_data['performance_comparison']['config_a'].get('avg_recall_at_10', 0)
        config_b_recall = report_data['performance_comparison']['config_b'].get('avg_recall_at_10', 0)
        
        # Extract SLO violations with safe defaults
        config_a_slo_violations = report_data['performance_comparison']['config_a'].get('total_slo_violations', 0)
        config_b_slo_violations = report_data['performance_comparison']['config_b'].get('total_slo_violations', 0)
        
        # Generate sample time series data (in real implementation, this would come from actual metrics)
        time_series_data = self._generate_sample_time_series()
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Canary Deployment A/B Test Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }}
        .header h1 {{
            color: #2c3e50;
            margin: 0;
            font-size: 2.5em;
        }}
        .header .timestamp {{
            color: #7f8c8d;
            margin-top: 10px;
            font-size: 1.1em;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            font-size: 1.2em;
        }}
        .summary-card .value {{
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .charts-section {{
            margin: 30px 0;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .chart-title {{
            font-size: 1.5em;
            margin-bottom: 20px;
            color: #2c3e50;
            text-align: center;
        }}
        .kpi-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .kpi-table th {{
            background: #34495e;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        .kpi-table td {{
            padding: 15px;
            border-bottom: 1px solid #ecf0f1;
        }}
        .kpi-table tr:hover {{
            background-color: #f8f9fa;
        }}
        .improvement {{
            color: #27ae60;
            font-weight: bold;
        }}
        .degradation {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .neutral {{
            color: #f39c12;
            font-weight: bold;
        }}
        .recommendation {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 5px solid #3498db;
        }}
        .recommendation h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        .status-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .status-valid {{
            background: #d5f4e6;
            color: #27ae60;
        }}
        .status-invalid {{
            background: #fadbd8;
            color: #e74c3c;
        }}
        .status-significant {{
            background: #d6eaf8;
            color: #2980b9;
        }}
        .status-insignificant {{
            background: #f8f9fa;
            color: #6c757d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Canary Deployment A/B Test Report</h1>
            <div class="timestamp">Generated: {report_data['timestamp']}</div>
            <div class="timestamp">Analysis Window: {window_minutes} minutes</div>
        </div>

        <div class="summary-grid">
            <div class="summary-card">
                <h3>Total Buckets</h3>
                <div class="value">{report_data['summary']['total_buckets']}</div>
            </div>
            <div class="summary-card">
                <h3>Valid Buckets</h3>
                <div class="value">{report_data['summary']['valid_buckets']}</div>
            </div>
            <div class="summary-card">
                <h3>Validity Rate</h3>
                <div class="value">{report_data['summary']['valid_percentage']:.1f}%</div>
            </div>
            <div class="summary-card">
                <h3>Bucket A (90%)</h3>
                <div class="value">{bucket_distribution['bucket_a_count']}</div>
            </div>
            <div class="summary-card">
                <h3>Bucket B (10%)</h3>
                <div class="value">{bucket_distribution['bucket_b_count']}</div>
            </div>
        </div>

        <div class="charts-section">
            <div class="chart-container">
                <div class="chart-title">📊 Performance Comparison</div>
                <canvas id="performanceChart" width="400" height="200"></canvas>
            </div>
            
            <div class="chart-container">
                <div class="chart-title">📈 Time Series - P95 Latency</div>
                <canvas id="latencyChart" width="400" height="200"></canvas>
            </div>
            
            <div class="chart-container">
                <div class="chart-title">📈 Time Series - Recall@10</div>
                <canvas id="recallChart" width="400" height="200"></canvas>
            </div>
        </div>

        <div class="chart-container">
            <div class="chart-title">📋 Key Performance Indicators</div>
            <table class="kpi-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Config A (Last Good)</th>
                        <th>Config B (Candidate)</th>
                        <th>Improvement</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>P95 Latency (ms)</strong></td>
                        <td>{config_a_p95:.2f}</td>
                        <td>{config_b_p95:.2f}</td>
                        <td class="{'improvement' if report_data['improvements']['p95_latency_ms']['absolute'] < 0 else 'degradation'}">
                            {report_data['improvements']['p95_latency_ms']['absolute']:.2f} ms
                        </td>
                        <td>
                            <span class="status-badge {'improvement' if report_data['improvements']['p95_latency_ms']['absolute'] < 0 else 'degradation'}">
                                {report_data['improvements']['p95_latency_ms']['direction']}
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <td><strong>Recall@10</strong></td>
                        <td>{config_a_recall:.3f}</td>
                        <td>{config_b_recall:.3f}</td>
                        <td class="{'improvement' if report_data['improvements']['recall_at_10']['absolute'] > 0 else 'degradation'}">
                            {report_data['improvements']['recall_at_10']['absolute']:.3f}
                        </td>
                        <td>
                            <span class="status-badge {'improvement' if report_data['improvements']['recall_at_10']['absolute'] > 0 else 'degradation'}">
                                {report_data['improvements']['recall_at_10']['direction']}
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <td><strong>SLO Violations</strong></td>
                        <td>{config_a_slo_violations}</td>
                        <td>{config_b_slo_violations}</td>
                        <td class="{'improvement' if report_data['improvements']['slo_violations']['absolute'] < 0 else 'degradation'}">
                            {report_data['improvements']['slo_violations']['absolute']}
                        </td>
                        <td>
                            <span class="status-badge {'improvement' if report_data['improvements']['slo_violations']['absolute'] < 0 else 'degradation'}">
                                {report_data['improvements']['slo_violations']['direction']}
                            </span>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="recommendation">
            <h3>🎯 Recommendation</h3>
            <p>{report_data['recommendation']}</p>
            <div style="margin-top: 15px;">
                <span class="status-badge {'status-valid' if report_data['summary']['is_valid'] else 'status-invalid'}">
                    Data Validity: {'Valid' if report_data['summary']['is_valid'] else 'Invalid'}
                </span>
                <span class="status-badge {'status-significant' if report_data['statistical_significance']['is_significant'] else 'status-insignificant'}">
                    Significance: {report_data['statistical_significance']['confidence_level']:.0f}% Confidence
                </span>
            </div>
        </div>
    </div>

    <script>
        // Performance Comparison Chart
        const performanceCtx = document.getElementById('performanceChart').getContext('2d');
        new Chart(performanceCtx, {{
            type: 'bar',
            data: {{
                labels: ['P95 Latency (ms)', 'Recall@10', 'SLO Violations'],
                datasets: [{{
                    label: 'Config A (Last Good)',
                    data: [{config_a_p95}, {config_a_recall}, {config_a_slo_violations}],
                    backgroundColor: 'rgba(52, 152, 219, 0.8)',
                    borderColor: 'rgba(52, 152, 219, 1)',
                    borderWidth: 1
                }}, {{
                    label: 'Config B (Candidate)',
                    data: [{config_b_p95}, {config_b_recall}, {config_b_slo_violations}],
                    backgroundColor: 'rgba(231, 76, 60, 0.8)',
                    borderColor: 'rgba(231, 76, 60, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});

        // Time Series Charts
        const timeLabels = {json.dumps(time_series_data['timestamps'])};
        
        // Latency Chart
        const latencyCtx = document.getElementById('latencyChart').getContext('2d');
        new Chart(latencyCtx, {{
            type: 'line',
            data: {{
                labels: timeLabels,
                datasets: [{{
                    label: 'Config A (Last Good)',
                    data: {json.dumps(time_series_data['config_a_p95'])},
                    borderColor: 'rgba(52, 152, 219, 1)',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4
                }}, {{
                    label: 'Config B (Candidate)',
                    data: {json.dumps(time_series_data['config_b_p95'])},
                    borderColor: 'rgba(231, 76, 60, 1)',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Latency (ms)'
                        }}
                    }}
                }}
            }}
        }});

        // Recall Chart
        const recallCtx = document.getElementById('recallChart').getContext('2d');
        new Chart(recallCtx, {{
            type: 'line',
            data: {{
                labels: timeLabels,
                datasets: [{{
                    label: 'Config A (Last Good)',
                    data: {json.dumps(time_series_data['config_a_recall'])},
                    borderColor: 'rgba(52, 152, 219, 1)',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4
                }}, {{
                    label: 'Config B (Candidate)',
                    data: {json.dumps(time_series_data['config_b_recall'])},
                    borderColor: 'rgba(231, 76, 60, 1)',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 1.0,
                        title: {{
                            display: true,
                            text: 'Recall@10'
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
        
        return html_template
    
    def _generate_sample_time_series(self) -> Dict[str, List]:
        """Generate sample time series data for charts."""
        # In a real implementation, this would fetch actual time series data
        # For now, generate sample data
        timestamps = []
        config_a_p95 = []
        config_b_p95 = []
        config_a_recall = []
        config_b_recall = []
        
        base_time = time.time() - 600  # 10 minutes ago
        
        for i in range(12):  # 12 data points (5-minute intervals)
            timestamp = time.strftime("%H:%M", time.gmtime(base_time + i * 300))
            timestamps.append(timestamp)
            
            # Generate realistic sample data with some variation
            config_a_p95.append(850 + (i % 3) * 50)
            config_b_p95.append(780 + (i % 4) * 40)
            config_a_recall.append(0.32 + (i % 2) * 0.02)
            config_b_recall.append(0.35 + (i % 3) * 0.01)
        
        return {
            "timestamps": timestamps,
            "config_a_p95": config_a_p95,
            "config_b_p95": config_b_p95,
            "config_a_recall": config_a_recall,
            "config_b_recall": config_b_recall
        }


# Global report generator instance
_global_report_generator = None


def get_report_generator() -> ReportGenerator:
    """Get the global report generator instance."""
    global _global_report_generator
    if _global_report_generator is None:
        _global_report_generator = ReportGenerator()
    return _global_report_generator
