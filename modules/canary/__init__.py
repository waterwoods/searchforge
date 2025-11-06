"""
Canary Deployment System for SearchForge

This module provides a complete canary deployment system with:
- Configuration versioning and management
- 90/10 traffic splitting
- Real-time metrics collection
- SLO monitoring and automatic rollback
- Comprehensive audit logging

Components:
- ConfigManager: Manages configuration versions and deployment state
- MetricsCollector: Collects and aggregates performance metrics
- SLOMonitor: Monitors SLO violations and triggers rollbacks
- CanaryExecutor: Main orchestrator for canary deployments
- AuditLogger: Comprehensive audit logging
"""

from .config_manager import ConfigManager, ConfigVersion, ConfigState
from .metrics_collector import MetricsCollector, MetricsBucket, SearchMetrics
from .slo_monitor import SLOMonitor, SLORule, SLOViolation
from .canary_executor import CanaryExecutor, CanaryResult
from .audit_logger import AuditLogger, AuditEvent, AuditEventType
from .ab_evaluator import ABEvaluator, ABBucket, ABComparison
from .report_generator import ReportGenerator
from .slo_strategy import SLOStrategyManager, SLOStrategy, AlertConfig, RollbackConfig
from .observability_package import ObservabilityPackageGenerator, ObservabilityPackage
from .config_selector import ConfigSelector, ConfigSelection

# Global instances
from .metrics_collector import get_metrics_collector
from .slo_monitor import get_slo_monitor
from .canary_executor import get_canary_executor
from .audit_logger import get_audit_logger
from .ab_evaluator import get_ab_evaluator
from .report_generator import get_report_generator
from .slo_strategy import get_slo_strategy_manager
from .observability_package import get_observability_generator, generate_observability_package
from .config_selector import get_config_selector

# Global singleton instances
_global_config_manager = None

def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager

def get_global_instances():
    """Get all global instances for easy access."""
    return {
        'config_manager': get_config_manager(),
        'metrics_collector': get_metrics_collector(),
        'slo_monitor': get_slo_monitor(),
        'canary_executor': get_canary_executor(),
        'audit_logger': get_audit_logger(),
        'ab_evaluator': get_ab_evaluator(),
        'report_generator': get_report_generator(),
        'slo_strategy_manager': get_slo_strategy_manager(),
        'observability_generator': get_observability_generator(),
        'config_selector': get_config_selector()
    }

__all__ = [
    'ConfigManager',
    'ConfigVersion', 
    'ConfigState',
    'MetricsCollector',
    'MetricsBucket',
    'SearchMetrics',
    'SLOMonitor',
    'SLORule',
    'SLOViolation',
    'CanaryExecutor',
    'CanaryResult',
    'AuditLogger',
    'AuditEvent',
    'AuditEventType',
    'ABEvaluator',
    'ABBucket',
    'ABComparison',
    'ReportGenerator',
    'SLOStrategyManager',
    'SLOStrategy',
    'AlertConfig',
    'RollbackConfig',
    'ObservabilityPackageGenerator',
    'ObservabilityPackage',
    'ConfigSelector',
    'ConfigSelection',
    'get_config_manager',
    'get_metrics_collector',
    'get_slo_monitor',
    'get_canary_executor',
    'get_audit_logger',
    'get_ab_evaluator',
    'get_report_generator',
    'get_slo_strategy_manager',
    'get_observability_generator',
    'generate_observability_package',
    'get_config_selector',
    'get_global_instances'
]
