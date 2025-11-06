"""
Judge Component for Agent's Runtime

This module provides the Judge class that performs quality control on the results
returned by the Executor, ensuring that every piece of information is backed
by solid evidence according to our "evidence card" principle.

Enhanced with Vibe Coding: Inner Script + Minimal Validation approach.
"""

from typing import Dict, List, Any, Optional
from .vibe_validator import VibeValidator


class Judge:
    """
    Judge class that validates execution results for evidence completeness.
    
    The Judge is responsible for ensuring that all data returned by the Executor
    contains proper evidence fields, maintaining the quality and reliability
    of our Agent's output.
    """
    
    def __init__(self):
        """
        Initialize the Judge with validation rules and Vibe Coding validator.
        """
        # Required evidence fields that must be present in every node
        self.required_evidence_fields = ['file', 'span', 'snippet']
        
        # Additional validation rules
        self.validation_rules = {
            'file': self._validate_file_field,
            'span': self._validate_span_field,
            'snippet': self._validate_snippet_field
        }
        
        # Initialize Vibe Coding validator
        self.vibe_validator = VibeValidator()
    
    def _unwrap_data(self, data: dict) -> dict:
        """
        Recursively unpacks data from nested 'result' keys.
        
        This function handles cases where data is wrapped in multiple layers
        of 'result' keys, which can happen when tools return data that gets
        wrapped by the Executor and then wrapped again by other components.
        
        Args:
            data: Dictionary that may contain nested 'result' keys
            
        Returns:
            Dictionary with all 'result' wrappers removed
        """
        if isinstance(data, dict) and 'result' in data and len(data.keys()) == 1:
            # If the dict has only one key 'result', unwrap it recursively
            return self._unwrap_data(data['result'])
        
        # Return the data as-is if it doesn't match the unwrapping pattern
        return data
    
    def review_execution_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review an execution result and validate evidence completeness.
        
        Args:
            result: Result dictionary returned by the Executor
            
        Returns:
            Dictionary containing verdict and list of issues found
        """
        # 🔍 FORENSIC INVESTIGATION: Log what Judge receives
        print(f"🔍 forensic_investigation JUDGE RECEIVED: {result}")
        print(f"🔍 forensic_investigation JUDGE RECEIVED TYPE: {type(result)}")
        if isinstance(result, dict):
            print(f"🔍 forensic_investigation JUDGE RECEIVED KEYS: {list(result.keys())}")
            if 'result' in result:
                print(f"🔍 forensic_investigation JUDGE RECEIVED RESULT FIELD: {result['result']}")
                print(f"🔍 forensic_investigation JUDGE RECEIVED RESULT FIELD TYPE: {type(result['result'])}")
        
        issues = []
        
        # Check if result has the expected structure
        if not isinstance(result, dict):
            return {
                "verdict": "revise",
                "issues": ["Result is not a dictionary"]
            }
        
        # Check if result contains nodes
        if 'result' not in result:
            return {
                "verdict": "revise", 
                "issues": ["Result missing 'result' field"]
            }
        
        execution_result = result['result']
        
        # CRITICAL FIX: Use recursive unwrapper to handle deeply nested data
        unwrapped_data = self._unwrap_data(execution_result)
        
        # 🔍 FORENSIC INVESTIGATION: Log unwrapped data
        print(f"🔍 forensic_investigation JUDGE UNWRAPPED DATA: {unwrapped_data}")
        print(f"🔍 forensic_investigation JUDGE UNWRAPPED DATA TYPE: {type(unwrapped_data)}")
        if isinstance(unwrapped_data, dict):
            print(f"🔍 forensic_investigation JUDGE UNWRAPPED DATA KEYS: {list(unwrapped_data.keys())}")
        elif isinstance(unwrapped_data, list):
            print(f"🔍 forensic_investigation JUDGE UNWRAPPED DATA LENGTH: {len(unwrapped_data)}")
            if unwrapped_data:
                print(f"🔍 forensic_investigation JUDGE UNWRAPPED DATA FIRST ITEM: {unwrapped_data[0]}")
                print(f"🔍 forensic_investigation JUDGE UNWRAPPED DATA FIRST ITEM TYPE: {type(unwrapped_data[0])}")
        
        # Handle different result types
        nodes_found = False
        edges_found = False
        
        if isinstance(unwrapped_data, dict):
            # Check if it's a nodes/edges result
            if 'nodes' in unwrapped_data:
                nodes_found = True
                issues.extend(self._validate_nodes(unwrapped_data['nodes']))
            if 'edges' in unwrapped_data:
                edges_found = True
            # Check if it's a stats result (no nodes to validate)
            elif 'total_nodes' in unwrapped_data:
                # Stats results don't have nodes, so they pass by default
                pass
            else:
                issues.append("Result structure not recognized")
        
        elif isinstance(unwrapped_data, list):
            # Handle list of nodes directly
            nodes_found = True
            issues.extend(self._validate_nodes(unwrapped_data))
        
        else:
            issues.append(f"Unexpected result type: {type(unwrapped_data)}")
        
        # Determine verdict based on issues found
        verdict = "pass" if len(issues) == 0 else "revise"
        
        return {
            "verdict": verdict,
            "issues": issues
        }
    
    def _validate_nodes(self, nodes: List[Dict[str, Any]]) -> List[str]:
        """
        Validate a list of nodes for evidence completeness.
        
        Args:
            nodes: List of node dictionaries
            
        Returns:
            List of validation issues found
        """
        issues = []
        
        if not isinstance(nodes, list):
            return ["Nodes field is not a list"]
        
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                issues.append(f"Node {i} is not a dictionary")
                continue
            
            # Get node ID for better error reporting
            node_id = node.get('id', f'Node {i}')
            
            # Check for evidence field
            if 'evidence' not in node:
                issues.append(f"Node {node_id} is missing the 'evidence' field.")
                continue
            
            evidence = node['evidence']
            
            # Check if evidence is a dictionary
            if not isinstance(evidence, dict):
                issues.append(f"Node {node_id} has evidence field that is not a dictionary.")
                continue
            
            # Check for required evidence fields
            missing_fields = []
            for field in self.required_evidence_fields:
                if field not in evidence:
                    missing_fields.append(field)
            
            if missing_fields:
                issues.append(f"Node {node_id} has an incomplete evidence field: missing {', '.join(missing_fields)}.")
                continue
            
            # Validate individual evidence fields
            for field in self.required_evidence_fields:
                validation_issue = self.validation_rules[field](evidence[field], node_id)
                if validation_issue:
                    issues.append(validation_issue)
        
        return issues
    
    def _validate_file_field(self, file_value: Any, node_id: str) -> Optional[str]:
        """
        Validate the 'file' field in evidence.
        
        Args:
            file_value: Value of the file field
            node_id: ID of the node for error reporting
            
        Returns:
            Error message if validation fails, None if valid
        """
        if not isinstance(file_value, str):
            return f"Node {node_id} has invalid 'file' field: must be a string"
        
        if not file_value.strip():
            return f"Node {node_id} has empty 'file' field"
        
        return None
    
    def _validate_span_field(self, span_value: Any, node_id: str) -> Optional[str]:
        """
        Validate the 'span' field in evidence.
        
        Args:
            span_value: Value of the span field
            node_id: ID of the node for error reporting
            
        Returns:
            Error message if validation fails, None if valid
        """
        if not isinstance(span_value, dict):
            return f"Node {node_id} has invalid 'span' field: must be a dictionary"
        
        required_span_fields = ['start', 'end']
        missing_fields = [field for field in required_span_fields if field not in span_value]
        
        if missing_fields:
            return f"Node {node_id} has incomplete 'span' field: missing {', '.join(missing_fields)}"
        
        # Validate start and end are integers
        try:
            start = int(span_value['start'])
            end = int(span_value['end'])
            
            if start < 0 or end < 0:
                return f"Node {node_id} has invalid 'span' field: start and end must be non-negative"
            
            if start > end:
                return f"Node {node_id} has invalid 'span' field: start ({start}) cannot be greater than end ({end})"
                
        except (ValueError, TypeError):
            return f"Node {node_id} has invalid 'span' field: start and end must be integers"
        
        return None
    
    def _validate_snippet_field(self, snippet_value: Any, node_id: str) -> Optional[str]:
        """
        Validate the 'snippet' field in evidence.
        
        Args:
            snippet_value: Value of the snippet field
            node_id: ID of the node for error reporting
            
        Returns:
            Error message if validation fails, None if valid
        """
        if not isinstance(snippet_value, str):
            return f"Node {node_id} has invalid 'snippet' field: must be a string"
        
        if not snippet_value.strip():
            return f"Node {node_id} has empty 'snippet' field"
        
        return None
    
    def get_validation_rules(self) -> Dict[str, List[str]]:
        """
        Get information about validation rules.
        
        Returns:
            Dictionary containing validation rules and requirements
        """
        return {
            "required_evidence_fields": self.required_evidence_fields.copy(),
            "validation_rules": list(self.validation_rules.keys())
        }
    
    def validate_single_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single node for evidence completeness.
        
        Args:
            node: Single node dictionary to validate
            
        Returns:
            Dictionary containing verdict and issues for this node
        """
        if not isinstance(node, dict):
            return {
                "verdict": "revise",
                "issues": ["Node is not a dictionary"]
            }
        
        node_id = node.get('id', 'Unknown')
        issues = []
        
        # Check for evidence field
        if 'evidence' not in node:
            issues.append(f"Node {node_id} is missing the 'evidence' field.")
        else:
            evidence = node['evidence']
            
            if not isinstance(evidence, dict):
                issues.append(f"Node {node_id} has evidence field that is not a dictionary.")
            else:
                # Check for required fields
                missing_fields = [field for field in self.required_evidence_fields if field not in evidence]
                if missing_fields:
                    issues.append(f"Node {node_id} has an incomplete evidence field: missing {', '.join(missing_fields)}.")
                else:
                    # Validate individual fields
                    for field in self.required_evidence_fields:
                        validation_issue = self.validation_rules[field](evidence[field], node_id)
                        if validation_issue:
                            issues.append(validation_issue)
        
        return {
            "verdict": "pass" if len(issues) == 0 else "revise",
            "issues": issues
        }
    
    def vibe_review_execution_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review execution result using Vibe Coding: Inner Script + Minimal Validation.
        
        Args:
            result: Result dictionary returned by the Executor
            
        Returns:
            Dictionary containing vibe score, verdict, and detailed issues
        """
        # Extract the actual data for validation
        execution_result = result.get('result', {})
        
        # Perform Vibe Coding validation
        vibe_result = self.vibe_validator.vibe_validate(execution_result)
        
        # Determine verdict based on vibe score
        if vibe_result['vibe_score'] >= 80:
            verdict = "pass"
        elif vibe_result['vibe_score'] >= 60:
            verdict = "revise"
        else:
            verdict = "fail"
        
        return {
            "verdict": verdict,
            "vibe_score": vibe_result['vibe_score'],
            "issues": vibe_result['issues'],
            "validation_type": "vibe_coding",
            "vibe_report": self.vibe_validator.get_vibe_report(execution_result)
        }
