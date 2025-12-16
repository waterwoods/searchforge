"""
jd_interpreter.py - Core JD Interpreter Module
==============================================

This is the core "JD explanation brain" for the JobHunter system.

It takes a job description and produces a structured summary with:
- Gold/silver/bronze bullet points
- Skills extraction
- Risks/red flags identification
- Recommendation (APPLY / MAYBE / SKIP)

This module will later be reused by:
- JobHunter report generation (to add JD summaries to top jobs)
- An interactive JD explainer for direct JD paste/URL

Usage:
    from services.fiqa_api.jobhunter.jd_interpreter import interpret_job_jd, JobJDInput
    
    jd = JobJDInput(
        job_id="123",
        company="Anthropic",
        title="Staff Engineer",
        location="SF",
        description="...",
        candidate_profile="Senior backend engineer..."
    )
    
    summary = interpret_job_jd(jd)
"""

import json
import logging
import re
from typing import Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

from services.fiqa_api.clients import get_openai_client
from services.fiqa_api.jobhunter.schemas import JobJDInput, JobJDSummary

logger = logging.getLogger(__name__)

# Default model (matching repo conventions)
DEFAULT_MODEL = "gpt-4o-mini"

# Maximum description length to send to LLM (to avoid token limits)
MAX_DESC_CHARS = 4000


def truncate_description(description: str, max_length: int = MAX_DESC_CHARS) -> str:
    """
    Truncate job description to avoid token limits.
    
    Args:
        description: Full job description
        max_length: Maximum length in characters
        
    Returns:
        Truncated description with ellipsis if needed
    """
    if not description:
        return ""
    
    if len(description) <= max_length:
        return description
    
    return description[:max_length] + "\n\n...[truncated]..."


def create_jd_interpreter_chain(client: Any, model: str = DEFAULT_MODEL) -> Any:
    """
    Create a LangChain chain for interpreting job descriptions.
    
    Args:
        client: OpenAI client instance
        model: OpenAI model name to use
        
    Returns:
        LangChain chain (prompt | llm_call | parse)
    """
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert job description interpreter helping candidates understand what companies really want.

