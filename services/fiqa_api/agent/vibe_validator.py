"""
Vibe Coding Validator - Inner Script + Minimal Validation

This module implements Vibe Coding principles with inner script validation
and minimal verification to ensure data integrity without performance overhead.
"""

from typing import Dict, List, Any, Optional, Callable
import re
from pathlib import Path


class VibeValidator:
    """
    Vibe Coding validator that combines inner script validation with minimal verification.
    
    Principles:
    - Inner Script: Internal validation logic embedded in data processing
    - Minimal Validation: Lightweight checks without performance overhead
    """
    
    def __init__(self):
        """Initialize the Vibe validator with minimal validation rules."""
        # Inner script validation functions
        self.inner_scripts = {
            'node_integrity': self._validate_node_integrity,
            'edge_consistency': self._validate_edge_consistency,
            'evidence_completeness': self._validate_evidence_completeness,
            'fqname_format': self._validate_fqname_format
        }
        
        # Minimal validation rules (lightweight checks)
        self.minimal_rules = {
            'required_fields': ['id', 'fqName', 'kind', 'evidence'],
            'evidence_fields': ['file', 'span', 'snippet'],
            'span_format': r'^\d+:\d+$',  # start:end format
            'file_path_pattern': r'^[a-zA-Z0-9_/\.-]+\.py$'
        }
    
    def vibe_validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform Vibe Coding validation with inner script + minimal verification.
        
        Args:
            data: Data to validate (nodes, edges, or complete graph)
            
        Returns:
            Validation result with vibe score and issues
        """
        vibe_score = 100  # Start with perfect vibe
        issues = []
        
        # Inner script validation (embedded logic)
        for script_name, script_func in self.inner_scripts.items():
            try:
                script_result = script_func(data)
                if not script_result['valid']:
                    vibe_score -= script_result['penalty']
                    issues.extend(script_result['issues'])
            except Exception as e:
                vibe_score -= 10
                issues.append(f"Inner script {script_name} failed: {str(e)}")
        
        # Minimal validation (lightweight checks)
        minimal_result = self._minimal_validation(data)
        vibe_score -= minimal_result['penalty']
        issues.extend(minimal_result['issues'])
        
        return {
            'vibe_score': max(0, vibe_score),
            'issues': issues,
            'valid': vibe_score >= 80,  # 80% vibe threshold
            'validation_type': 'vibe_coding'
        }
    
    def _validate_node_integrity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Inner script: Validate node data integrity."""
        issues = []
        penalty = 0
        
        nodes = data.get('nodes', [])
        if not nodes:
            return {'valid': True, 'penalty': 0, 'issues': []}
        
        for i, node in enumerate(nodes):
            # Check node structure
            if not isinstance(node, dict):
                issues.append(f"Node {i} is not a dictionary")
                penalty += 5
                continue
            
            # Check required fields
            for field in self.minimal_rules['required_fields']:
                if field not in node:
                    issues.append(f"Node {i} missing required field: {field}")
                    penalty += 3
        
        return {
            'valid': penalty == 0,
            'penalty': penalty,
            'issues': issues
        }
    
    def _validate_edge_consistency(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Inner script: Validate edge consistency with nodes."""
        issues = []
        penalty = 0
        
        nodes = data.get('nodes', [])
        edges = data.get('edges', [])
        
        if not edges:
            return {'valid': True, 'penalty': 0, 'issues': []}
        
        # Create node ID lookup
        node_ids = {node['id'] for node in nodes if 'id' in node}
        
        for i, edge in enumerate(edges):
            if not isinstance(edge, dict):
                issues.append(f"Edge {i} is not a dictionary")
                penalty += 5
                continue
            
            # Check edge references valid nodes
            from_id = edge.get('from')
            to_id = edge.get('to')
            
            if from_id and from_id not in node_ids:
                issues.append(f"Edge {i} references non-existent node: {from_id}")
                penalty += 2
            
            if to_id and to_id not in node_ids:
                issues.append(f"Edge {i} references non-existent node: {to_id}")
                penalty += 2
        
        return {
            'valid': penalty == 0,
            'penalty': penalty,
            'issues': issues
        }
    
    def _validate_evidence_completeness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Inner script: Validate evidence completeness."""
        issues = []
        penalty = 0
        
        nodes = data.get('nodes', [])
        
        for i, node in enumerate(nodes):
            evidence = node.get('evidence', {})
            if not isinstance(evidence, dict):
                issues.append(f"Node {i} evidence is not a dictionary")
                penalty += 5
                continue
            
            # Check evidence fields
            for field in self.minimal_rules['evidence_fields']:
                if field not in evidence:
                    issues.append(f"Node {i} missing evidence field: {field}")
                    penalty += 3
                elif not evidence[field]:
                    issues.append(f"Node {i} has empty evidence field: {field}")
                    penalty += 2
        
        return {
            'valid': penalty == 0,
            'penalty': penalty,
            'issues': issues
        }
    
    def _validate_fqname_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Inner script: Validate FQName format consistency."""
        issues = []
        penalty = 0
        
        nodes = data.get('nodes', [])
        
        for i, node in enumerate(nodes):
            fqname = node.get('fqName', '')
            if not fqname:
                issues.append(f"Node {i} has empty fqName")
                penalty += 3
                continue
            
            # Check FQName format (module.function or module.class.method)
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_.]*$', fqname):
                issues.append(f"Node {i} has invalid fqName format: {fqname}")
                penalty += 2
        
        return {
            'valid': penalty == 0,
            'penalty': penalty,
            'issues': issues
        }
    
    def _minimal_validation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Minimal validation: Lightweight checks without performance overhead."""
        issues = []
        penalty = 0
        
        # Check data structure
        if not isinstance(data, dict):
            issues.append("Data is not a dictionary")
            penalty += 10
            return {'penalty': penalty, 'issues': issues}
        
        # Check for required top-level fields
        required_top_fields = ['nodes', 'edges', 'indices']
        for field in required_top_fields:
            if field not in data:
                issues.append(f"Missing top-level field: {field}")
                penalty += 5
        
        return {
            'penalty': penalty,
            'issues': issues
        }
    
    def get_vibe_report(self, data: Dict[str, Any]) -> str:
        """Generate a vibe report for the validated data."""
        result = self.vibe_validate(data)
        
        vibe_score = result['vibe_score']
        issues = result['issues']
        
        if vibe_score >= 90:
            vibe_status = "🟢 Excellent Vibe"
        elif vibe_score >= 80:
            vibe_status = "🟡 Good Vibe"
        elif vibe_score >= 70:
            vibe_status = "🟠 Fair Vibe"
        else:
            vibe_status = "🔴 Poor Vibe"
        
        report = f"""
# Vibe Coding Validation Report

**Vibe Score**: {vibe_score}/100 - {vibe_status}

## Issues Found ({len(issues)})
"""
        
        for issue in issues:
            report += f"- {issue}\n"
        
        if not issues:
            report += "- No issues found! 🎉\n"
        
        return report


