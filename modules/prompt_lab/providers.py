"""
Provider Abstraction Layer

Interface for LLM providers with mock implementation for testing.
Zero external dependencies in core (no API keys required).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ProviderConfig:
    """Configuration for LLM provider."""
    temperature: float = 0.0
    max_tokens: int = 500
    model: str = "gpt-4o-mini"


class RewriterProvider(ABC):
    """Abstract interface for query rewriting providers."""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
    
    @abstractmethod
    def rewrite(self, messages: List[Dict[str, str]], mode: str = "json") -> Dict[str, Any]:
        """
        Execute rewrite using specified mode.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            mode: Either 'json' or 'function'
            
        Returns:
            Dict containing the structured output
        """
        pass


class MockProvider(RewriterProvider):
    """
    Deterministic mock provider for testing.
    Returns fixed structured outputs with no network calls.
    """
    
    def __init__(self, config: ProviderConfig = None, response_override: Optional[Dict[str, Any]] = None):
        super().__init__(config or ProviderConfig())
        self._response_override = response_override
        self._call_count = 0
    
    def rewrite(self, messages: List[Dict[str, str]], mode: str = "json") -> Dict[str, Any]:
        """Return deterministic mock response."""
        self._call_count += 1
        
        if self._response_override:
            return self._response_override
        
        # Extract query from messages for smart mock
        query = "test query"
        for msg in messages:
            if msg.get("role") == "user" and "query" in msg.get("content", "").lower():
                # Try to extract actual query
                content = msg.get("content", "")
                if '"query":' in content:
                    import json
                    try:
                        data = json.loads(content)
                        query = data.get("query", query)
                    except:
                        pass
        
        # Default valid response
        return {
            "topic": "general inquiry",
            "entities": ["test", "mock"],
            "time_range": None,
            "query_rewrite": query,
            "filters": {
                "date_from": None,
                "date_to": None
            }
        }
    
    def get_call_count(self) -> int:
        """Get number of times rewrite was called."""
        return self._call_count


class OpenAIProvider(RewriterProvider):
    """
    OpenAI-compatible provider adapter.
    Requires API key only when actually used (not in unit tests).
    """
    
    def __init__(self, config: ProviderConfig, api_key: Optional[str] = None):
        super().__init__(config)
        self._api_key = api_key
        self._client = None
    
    def _ensure_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self._api_key)
            except ImportError:
                raise ImportError("openai package required for OpenAIProvider. Install with: pip install openai")
    
    def rewrite(self, messages: List[Dict[str, str]], mode: str = "json") -> Dict[str, Any]:
        """
        Call OpenAI API with specified mode.
        
        Args:
            messages: Chat messages
            mode: 'json' for JSON Mode, 'function' for Function Calling
            
        Returns:
            Structured output dict
        """
        self._ensure_client()
        
        import json
        
        if mode == "json":
            # [CORE: json-mode] - Use response_format for JSON Mode
            response = self._client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return json.loads(content)
        
        elif mode == "function":
            # [CORE: function-calling] - Use tools/function calling
            tools = [{
                "type": "function",
                "function": {
                    "name": "rewrite_query",
                    "description": "Rewrite and analyze a search query",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string", "description": "Main topic of the query"},
                            "entities": {"type": "array", "items": {"type": "string"}, "description": "Named entities"},
                            "time_range": {"type": "string", "description": "Time range if any", "nullable": True},
                            "query_rewrite": {"type": "string", "description": "Rewritten query"},
                            "filters": {
                                "type": "object",
                                "properties": {
                                    "date_from": {"type": "string", "nullable": True},
                                    "date_to": {"type": "string", "nullable": True}
                                },
                                "required": ["date_from", "date_to"]
                            }
                        },
                        "required": ["topic", "entities", "time_range", "query_rewrite", "filters"]
                    }
                }
            }]
            
            response = self._client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "rewrite_query"}}
            )
            
            tool_call = response.choices[0].message.tool_calls[0]
            return json.loads(tool_call.function.arguments)
        
        else:
            raise ValueError(f"Unknown mode: {mode}. Use 'json' or 'function'")