Your goal is to go beyond generic summaries and reveal the REAL story behind each job: what problems the company is solving, what the candidate will actually do day-to-day, and how this role fits (or doesn't fit) the specific candidate.

Given a job description, analyze it and return a structured JSON summary with:

1. **gold_points**: 2-3 bullets describing what this company MOST wants (core responsibilities / value) - the primary value they're seeking
2. **silver_points**: 2-4 bullets describing key skills/experience that are MUST-HAVES (must be strong)
3. **bronze_points**: 2-3 bullets describing nice-to-haves / bonus qualifications
4. **core_skills**: List of short skill tags (e.g., "llm_infra", "gcp", "kubernetes", "rag_systems", "langgraph")
5. **nice_to_have_skills**: List of short skill tags for nice-to-haves
6. **risks_or_red_flags**: List of potential concerns for candidates (e.g., "high travel", "fully on-site", "sales-heavy", "unclear compensation")
7. **recommendation**: One of "APPLY", "MAYBE", or "SKIP" - your overall recommendation FOR THIS SPECIFIC CANDIDATE
8. **reasoning_summary**: 2-4 sentences explaining why you chose this recommendation FOR THIS CANDIDATE
9. **evidence_snippets**: 2-4 short quotes copied directly from the JD that support your analysis

10. **reflection_problem_summary**: 
    - Question: "What are the 1-2 most specific problems this company/team is trying to solve RIGHT NOW?"
    - Requirements: 
      * Analyze ONLY from the employer's perspective - ignore any candidate profile
      * Combine business context + technical challenges
      * Be SPECIFIC - mention actual technologies, systems, or domains (e.g., "BigQuery", "Snowflake", "GCP", "Airflow", "billing data", "grid planning", "data quality", "Palantir Foundry", "SAP", "Snowflake Data Cloud")
      * Avoid generic statements like "improve efficiency" or "scale systems"
      * Example: "Electric utility company needs to integrate customer billing and usage data across multiple legacy systems while ensuring compliance and privacy. They're dealing with inconsistent data formats and need real-time processing capabilities."
    - Format: 2-3 sentences

11. **reflection_day_in_life**: 
    - Question: "What would an ideal candidate do in a typical day?"
    - Requirements:
      * Analyze ONLY from the employer's perspective - describe what the ideal candidate would do, not personalized to any specific candidate
      * 3-5 concrete actions, one per line
      * Each action MUST mention specific tools, systems, or workflows
      * Focus on actual tasks, not just skills
      * Example format:
        - "Write SQL queries and build data models in GCP BigQuery to support new reporting requirements"
        - "Manage ETL pipeline scheduling and monitoring using Airflow DAGs"
        - "Collaborate with business stakeholders to define Data-as-a-Service API interfaces using FastAPI"
    - Format: 3-5 bullet points

12. **reflection_pros_for_candidate**: 
    - Question: "What are the 2-3 biggest benefits of this role FOR THIS SPECIFIC CANDIDATE?"
    - Requirements:
      * Consider the candidate's background, skills, and career goals from their profile
      * Be specific and personalized - don't use generic statements
      * Reference how this role aligns with their preferences (e.g., remote work, technical depth, domain interests)
      * Example: "Strong match with candidate's GCP and data engineering experience; opportunity to work on production ML systems at scale"
    - Format: 2-4 bullet points
    - NOTE: If no candidate profile is provided, this field can be None or empty

13. **reflection_risks_for_candidate**: 
    - Question: "What are the 2-3 biggest risks or pitfalls FOR THIS SPECIFIC CANDIDATE?"
    - Requirements:
      * Be personalized - what would be challenging for THIS candidate specifically
      * Consider: location constraints, on-site requirements, domain knowledge gaps, technical depth concerns, work style mismatches
      * Examples: "Hybrid mode conflicts with candidate's remote-first preference", "Requires deep domain knowledge in utility billing systems which candidate lacks", "Heavy on-call rotation may conflict with preferred work-life balance"
    - Format: 2-4 bullet points
    - NOTE: If no candidate profile is provided, this field can be None or empty

14. **top_story_points**: 
    - Question: "Pick the 3 most critical work scenarios and write each as a 'problem + solution' work story."
    - Requirements:
      * Analyze ONLY from the employer's perspective - ignore any candidate profile
      * Maximum 3 items
      * Each item is ONE sentence combining:
        - "上联" (Upper part): The specific problem/scenario the company needs to solve (include data/system names)
        - "下联" (Lower part): What the ideal candidate will actually do day-to-day (include tools/tech stack)
      * Each story must mention at least ONE specific technology/system name (e.g., "BigQuery", "Snowflake", "Airflow", "GCP", "Palantir Foundry", "Kubernetes", "DBT", "SAP", "Kafka") OR specific business scenario (e.g., "billing data", "grid planning", "data quality monitoring", "customer 360", "real-time fraud detection")
      * Example: "Company needs to unify data from multiple operational systems into a cloud data warehouse; ideal candidate will design layered ETL pipelines and data models using BigQuery + Airflow + DBT"
    - Format: List of 3 strings (or fewer if JD doesn't provide enough detail)

15. **lifecycle_summary**:
    - Question: "What is the complete lifecycle/workflow of this role from data/signal ingestion to business consumption?"
    - Requirements:
      * Analyze ONLY from the employer's perspective - ignore any candidate profile
      * Describe the END-TO-END workflow using 2-4 sentences
      * Must include the complete data/process flow: source systems → transformation/processing → storage/warehouse → consumption/delivery
      * Mention specific technologies, tools, or systems where applicable
      * Example formats:
        - "Daily workflow: Extract data from multiple business systems (SAP, Salesforce, internal APIs) → Transform and validate using Airflow DAGs and DBT models → Load into Snowflake Data Cloud → Serve to business teams via Tableau dashboards and REST APIs"
        - "End-to-end pipeline: Real-time event streams from Kafka → Processed by Spark/Flink for feature engineering → Stored in feature store (Feast/Tecton) → Consumed by ML models for fraud detection and recommendation APIs"
        - "Data lifecycle: Source systems (GCP BigQuery, S3) → ETL orchestration (Airflow) → Data warehouse (Snowflake/BigQuery Data Mart) → Business intelligence (Looker, Tableau) and API services (FastAPI) for downstream teams"
    - Format: Single paragraph (2-4 sentences, no bullet points)

CRITICAL REQUIREMENTS - DO NOT:
- Simply repeat JD text verbatim
- Use generic clichés like "strong communication skills", "fast-paced environment", "team player"
- Write vague statements without specific technologies, systems, or business contexts
- Every reflection field MUST include at least one concrete technical term (tool/system name) or specific business scenario

IMPORTANT: For reflection fields (reflection_problem_summary, reflection_day_in_life, lifecycle_summary, top_story_points), you MUST analyze ONLY from the employer's perspective. Ignore any candidate profile - focus on what problems the company is solving and what the ideal candidate would do day-to-day. These fields should describe the job itself and the employer's needs, not personalized to any specific candidate.

For recommendation and reasoning_summary fields, you may consider the candidate profile if provided to give personalized advice. However, the reflection fields (problem_summary, day_in_life, lifecycle_summary, top_story_points) must remain employer-focused and candidate-agnostic.

Be concise but insightful. Every reflection field should reveal the REAL story behind the job (the employer's story and the complete workflow lifecycle), not just summarize the JD verbatim.

Return ONLY valid JSON, no markdown formatting."""),
        ("user", """Job Information:
- Title: {title}
- Company: {company}
- Location: {location}

{candidate_context}

Job Description:
{description}

Please analyze this job and return a JSON object with the fields described above. If a candidate profile was provided, evaluate this job specifically for that candidate and tailor your recommendation, reasoning, and risk assessment accordingly.""")
    ])
    
    # Create LLM call function using existing OpenAI client
    def llm_call(prompt_value: Any) -> str:
        """Call OpenAI API and return content."""
        try:
            # Convert prompt value to messages format
            messages = prompt_value.to_messages()
            # Convert to OpenAI format
            openai_messages = []
            for msg in messages:
                # Map message types to OpenAI roles
                role_map = {
                    "system": "system",
                    "human": "user",
                    "ai": "assistant",
                }
                role = role_map.get(msg.type, "user")
                content = msg.content if hasattr(msg, "content") else str(msg)
                openai_messages.append({"role": role, "content": content})
            
            response = client.chat.completions.create(
                model=model,
                messages=openai_messages,
                temperature=0.3,
                response_format={"type": "json_object"},  # Force JSON output
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    # Create parsing function
    def parse_response(response_text: str) -> dict:
        """Parse LLM JSON response and return as dict."""
        try:
            # Try to extract JSON from response (in case there's extra text)
            # Look for JSON object boundaries
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text
            
            parsed = json.loads(json_str)
            return parsed
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            # Return a fallback structure
            return {
                "gold_points": [],
                "silver_points": [],
                "bronze_points": [],
                "core_skills": [],
                "nice_to_have_skills": [],
                "risks_or_red_flags": [],
                "recommendation": "MAYBE",
                "reasoning_summary": "Failed to parse LLM response. Please review the job description manually.",
                "evidence_snippets": [],
                "reflection_problem_summary": None,
                "reflection_day_in_life": None,
                "reflection_pros_for_candidate": None,
                "reflection_risks_for_candidate": None,
                "top_story_points": None,
                "lifecycle_summary": None,
                "lifecycle": None,
                "spotlight_stories": None,
            }
    
    parse_fn = RunnableLambda(parse_response)
    
    # Chain: prompt | llm_call | parse
    chain = prompt | RunnableLambda(llm_call) | parse_fn
    
    return chain


def interpret_job_jd(
    jd: JobJDInput,
    client: Optional[Any] = None,
    model: str = DEFAULT_MODEL,
) -> JobJDSummary:
    """
    Interpret a job description and return a structured summary.
    
    This is the main entry point for the JD interpreter. It:
    1. Truncates the description if needed
    2. Creates a LangChain chain for analysis
    3. Invokes the chain with the job data
    4. Parses and validates the response
    5. Returns a JobJDSummary
    
    Args:
        jd: JobJDInput containing job description and metadata
        client: Optional OpenAI client (if None, uses get_openai_client())
        model: OpenAI model name (default: "gpt-4o-mini")
        
    Returns:
        JobJDSummary with structured analysis
        
    Raises:
        RuntimeError: If OpenAI client is unavailable
        ValueError: If parsing fails completely
    """
    # Get OpenAI client if not provided
    if client is None:
        client = get_openai_client()
        if client is None:
            raise RuntimeError("OpenAI client not available. Make sure OPENAI_API_KEY is set.")
    
    # Truncate description if needed
    truncated_desc = truncate_description(jd.description)
    
    # Build candidate context
    candidate_context = ""
    if jd.candidate_profile:
        candidate_context = (
            "You are evaluating this job for a specific candidate. "
            "Here is their profile:\n\n"
            f"{jd.candidate_profile}\n\n"
            "Please analyze this job from THIS candidate's perspective, considering their skills, "
            "preferences, and career goals. Your recommendation should be specific to this candidate."
        )
    
    # Create chain
    chain = create_jd_interpreter_chain(client, model=model)
    
    # Invoke chain
    try:
        result_dict = chain.invoke({
            "title": jd.title or "Not specified",
            "company": jd.company or "Not specified",
            "location": jd.location or "Not specified",
            "candidate_context": candidate_context,
            "description": truncated_desc,
        })
    except (TimeoutError, Exception) as e:
        # Check if this is a timeout-related error
        error_str = str(e).lower()
        is_timeout = (
            isinstance(e, TimeoutError) or
            "timeout" in error_str or
            "timed out" in error_str or
            "request timed out" in error_str
        )
        
        logger.error(f"Failed to interpret JD: {e}")
        
        # Use more specific error message for timeouts
        if is_timeout:
            error_message = "Request timed out. The job description analysis took too long. Please try again or use a shorter job description."
        else:
            error_message = f"Failed to analyze job description: {str(e)}"
        
        # Return a minimal fallback summary
        return JobJDSummary(
            job_id=jd.job_id,
            company=jd.company,
            title=jd.title,
            location=jd.location,
            gold_points=[],
            silver_points=[],
            bronze_points=[],
            core_skills=[],
            nice_to_have_skills=[],
            risks_or_red_flags=[],
            recommendation="MAYBE",
            reasoning_summary=error_message,
            evidence_snippets=[],
            reflection_problem_summary=None,
            reflection_day_in_life=None,
            reflection_pros_for_candidate=None,
            reflection_risks_for_candidate=None,
            top_story_points=None,
            lifecycle_summary=None,
            lifecycle=None,
            spotlight_stories=None,
        )
    
    # Helper function to convert list to string (for reflection fields)
    def _normalize_reflection_field(value):
        """Convert reflection field value to string (handles both list and string formats)."""
        if value is None:
            return None
        if isinstance(value, list):
            # Join list items with newlines, add bullet points if not present
            lines = []
            for item in value:
                item_str = str(item).strip()
                if item_str:
                    # Add bullet point if not already present
                    if not item_str.startswith('-') and not item_str.startswith('•'):
                        lines.append(f"- {item_str}")
                    else:
                        lines.append(item_str)
            return "\n".join(lines) if lines else None
        return str(value).strip() if value else None
    
    # Helper function to normalize top_story_points (handles string, list, or None)
    def _normalize_top_story_points(value):
        """Convert top_story_points to list of strings (handles string, list, or None)."""
        if value is None:
            return None
        if isinstance(value, str):
            # If it's a string, split by newlines and filter empty lines
            lines = [line.strip() for line in value.split('\n') if line.strip()]
            return lines if lines else None
        if isinstance(value, list):
            # If it's already a list, convert each item to string and filter empty
            result = [str(item).strip() for item in value if str(item).strip()]
            # Limit to 3 items as per requirements
            return result[:3] if result else None
        # Fallback: convert to string and wrap in list
        str_value = str(value).strip()
        return [str_value] if str_value else None
    
    # Helper function to normalize lifecycle_summary (handles string, list, or None)
    def _normalize_lifecycle_summary(value):
        """Convert lifecycle_summary to string (handles string, list, or None)."""
        if value is None:
            return None
        if isinstance(value, list):
            # If it's a list, join items with spaces
            parts = [str(item).strip() for item in value if str(item).strip()]
            return " ".join(parts) if parts else None
        # Convert to string and strip
        str_value = str(value).strip()
        return str_value if str_value else None
    
    # Build JobJDSummary from result
    try:
        summary = JobJDSummary(
            job_id=jd.job_id,
            company=jd.company,
            title=jd.title,
            location=jd.location,
            gold_points=result_dict.get("gold_points", [])[:3],  # Limit to 3
            silver_points=result_dict.get("silver_points", [])[:4],  # Limit to 4
            bronze_points=result_dict.get("bronze_points", [])[:3],  # Limit to 3
            core_skills=result_dict.get("core_skills", []),
            nice_to_have_skills=result_dict.get("nice_to_have_skills", []),
            risks_or_red_flags=result_dict.get("risks_or_red_flags", []),
            recommendation=result_dict.get("recommendation", "MAYBE"),
            reasoning_summary=result_dict.get("reasoning_summary", "No reasoning provided."),
            evidence_snippets=result_dict.get("evidence_snippets", [])[:4],  # Limit to 4
            # Reflection fields (optional, may be None if LLM doesn't provide them)
            # Handle both list and string formats from LLM
            reflection_problem_summary=_normalize_reflection_field(result_dict.get("reflection_problem_summary")),
            reflection_day_in_life=_normalize_reflection_field(result_dict.get("reflection_day_in_life")),
            reflection_pros_for_candidate=_normalize_reflection_field(result_dict.get("reflection_pros_for_candidate")),
            reflection_risks_for_candidate=_normalize_reflection_field(result_dict.get("reflection_risks_for_candidate")),
            # Top story points (optional, may be None if LLM doesn't provide them)
            top_story_points=_normalize_top_story_points(result_dict.get("top_story_points")),
            # Lifecycle summary (optional, may be None if LLM doesn't provide it)
            lifecycle_summary=_normalize_lifecycle_summary(result_dict.get("lifecycle_summary")),
        )
        
        # Validate recommendation
        if summary.recommendation not in ["APPLY", "MAYBE", "SKIP"]:
            logger.warning(f"Invalid recommendation '{summary.recommendation}', defaulting to MAYBE")
            summary.recommendation = "MAYBE"
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to build JobJDSummary from result: {e}")
        logger.debug(f"Result dict: {result_dict}")
        # Return minimal fallback
        return JobJDSummary(
            job_id=jd.job_id,
            company=jd.company,
            title=jd.title,
            location=jd.location,
            gold_points=[],
            silver_points=[],
            bronze_points=[],
            core_skills=[],
            nice_to_have_skills=[],
            risks_or_red_flags=[],
            recommendation="MAYBE",
            reasoning_summary=f"Failed to build summary: {str(e)}",
            evidence_snippets=[],
            reflection_problem_summary=None,
            reflection_day_in_life=None,
            reflection_pros_for_candidate=None,
            reflection_risks_for_candidate=None,
            top_story_points=None,
            lifecycle_summary=None,
            lifecycle=None,
            spotlight_stories=None,
        )
