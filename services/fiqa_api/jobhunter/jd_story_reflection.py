"""
jd_story_reflection.py - Lifecycle and Spotlight Story Reflection Nodes
=========================================================================

This module provides two LangGraph nodes for deeper JD understanding:

1. Lifecycle Reflection Node (Python, no LLM):
   - Infers job lifecycle from existing JD summary fields
   - Derives end-to-end workflow stages using keyword heuristics

2. Spotlight Deep-Dive Node (LLM-based):
   - Picks 1-2 critical lifecycle stages
   - Creates detailed technical story templates for each stage
"""

import json
import logging
import re
from typing import Dict, Any, Optional, List

from services.fiqa_api.jobhunter.schemas import (
    JobJDSummary,
    LifecycleSummary,
    SpotlightStory,
    JDAnalysisState,
)
from services.fiqa_api.clients import get_openai_client

logger = logging.getLogger(__name__)

# Default model (matching repo conventions)
DEFAULT_MODEL = "gpt-4o-mini"


def infer_lifecycle_from_summary(summary: JobJDSummary) -> LifecycleSummary:
    """
    Heuristic function: look at reflection fields + gold/silver/nice-to-have
    and derive a simple end-to-end lifecycle for this job.
    
    Goal: for Data Engineer roles, we want something like:
    'ingest → clean & normalize → model/aggregate → publish as Data-as-a-Service → monitor & improve'
    
    For LLM/Agent roles, we might get:
    'gather data → build / eval models → deploy agents → monitor behavior & safety → iterate'
    
    Args:
        summary: JobJDSummary with existing fields
        
    Returns:
        LifecycleSummary with summary and stages
    """
    # Collect all text fields for keyword analysis
    all_text = " ".join([
        " ".join(summary.gold_points or []),
        " ".join(summary.silver_points or []),
        " ".join(summary.bronze_points or []),
        " ".join(summary.core_skills or []),
        summary.reflection_problem_summary or "",
        summary.reflection_day_in_life or "",
        summary.lifecycle_summary or "",
    ]).lower()
    
    # Detect role type based on keywords
    is_data_eng = any(keyword in all_text for keyword in [
        "data engineer", "etl", "data pipeline", "data warehouse", "bigquery",
        "snowflake", "data lake", "data quality", "data governance", "dbt",
        "airflow", "spark", "data modeling", "data integration", "data platform"
    ])
    
    is_llm_agent = any(keyword in all_text for keyword in [
        "llm", "large language model", "agent", "langchain", "langgraph",
        "rag", "retrieval augmented", "vector", "embedding", "prompt",
        "fine-tune", "model training", "ai safety", "guardrails"
    ])
    
    is_ml_platform = any(keyword in all_text for keyword in [
        "ml platform", "machine learning", "model serving", "feature store",
        "mlops", "model deployment", "model monitoring", "experiment tracking"
    ])
    
    # Define canonical stages based on role type
    if is_data_eng:
        stages = [
            "ingest raw data from source systems",
            "clean, validate, and normalize data",
            "model/aggregate data in warehouse",
            "publish as Data-as-a-Service (APIs/dashboards)",
            "monitor data quality and iterate"
        ]
        summary_text = (
            "This role focuses on building end-to-end data pipelines: "
            "ingesting data from various source systems (SAP, Salesforce, APIs), "
            "transforming and validating it through ETL processes, "
            "storing in cloud data warehouses (BigQuery, Snowflake), "
            "and serving it to business teams via APIs, dashboards, or Data-as-a-Service platforms. "
            "Continuous monitoring and iteration ensure data quality and reliability."
        )
    elif is_llm_agent:
        stages = [
            "collect and evaluate training/eval data",
            "build, fine-tune, and evaluate LLM models & agents",
            "integrate agents into production systems",
            "monitor behavior, safety, and guardrails",
            "iterate based on feedback and performance"
        ]
        summary_text = (
            "This role involves the complete lifecycle of LLM/agent systems: "
            "gathering and curating training/evaluation datasets, "
            "building and fine-tuning models and agent frameworks (LangChain, LangGraph), "
            "deploying agents into production with proper observability, "
            "monitoring for safety, accuracy, and performance, "
            "and continuously iterating based on real-world feedback."
        )
    elif is_ml_platform:
        stages = [
            "collect and prepare training data",
            "build, train, and evaluate ML models",
            "deploy models to production serving infrastructure",
            "monitor model performance and drift",
            "iterate and retrain based on metrics"
        ]
        summary_text = (
            "This role covers the ML platform lifecycle: "
            "data collection and feature engineering, "
            "model development and training, "
            "deployment to production serving systems, "
            "monitoring for performance and drift, "
            "and continuous iteration to improve model quality."
        )
    else:
        # Generic/default stages
        stages = [
            "gather requirements and data",
            "design and implement solution",
            "deploy to production",
            "monitor and maintain",
            "iterate and improve"
        ]
        summary_text = (
            "This role involves a standard software development lifecycle: "
            "gathering requirements and understanding business needs, "
            "designing and implementing solutions, "
            "deploying to production environments, "
            "monitoring system health and performance, "
            "and iterating based on feedback and metrics."
        )
    
    return LifecycleSummary(
        summary=summary_text,
        stages=stages
    )


