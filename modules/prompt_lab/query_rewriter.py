"""
[CORE] Query Rewriter with Structured Output

Implements JSON Mode and Function Calling with schema validation and retry logic.
Pure logic with no I/O - provider handles network calls.
"""

import json
import re
from typing import Dict, Any, List, Optional
from .contracts import RewriteInput, RewriteOutput, validate, from_dict
from .providers import RewriterProvider, ProviderConfig


class QueryRewriter:
    """
    Query rewriter with structured output support.
    
    Features:
    - JSON Mode and Function Calling
    - Schema validation with retry-repair
    - Entity and time range normalization
    - Zero I/O in core logic
    """
    
    # [CORE: role-prompt] - System prompt for structured output
    SYSTEM_PROMPT = """You are a query analysis expert. Analyze the user's search query and extract:
- topic: The main subject or intent
- entities: Named entities (people, places, organizations, products, etc.)
- time_range: Any temporal context (e.g., "last week", "2023", "recent")
- query_rewrite: An optimized version of the query for search
- filters: Structured date filters (date_from, date_to in YYYY-MM-DD or null)

Always respond with valid JSON matching this exact structure:
{
  "topic": "string",
  "entities": ["string"],
  "time_range": "string or null",
  "query_rewrite": "string",
  "filters": {
    "date_from": "YYYY-MM-DD or null",
    "date_to": "YYYY-MM-DD or null"
  }
}

Do not include any text outside the JSON object."""
    
    def __init__(self, provider: RewriterProvider, config: Optional[ProviderConfig] = None):
        """
        Initialize query rewriter.
        
        Args:
            provider: LLM provider implementation
            config: Provider configuration (optional, provider may have its own)
        """
        self.provider = provider
        self.config = config or ProviderConfig()
    
    def build_messages(self, input_data: RewriteInput) -> List[Dict[str, str]]:
        """
        [CORE: role-prompt] - Build message array with context.
        
        Args:
            input_data: Query rewrite input
            
        Returns:
            List of messages for LLM
        """
        user_content = json.dumps({
            "query": input_data.query,
            "locale": input_data.locale,
            "time_range": input_data.time_range
        }, ensure_ascii=False)
        
        return [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]
    
    def _strip_code_fences(self, text: str) -> str:
        """
        Remove markdown code fences and extra text.
        
        Args:
            text: Raw response text
            
        Returns:
            Cleaned JSON string
        """
        # Remove ```json ... ``` or ``` ... ```
        text = re.sub(r'^```(?:json)?\s*\n', '', text.strip())
        text = re.sub(r'\n```\s*$', '', text.strip())
        
        # Find JSON object boundaries
        start = text.find('{')
        end = text.rfind('}')
        if start >= 0 and end >= 0:
            text = text[start:end+1]
        
        return text.strip()
    
    def call_json_mode(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        [CORE: json-mode] - Call provider with JSON Mode.
        
        Args:
            messages: Chat messages
            
        Returns:
            Parsed JSON response
        """
        response = self.provider.rewrite(messages, mode="json")
        
        # Handle both dict and string responses
        if isinstance(response, str):
            cleaned = self._strip_code_fences(response)
            return json.loads(cleaned)
        
        return response
    
    def call_function_calling(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        [CORE: function-calling] - Call provider with Function Calling.
        
        Args:
            messages: Chat messages
            
        Returns:
            Parsed function arguments
        """
        response = self.provider.rewrite(messages, mode="function")
        
        # Handle both dict and string responses
        if isinstance(response, str):
            cleaned = self._strip_code_fences(response)
            return json.loads(cleaned)
        
        return response
    
    def _normalize_output(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        [CORE: normalize] - Normalize and clean output data.
        
        Args:
            data: Raw output dict
            
        Returns:
            Normalized output dict
        """
        normalized = data.copy()
        
        # Normalize entities: trim whitespace, remove empty strings
        if "entities" in normalized:
            entities = normalized["entities"]
            if isinstance(entities, list):
                normalized["entities"] = [
                    e.strip() for e in entities 
                    if isinstance(e, str) and e.strip()
                ]
        
        # Normalize topic: trim whitespace
        if "topic" in normalized and isinstance(normalized["topic"], str):
            normalized["topic"] = normalized["topic"].strip()
        
        # Normalize query_rewrite: trim whitespace
        if "query_rewrite" in normalized and isinstance(normalized["query_rewrite"], str):
            normalized["query_rewrite"] = normalized["query_rewrite"].strip()
        
        # Normalize time_range: trim or set to None
        if "time_range" in normalized:
            tr = normalized["time_range"]
            if isinstance(tr, str):
                tr = tr.strip()
                normalized["time_range"] = tr if tr else None
            elif tr is None:
                pass
            else:
                normalized["time_range"] = None
        
        return normalized
    
    def rewrite(self, input_data: RewriteInput, mode: str = "json", max_retries: int = 1) -> RewriteOutput:
        """
        [CORE: schema-validate] [CORE: retry-repair] - Execute query rewrite with validation.
        
        Args:
            input_data: Input query data
            mode: Either 'json' or 'function'
            max_retries: Number of retry attempts if validation fails
            
        Returns:
            Validated and normalized RewriteOutput
            
        Raises:
            ValueError: If mode is invalid
            jsonschema.ValidationError: If output fails validation after retries
        """
        if mode not in ["json", "function"]:
            raise ValueError(f"Invalid mode: {mode}. Use 'json' or 'function'")
        
        messages = self.build_messages(input_data)
        attempt = 0
        last_error = None
        
        while attempt <= max_retries:
            try:
                # Call provider with appropriate mode
                if mode == "json":
                    raw_output = self.call_json_mode(messages)
                else:
                    raw_output = self.call_function_calling(messages)
                
                # [CORE: normalize] - Apply normalization
                normalized = self._normalize_output(raw_output)
                
                # [CORE: schema-validate] - Validate against schema
                output = from_dict(normalized)
                return output
                
            except Exception as e:
                last_error = e
                attempt += 1
                
                if attempt <= max_retries:
                    # [CORE: retry-repair] - Add repair hint and retry
                    repair_hint = f"""The previous response had an error: {str(e)}

Please ensure your response:
1. Is valid JSON matching the exact schema
2. Has all required fields: topic, entities, time_range, query_rewrite, filters
3. filters must have date_from and date_to (can be null)
4. No extra fields (additionalProperties not allowed)

Try again with the same query:"""
                    
                    messages.append({
                        "role": "assistant",
                        "content": json.dumps(raw_output) if 'raw_output' in locals() else "{}"
                    })
                    messages.append({
                        "role": "user",
                        "content": repair_hint
                    })
                else:
                    # Max retries exceeded
                    raise last_error
        
        # Should never reach here
        raise last_error or Exception("Unknown error in rewrite")
