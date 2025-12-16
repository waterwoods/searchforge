"""
jd_core_signals.py - Core Signals Extraction Node
==================================================

This module extracts 2-3 core themes (Core Signals) from JD analysis results,
including lifecycle, spotlight stories, and evidence snippets.

The goal is to help candidates quickly identify the 2-3 most important themes
that this JD really cares about.
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional

from services.fiqa_api.jobhunter.schemas import (
    JDAnalysisState,
    JobJDSummary,
    CoreSignal,
    LifecycleSummary,
    SpotlightStory,
)
from services.fiqa_api.clients import get_openai_client

logger = logging.getLogger(__name__)

# Default model (matching repo conventions)
DEFAULT_MODEL = "gpt-4o-mini"


def _extract_candidate_themes(state: JDAnalysisState) -> List[Dict[str, Any]]:
    """
    从 gold_points / core_skills / lifecycle / spotlight_stories 里抽取候选主题并打分。
    
    Args:
        state: JDAnalysisState with jd_summary, lifecycle, spotlight_stories
        
    Returns:
        List of candidate themes with scores and related spotlight info
    """
    candidates = []
    jd_summary = state.get("jd_summary")
    
    if not jd_summary:
        return candidates
    
    # Ensure jd_summary is JobJDSummary type
    if isinstance(jd_summary, dict):
        jd_summary = JobJDSummary(**jd_summary)
    elif not isinstance(jd_summary, JobJDSummary):
        jd_summary = JobJDSummary.model_validate(jd_summary)
    
    # Extract themes from gold_points (highest weight)
    for idx, gold_point in enumerate(jd_summary.gold_points or []):
        # Simple keyword extraction from gold points
        # Look for technical terms, systems, or key concepts
        theme_keywords = []
        gold_lower = gold_point.lower()
        
        # Extract technology/system names
        tech_keywords = [
            "gcp", "bigquery", "snowflake", "airflow", "dbt", "spark",
            "kubernetes", "docker", "python", "java", "scala",
            "llm", "langchain", "langgraph", "rag", "vector", "embedding",
            "ml", "machine learning", "data pipeline", "etl", "data warehouse",
            "data-as-a-service", "daas", "data product", "api", "rest",
            "data governance", "metadata", "data quality", "data validation"
        ]
        
        for keyword in tech_keywords:
            if keyword in gold_lower:
                theme_keywords.append(keyword)
        
        if theme_keywords or len(gold_point) > 20:
            # Create a candidate theme from gold point
            theme_text = gold_point[:100]  # Truncate if too long
            score = 10.0 - (idx * 0.5)  # First gold point gets highest score
            candidates.append({
                "theme": theme_text,
                "score": score,
                "source": "gold_points",
                "related_spotlights": []
            })
    
    # Extract themes from lifecycle stages (medium weight)
    lifecycle = state.get("lifecycle")
    if lifecycle:
        if isinstance(lifecycle, dict):
            lifecycle = LifecycleSummary(**lifecycle)
        elif not isinstance(lifecycle, LifecycleSummary):
            lifecycle = LifecycleSummary.model_validate(lifecycle)
        
        if lifecycle.stages:
            for idx, stage in enumerate(lifecycle.stages[:3]):  # Top 3 stages
                score = 7.0 - (idx * 0.5)
                candidates.append({
                    "theme": stage,
                    "score": score,
                    "source": "lifecycle_stages",
                    "related_spotlights": []
                })
    
    # Extract themes from spotlight stories (medium weight)
    spotlight_stories = state.get("spotlight_stories", [])
    if spotlight_stories:
        for idx, story in enumerate(spotlight_stories[:3]):  # Top 3 stories
            if isinstance(story, dict):
                story = SpotlightStory(**story)
            elif not isinstance(story, SpotlightStory):
                story = SpotlightStory.model_validate(story)
            
            # Use focus_area as theme
            score = 8.0 - (idx * 0.5)
            candidates.append({
                "theme": story.focus_area,
                "score": score,
                "source": "spotlight_stories",
                "related_spotlights": [story.focus_area]
            })
    
    # Extract themes from core_skills (lower weight)
    for skill in (jd_summary.core_skills or [])[:5]:  # Top 5 skills
        score = 5.0
        candidates.append({
            "theme": skill,
            "score": score,
            "source": "core_skills",
            "related_spotlights": []
        })
    
    # Sort by score (descending) and return top candidates
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:10]  # Return top 10 candidates for LLM to choose from


def _build_core_signals_prompt(state: JDAnalysisState, candidates: List[Dict[str, Any]]) -> str:
    """
    构造一个 system+user prompt，要求 LLM 做：
    - 从候选主题里选出 2–3 个最核心的；
    - 对每个写出 2–3 句 rationale，必须引用 JD 中真实提到的职责/场景；
    - 输出 JSON: { "core_signals": [...], "core_narrative": "..." }。
    
    Args:
        state: JDAnalysisState
        candidates: List of candidate themes with scores
        
    Returns:
        Prompt string for LLM
    """
    jd_input = state.get("jd_input")
    jd_summary = state.get("jd_summary")
    lifecycle = state.get("lifecycle")
    spotlight_stories = state.get("spotlight_stories", [])
    
    # Ensure types
    if isinstance(jd_input, dict):
        from services.fiqa_api.jobhunter.schemas import JobJDInput
        jd_input = JobJDInput(**jd_input)
    
    if isinstance(jd_summary, dict):
        jd_summary = JobJDSummary(**jd_summary)
    elif not isinstance(jd_summary, JobJDSummary):
        jd_summary = JobJDSummary.model_validate(jd_summary)
    
    # Build context from JD summary
    jd_description = jd_input.description if jd_input else ""
    max_jd_chars = 2000
    truncated_jd = jd_description[:max_jd_chars]
    if len(jd_description) > max_jd_chars:
        truncated_jd += "\n\n...[truncated]..."
    
    # Build gold points context
    gold_context = ""
    if jd_summary.gold_points:
        gold_context = "\nGold Points (most important requirements):\n"
        for point in jd_summary.gold_points[:3]:
            gold_context += f"- {point}\n"
    
    # Build lifecycle context
    lifecycle_context = ""
    if lifecycle:
        if isinstance(lifecycle, dict):
            lifecycle = LifecycleSummary(**lifecycle)
        elif not isinstance(lifecycle, LifecycleSummary):
            lifecycle = LifecycleSummary.model_validate(lifecycle)
        
        if lifecycle.summary:
            lifecycle_context = f"\nLifecycle Summary: {lifecycle.summary}\n"
        if lifecycle.stages:
            lifecycle_context += "\nLifecycle Stages:\n"
            for stage in lifecycle.stages[:5]:
                lifecycle_context += f"- {stage}\n"
    
    # Build spotlight stories context
    spotlight_context = ""
    if spotlight_stories:
        spotlight_context = "\nSpotlight Stories (critical focus areas):\n"
        for idx, story in enumerate(spotlight_stories[:3], 1):
            if isinstance(story, dict):
                story = SpotlightStory(**story)
            elif not isinstance(story, SpotlightStory):
                story = SpotlightStory.model_validate(story)
            
            spotlight_context += f"\n{idx}. {story.focus_area}\n"
            spotlight_context += f"   Why important: {story.why_important[:200]}...\n"
    
    # Build candidate themes context
    candidates_context = "\nCandidate Themes (from analysis, sorted by importance):\n"
    for idx, candidate in enumerate(candidates[:8], 1):  # Top 8 candidates
        candidates_context += f"{idx}. {candidate['theme']} (score: {candidate['score']:.1f}, source: {candidate['source']})\n"
    
    prompt = f"""You are analyzing a job description to extract the 2-3 MOST CORE themes that this JD really cares about.

