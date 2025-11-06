"""
Planner Component for Agent's Runtime

This module provides the Planner class that takes structured commands from the Router
and creates machine-readable, step-by-step action plans for the Executor to follow.
"""

import json
from typing import Dict, Any, List


class Planner:
    """
    Planner class that generates action plans from structured queries.
    
    The Planner is responsible for converting the Router's structured commands
    into detailed, executable plans that the Executor can follow step by step.
    """
    
    def __init__(self):
        """
        Initialize the Planner with default configuration.
        """
        # Default stop conditions for plans
        self.default_stop = {
            "max_rounds": 1,
            "budget_s": 30
        }
        
        # Available tools and their configurations
        self.available_tools = {
            "codegraph": {
                "get_neighbors_by_fqname": {
                    "description": "Get neighbors of a function by its fully qualified name",
                    "required_args": ["fqname"],
                    "optional_args": ["max_hops"]
                },
                "get_nodes_by_file": {
                    "description": "Get all nodes within a specific file",
                    "required_args": ["file_path"]
                },
                "get_graph_stats": {
                    "description": "Get overall statistics about the codegraph",
                    "required_args": []
                },
                "get_node_by_fqname": {
                    "description": "Get a specific node by its fully qualified name",
                    "required_args": ["fqname"]
                },
                "get_all_nodes_and_edges": {
                    "description": "Get all nodes and edges from the graph",
                    "required_args": []
                }
            }
        }
    
    def create_plan(self, structured_query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an action plan based on the structured query from the Router.
        
        Args:
            structured_query: Dictionary output from the Router containing 'type' and optionally 'target'
            
        Returns:
            Dictionary containing the complete action plan with goal, steps, and stop conditions
        """
        if not structured_query or 'type' not in structured_query:
            return self._create_error_plan("Invalid structured query: missing 'type' field")
        
        query_type = structured_query['type']
        
        # Route to appropriate plan generation method
        if query_type == 'function':
            return self._create_function_plan(structured_query)
        elif query_type == 'file':
            return self._create_file_plan(structured_query)
        elif query_type == 'overview':
            return self._create_overview_plan(structured_query)
        elif query_type == 'unknown':
            return self._create_error_plan(structured_query.get('error', 'Unknown query type'))
        elif query_type == 'error':
            return self._create_error_plan(structured_query.get('error', 'Query error'))
        else:
            return self._create_error_plan(f"Unsupported query type: {query_type}")
    
    def _create_function_plan(self, structured_query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a plan for analyzing a specific function.
        
        Args:
            structured_query: Query containing 'type': 'function' and 'target': function_name
            
        Returns:
            Action plan for function analysis
        """
        target = structured_query.get('target')
        if not target:
            return self._create_error_plan("Function query missing 'target' parameter")
        
        return {
            "goal": f"Explain function {target} and its immediate neighbors",
            "steps": [
                {
                    "tool": "codegraph.get_node_by_fqname",
                    "args": {
                        "fqname": target
                    }
                },
                {
                    "tool": "codegraph.get_neighbors",
                    "args": {
                        "node_id": f"{{previous_step_result.id}}",
                        "max_hops": 1
                    }
                }
            ],
            "stop": self.default_stop.copy()
        }
    
    def _create_file_plan(self, structured_query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a plan for analyzing a specific file.
        
        Args:
            structured_query: Query containing 'type': 'file' and 'target': file_path
            
        Returns:
            Action plan for file analysis
        """
        target = structured_query.get('target')
        if not target:
            return self._create_error_plan("File query missing 'target' parameter")
        
        return {
            "goal": f"Analyze all functions within the file {target}",
            "steps": [
                {
                    "tool": "codegraph.get_nodes_by_file",
                    "args": {
                        "file_path": target
                    }
                }
            ],
            "stop": self.default_stop.copy()
        }
    
    def _create_overview_plan(self, structured_query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a plan for getting repository overview.
        
        Args:
            structured_query: Query containing 'type': 'overview'
            
        Returns:
            Action plan for overview analysis
        """
        return {
            "goal": "Provide a comprehensive overview of the repository structure and statistics",
            "steps": [
                {
                    "tool": "codegraph.get_all_nodes_and_edges",
                    "args": {}
                }
            ],
            "stop": self.default_stop.copy()
        }
    
    def _create_error_plan(self, error_message: str) -> Dict[str, Any]:
        """
        Create an error plan when the query cannot be processed.
        
        Args:
            error_message: Description of the error
            
        Returns:
            Error plan with appropriate message
        """
        return {
            "goal": f"Handle query error: {error_message}",
            "steps": [
                {
                    "tool": "codegraph.get_graph_stats",
                    "args": {}
                }
            ],
            "stop": {
                "max_rounds": 1,
                "budget_s": 5
            }
        }
    
    def validate_plan(self, plan: Dict[str, Any]) -> bool:
        """
        Validate that a plan follows the required schema.
        
        Args:
            plan: Plan dictionary to validate
            
        Returns:
            True if plan is valid, False otherwise
        """
        required_fields = ['goal', 'steps', 'stop']
        
        # Check required fields
        for field in required_fields:
            if field not in plan:
                return False
        
        # Validate goal is a string
        if not isinstance(plan['goal'], str):
            return False
        
        # Validate steps is a list
        if not isinstance(plan['steps'], list):
            return False
        
        # Validate each step
        for step in plan['steps']:
            if not isinstance(step, dict):
                return False
            if 'tool' not in step or 'args' not in step:
                return False
            if not isinstance(step['tool'], str) or not isinstance(step['args'], dict):
                return False
        
        # Validate stop conditions
        stop = plan['stop']
        if not isinstance(stop, dict):
            return False
        if 'max_rounds' not in stop or 'budget_s' not in stop:
            return False
        if not isinstance(stop['max_rounds'], int) or not isinstance(stop['budget_s'], int):
            return False
        
        return True
    
    def get_available_tools(self) -> Dict[str, Any]:
        """
        Get information about available tools for plan generation.
        
        Returns:
            Dictionary containing available tools and their configurations
        """
        return self.available_tools.copy()
    
    def format_plan_as_json(self, plan: Dict[str, Any]) -> str:
        """
        Format a plan as a pretty-printed JSON string.
        
        Args:
            plan: Plan dictionary to format
            
        Returns:
            Pretty-printed JSON string
        """
        return json.dumps(plan, indent=2, ensure_ascii=False)
