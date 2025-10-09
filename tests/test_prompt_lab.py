"""
Fast unit tests for Prompt Lab (<1s with mocks)

All tests use MockProvider - no network calls, no file I/O.
"""

import pytest
import json
from modules.prompt_lab import (
    RewriteInput,
    RewriteOutput,
    MockProvider,
    QueryRewriter,
)
from modules.prompt_lab.contracts import validate, REWRITE_OUTPUT_SCHEMA
from modules.prompt_lab.providers import ProviderConfig


def test_contracts_valid():
    """Test that contracts can be created and validated."""
    input_data = RewriteInput(query="test query", locale="en", time_range="recent")
    assert input_data.query == "test query"
    
    output_data = RewriteOutput(
        topic="test",
        entities=["entity1"],
        time_range=None,
        query_rewrite="test",
        filters={"date_from": None, "date_to": None}
    )
    
    # Validate against schema
    assert validate(output_data.to_dict()) is True


def test_json_schema_validation():
    """Test JSON schema validation with valid and invalid data."""
    # Valid data
    valid = {
        "topic": "tech",
        "entities": ["AI", "ML"],
        "time_range": None,
        "query_rewrite": "artificial intelligence",
        "filters": {"date_from": None, "date_to": None}
    }
    assert validate(valid) is True
    
    # Invalid: missing required field
    invalid = {
        "topic": "tech",
        "entities": ["AI"],
        "query_rewrite": "test"
        # Missing filters
    }
    with pytest.raises(Exception):  # jsonschema.ValidationError
        validate(invalid)
    
    # Invalid: extra field
    invalid_extra = {
        "topic": "tech",
        "entities": ["AI"],
        "time_range": None,
        "query_rewrite": "test",
        "filters": {"date_from": None, "date_to": None},
        "extra_field": "not allowed"
    }
    with pytest.raises(Exception):  # jsonschema.ValidationError
        validate(invalid_extra)


def test_mock_provider_deterministic():
    """Test that MockProvider returns deterministic results."""
    provider = MockProvider()
    messages = [{"role": "user", "content": "test"}]
    
    result1 = provider.rewrite(messages, mode="json")
    result2 = provider.rewrite(messages, mode="json")
    
    assert result1 == result2
    assert provider.get_call_count() == 2


def test_json_mode_valid():
    """Test JSON mode with valid mock response."""
    provider = MockProvider(response_override={
        "topic": "machine learning",
        "entities": ["Python", "TensorFlow"],
        "time_range": None,
        "query_rewrite": "machine learning with Python and TensorFlow",
        "filters": {"date_from": None, "date_to": None}
    })
    
    rewriter = QueryRewriter(provider)
    input_data = RewriteInput(query="ML with Python")
    
    result = rewriter.rewrite(input_data, mode="json")
    
    assert isinstance(result, RewriteOutput)
    assert result.topic == "machine learning"
    assert "Python" in result.entities
    assert result.filters["date_from"] is None


def test_function_calling_valid():
    """Test function calling mode with valid mock response."""
    provider = MockProvider(response_override={
        "topic": "scientific research",
        "entities": ["COVID-19", "vaccine"],
        "time_range": "2023",
        "query_rewrite": "COVID-19 vaccine research 2023",
        "filters": {"date_from": "2023-01-01", "date_to": "2023-12-31"}
    })
    
    rewriter = QueryRewriter(provider)
    input_data = RewriteInput(query="covid vaccine research", time_range="2023")
    
    result = rewriter.rewrite(input_data, mode="function")
    
    assert isinstance(result, RewriteOutput)
    assert result.topic == "scientific research"
    assert result.time_range == "2023"
    assert result.filters["date_from"] == "2023-01-01"


def test_invalid_then_retry_repairs():
    """Test retry logic when first response is invalid."""
    
    class RetryMockProvider(MockProvider):
        def __init__(self):
            super().__init__()
            self.attempt = 0
        
        def rewrite(self, messages, mode="json"):
            self.attempt += 1
            if self.attempt == 1:
                # First attempt: invalid (missing filters)
                return {
                    "topic": "test",
                    "entities": ["foo"],
                    "time_range": None,
                    "query_rewrite": "test query"
                }
            else:
                # Second attempt: valid
                return {
                    "topic": "test",
                    "entities": ["foo"],
                    "time_range": None,
                    "query_rewrite": "test query",
                    "filters": {"date_from": None, "date_to": None}
                }
    
    provider = RetryMockProvider()
    rewriter = QueryRewriter(provider)
    input_data = RewriteInput(query="test")
    
    # Should succeed after retry
    result = rewriter.rewrite(input_data, mode="json", max_retries=1)
    
    assert isinstance(result, RewriteOutput)
    assert result.topic == "test"
    assert provider.attempt == 2  # Two attempts


def test_normalization():
    """Test entity and text normalization."""
    provider = MockProvider(response_override={
        "topic": "  machine learning  ",
        "entities": ["  Python  ", "  TensorFlow  ", "", "   "],
        "time_range": "   ",
        "query_rewrite": "  ML query  ",
        "filters": {"date_from": None, "date_to": None}
    })
    
    rewriter = QueryRewriter(provider)
    input_data = RewriteInput(query="test")
    
    result = rewriter.rewrite(input_data, mode="json")
    
    # Check normalization
    assert result.topic == "machine learning"  # Trimmed
    assert result.entities == ["Python", "TensorFlow"]  # Trimmed, empty removed
    assert result.time_range is None  # Empty string -> None
    assert result.query_rewrite == "ML query"  # Trimmed


def test_no_io():
    """Test that QueryRewriter core does not perform I/O."""
    # Use MockProvider which has no I/O
    provider = MockProvider()
    rewriter = QueryRewriter(provider)
    
    # Should work without any environment variables or file access
    input_data = RewriteInput(query="test query")
    result = rewriter.rewrite(input_data, mode="json")
    
    assert isinstance(result, RewriteOutput)
    # No exceptions means no I/O attempted


def test_build_messages():
    """Test message building with context."""
    provider = MockProvider()
    rewriter = QueryRewriter(provider)
    
    input_data = RewriteInput(
        query="最新的AI发展", 
        locale="zh-CN", 
        time_range="最近一周"
    )
    
    messages = rewriter.build_messages(input_data)
    
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "JSON" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    
    # User content should contain query data
    user_data = json.loads(messages[1]["content"])
    assert user_data["query"] == "最新的AI发展"
    assert user_data["locale"] == "zh-CN"


def test_invalid_mode_raises():
    """Test that invalid mode raises ValueError."""
    provider = MockProvider()
    rewriter = QueryRewriter(provider)
    input_data = RewriteInput(query="test")
    
    with pytest.raises(ValueError, match="Invalid mode"):
        rewriter.rewrite(input_data, mode="invalid_mode")


def test_max_retries_exceeded():
    """Test that max retries exceeded raises final error."""
    
    class AlwaysInvalidProvider(MockProvider):
        def rewrite(self, messages, mode="json"):
            # Always return invalid data
            return {"invalid": "data"}
    
    provider = AlwaysInvalidProvider()
    rewriter = QueryRewriter(provider)
    input_data = RewriteInput(query="test")
    
    # Should fail after retries
    with pytest.raises(Exception):
        rewriter.rewrite(input_data, mode="json", max_retries=1)