Job Description (truncated):
{truncated_jd}

{gold_context}

{lifecycle_context}

{spotlight_context}

{candidates_context}

Your task:
1. Select EXACTLY 2-3 themes from the candidate themes above (or synthesize new, more specific themes based on them)
2. For each selected theme, write a 2-3 sentence rationale that:
   - Explains why this is a core theme for this JD
   - References specific responsibilities, scenarios, or technologies mentioned in the JD
   - Explains what would hurt the company if this theme is not addressed
3. Write a core_narrative (4-5 sentences max) that summarizes: "What kind of warrior is this JD really looking for, and what battle are they fighting?"

CRITICAL REQUIREMENTS:
- Select ONLY 2-3 themes (not more, not less)
- Each theme should be SPECIFIC (e.g., "Data-as-a-Service on GCP/BigQuery + data governance", not just "data engineering")
- Rationale must reference real JD content (responsibilities, tools, systems mentioned)
- core_narrative should be concise and actionable (like explaining to an engineering manager)

Return a JSON object with this structure:
{{
  "core_signals": [
    {{
      "theme": "Specific theme name (e.g., 'Data-as-a-Service on GCP/BigQuery + data governance')",
      "importance": "HIGH" or "MEDIUM",
      "rationale": "2-3 sentences explaining why this is core, referencing JD content",
      "related_spotlights": ["spotlight focus_area 1", "spotlight focus_area 2"]  // optional, can be empty
    }}
  ],
  "core_narrative": "4-5 sentence summary: what kind of person is this JD looking for, what battle are they fighting"
}}

