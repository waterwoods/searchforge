"""
test_nl_to_intent.py - Unit tests for nl_to_intent module

Tests the LLM-based NL parsing with mocking to avoid real API calls.
"""

import pytest
import json
from unittest.mock import patch, MagicMock

from services.fiqa_api.ecommerce.nl_to_intent import (
    parse_user_message,
    EcommerceNLParseResult,
    EcommerceNLParseError,
)


def test_parse_user_message_refund_damaged():
    """Test parsing a refund request for damaged item with order ID."""
    user_message = "I received a broken mug for order A10001, I want a refund."
    
    # Mock LLM response
    mock_response = {
        "intent": "refund",
        "order_id": "A10001",
        "reason_type": "DAMAGED_OR_DEFECTIVE",
        "reason_description": "Broken mug"
    }
    
    mock_llm_response = MagicMock()
    mock_llm_response.choices = [MagicMock()]
    mock_llm_response.choices[0].message.content = json.dumps(mock_response)
    
    with patch("services.fiqa_api.ecommerce.nl_to_intent.get_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_llm_response
        mock_get_client.return_value = mock_client
        
        result = parse_user_message(user_message)
        
        assert result.intent == "refund"
        assert result.order_id == "A10001"
        assert result.reason_type == "DAMAGED_OR_DEFECTIVE"
        assert result.reason_description == "Broken mug"


def test_parse_user_message_return_change_of_mind():
    """Test parsing a return request due to change of mind."""
    user_message = "I changed my mind about order A10002, can I return it?"
    
    # Mock LLM response
    mock_response = {
        "intent": "return",
        "order_id": "A10002",
        "reason_type": "NO_LONGER_WANTED",
        "reason_description": "Changed my mind"
    }
    
    mock_llm_response = MagicMock()
    mock_llm_response.choices = [MagicMock()]
    mock_llm_response.choices[0].message.content = json.dumps(mock_response)
    
    with patch("services.fiqa_api.ecommerce.nl_to_intent.get_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_llm_response
        mock_get_client.return_value = mock_client
        
        result = parse_user_message(user_message)
        
        assert result.intent in ["refund", "return"]  # Either is acceptable
        assert result.order_id == "A10002"
        assert result.reason_type == "NO_LONGER_WANTED"


def test_parse_user_message_other_intent():
    """Test parsing a message that doesn't match refund/return/exchange."""
    user_message = "Where is my order?"
    
    # Mock LLM response
    mock_response = {
        "intent": "other",
        "order_id": None,
        "reason_type": None,
        "reason_description": None
    }
    
    mock_llm_response = MagicMock()
    mock_llm_response.choices = [MagicMock()]
    mock_llm_response.choices[0].message.content = json.dumps(mock_response)
    
    with patch("services.fiqa_api.ecommerce.nl_to_intent.get_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_llm_response
        mock_get_client.return_value = mock_client
        
        result = parse_user_message(user_message)
        
        assert result.intent == "other"
        assert result.order_id is None
        assert result.reason_type is None


def test_parse_user_message_with_default_order_id():
    """Test that default_order_id is used when not found in message."""
    user_message = "I want a refund for a damaged item"
    default_order_id = "A10003"
    
    # Mock LLM response (no order_id extracted)
    mock_response = {
        "intent": "refund",
        "order_id": None,
        "reason_type": "DAMAGED_OR_DEFECTIVE",
        "reason_description": "Damaged item"
    }
    
    mock_llm_response = MagicMock()
    mock_llm_response.choices = [MagicMock()]
    mock_llm_response.choices[0].message.content = json.dumps(mock_response)
    
    with patch("services.fiqa_api.ecommerce.nl_to_intent.get_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_llm_response
        mock_get_client.return_value = mock_client
        
        result = parse_user_message(user_message, default_order_id=default_order_id)
        
        # Should use default_order_id
        assert result.order_id == "A10003"


def test_parse_user_message_order_id_normalization():
    """Test that order_id is normalized to uppercase."""
    user_message = "Refund for order a10004"
    
    # Mock LLM response with lowercase order_id
    mock_response = {
        "intent": "refund",
        "order_id": "a10004",
        "reason_type": "OTHER",
        "reason_description": None
    }
    
    mock_llm_response = MagicMock()
    mock_llm_response.choices = [MagicMock()]
    mock_llm_response.choices[0].message.content = json.dumps(mock_response)
    
    with patch("services.fiqa_api.ecommerce.nl_to_intent.get_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_llm_response
        mock_get_client.return_value = mock_client
        
        result = parse_user_message(user_message)
        
        # Should be normalized to uppercase
        assert result.order_id == "A10004"


def test_parse_user_message_llm_failure():
    """Test that EcommerceNLParseError is raised when LLM call fails."""
    user_message = "I want a refund"
    
    with patch("services.fiqa_api.ecommerce.nl_to_intent.get_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        mock_get_client.return_value = mock_client
        
        with pytest.raises(EcommerceNLParseError) as exc_info:
            parse_user_message(user_message)
        
        assert "LLM call failed" in str(exc_info.value)


def test_parse_user_message_invalid_json():
    """Test handling of invalid JSON in LLM response."""
    user_message = "I want a refund"
    
    mock_llm_response = MagicMock()
    mock_llm_response.choices = [MagicMock()]
    mock_llm_response.choices[0].message.content = "This is not JSON"
    
    with patch("services.fiqa_api.ecommerce.nl_to_intent.get_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_llm_response
        mock_get_client.return_value = mock_client
        
        with pytest.raises(EcommerceNLParseError):
            parse_user_message(user_message)


def test_parse_user_message_no_openai_client():
    """Test that error is raised when OpenAI client is not available."""
    user_message = "I want a refund"
    
    with patch("services.fiqa_api.ecommerce.nl_to_intent.get_openai_client") as mock_get_client:
        mock_get_client.return_value = None
        
        with pytest.raises(EcommerceNLParseError) as exc_info:
            parse_user_message(user_message)
        
        assert "OpenAI client not available" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
