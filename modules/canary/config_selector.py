"""
Configuration Selector for SearchPipeline Integration

This module provides a lightweight config_selector() hook for SearchPipeline
to enable A/B testing with 90/10 traffic splitting.
"""

import time
import hashlib
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .config_manager import ConfigManager
from .ab_evaluator import ABEvaluator

logger = logging.getLogger(__name__)


@dataclass
class ConfigSelection:
    """Represents a configuration selection result."""
    config_name: str
    bucket: str  # "A" or "B"
    selection_ratio: float
    trace_id: str
    timestamp: str


class ConfigSelector:
    """
    Lightweight configuration selector for SearchPipeline integration.
    
    Features:
    - 90/10 traffic splitting (A=last_good, B=candidate)
    - Consistent bucket assignment based on trace_id
    - Minimal overhead for production use
    - Integration with canary deployment system
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None,
                 ab_evaluator: Optional[ABEvaluator] = None):
        """
        Initialize the configuration selector.
        
        Args:
            config_manager: Configuration manager instance
            ab_evaluator: A/B evaluator instance
        """
        self.config_manager = config_manager or ConfigManager()
        self.ab_evaluator = ab_evaluator or ABEvaluator()
        
        # Traffic split configuration
        self.split_ratio = {"A": 0.9, "B": 0.1}
        
        # Selection tracking for monitoring
        self._selection_count = {"A": 0, "B": 0}
        self._total_selections = 0
        
        logger.info("ConfigSelector initialized with 90/10 split")
    
    def select_config(self, trace_id: str, query: Optional[str] = None) -> ConfigSelection:
        """
        Select configuration based on trace_id with 90/10 split.
        
        Args:
            trace_id: Unique trace identifier
            query: Optional query string for additional context
            
        Returns:
            ConfigSelection object with selected configuration
        """
        # Get current canary status
        canary_status = self.config_manager.get_canary_status()
        
        # Check if canary is active
        if canary_status.get('status') != 'running':
            # No canary active, use last_good configuration
            config_selection = ConfigSelection(
                config_name=canary_status['last_good_config'],
                bucket="A",
                selection_ratio=1.0,
                trace_id=trace_id,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ")
            )
            
            self._update_selection_stats("A")
            return config_selection
        
        # Canary is active, determine bucket assignment
        bucket = self.ab_evaluator.assign_bucket(trace_id)
        
        # Select configuration based on bucket
        if bucket == "A":
            config_name = canary_status['last_good_config']
            selection_ratio = self.split_ratio["A"]
        else:  # bucket == "B"
            config_name = canary_status['candidate_config']
            selection_ratio = self.split_ratio["B"]
        
        config_selection = ConfigSelection(
            config_name=config_name,
            bucket=bucket,
            selection_ratio=selection_ratio,
            trace_id=trace_id,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        
        self._update_selection_stats(bucket)
        
        # Log selection for monitoring
        logger.debug(f"Config selected: {config_name} (bucket {bucket}) for trace {trace_id}")
        
        return config_selection
    
    def _update_selection_stats(self, bucket: str) -> None:
        """Update selection statistics."""
        self._selection_count[bucket] += 1
        self._total_selections += 1
    
    def get_selection_stats(self) -> Dict[str, Any]:
        """
        Get current selection statistics.
        
        Returns:
            Dictionary with selection statistics
        """
        if self._total_selections == 0:
            return {
                "total_selections": 0,
                "bucket_a_count": 0,
                "bucket_b_count": 0,
                "bucket_a_percentage": 0.0,
                "bucket_b_percentage": 0.0,
                "target_split": self.split_ratio
            }
        
        bucket_a_count = self._selection_count["A"]
        bucket_b_count = self._selection_count["B"]
        
        return {
            "total_selections": self._total_selections,
            "bucket_a_count": bucket_a_count,
            "bucket_b_count": bucket_b_count,
            "bucket_a_percentage": (bucket_a_count / self._total_selections) * 100,
            "bucket_b_percentage": (bucket_b_count / self._total_selections) * 100,
            "target_split": self.split_ratio
        }
    
    def reset_stats(self) -> None:
        """Reset selection statistics."""
        self._selection_count = {"A": 0, "B": 0}
        self._total_selections = 0
        logger.info("Config selection statistics reset")
    
    def validate_split_ratio(self, tolerance: float = 0.05) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate that the actual split ratio is close to target.
        
        Args:
            tolerance: Acceptable deviation from target ratio
            
        Returns:
            Tuple of (is_valid, stats_dict)
        """
        stats = self.get_selection_stats()
        
        if stats["total_selections"] == 0:
            return False, stats
        
        target_a = self.split_ratio["A"] * 100
        actual_a = stats["bucket_a_percentage"]
        
        is_valid = abs(actual_a - target_a) <= (tolerance * 100)
        
        stats["split_validation"] = {
            "is_valid": is_valid,
            "target_percentage": target_a,
            "actual_percentage": actual_a,
            "deviation": abs(actual_a - target_a),
            "tolerance": tolerance * 100
        }
        
        return is_valid, stats


# Global config selector instance
_global_config_selector = None


def get_config_selector() -> ConfigSelector:
    """Get the global config selector instance."""
    global _global_config_selector
    if _global_config_selector is None:
        _global_config_selector = ConfigSelector()
    return _global_config_selector


def config_selector(trace_id: str, query: Optional[str] = None) -> str:
    """
    Lightweight hook function for SearchPipeline integration.
    
    This is the main function that SearchPipeline should call to select
    the appropriate configuration for a search request.
    
    Args:
        trace_id: Unique trace identifier
        query: Optional query string
        
    Returns:
        Configuration name to use for this request
    """
    selector = get_config_selector()
    selection = selector.select_config(trace_id, query)
    return selection.config_name


def get_routing_stats() -> Dict[str, Any]:
    """
    Get routing statistics for monitoring.
    
    Returns:
        Dictionary with routing statistics
    """
    selector = get_config_selector()
    return selector.get_selection_stats()


def validate_routing(tolerance: float = 0.05) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate routing split ratio.
    
    Args:
        tolerance: Acceptable deviation from target ratio
        
    Returns:
        Tuple of (is_valid, stats_dict)
    """
    selector = get_config_selector()
    return selector.validate_split_ratio(tolerance)