def node_lifecycle_reflection(state: JDAnalysisState) -> Dict[str, Any]:
    """
    Node: Lifecycle Reflection (Python, no LLM call)
    
    Reads state.jd_summary and infers lifecycle information using heuristics.
    Writes the result to state.jd_summary.lifecycle.
    
    Args:
        state: JDAnalysisState
        
    Returns:
        Updated state dict with lifecycle field
    """
    jd_summary = state.get("jd_summary")
    if not jd_summary:
        logger.warning("No jd_summary in state, skipping lifecycle reflection")
        return {}
    
    # Ensure jd_summary is JobJDSummary type
    if isinstance(jd_summary, dict):
        jd_summary = JobJDSummary(**jd_summary)
    elif not isinstance(jd_summary, JobJDSummary):
        jd_summary = JobJDSummary.model_validate(jd_summary)
    
    # Infer lifecycle
    logger.info("Inferring lifecycle from JD summary...")
    lifecycle = infer_lifecycle_from_summary(jd_summary)
    
    # Update jd_summary with lifecycle
    jd_summary.lifecycle = lifecycle
    
    return {
        "jd_summary": jd_summary,
    }


def build_spotlight_prompt(jd_description: str, summary: JobJDSummary) -> str:
    """
    Build a focused prompt for spotlight deep-dive analysis.
    
    This function is optimized for Data Engineer and LLM/Agent Engineer JDs,
    with special handling for Data-as-a-Service (DaaS) and data governance themes.
    
    Args:
        jd_description: Original JD description text
        summary: JobJDSummary with lifecycle and other fields
        
    Returns:
        Prompt string for LLM
    """
    # Truncate JD description if too long
    max_jd_chars = 3000
    truncated_jd = jd_description[:max_jd_chars]
    if len(jd_description) > max_jd_chars:
        truncated_jd += "\n\n...[truncated]..."
    
    # Detect DaaS and data governance keywords in JD
    jd_lower = jd_description.lower()
    has_daas_keywords = any(keyword in jd_lower for keyword in [
        "data-as-a-service", "data as a service", "data product", "data products",
        "data api", "data apis", "daas"
    ])
    has_governance_keywords = any(keyword in jd_lower for keyword in [
        "data governance", "metadata management", "data validation", "data quality",
        "governance and oversight", "data asset", "data assets"
    ])
    
    # Build lifecycle context
    lifecycle_context = ""
    if summary.lifecycle:
        lifecycle_context = f"""
Lifecycle Summary: {summary.lifecycle.summary}

Lifecycle Stages:
{chr(10).join(f"- {stage}" for stage in (summary.lifecycle.stages or []))}
"""
    
    # Build gold/silver points context
    points_context = ""
    if summary.gold_points or summary.silver_points:
        points_context = "\nKey Requirements:\n"
        if summary.gold_points:
            points_context += "Gold (most important):\n"
            for point in summary.gold_points[:3]:
                points_context += f"- {point}\n"
        if summary.silver_points:
            points_context += "Silver (key skills):\n"
            for point in summary.silver_points[:3]:
                points_context += f"- {point}\n"
    
    # Build core skills context
    skills_context = ""
    if summary.core_skills or summary.nice_to_have_skills:
        skills_context = "\nCore Skills:\n"
        if summary.core_skills:
            skills_context += f"- {', '.join(summary.core_skills[:10])}\n"
        if summary.nice_to_have_skills:
            skills_context += f"\nNice-to-have Skills:\n- {', '.join(summary.nice_to_have_skills[:10])}\n"
    
    # Build top story points context
    story_context = ""
    if summary.top_story_points:
        story_context = "\nTop Story Points:\n"
        for i, story in enumerate(summary.top_story_points[:3], 1):
            story_context += f"{i}. {story}\n"
    
    # Build mandatory focus areas based on keywords
    mandatory_focus = ""
    if has_daas_keywords:
        mandatory_focus += "\n⚠️ MANDATORY: At least ONE spotlight story MUST focus on Data-as-a-Service / data products / API design and delivery. This is explicitly mentioned in the JD.\n"
    if has_governance_keywords:
        mandatory_focus += "\n⚠️ MANDATORY: At least ONE spotlight story MUST highlight data governance, metadata management, or data quality control. This is explicitly mentioned in the JD.\n"
    
    prompt = f"""You are analyzing a job description to create deep-dive spotlight stories for the most critical lifecycle stages.

Job Description (truncated):
{truncated_jd}

{lifecycle_context}

{points_context}

{skills_context}

{story_context}

{mandatory_focus}

Your task: Pick 2-3 of the MOST CRITICAL lifecycle stages or focus areas from the list above, and for each stage, write a detailed technical story template.

SELECTION PRIORITY RULES:
1. If the JD contains "Data-as-a-Service", "data product", "data API" keywords:
   → At least ONE spotlight story MUST be about DaaS/data product/API design, delivery, and consumption patterns.
   
2. If the JD contains "data governance", "metadata management", "data validation", "data quality" keywords:
   → At least ONE spotlight story MUST emphasize data governance, metadata management, or data quality control processes.
   
3. If neither DaaS nor governance keywords are present:
   → Select the 2-3 most critical stages from: pipeline ingestion, data cleaning/transformation, data modeling/warehousing, serving/BI, monitoring, streaming, feature store, etc.
   
4. For each selected focus area, you must combine information from multiple JD sections to create a "scenario-based work story" - not just verbatim repetition.

For each critical stage, provide a JSON object with these fields:
- focus_area: A clear, specific description of the stage (e.g., "Data-as-a-Service APIs for improved data availability", "Data governance and metadata management for enterprise data assets")
- why_important: Why this stage is critical from business/risk/cost perspective (2-3 sentences)
- upstream_downstream: Describe where data/signals come from (upstream) and where they flow to (downstream). MUST mention specific systems if JD lists them (e.g., SAP, Oracle, OMS/ADMS, ODRM, Snowflake, BigQuery, Palantir Foundry, etc.) (2-3 sentences)
- tools_and_systems: List ALL specific tools, systems, and technologies mentioned in the JD. Scan the entire JD text for system names (e.g., "Apache Airflow, GCP BigQuery, Snowflake, Oracle, SAP, Palantir Foundry, OMS/ADMS, ODRM, Python, SQL, dbt, REST APIs, Tableau, Azure Data Factory"). If JD mentions specific certifications (e.g., "SnowPro Advanced", "Palantir Foundry Data Engineer"), include those platforms. Be comprehensive - don't miss systems mentioned in Preferred Qualifications or Additional Information sections.
- constraints_and_risks: Describe constraints and risks (cost, SLA, regulatory/compliance, schema drift, PII handling, data privacy, scalability, etc.) (2-3 sentences)
- success_metrics: List concrete, quantifiable success metrics (e.g., "API response latency < 2s, data quality score > 95%, cost reduction by 30%, metadata coverage > 90%, compliance audit pass rate 100%"). If JD doesn't specify metrics, make reasonable assumptions and note them.

CRITICAL REQUIREMENTS:
1. Pick 2-3 focus areas (not just 1-2) to provide comprehensive coverage
2. Be SPECIFIC - mention actual technology names from the JD (BigQuery, Snowflake, Airflow, dbt, Palantir Foundry, SAP, Oracle, etc.)
3. NO generic statements - avoid vague phrases like "improve data quality" without context
4. Ground everything in concrete tools, systems, data types, and business scenarios
5. Each story MUST include at least 1-2 specific system/tool names mentioned in the JD
6. Combine multiple JD sections to create scenario-based work stories, not verbatim repetition
7. If you cannot find specific data for a field (e.g., success metrics), make reasonable assumptions and explicitly note them as assumptions

Return a JSON object with a "stories" key containing an array of 2-3 spotlight story objects:
{{
  "stories": [
    {{
      "focus_area": "...",
      "why_important": "...",
      "upstream_downstream": "...",
      "tools_and_systems": "...",
      "constraints_and_risks": "...",
      "success_metrics": "..."
    }}
  ]
}}

Return ONLY valid JSON, no markdown formatting, no extra text."""
    
    return prompt


