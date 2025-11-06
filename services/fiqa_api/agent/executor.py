"""
Executor Component for Agent's Runtime

This module provides the Executor class that takes action plans from the Planner
and executes them by calling the appropriate methods on the available tools.
"""

import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the parent directory to the path to import tools
sys.path.append(str(Path(__file__).parent.parent))
from tools.codegraph import CodeGraph


class Executor:
    """
    Executor class that executes action plans by calling tool methods.
    
    The Executor is responsible for taking the structured plans from the Planner
    and actually executing them by dynamically calling methods on the available tools.
    """
    
    def __init__(self, codegraph: CodeGraph):
        """
        Initialize the Executor with access to tools.
        
        Args:
            codegraph: Instance of CodeGraph tool for executing queries
        """
        self.codegraph = codegraph
        
        # Registry of available tools
        self.tools = {
            'codegraph': codegraph
        }
        
        # Pattern for matching step dependencies
        self.dependency_pattern = re.compile(r'\{previous_step_result\.(\w+)\}')
    
    def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a complete action plan step by step.
        
        Args:
            plan: Plan dictionary containing 'steps' array and other metadata
            
        Returns:
            Result from the last step in the plan
        """
        if not plan or 'steps' not in plan:
            return {
                'error': 'Invalid plan: missing steps',
                'success': False
            }
        
        steps = plan['steps']
        if not steps:
            return {
                'error': 'Invalid plan: empty steps array',
                'success': False
            }
        
        # Track results from each step for dependency resolution
        step_results = []
        
        try:
            # Execute each step in sequence
            for i, step in enumerate(steps):
                print(f"🔧 Executing step {i+1}/{len(steps)}: {step.get('tool', 'unknown')}")
                
                # Execute the step
                result = self._execute_step(step, step_results)
                
                # Store result for potential use in subsequent steps
                step_results.append(result)
                
                # Check if step failed
                if isinstance(result, dict) and result.get('error'):
                    return {
                        'error': f"Step {i+1} failed: {result['error']}",
                        'success': False,
                        'step_results': step_results
                    }
            
            # Return the result from the last step
            final_result = step_results[-1] if step_results else None
            
            return {
                'result': final_result,
                'success': True,
                'steps_executed': len(steps),
                'step_results': step_results
            }
            
        except Exception as e:
            return {
                'error': f"Execution failed: {str(e)}",
                'success': False,
                'step_results': step_results
            }
    
    def _execute_step(self, step: Dict[str, Any], previous_results: List[Any]) -> Any:
        """
        Execute a single step in the plan.
        
        Args:
            step: Step dictionary containing 'tool' and 'args'
            previous_results: Results from previous steps for dependency resolution
            
        Returns:
            Result from executing the step
        """
        if 'tool' not in step:
            return {'error': 'Step missing tool specification'}
        
        if 'args' not in step:
            return {'error': 'Step missing args specification'}
        
        tool_name = step['tool']
        args = step['args'].copy()  # Make a copy to avoid modifying original
        
        # Parse tool name to extract tool and method
        tool_instance, method_name = self._parse_tool_name(tool_name)
        if not tool_instance or not method_name:
            return {'error': f'Invalid tool specification: {tool_name}'}
        
        # Resolve step dependencies in arguments
        resolved_args = self._resolve_dependencies(args, previous_results)
        
        # Get the method from the tool instance
        try:
            method = getattr(tool_instance, method_name)
        except AttributeError:
            return {'error': f'Method {method_name} not found on tool {tool_name}'}
        
        # Execute the method with resolved arguments
        try:
            result = method(**resolved_args)
            
            # 🔍 FORENSIC INVESTIGATION: Log raw tool result immediately after execution
            print(f"🔍 forensic_investigation RAW TOOL RESULT for '{tool_name}': {result}")
            print(f"🔍 forensic_investigation RAW TOOL RESULT TYPE: {type(result)}")
            if isinstance(result, dict):
                print(f"🔍 forensic_investigation RAW TOOL RESULT KEYS: {list(result.keys())}")
            
            return result
        except Exception as e:
            error_result = {'error': f'Tool execution failed: {str(e)}'}
            print(f"🔍 forensic_investigation RAW TOOL ERROR for '{tool_name}': {error_result}")
            return error_result
    
    def _parse_tool_name(self, tool_name: str) -> tuple[Optional[Any], Optional[str]]:
        """
        Parse a tool name like 'codegraph.get_node_by_fqname' into tool instance and method.
        
        Args:
            tool_name: Tool specification string
            
        Returns:
            Tuple of (tool_instance, method_name) or (None, None) if invalid
        """
        if '.' not in tool_name:
            return None, None
        
        tool_key, method_name = tool_name.split('.', 1)
        
        if tool_key not in self.tools:
            return None, None
        
        return self.tools[tool_key], method_name
    
    def _resolve_dependencies(self, args: Dict[str, Any], previous_results: List[Any]) -> Dict[str, Any]:
        """
        Resolve step dependencies in arguments by replacing placeholders with actual values.
        
        Args:
            args: Arguments dictionary that may contain dependency placeholders
            previous_results: Results from previous steps
            
        Returns:
            Arguments dictionary with dependencies resolved
        """
        resolved_args = {}
        
        for key, value in args.items():
            if isinstance(value, str):
                # Check for dependency patterns
                match = self.dependency_pattern.search(value)
                if match:
                    field_name = match.group(1)
                    
                    # Get the value from the most recent step result
                    if previous_results:
                        last_result = previous_results[-1]
                        if isinstance(last_result, dict) and field_name in last_result:
                            resolved_args[key] = last_result[field_name]
                        else:
                            resolved_args[key] = value  # Keep original if can't resolve
                    else:
                        resolved_args[key] = value  # Keep original if no previous results
                else:
                    resolved_args[key] = value
            else:
                resolved_args[key] = value
        
        return resolved_args
    
    def get_available_tools(self) -> Dict[str, Any]:
        """
        Get information about available tools.
        
        Returns:
            Dictionary containing available tools and their methods
        """
        tools_info = {}
        
        for tool_name, tool_instance in self.tools.items():
            if hasattr(tool_instance, '__class__'):
                class_name = tool_instance.__class__.__name__
                methods = [method for method in dir(tool_instance) 
                          if not method.startswith('_') and callable(getattr(tool_instance, method))]
                
                tools_info[tool_name] = {
                    'class': class_name,
                    'methods': methods
                }
        
        return tools_info
    
    def validate_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that a plan can be executed with available tools.
        
        Args:
            plan: Plan dictionary to validate
            
        Returns:
            Validation result with success status and any errors
        """
        if not plan or 'steps' not in plan:
            return {
                'valid': False,
                'error': 'Plan missing steps'
            }
        
        steps = plan['steps']
        if not steps:
            return {
                'valid': False,
                'error': 'Plan has empty steps array'
            }
        
        errors = []
        
        for i, step in enumerate(steps):
            if 'tool' not in step:
                errors.append(f'Step {i+1}: missing tool specification')
                continue
            
            tool_name = step['tool']
            tool_instance, method_name = self._parse_tool_name(tool_name)
            
            if not tool_instance:
                errors.append(f'Step {i+1}: unknown tool in "{tool_name}"')
                continue
            
            if not method_name:
                errors.append(f'Step {i+1}: invalid tool format "{tool_name}"')
                continue
            
            # Check if method exists
            if not hasattr(tool_instance, method_name):
                errors.append(f'Step {i+1}: method "{method_name}" not found on tool')
                continue
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
