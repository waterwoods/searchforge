"""
test_response_generator.py - Unit tests for response_generator module

Tests the LLM-based customer response generation with mocking.
"""

import pytest
from unittest.mock import patch, MagicMock
from services.fiqa_api.ecommerce.response_generator import (
    EcommerceResponseFacts,
    generate_customer_reply,
    _generate_fallback_response,
)


def test_ecommerce_response_facts_model():
    """Test that EcommerceResponseFacts model can be constructed and serialized."""
    facts = EcommerceResponseFacts(
        order_id="A10001",
        order_status="delivered",
        refund_eligible=True,
        refund_amount=99.99,
        currency="USD",
        refund_reason="Damaged item",
        policy_summary="30-day return policy",
    )
    
    assert facts.order_id == "A10001"
    assert facts.refund_eligible is True
    assert facts.refund_amount == 99.99
    
    # Test serialization
    facts_dict = facts.model_dump(exclude_none=True)
    assert "order_id" in facts_dict
    assert "refund_amount" in facts_dict


def test_generate_customer_reply_with_llm_success():
    """Test generate_customer_reply when LLM call succeeds."""
    facts = EcommerceResponseFacts(
        order_id="A10001",
        order_status="delivered",
        refund_eligible=True,
        refund_amount=99.99,
        currency="USD",
        refund_reason="Damaged item",
        policy_summary="30-day return policy",
    )
    
    # Mock OpenAI client and response
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="Your refund of $99.99 for order A10001 has been approved. The amount will be processed shortly."))
    ]
    mock_client.chat.completions.create.return_value = mock_response
    
    with patch("services.fiqa_api.ecommerce.response_generator.get_openai_client", return_value=mock_client):
        reply = generate_customer_reply(facts)
        
        # Verify LLM was called
        mock_client.chat.completions.create.assert_called_once()
        
        # Verify response is not empty
        assert reply
        assert len(reply.strip()) > 0
        assert "A10001" in reply or "99.99" in reply  # Should mention order or amount


def test_generate_customer_reply_with_llm_failure_fallback():
    """Test generate_customer_reply falls back when LLM call fails."""
    facts = EcommerceResponseFacts(
        order_id="A10001",
        order_status="delivered",
        refund_eligible=True,
        refund_amount=99.99,
        currency="USD",
        refund_reason="Damaged item",
    )
    
    # Mock OpenAI client to raise exception
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("API error")
    
    with patch("services.fiqa_api.ecommerce.response_generator.get_openai_client", return_value=mock_client):
        reply = generate_customer_reply(facts)
        
        # Should fall back to template response
        assert reply
        assert "A10001" in reply
        assert "99.99" in reply or "refund" in reply.lower()


def test_generate_customer_reply_with_no_openai_client():
    """Test generate_customer_reply when OpenAI client is not available."""
    facts = EcommerceResponseFacts(
        order_id="A10001",
        order_status="delivered",
        refund_eligible=True,
        refund_amount=99.99,
    )
    
    # Mock get_openai_client to return None
    with patch("services.fiqa_api.ecommerce.response_generator.get_openai_client", return_value=None):
        reply = generate_customer_reply(facts)
        
        # Should fall back to template response
        assert reply
        assert "A10001" in reply


def test_generate_customer_reply_empty_llm_response_fallback():
    """Test generate_customer_reply falls back when LLM returns empty string."""
    facts = EcommerceResponseFacts(
        order_id="A10001",
        order_status="delivered",
        refund_eligible=False,
    )
    
    # Mock LLM to return empty response
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=""))]
    mock_client.chat.completions.create.return_value = mock_response
    
    with patch("services.fiqa_api.ecommerce.response_generator.get_openai_client", return_value=mock_client):
        reply = generate_customer_reply(facts)
        
        # Should fall back to template response
        assert reply
        assert len(reply.strip()) > 0
        assert "A10001" in reply


def test_generate_fallback_response_eligible():
    """Test fallback response generation for eligible refund."""
    facts = EcommerceResponseFacts(
        order_id="A10001",
        refund_eligible=True,
        refund_amount=99.99,
        currency="USD",
        refund_reason="Damaged item",
        policy_summary="30-day policy",
    )
    
    reply = _generate_fallback_response(facts)
    
    assert "A10001" in reply
    assert "99.99" in reply or "$99.99" in reply
    assert "refund" in reply.lower()


def test_generate_fallback_response_not_eligible():
    """Test fallback response generation for non-eligible refund."""
    facts = EcommerceResponseFacts(
        order_id="A10002",
        refund_eligible=False,
    )
    
    reply = _generate_fallback_response(facts)
    
    assert "A10002" in reply
    assert "does not meet" in reply.lower() or "eligibility" in reply.lower()
    assert "customer service" in reply.lower()


def test_generate_fallback_response_unknown():
    """Test fallback response generation for unknown/error case."""
    facts = EcommerceResponseFacts(
        order_id="A10003",
        refund_eligible=None,
    )
    
    reply = _generate_fallback_response(facts)
    
    assert "A10003" in reply
    assert "unable" in reply.lower() or "contact" in reply.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