def run_spotlight_deep_dive(
    jd_description: str,
    summary: JobJDSummary,
    client: Optional[Any] = None,
    model: str = DEFAULT_MODEL,
) -> List[SpotlightStory]:
    """
    Run LLM call to generate spotlight stories for critical lifecycle stages.
    
    Args:
        jd_description: Original JD description text
        summary: JobJDSummary with lifecycle and other fields
        client: Optional OpenAI client (if None, uses get_openai_client())
        model: OpenAI model name (default: "gpt-4o-mini")
        
    Returns:
        List of SpotlightStory objects (max 2-3)
        
    Raises:
        RuntimeError: If OpenAI client is unavailable
    """
    # Get OpenAI client if not provided
    if client is None:
        client = get_openai_client()
        if client is None:
            raise RuntimeError("OpenAI client not available. Make sure OPENAI_API_KEY is set.")
    
    # Build prompt
    prompt = build_spotlight_prompt(jd_description, summary)
    
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
        # The LLM might return a JSON object with a "stories" key or directly an array
        try:
            parsed = json.loads(response_text)
            
            # Handle different response formats
            if isinstance(parsed, list):
                stories_data = parsed
            elif isinstance(parsed, dict) and "stories" in parsed:
                stories_data = parsed["stories"]
            elif isinstance(parsed, dict) and "spotlight_stories" in parsed:
                stories_data = parsed["spotlight_stories"]
            else:
                # Try to find any array in the response
                stories_data = list(parsed.values())[0] if parsed else []
            
            # Validate and convert to SpotlightStory objects
            stories = []
            for story_data in stories_data[:3]:  # Limit to 3 stories (increased from 2)
                try:
                    # Defensive parsing: handle missing fields gracefully
                    normalized_story = {
                        "focus_area": story_data.get("focus_area", "Unknown focus area"),
                        "why_important": story_data.get("why_important", "Not specified"),
                        "upstream_downstream": story_data.get("upstream_downstream", "Not specified"),
                        "tools_and_systems": story_data.get("tools_and_systems", "Not specified"),
                        "constraints_and_risks": story_data.get("constraints_and_risks", "Not specified"),
                        "success_metrics": story_data.get("success_metrics", "Not specified"),
                    }
                    story = SpotlightStory(**normalized_story)
                    stories.append(story)
                except Exception as e:
                    logger.warning(f"Failed to parse spotlight story: {e}, data: {story_data}")
                    continue
            
            return stories
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            # Try to extract JSON from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group(0))
                    stories = []
                    for s in parsed[:3] if isinstance(parsed, list) else []:
                        if isinstance(s, dict):
                            try:
                                normalized_story = {
                                    "focus_area": s.get("focus_area", "Unknown focus area"),
                                    "why_important": s.get("why_important", "Not specified"),
                                    "upstream_downstream": s.get("upstream_downstream", "Not specified"),
                                    "tools_and_systems": s.get("tools_and_systems", "Not specified"),
                                    "constraints_and_risks": s.get("constraints_and_risks", "Not specified"),
                                    "success_metrics": s.get("success_metrics", "Not specified"),
                                }
                                stories.append(SpotlightStory(**normalized_story))
                            except Exception as e:
                                logger.warning(f"Failed to parse story from fallback: {e}")
                                continue
                    return stories
                except:
                    pass
            
            # Return empty list on parse failure
            return []
            
    except Exception as e:
        logger.error(f"LLM call failed for spotlight deep-dive: {e}")
        return []


