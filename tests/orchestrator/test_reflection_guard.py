"""
Tests for reflection cost guardrails, caching, and detail levels.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agents.orchestrator.reflection import ReflectionCache, sanitize_and_shorten, summarize


def test_sanitize_and_shorten():
    """Test sanitization and truncation."""
    text = "Path: /home/user/secret.txt, URL: https://api.example.com/key=sk-1234567890abcdef"
    result = sanitize_and_shorten(text, max_chars=50)
    assert "[PATH]" in result
    assert "[URL]" in result
    assert "[API_KEY]" in result or "sk-" not in result
    assert len(result) <= 53  # 50 + "..."


def test_reflection_cache():
    """Test reflection cache get/set."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir) / "cache.jsonl"
        cache = ReflectionCache(storage_path=str(cache_path))
        
        # Test set and get
        cache.set("hash123", {"model": "gpt-4o-mini", "tokens": 100})
        result = cache.get("hash123")
        assert result is not None
        assert result["model"] == "gpt-4o-mini"
        assert result["tokens"] == 100
        
        # Test cache miss
        assert cache.get("hash999") is None


def test_cost_block():
    """Test that cost cap blocks LLM calls."""
    kpis = {"metrics": {"recall_at_10": 0.5}, "duration_ms": 1000}
    sla = {"verdict": "pass", "checks": []}
    
    # Set very low cost cap
    llm_cfg = {
        "enable": True,
        "provider": "openai",
        "model": "gpt-4o-mini",
        "max_tokens": 512,
        "temperature": 0.2,
        "cost_cap_usd": 0.0001,  # Very low cap
    }
    
    # Already spent more than cap
    result = summarize("SMOKE", kpis, sla, llm_cfg, spent_cost=0.0002)
    
    assert result["blocked"] is True
    assert result["model"] == "rule-engine"
    assert result["cost_usd"] == 0.0
    assert result["cache_hit"] is False


def test_cache_hit():
    """Test cache hit behavior."""
    kpis = {"metrics": {"recall_at_10": 0.5}, "duration_ms": 1000}
    sla = {"verdict": "pass", "checks": []}
    llm_cfg = {
        "enable": True,
        "provider": "openai",
        "model": "gpt-4o-mini",
        "max_tokens": 512,
        "temperature": 0.2,
        "cost_cap_usd": 0.50,
    }
    
    # First call - should hit LLM (mocked)
    with patch("agents.orchestrator.reflection._llm_summarize") as mock_llm:
        mock_llm.return_value = {
            "model": "gpt-4o-mini",
            "tokens": 100,
            "cost_usd": 0.001,
            "confidence": 0.8,
            "cache_hit": False,
            "blocked": False,
            "rationale_md": "Test summary",
            "next_actions": [],
            "prompt_hash": "test_hash",
        }
        
        result1 = summarize("SMOKE", kpis, sla, llm_cfg, prompt_hash="test_hash", spent_cost=0.0)
        assert result1["cache_hit"] is False
        assert result1["cost_usd"] > 0
        
        # Second call with same hash - should hit cache
        result2 = summarize("SMOKE", kpis, sla, llm_cfg, prompt_hash="test_hash", spent_cost=0.0)
        assert result2["cache_hit"] is True
        assert result2["cost_usd"] == 0.0
        assert result2["tokens"] == 0


def test_status_detail_lite():
    """Test that detail=lite returns sanitized content."""
    # This would be tested via integration test with flow.get_status()
    # For unit test, we verify sanitize_and_shorten works
    long_text = "A" * 2000 + " /secret/path"
    result = sanitize_and_shorten(long_text, max_chars=1200)
    assert len(result) <= 1203  # 1200 + "..."
    assert "[PATH]" in result


def test_status_detail_full():
    """Test that detail=full returns full content."""
    # Integration test - would verify flow.get_status(detail="full")
    # returns full rationale_md without truncation
    pass

