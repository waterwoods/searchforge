"""
Observability and Regression Package for Canary Deployments

This module provides comprehensive observability and regression analysis
capabilities for canary deployment results.
"""

import json
import csv
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

from .config_manager import ConfigManager
from .canary_executor import CanaryExecutor
from .ab_evaluator import ABEvaluator
from .report_generator import ReportGenerator
from .slo_strategy import SLOStrategyManager

logger = logging.getLogger(__name__)


@dataclass
class ObservabilityPackage:
    """Represents a complete observability package for a canary deployment."""
    deployment_id: str
    timestamp: str
    config_a: str  # last_good
    config_b: str  # candidate
    deployment_status: str  # "successful", "rolled_back", "in_progress"
    duration_seconds: float
    total_requests: int
    
    # Performance metrics
    config_a_metrics: Dict[str, Any]
    config_b_metrics: Dict[str, Any]
    
    # A/B comparison results
    ab_comparison: Dict[str, Any]
    
    # SLO violations
    slo_violations: List[Dict[str, Any]]
    
    # Files generated
    generated_files: List[str]


class ObservabilityPackageGenerator:
    """
    Generates comprehensive observability packages for canary deployments.
    
    Features:
    - Export canary_result.json with complete deployment data
    - Export metrics.json with detailed performance metrics
    - Generate one_pager.html with visual summary
    - Create 5-minute regression baseline CSV
    - Support for multiple deployment formats
    """
    
    def __init__(self, 
                 config_manager: Optional[ConfigManager] = None,
                 canary_executor: Optional[CanaryExecutor] = None,
                 ab_evaluator: Optional[ABEvaluator] = None,
                 report_generator: Optional[ReportGenerator] = None,
                 slo_strategy_manager: Optional[SLOStrategyManager] = None):
        """
        Initialize the observability package generator.
        
        Args:
            config_manager: Configuration manager instance
            canary_executor: Canary executor instance
            ab_evaluator: A/B evaluator instance
            report_generator: Report generator instance
            slo_strategy_manager: SLO strategy manager instance
        """
        self.config_manager = config_manager or ConfigManager()
        self.canary_executor = canary_executor or CanaryExecutor()
        self.ab_evaluator = ab_evaluator or ABEvaluator()
        self.report_generator = report_generator or ReportGenerator()
        self.slo_strategy_manager = slo_strategy_manager or SLOStrategyManager()
        
        # Output directory
        self.output_dir = Path("reports/canary")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("ObservabilityPackageGenerator initialized")
    
    def generate_package(self, deployment_id: Optional[str] = None, 
                        output_prefix: Optional[str] = None) -> ObservabilityPackage:
        """
        Generate a complete observability package for a canary deployment.
        
        Args:
            deployment_id: Specific deployment ID, or None for latest
            output_prefix: Prefix for output files
            
        Returns:
            ObservabilityPackage object with all data and generated files
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        if output_prefix is None:
            output_prefix = f"canary_package_{timestamp}"
        
        # Get deployment data
        deployment_data = self._get_deployment_data(deployment_id)
        
        # Generate package
        package = ObservabilityPackage(
            deployment_id=deployment_data['deployment_id'],
            timestamp=timestamp,
            config_a=deployment_data['config_a'],
            config_b=deployment_data['config_b'],
            deployment_status=deployment_data['status'],
            duration_seconds=deployment_data['duration'],
            total_requests=deployment_data['total_requests'],
            config_a_metrics=deployment_data['config_a_metrics'],
            config_b_metrics=deployment_data['config_b_metrics'],
            ab_comparison=deployment_data['ab_comparison'],
            slo_violations=deployment_data['slo_violations'],
            generated_files=[]
        )
        
        # Generate files
        generated_files = []
        
        # 1. Export canary_result.json
        canary_result_file = self.output_dir / f"{output_prefix}_canary_result.json"
        self._export_canary_result(package, canary_result_file)
        generated_files.append(str(canary_result_file))
        
        # 2. Export metrics.json
        metrics_file = self.output_dir / f"{output_prefix}_metrics.json"
        self._export_metrics(package, metrics_file)
        generated_files.append(str(metrics_file))
        
        # 3. Generate one_pager.html
        one_pager_file = self.output_dir / f"{output_prefix}_one_pager.html"
        self._generate_one_pager(package, one_pager_file)
        generated_files.append(str(one_pager_file))
        
        # 4. Create regression baseline CSV
        baseline_csv_file = self.output_dir / f"{output_prefix}_regression_baseline.csv"
        self._generate_regression_baseline(package, baseline_csv_file)
        generated_files.append(str(baseline_csv_file))
        
        package.generated_files = generated_files
        
        logger.info(f"Generated observability package: {output_prefix}")
        logger.info(f"Generated files: {len(generated_files)}")
        
        return package
    
    def _get_deployment_data(self, deployment_id: Optional[str] = None) -> Dict[str, Any]:
        """Get deployment data for package generation."""
        # Get canary status
        canary_status = self.config_manager.get_canary_status()
        
        # Get A/B comparison
        ab_comparison = self.ab_evaluator.generate_kpi_report(window_minutes=10)
        
        # Get SLO violations
        violations_summary = self.slo_strategy_manager.get_violations_summary()
        
        # Calculate deployment metrics
        config_a_metrics = ab_comparison['performance_comparison']['config_a']
        config_b_metrics = ab_comparison['performance_comparison']['config_b']
        
        # Estimate duration and total requests
        duration = 300.0  # Default 5 minutes
        total_requests = config_a_metrics.get('total_responses', 0) + config_b_metrics.get('total_responses', 0)
        
        return {
            'deployment_id': deployment_id or f"deployment_{int(time.time())}",
            'config_a': canary_status['last_good_config'],
            'config_b': canary_status.get('candidate_config', 'none'),
            'status': canary_status['status'],
            'duration': duration,
            'total_requests': total_requests,
            'config_a_metrics': config_a_metrics,
            'config_b_metrics': config_b_metrics,
            'ab_comparison': ab_comparison,
            'slo_violations': violations_summary
        }
    
    def _export_canary_result(self, package: ObservabilityPackage, output_file: Path) -> None:
        """Export canary_result.json with complete deployment data."""
        result_data = {
            "deployment_summary": {
                "deployment_id": package.deployment_id,
                "timestamp": package.timestamp,
                "status": package.deployment_status,
                "duration_seconds": package.duration_seconds,
                "total_requests": package.total_requests
            },
            "configurations": {
                "config_a": {
                    "name": package.config_a,
                    "description": "Last Good Configuration",
                    "metrics": package.config_a_metrics
                },
                "config_b": {
                    "name": package.config_b,
                    "description": "Candidate Configuration", 
                    "metrics": package.config_b_metrics
                }
            },
            "ab_comparison": package.ab_comparison,
            "slo_violations": package.slo_violations,
            "generated_files": package.generated_files,
            "export_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        
        try:
            with open(output_file, 'w') as f:
                json.dump(result_data, f, indent=2)
            logger.info(f"Exported canary result to {output_file}")
        except Exception as e:
            logger.error(f"Failed to export canary result: {e}")
            raise
    
    def _export_metrics(self, package: ObservabilityPackage, output_file: Path) -> None:
        """Export detailed metrics.json."""
        metrics_data = {
            "deployment_id": package.deployment_id,
            "timestamp": package.timestamp,
            "duration_seconds": package.duration_seconds,
            "total_requests": package.total_requests,
            "performance_metrics": {
                "config_a": package.config_a_metrics,
                "config_b": package.config_b_metrics
            },
            "ab_analysis": package.ab_comparison,
            "slo_analysis": package.slo_violations,
            "statistical_significance": package.ab_comparison.get('statistical_significance', {}),
            "recommendations": package.ab_comparison.get('recommendation', ''),
            "export_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        
        try:
            with open(output_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            logger.info(f"Exported metrics to {output_file}")
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            raise
    
    def _generate_one_pager(self, package: ObservabilityPackage, output_file: Path) -> None:
        """Generate one_pager.html with visual summary."""
        # Use the existing report generator
        try:
            self.report_generator.generate_html_report(str(output_file), window_minutes=10)
            logger.info(f"Generated one-pager HTML to {output_file}")
        except Exception as e:
            logger.error(f"Failed to generate one-pager: {e}")
            raise
    
    def _generate_regression_baseline(self, package: ObservabilityPackage, output_file: Path) -> None:
        """Generate 5-minute regression baseline CSV."""
        baseline_data = []
        
        # Add deployment summary
        baseline_data.append({
            "metric": "deployment_id",
            "value": package.deployment_id,
            "timestamp": package.timestamp,
            "config": "summary"
        })
        
        baseline_data.append({
            "metric": "duration_seconds",
            "value": package.duration_seconds,
            "timestamp": package.timestamp,
            "config": "summary"
        })
        
        baseline_data.append({
            "metric": "total_requests",
            "value": package.total_requests,
            "timestamp": package.timestamp,
            "config": "summary"
        })
        
        # Add performance metrics
        for config_name, metrics in [("config_a", package.config_a_metrics), ("config_b", package.config_b_metrics)]:
            baseline_data.append({
                "metric": "p95_latency_ms",
                "value": metrics.get('avg_p95_ms', 0),
                "timestamp": package.timestamp,
                "config": config_name
            })
            
            baseline_data.append({
                "metric": "recall_at_10",
                "value": metrics.get('avg_recall_at_10', 0),
                "timestamp": package.timestamp,
                "config": config_name
            })
            
            baseline_data.append({
                "metric": "slo_violations",
                "value": metrics.get('total_slo_violations', 0),
                "timestamp": package.timestamp,
                "config": config_name
            })
            
            baseline_data.append({
                "metric": "response_count",
                "value": metrics.get('total_responses', 0),
                "timestamp": package.timestamp,
                "config": config_name
            })
        
        # Add A/B comparison metrics
        improvements = package.ab_comparison.get('improvements', {})
        baseline_data.append({
            "metric": "p95_improvement_ms",
            "value": improvements.get('p95_latency_ms', {}).get('absolute', 0),
            "timestamp": package.timestamp,
            "config": "comparison"
        })
        
        baseline_data.append({
            "metric": "recall_improvement",
            "value": improvements.get('recall_at_10', {}).get('absolute', 0),
            "timestamp": package.timestamp,
            "config": "comparison"
        })
        
        baseline_data.append({
            "metric": "slo_violation_reduction",
            "value": improvements.get('slo_violations', {}).get('absolute', 0),
            "timestamp": package.timestamp,
            "config": "comparison"
        })
        
        # Write CSV
        try:
            with open(output_file, 'w', newline='') as f:
                if baseline_data:
                    writer = csv.DictWriter(f, fieldnames=baseline_data[0].keys())
                    writer.writeheader()
                    writer.writerows(baseline_data)
            logger.info(f"Generated regression baseline CSV to {output_file}")
        except Exception as e:
            logger.error(f"Failed to generate regression baseline CSV: {e}")
            raise
    
    def generate_multiple_packages(self, deployment_ids: List[str]) -> List[ObservabilityPackage]:
        """
        Generate observability packages for multiple deployments.
        
        Args:
            deployment_ids: List of deployment IDs
            
        Returns:
            List of ObservabilityPackage objects
        """
        packages = []
        
        for i, deployment_id in enumerate(deployment_ids):
            output_prefix = f"deployment_{i+1}_{deployment_id}"
            package = self.generate_package(deployment_id, output_prefix)
            packages.append(package)
        
        logger.info(f"Generated {len(packages)} observability packages")
        return packages
    
    def compare_packages(self, packages: List[ObservabilityPackage]) -> Dict[str, Any]:
        """
        Compare multiple observability packages for regression analysis.
        
        Args:
            packages: List of ObservabilityPackage objects
            
        Returns:
            Comparison analysis dictionary
        """
        if len(packages) < 2:
            return {"error": "Need at least 2 packages for comparison"}
        
        comparison = {
            "total_packages": len(packages),
            "comparison_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "packages": []
        }
        
        for i, package in enumerate(packages):
            package_summary = {
                "index": i,
                "deployment_id": package.deployment_id,
                "timestamp": package.timestamp,
                "status": package.deployment_status,
                "duration": package.duration_seconds,
                "total_requests": package.total_requests,
                "config_a_p95": package.config_a_metrics.get('avg_p95_ms', 0),
                "config_b_p95": package.config_b_metrics.get('avg_p95_ms', 0),
                "config_a_recall": package.config_a_metrics.get('avg_recall_at_10', 0),
                "config_b_recall": package.config_b_metrics.get('avg_recall_at_10', 0)
            }
            comparison["packages"].append(package_summary)
        
        # Calculate trends
        if len(packages) >= 2:
            first_package = packages[0]
            last_package = packages[-1]
            
            p95_trend = last_package.config_b_metrics.get('avg_p95_ms', 0) - first_package.config_b_metrics.get('avg_p95_ms', 0)
            recall_trend = last_package.config_b_metrics.get('avg_recall_at_10', 0) - first_package.config_b_metrics.get('avg_recall_at_10', 0)
            
            comparison["trends"] = {
                "p95_latency_trend_ms": p95_trend,
                "recall_trend": recall_trend,
                "p95_improvement": p95_trend < 0,
                "recall_improvement": recall_trend > 0
            }
        
        return comparison


# Global observability package generator instance
_global_observability_generator = None


def get_observability_generator() -> ObservabilityPackageGenerator:
    """Get the global observability package generator instance."""
    global _global_observability_generator
    if _global_observability_generator is None:
        _global_observability_generator = ObservabilityPackageGenerator()
    return _global_observability_generator


def generate_observability_package(deployment_id: Optional[str] = None,
                                 output_prefix: Optional[str] = None) -> ObservabilityPackage:
    """
    Generate a complete observability package for a canary deployment.
    
    Args:
        deployment_id: Specific deployment ID, or None for latest
        output_prefix: Prefix for output files
        
    Returns:
        ObservabilityPackage object
    """
    generator = get_observability_generator()
    return generator.generate_package(deployment_id, output_prefix)


