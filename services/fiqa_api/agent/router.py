"""
Router Component for Agent's Runtime

This module provides the Router class that takes raw user queries and classifies
them into structured, machine-readable commands for the Planner to use.
"""

import re
from typing import Dict, Optional


class Router:
    """
    Router class that classifies user queries into structured commands.
    
    The Router is the entry point for the Agent's decision-making process,
    taking natural language queries and converting them into structured
    commands that can be processed by downstream components.
    """
    
    def __init__(self):
        """
        Initialize the Router with predefined patterns for query classification.
        """
        # Define patterns for different query types
        self.patterns = {
            'overview': re.compile(r'^#overview\s*$', re.IGNORECASE),
            'file': re.compile(r'^#file\s+(.+)$', re.IGNORECASE),
            'function': re.compile(r'^#func\s+(.+)$', re.IGNORECASE),
        }
        
        # Alternative patterns for more natural language support
        self.natural_patterns = {
            'overview': [
                re.compile(r'^(show|give|provide)\s+(me\s+)?(a\s+)?(overview|summary|overall\s+view)', re.IGNORECASE),
                re.compile(r'^(what|how)\s+(is|does)\s+(the\s+)?(repository|codebase|project)', re.IGNORECASE),
                re.compile(r'^(repository|codebase|project)\s+(overview|summary)', re.IGNORECASE),
                re.compile(r'^(overview|summary)', re.IGNORECASE),
            ],
            'file': [
                re.compile(r'^(analyze|examine|look\s+at|show)\s+(the\s+)?(file|code)\s+(at\s+)?(.+)$', re.IGNORECASE),
                re.compile(r'^(what|how)\s+(is|does)\s+(the\s+)?(file|code)\s+(at\s+)?(.+)$', re.IGNORECASE),
            ],
            'function': [
                re.compile(r'^(analyze|examine|look\s+at|show)\s+(the\s+)?(function|method)\s+(.+)$', re.IGNORECASE),
                re.compile(r'^(what|how)\s+(is|does)\s+(the\s+)?(function|method)\s+(.+)$', re.IGNORECASE),
            ]
        }
    
    def route_query(self, query: str) -> Dict[str, str]:
        """
        Route a user query to determine the intent and extract parameters.
        
        Args:
            query: Raw user query string
            
        Returns:
            Dictionary with structured command information
        """
        if not query or not query.strip():
            return {
                'type': 'error',
                'error': 'Empty query provided.'
            }
        
        # Clean the query
        query = query.strip()
        
        # First, try exact tag-based patterns
        result = self._match_tag_patterns(query)
        if result['type'] != 'unknown':
            return result
        
        # Then try natural language patterns
        result = self._match_natural_patterns(query)
        if result['type'] != 'unknown':
            return result
        
        # If no pattern matches, return unknown
        return {
            'type': 'unknown',
            'error': 'Query does not match any known pattern.'
        }
    
    def _match_tag_patterns(self, query: str) -> Dict[str, str]:
        """
        Match query against tag-based patterns (#overview, #file, #func).
        
        Args:
            query: Query string to match
            
        Returns:
            Dictionary with routing result
        """
        # Check overview pattern
        if self.patterns['overview'].match(query):
            return {'type': 'overview'}
        
        # Check file pattern
        file_match = self.patterns['file'].match(query)
        if file_match:
            file_path = file_match.group(1).strip()
            if file_path:
                return {
                    'type': 'file',
                    'target': file_path
                }
        
        # Check function pattern
        func_match = self.patterns['function'].match(query)
        if func_match:
            func_name = func_match.group(1).strip()
            if func_name:
                return {
                    'type': 'function',
                    'target': func_name
                }
        
        return {'type': 'unknown'}
    
    def _match_natural_patterns(self, query: str) -> Dict[str, str]:
        """
        Match query against natural language patterns.
        
        Args:
            query: Query string to match
            
        Returns:
            Dictionary with routing result
        """
        # Check overview patterns
        for pattern in self.natural_patterns['overview']:
            if pattern.match(query):
                return {'type': 'overview'}
        
        # Check file patterns
        for pattern in self.natural_patterns['file']:
            match = pattern.match(query)
            if match:
                # Extract file path from the last group
                file_path = match.groups()[-1].strip()
                if file_path:
                    return {
                        'type': 'file',
                        'target': file_path
                    }
        
        # Check function patterns
        for pattern in self.natural_patterns['function']:
            match = pattern.match(query)
            if match:
                # Extract function name from the last group
                func_name = match.groups()[-1].strip()
                if func_name:
                    return {
                        'type': 'function',
                        'target': func_name
                    }
        
        return {'type': 'unknown'}
    
    def get_supported_intents(self) -> Dict[str, list]:
        """
        Get information about supported query intents and their patterns.
        
        Returns:
            Dictionary mapping intent types to example patterns
        """
        return {
            'overview': [
                '#overview',
                'show me an overview',
                'what is the repository',
                'repository overview'
            ],
            'file': [
                '#file src/api/routes.py',
                'analyze the file at src/api/routes.py',
                'examine the code at services/main.py'
            ],
            'function': [
                '#func my_app.utils.helpers.clean_data',
                'analyze the function clean_data',
                'examine the method process_data'
            ]
        }
    
    def validate_target(self, intent_type: str, target: str) -> bool:
        """
        Validate that a target parameter is reasonable for the given intent type.
        
        Args:
            intent_type: Type of intent ('file' or 'function')
            target: Target parameter to validate
            
        Returns:
            True if target appears valid, False otherwise
        """
        if not target or not target.strip():
            return False
        
        target = target.strip()
        
        if intent_type == 'file':
            # Basic file path validation
            # Should not contain certain characters and should look like a path
            if any(char in target for char in ['<', '>', '|', '*', '?']):
                return False
            # Should have some path-like structure
            return '.' in target or '/' in target or '\\' in target
        
        elif intent_type == 'function':
            # Basic function name validation
            # Should contain dots (for module.function) or be a simple identifier
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_.]*$', target):
                return False
            return True
        
        return True
