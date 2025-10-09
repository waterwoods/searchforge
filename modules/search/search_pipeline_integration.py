"""
SearchPipeline Integration Example

This module demonstrates how to integrate the config_selector hook
into SearchPipeline with minimal changes.
"""

import time
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.canary.config_selector import config_selector, get_routing_stats, validate_routing
from modules.search.search_pipeline import SearchPipeline

logger = logging.getLogger(__name__)


class SearchPipelineWithCanary(SearchPipeline):
    """
    SearchPipeline with integrated canary deployment support.
    
    This class extends the original SearchPipeline with minimal changes
    to support A/B testing and canary deployments.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize SearchPipeline with canary support."""
        super().__init__(*args, **kwargs)
        self._canary_enabled = True
        logger.info("SearchPipeline initialized with canary support")
    
    def search(self, query: str, trace_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Enhanced search method with configuration selection.
        
        Args:
            query: Search query
            trace_id: Optional trace ID for A/B testing
            **kwargs: Additional search parameters
            
        Returns:
            Search results with routing information
        """
        # Generate trace_id if not provided
        if trace_id is None:
            trace_id = f"search_{int(time.time() * 1000)}_{hash(query) % 10000}"
        
        # Select configuration using canary selector
        if self._canary_enabled:
            try:
                selected_config = config_selector(trace_id, query)
                logger.debug(f"Selected config '{selected_config}' for trace {trace_id}")
                
                # Override configuration if needed
                if 'config_name' not in kwargs:
                    kwargs['config_name'] = selected_config
                    
            except Exception as e:
                logger.warning(f"Config selection failed, using default: {e}")
                # Fall back to default behavior
                pass
        
        # Call original search method
        result = super().search(query, trace_id=trace_id, **kwargs)
        
        # Add routing information to result
        if self._canary_enabled:
            result['routing'] = {
                'trace_id': trace_id,
                'config_selected': kwargs.get('config_name', 'default'),
                'canary_enabled': True
            }
        
        return result
    
    def enable_canary(self) -> None:
        """Enable canary deployment routing."""
        self._canary_enabled = True
        logger.info("Canary routing enabled")
    
    def disable_canary(self) -> None:
        """Disable canary deployment routing."""
        self._canary_enabled = False
        logger.info("Canary routing disabled")
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get current routing statistics."""
        if not self._canary_enabled:
            return {"canary_enabled": False}
        
        stats = get_routing_stats()
        stats["canary_enabled"] = True
        return stats
    
    def validate_routing(self, tolerance: float = 0.05) -> Dict[str, Any]:
        """
        Validate routing split ratio.
        
        Args:
            tolerance: Acceptable deviation from target ratio
            
        Returns:
            Validation results
        """
        if not self._canary_enabled:
            return {
                "canary_enabled": False,
                "validation_skipped": True
            }
        
        is_valid, stats = validate_routing(tolerance)
        
        return {
            "canary_enabled": True,
            "validation_passed": is_valid,
            "stats": stats
        }


def create_search_pipeline_with_canary(**kwargs) -> SearchPipelineWithCanary:
    """
    Factory function to create SearchPipeline with canary support.
    
    Args:
        **kwargs: Arguments to pass to SearchPipeline constructor
        
    Returns:
        SearchPipelineWithCanary instance
    """
    return SearchPipelineWithCanary(**kwargs)


def integrate_config_selector_hook():
    """
    Example of how to integrate config_selector as a hook in existing SearchPipeline.
    
    This function shows the minimal changes needed to add canary support
    to an existing SearchPipeline without subclassing.
    """
    
    # Example hook function that can be added to existing SearchPipeline
    def canary_config_hook(trace_id: str, query: str, **kwargs) -> Dict[str, Any]:
        """
        Hook function for configuration selection.
        
        This can be called from within SearchPipeline.search() method.
        """
        try:
            selected_config = config_selector(trace_id, query)
            return {
                'config_name': selected_config,
                'canary_enabled': True,
                'trace_id': trace_id
            }
        except Exception as e:
            logger.warning(f"Canary config hook failed: {e}")
            return {
                'config_name': 'default',
                'canary_enabled': False,
                'trace_id': trace_id,
                'error': str(e)
            }
    
    return canary_config_hook


def demonstrate_minimal_integration():
    """
    Demonstrate minimal integration approach.
    
    This shows how to add canary support with just a few lines of code.
    """
    
    # Original SearchPipeline search method (pseudo-code)
    def original_search(self, query: str, trace_id: Optional[str] = None, **kwargs):
        # ... existing search logic ...
        pass
    
    # Modified search method with canary support (pseudo-code)
    def search_with_canary(self, query: str, trace_id: Optional[str] = None, **kwargs):
        # Generate trace_id if not provided
        if trace_id is None:
            trace_id = f"search_{int(time.time() * 1000)}_{hash(query) % 10000}"
        
        # Add this line for canary support
        if 'config_name' not in kwargs:
            kwargs['config_name'] = config_selector(trace_id, query)
        
        # Call original search logic
        return original_search(self, query, trace_id=trace_id, **kwargs)
    
    logger.info("Minimal integration example provided")


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    print("SearchPipeline Canary Integration Example")
    print("=" * 50)
    
    # Create pipeline with canary support
    pipeline = create_search_pipeline_with_canary()
    
    # Test routing
    print("Testing configuration selection...")
    for i in range(10):
        trace_id = f"test_trace_{i}"
        config = config_selector(trace_id, f"test query {i}")
        print(f"  Trace {trace_id}: {config}")
    
    # Get routing stats
    print("\nRouting Statistics:")
    stats = pipeline.get_routing_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Validate routing
    print("\nRouting Validation:")
    validation = pipeline.validate_routing()
    print(f"  Validation passed: {validation.get('validation_passed', False)}")
    
    print("\nIntegration example completed!")


