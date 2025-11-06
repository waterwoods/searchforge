"""
Explainer Component for Agent's Runtime

This module provides the Explainer class that generates human-readable explanations
of code graph data using Large Language Model capabilities. The Explainer acts as
an intelligence layer that interprets validated graph data and produces structured
Markdown summaries.
"""

from typing import Dict, List, Any, Optional
import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from openai import APIError


class Explainer:
    """
    Explainer class that generates human-readable explanations from graph data.
    
    The Explainer is responsible for taking validated data from the Judge and
    using LLM capabilities to generate comprehensive Markdown summaries that
    explain the code structure, relationships, and architectural insights.
    """
    
    def __init__(self):
        """
        Initialize the Explainer with configuration for LLM interactions.
        """
        # Load environment variables from .env file
        load_dotenv()
        
        # Configuration for explanation generation
        self.max_nodes_for_detailed_analysis = 50
        self.max_edges_for_relationship_analysis = 100
        
        # Initialize OpenAI client
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model_name = os.getenv('CODE_LOOKUP_LLM_MODEL', 'gpt-4o-mini')
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Template for LLM prompts
        self.prompt_template = """
You are a senior principal software architect with extensive experience in analyzing complex codebases. 
Your task is to provide a comprehensive architectural analysis of the provided code graph data.

Graph Data (JSON format):
{graph_data}

As a senior principal software architect, please analyze this codebase and provide insights covering:

1. **Architecture Overview**: High-level architectural patterns, design principles, and structural organization
2. **Key Components**: Critical modules, classes, functions, and their roles in the system
3. **Entry Points & Flow**: Main entry points, execution flows, and how components interact
4. **Dependencies & Relationships**: Critical dependency chains, coupling analysis, and integration patterns
5. **Architecture Patterns**: Identified design patterns, architectural decisions, and their implications
6. **Complexity Assessment**: Code complexity analysis, potential bottlenecks, and maintainability concerns
7. **Risk Analysis**: Potential architectural risks, technical debt, and areas of concern
8. **Recommendations**: Strategic recommendations for improvement, refactoring opportunities, and best practices

Please provide your analysis in clean, well-structured Markdown format with clear sections and actionable insights.
Focus on architectural perspective rather than just code-level details.
"""
    
    def generate_explanation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a human-readable explanation from graph data using OpenAI API.
        
        Args:
            data: Dictionary containing validated graph data (nodes and edges)
            
        Returns:
            Dictionary containing explanation text and usage metadata
        """
        try:
            # Extract nodes and edges from the data
            nodes = self._extract_nodes(data)
            edges = self._extract_edges(data)
            
            # Prepare graph data for the LLM
            graph_data = {
                "nodes": nodes,
                "edges": edges,
                "summary": {
                    "total_nodes": len(nodes),
                    "total_edges": len(edges),
                    "node_types": self._get_node_type_distribution(nodes),
                    "languages": self._get_language_distribution(nodes)
                }
            }
            
            # Generate analysis using OpenAI API
            return self._call_openai_api(graph_data)
                
        except APIError as e:
            # Return error explanation with zero usage for API errors
            return {
                'explanation': self._generate_api_error_explanation(str(e)),
                'usage': None
            }
        except Exception as e:
            # Return error explanation with zero usage for other errors
            return {
                'explanation': self._generate_error_explanation(str(e)),
                'usage': None
            }
    
    def _extract_nodes(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract nodes from the data structure.
        
        Args:
            data: Input data dictionary
            
        Returns:
            List of node dictionaries
        """
        if isinstance(data, dict):
            if 'nodes' in data:
                return data['nodes']
            elif 'result' in data and isinstance(data['result'], dict) and 'nodes' in data['result']:
                return data['result']['nodes']
            elif 'result' in data and isinstance(data['result'], list):
                return data['result']
        elif isinstance(data, list):
            return data
        
        return []
    
    def _extract_edges(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract edges from the data structure.
        
        Args:
            data: Input data dictionary
            
        Returns:
            List of edge dictionaries
        """
        if isinstance(data, dict):
            if 'edges' in data:
                return data['edges']
            elif 'result' in data and isinstance(data['result'], dict) and 'edges' in data['result']:
                return data['result']['edges']
        
        return []
    
    def _call_openai_api(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make API call to OpenAI to generate explanation.
        
        Args:
            graph_data: Prepared graph data dictionary
            
        Returns:
            Dictionary containing explanation text and usage metadata
        """
        try:
            # Format the graph data as JSON string
            graph_data_json = json.dumps(graph_data, indent=2)
            
            # Create the prompt
            prompt = self.prompt_template.format(graph_data=graph_data_json)
            
            # Make the API call
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior principal software architect with expertise in code analysis and architectural design."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            # Extract both content and usage data
            explanation = response.choices[0].message.content.strip()
            usage = response.usage
            
            return {
                'explanation': explanation,
                'usage': usage
            }
            
        except APIError as e:
            raise e
        except Exception as e:
            raise Exception(f"Unexpected error during OpenAI API call: {str(e)}")
    
    def _get_node_type_distribution(self, nodes: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Get distribution of node types.
        
        Args:
            nodes: List of node dictionaries
            
        Returns:
            Dictionary mapping node types to counts
        """
        distribution = {}
        for node in nodes:
            kind = node.get('kind', 'unknown')
            distribution[kind] = distribution.get(kind, 0) + 1
        return distribution
    
    def _get_language_distribution(self, nodes: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Get distribution of programming languages.
        
        Args:
            nodes: List of node dictionaries
            
        Returns:
            Dictionary mapping languages to counts
        """
        distribution = {}
        for node in nodes:
            language = node.get('language', 'unknown')
            distribution[language] = distribution.get(language, 0) + 1
        return distribution
    
    def _generate_api_error_explanation(self, error_message: str) -> str:
        """
        Generate an explanation when an OpenAI API error occurs.
        
        Args:
            error_message: Error message from the API
            
        Returns:
            Error explanation in Markdown format
        """
        return f"""# OpenAI API Error

## Issue

An error occurred while calling the OpenAI API:

```
{error_message}
```

## Possible Causes

1. **Invalid API Key**: The OPENAI_API_KEY environment variable may be incorrect or missing
2. **Network Issues**: Connection problems preventing API access
3. **Model Unavailable**: The specified model ({self.model_name}) may not be available
4. **Rate Limiting**: API rate limits may have been exceeded
5. **Quota Exceeded**: API usage quota may have been reached

## Next Steps

1. Verify your OpenAI API key is correct and active
2. Check your internet connection
3. Ensure the model name is valid and accessible
4. Check your OpenAI account usage and billing
5. Retry the analysis after resolving the issue

---

*Please contact your system administrator if this error persists.*
"""
    
    
    
    def _generate_error_explanation(self, error_message: str) -> str:
        """
        Generate an explanation when an error occurs.
        
        Args:
            error_message: Error message from the analysis
            
        Returns:
            Error explanation in Markdown format
        """
        return f"""# Analysis Error

## Issue

An error occurred while analyzing the code graph:

```
{error_message}
```

## Next Steps

1. Verify the input data format
2. Check that all required fields are present
3. Retry the analysis with corrected data

---

*Please contact the system administrator if this error persists.*
"""
    
    def _detect_circular_dependencies(self, edges: List[Dict[str, Any]]) -> int:
        """
        Detect potential circular dependencies in the edge list.
        
        Args:
            edges: List of edge dictionaries
            
        Returns:
            Number of potential circular dependencies
        """
        # Simple heuristic: count edges where source and target might create cycles
        # This is a simplified implementation for demonstration
        cycles = 0
        edge_map = {}
        
        for edge in edges:
            source = edge.get('source', '')
            target = edge.get('target', '')
            if source and target:
                if target in edge_map and edge_map[target] == source:
                    cycles += 1
                edge_map[source] = target
        
        return cycles
    
    def _calculate_average_complexity(self, nodes: List[Dict[str, Any]]) -> float:
        """
        Calculate average complexity across all nodes.
        
        Args:
            nodes: List of node dictionaries
            
        Returns:
            Average complexity value
        """
        total_complexity = 0
        nodes_with_complexity = 0
        
        for node in nodes:
            complexity = node.get('metrics', {}).get('complexity', 0)
            if complexity > 0:
                total_complexity += complexity
                nodes_with_complexity += 1
        
        return total_complexity / nodes_with_complexity if nodes_with_complexity > 0 else 0.0
    
    def get_explanation_config(self) -> Dict[str, Any]:
        """
        Get configuration information about the Explainer.
        
        Returns:
            Dictionary containing configuration details
        """
        return {
            "max_nodes_for_detailed_analysis": self.max_nodes_for_detailed_analysis,
            "max_edges_for_relationship_analysis": self.max_edges_for_relationship_analysis,
            "supported_data_formats": ["nodes_and_edges", "execution_result", "node_list"],
            "output_format": "markdown",
            "llm_provider": "openai",
            "model_name": self.model_name,
            "api_key_configured": bool(self.api_key)
        }