def node_spotlight_story(state: JDAnalysisState) -> Dict[str, Any]:
    """
    Node: Spotlight Deep-Dive Story (LLM-based)
    
    Picks 1-2 critical lifecycle stages and creates detailed technical story templates.
    Writes the result to state.jd_summary.spotlight_stories.
    
    Args:
        state: JDAnalysisState
        
    Returns:
        Updated state dict with spotlight_stories field
    """
    jd_input = state.get("jd_input")
    jd_summary = state.get("jd_summary")
    
    if not jd_input or not jd_summary:
        logger.warning("Missing jd_input or jd_summary, skipping spotlight story")
        return {}
    
    # Ensure types
    if isinstance(jd_input, dict):
        from services.fiqa_api.jobhunter.schemas import JobJDInput
        jd_input = JobJDInput(**jd_input)
    
    if isinstance(jd_summary, dict):
        jd_summary = JobJDSummary(**jd_summary)
    elif not isinstance(jd_summary, JobJDSummary):
        jd_summary = JobJDSummary.model_validate(jd_summary)
    
    # Skip if lifecycle is missing
    if not jd_summary.lifecycle or not jd_summary.lifecycle.stages:
        logger.warning("No lifecycle stages found, skipping spotlight story")
        return {}
    
    # Run spotlight deep-dive
    logger.info("Generating spotlight stories for critical lifecycle stages...")
    spotlight_stories = run_spotlight_deep_dive(
        jd_description=jd_input.description,
        summary=jd_summary,
        client=None,  # Will use get_openai_client()
    )
    
    # Update jd_summary with spotlight stories
    jd_summary.spotlight_stories = spotlight_stories if spotlight_stories else None
    
    return {
        "jd_summary": jd_summary,
    }