Return ONLY valid JSON, no markdown formatting, no extra text."""
    
    return prompt


def run_core_signals(state: JDAnalysisState, client: Optional[Any] = None, model: str = DEFAULT_MODEL) -> JDAnalysisState:
    """
    基于 lifecycle + spotlight stories 提炼 2–3 个 Core Signals。
    
    Args:
        state: JDAnalysisState with jd_summary, lifecycle, spotlight_stories
        client: Optional OpenAI client (if None, uses get_openai_client())
        model: OpenAI model name (default: "gpt-4o-mini")
        
    Returns:
        Updated JDAnalysisState with core_signals populated
    """
    jd_summary = state.get("jd_summary")
    if not jd_summary:
        logger.warning("No jd_summary in state, skipping core signals extraction")
        return state
    
    # Ensure jd_summary is JobJDSummary type
    if isinstance(jd_summary, dict):
        jd_summary = JobJDSummary(**jd_summary)
    elif not isinstance(jd_summary, JobJDSummary):
        jd_summary = JobJDSummary.model_validate(jd_summary)
    
    # Extract candidate themes
    candidates = _extract_candidate_themes(state)
    if not candidates:
        logger.warning("No candidate themes found, skipping core signals extraction")
        return state
    
    # Get OpenAI client if not provided
    if client is None:
        client = get_openai_client()
        if client is None:
            logger.error("OpenAI client not available. Make sure OPENAI_API_KEY is set.")
            return state
    
    # Build prompt
    prompt = _build_core_signals_prompt(state, candidates)
    
    # Call LLM
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert job description analyst. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"},  # Force JSON output
        )
        
        response_text = response.choices[0].message.content or "{}"
        
        # Parse JSON response
        try:
            parsed = json.loads(response_text)
            
            # Extract core_signals and core_narrative
            core_signals_data = parsed.get("core_signals", [])
            core_narrative = parsed.get("core_narrative")
            
            # Convert to CoreSignal objects
            core_signals = []
            for signal_data in core_signals_data[:3]:  # Limit to 3 signals
                try:
                    # Defensive parsing: handle missing fields gracefully
                    normalized_signal = {
                        "theme": signal_data.get("theme", "Unknown theme"),
                        "importance": signal_data.get("importance", "HIGH"),
                        "rationale": signal_data.get("rationale", "Not specified"),
                        "related_spotlights": signal_data.get("related_spotlights", []),
                    }
                    signal = CoreSignal(**normalized_signal)
                    core_signals.append(signal)
                except Exception as e:
                    logger.warning(f"Failed to parse core signal: {e}, data: {signal_data}")
                    continue
            
            # Update state
            state["core_signals"] = core_signals
            
            # Update jd_summary with core_signals and core_narrative
            jd_summary.core_signals = core_signals
            jd_summary.core_narrative = core_narrative if core_narrative else None
            state["jd_summary"] = jd_summary
            
            logger.info(f"Extracted {len(core_signals)} core signals")
            return state
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group(0))
                    core_signals_data = parsed.get("core_signals", [])
                    core_narrative = parsed.get("core_narrative")
                    
                    core_signals = []
                    for signal_data in core_signals_data[:3]:
                        if isinstance(signal_data, dict):
                            try:
                                normalized_signal = {
                                    "theme": signal_data.get("theme", "Unknown theme"),
                                    "importance": signal_data.get("importance", "HIGH"),
                                    "rationale": signal_data.get("rationale", "Not specified"),
                                    "related_spotlights": signal_data.get("related_spotlights", []),
                                }
                                signal = CoreSignal(**normalized_signal)
                                core_signals.append(signal)
                            except Exception as e:
                                logger.warning(f"Failed to parse signal from fallback: {e}")
                                continue
                    
                    state["core_signals"] = core_signals
                    jd_summary.core_signals = core_signals
                    jd_summary.core_narrative = core_narrative if core_narrative else None
                    state["jd_summary"] = jd_summary
                    return state
                except:
                    pass
            
            # Return state unchanged on parse failure
            logger.error("Failed to parse core signals from LLM response")
            return state
            
    except Exception as e:
        logger.error(f"LLM call failed for core signals extraction: {e}")
        return state
