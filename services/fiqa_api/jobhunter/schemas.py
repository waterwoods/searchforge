"""
schemas.py - JobHunter Agent Data Models
=========================================
Pydantic models for job posting data used by the JobHunter Agent.

These models define the normalized schema for job postings fetched from
various ATS (Applicant Tracking System) sources like Greenhouse.

[改动标记 - Step 1 & 2]
- ConstraintCheckResult: 新增 hard_reasons 字段（Step 1）
- SpotlightStory: 新增 evidence_snippets 字段（Step 2）
"""

from typing import Optional, List, Dict, Any, Literal, TypedDict, Annotated
from enum import Enum
from datetime import datetime
from operator import add

from pydantic import BaseModel, Field


class JobPosting(BaseModel):
    """
    Normalized job posting model used by the JobHunter Agent.
    
    This model represents a unified schema for job postings from various sources,
    with all fields optional except critical identifiers.
    """
    
    job_id: str = Field(..., description="Unique job ID from the ATS (e.g., Greenhouse job id as string)")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: Optional[str] = Field(None, description="Job location (e.g., 'San Francisco, CA' or 'Remote')")
    is_remote: Optional[bool] = Field(None, description="Whether the position is remote")
    employment_type: Optional[str] = Field(None, description="Employment type (e.g., 'Full-time', 'Part-time', 'Contract')")
    department: Optional[str] = Field(None, description="Department name")
    source: str = Field(..., description="Source identifier (e.g., 'greenhouse:anthropic')")
    url: str = Field(..., description="Public job posting URL")
    description: str = Field(..., description="Full job description (HTML or plain text)")
    created_at: Optional[str] = Field(None, description="ISO datetime string when job was created")
    updated_at: Optional[str] = Field(None, description="ISO datetime string when job was last updated")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization (e.g., 'llm', 'rag', 'backend')")
    raw: Dict[str, Any] = Field(default_factory=dict, description="Raw ATS payload for debugging and reference")


class JobScore(BaseModel):
    """
    Scoring result produced by the JobHunter Agent for a single job.
    
    This model represents the LLM's evaluation of a job posting against
    a candidate profile, including classification, match scores, and recommendations.
    """
    
    job_id: str = Field(..., description="ID of the job posting being evaluated")
    
    category: Literal["A", "B", "C"] = Field(
        ...,
        description="A=strong match, B=related but not ideal, C=not a good fit"
    )
    
    match_score: int = Field(
        ...,
        ge=1,
        le=10,
        description="Overall match score between the job and the candidate profile (1-10)"
    )
    
    seniority_score: int = Field(
        ...,
        ge=1,
        le=10,
        description="How well the seniority level matches the candidate (1-10)"
    )
    
    compensation_tier: Literal["low", "mid", "high", "unknown"] = Field(
        ...,
        description="Heuristic view of compensation tier based on JD and company"
    )
    
    reasons: str = Field(
        ...,
        description="Short explanation of why this classification and score were chosen"
    )
    
    talk_track: str = Field(
        ...,
        description="Suggested way for the candidate to talk about their experience/projects for this job"
    )
    
    raw_llm_output: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw parsed JSON from the LLM for debugging"
    )


class JobApplicationStatus(str, Enum):
    """Application status enumeration."""
    APPLIED = "applied"
    SNOOZED = "snoozed"
    REJECTED = "rejected"


class JobApplicationRecord(BaseModel):
    """
    Record of a job application status tracked locally.
    
    This model represents the user's interaction with a job posting,
    tracking whether they've applied, snoozed it for later, or rejected it.
    """
    
    job_id: str = Field(..., description="Unique job ID from the ATS")
    company: str = Field(..., description="Company name")
    title: str = Field(..., description="Job title")
    source: str = Field(..., description="Source identifier (e.g., 'greenhouse:anthropic')")
    url: Optional[str] = Field(None, description="Public job posting URL")
    status: JobApplicationStatus = Field(..., description="Application status")
    notes: Optional[str] = Field(None, description="Optional notes about the application")
    last_updated: datetime = Field(..., description="ISO datetime when this record was last updated")
    location: Optional[str] = Field(None, description="Job location (e.g., 'San Francisco, CA' or 'Remote')")


class JobPreferenceRecord(BaseModel):
    """
    User preference rating for a job posting (RLHF-style feedback).
    
    This model represents the user's subjective rating of a job posting,
    which can be used to refine ranking beyond the model's match_score.
    """
    
    job_id: str = Field(..., description="Unique job ID from the ATS")
    company: str = Field(..., description="Company name")
    title: str = Field(..., description="Job title")
    source: Optional[str] = Field(None, description="Source identifier (e.g., 'greenhouse:anthropic')")
    user_rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="User rating (1=dislike, 5=very like)"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Optional tags describing why the user rated this way (e.g., 'remote', 'high-comp', 'infra', 'agents')"
    )
    notes: Optional[str] = Field(None, description="Optional notes about the preference")
    rated_at: datetime = Field(..., description="ISO datetime when this rating was recorded")


class ConstraintCheckResult(BaseModel):
    """
    Result of constraint checking for a job description.
    
    Identifies hard blocks (deal-breakers) and soft flags (potential concerns)
    based on work mode, location requirements, travel expectations, etc.
    
    [Step 1 改动] 新增 hard_reasons 字段用于记录触发硬条件的具体原因。
    [Quick Filter] 新增 profile_mismatch_score, profile_mismatch_reasons, skip_deep_analysis 字段用于快速过滤明显不匹配的职位。
    """
    hard_block: bool = Field(
        False,
        description="True if this job has hard constraints that make it a deal-breaker"
    )
    hard_reasons: List[str] = Field(
        default_factory=list,
        description="[Step 1 新增] Specific reasons why hard_block=True (e.g., 'onsite only requirement conflicts with remote-first preference')"
    )
    soft_flags: List[str] = Field(
        default_factory=list,
        description="List of soft constraint flags (e.g., 'location_restriction', 'heavy_travel', 'onsite_only')"
    )
    reasons: List[str] = Field(
        default_factory=list,
        description="Human-readable reasons for the flags and blocks"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Short tags identifying constraint types (e.g., 'onsite_only', 'must_reside_ca', 'heavy_travel')"
    )
    profile_mismatch_score: Optional[int] = Field(
        None,
        ge=0,
        le=10,
        description="[Quick Filter] Profile/JD mismatch score (0-10, lower = worse match). Only set when obvious mismatch detected."
    )
    profile_mismatch_reasons: List[str] = Field(
        default_factory=list,
        description="[Quick Filter] Human-readable reasons for profile mismatch (e.g., 'JD is dominated by sales/financial-advisor language, with almost no data-engineering keywords')"
    )
    skip_deep_analysis: bool = Field(
        False,
        description="[Quick Filter] If True, skip heavy LLM nodes (interpret_jd, lifecycle_reflection, spotlight_story, core_signals) and return low match score directly"
    )


class LifecycleSummary(BaseModel):
    """
    Lifecycle summary for a job role.
    
    Describes the end-to-end workflow/lifecycle of the job from data/signal ingestion
    to business consumption, including the key stages.
    """
    summary: Optional[str] = Field(
        None,
        description="2-3 sentence end-to-end workflow summary describing the complete lifecycle"
    )
    stages: Optional[List[str]] = Field(
        None,
        description="List of lifecycle stages (e.g., ['ingest raw data', 'clean & normalize', 'publish Data-as-a-Service', 'monitor & iterate'])"
    )


class SpotlightStory(BaseModel):
    """
    Deep-dive spotlight story for a critical lifecycle stage.
    
    Provides a detailed technical story template for 1-2 key lifecycle stages,
    including focus area, importance, upstream/downstream flows, tools, constraints, and success metrics.
    
    [Step 2 改动] 新增 evidence_snippets 字段用于存储从 JD 原文中提取的证据片段（反幻觉）。
    """
    focus_area: str = Field(
        ...,
        description="The critical lifecycle stage or focus area (e.g., 'Data quality and cleaning for large GCP/Snowflake datasets')"
    )
    why_important: str = Field(
        ...,
        description="Why this stage is important from business/risk/cost perspective"
    )
    upstream_downstream: str = Field(
        ...,
        description="Data flow: where data comes from (upstream) and where it goes (downstream)"
    )
    tools_and_systems: str = Field(
        ...,
        description="Specific tools, systems, and technologies used (e.g., 'GCP BigQuery, Snowflake, Oracle, Airflow, dbt, APIs')"
    )
    constraints_and_risks: str = Field(
        ...,
        description="Constraints and risks (cost, SLA, compliance, data quality issues, etc.)"
    )
    success_metrics: str = Field(
        ...,
        description="Success metrics (e.g., 'query latency, cost reduction %, data quality indicators, defect rate')"
    )
    evidence_snippets: List[str] = Field(
        default_factory=list,
        description="[Step 2 新增] Original JD text snippets (1-3 sentences) that support this spotlight story, used for anti-hallucination"
    )


class CoreSignal(BaseModel):
    """
    JD 最核心的 2–3 个主题信号，用于高亮展示。
    
    Core Signals 从 JD 的生命周期、Spotlight Stories 和证据中提炼出最核心的主题，
    帮助候选人快速理解这个 JD 最在乎的 2–3 件事。
    """
    theme: str = Field(
        ...,
        description="主题名称，例如 'Data-as-a-Service on GCP/BigQuery' / 'LLM agent orchestration'"
    )
    importance: Literal["HIGH", "MEDIUM"] = Field(
        "HIGH",
        description="重要性等级，目前可以只有 HIGH/MEDIUM"
    )
    rationale: str = Field(
        ...,
        description="为什么这是这个 JD 的核心，用 2–3 句话解释"
    )
    related_spotlights: List[str] = Field(
        default_factory=list,
        description="跟这个主题最相关的 spotlight_story focus_area 或标题列表"
    )


class JobJDInput(BaseModel):
    """
    Input model for JD interpreter.
    
    Represents a job description to be analyzed, with optional metadata.
    """
    
    job_id: Optional[str] = Field(None, description="Optional job ID (can be None for ad-hoc JD analysis)")
    company: Optional[str] = Field(None, description="Company name")
    title: Optional[str] = Field(None, description="Job title")
    location: Optional[str] = Field(None, description="Job location")
    description: str = Field(..., description="Full job description text")
    candidate_profile: Optional[str] = Field(None, description="Optional candidate profile for personalized analysis")


class JobJDSummary(BaseModel):
    """
    Structured summary of a job description interpretation.
    
    This is the core output of the JD interpreter, providing:
    - Gold/silver/bronze bullet points (what the company wants most, key skills, nice-to-haves)
    - Core skills and nice-to-have skills (short tags)
    - Risks/red flags
    - Recommendation (APPLY / MAYBE / SKIP)
    - Reasoning summary and evidence snippets from the JD
    """
    
    job_id: Optional[str] = Field(None, description="Job ID if available")
    company: Optional[str] = Field(None, description="Company name")
    title: Optional[str] = Field(None, description="Job title")
    location: Optional[str] = Field(None, description="Job location")
    
    gold_points: List[str] = Field(
        default_factory=list,
        description="2-3 bullets: what this company most wants (core responsibilities / value)"
    )
    silver_points: List[str] = Field(
        default_factory=list,
        description="2-4 bullets: key skills/experience (must be strong)"
    )
    bronze_points: List[str] = Field(
        default_factory=list,
        description="2-3 bullets: nice-to-have / bonus points"
    )
    
    core_skills: List[str] = Field(
        default_factory=list,
        description="Key skills as short tags (e.g., 'llm_infra', 'gcp', 'kubernetes')"
    )
    nice_to_have_skills: List[str] = Field(
        default_factory=list,
        description="Nice-to-have skills as short tags"
    )
    
    risks_or_red_flags: List[str] = Field(
        default_factory=list,
        description="可为空，列出对候选人不利的点（高出差、全 onsite、强销售导向等）"
    )
    
    recommendation: Literal["APPLY", "MAYBE", "SKIP"] = Field(
        ...,
        description="Recommendation for the candidate"
    )
    
    reasoning_summary: str = Field(
        ...,
        description="Brief natural language explanation: why this recommendation (2-4 sentences)"
    )
    
    evidence_snippets: List[str] = Field(
        default_factory=list,
        description="A few original text snippets extracted from the JD text, used as 'evidence'"
    )
    
    # Advanced JD Reflection fields (for deeper insights)
    reflection_problem_summary: Optional[str] = Field(
        None,
        description="What problem is the company/team really trying to solve? (business + technical, 2-4 sentences)"
    )
    reflection_day_in_life: Optional[str] = Field(
        None,
        description="What would an ideal candidate do day-to-day? (3-6 bullet points describing daily workflow)"
    )
    reflection_pros_for_candidate: Optional[str] = Field(
        None,
        description="From the candidate's perspective, what are the most attractive aspects of this role? (2-4 points)"
    )
    reflection_risks_for_candidate: Optional[str] = Field(
        None,
        description="From the candidate's perspective, what are the biggest risks/pitfalls? (2-4 points)"
    )
    
    top_story_points: Optional[List[str]] = Field(
        None,
        description="Top 3 key work stories, each as a 'problem + solution' pair. Format: 'Company needs to solve: [specific problem]; Candidate will do: [specific actions with tools/tech stack]'"
    )
    
    lifecycle_summary: Optional[str] = Field(
        None,
        description="Complete lifecycle/workflow description: how data/signals flow from source systems through processing to business consumption (2-4 sentences, like 'source systems → ETL/orchestration → warehouse/feature store → APIs/dashboards/ML models')"
    )
    
    # New lifecycle and spotlight story fields
    lifecycle: Optional[LifecycleSummary] = Field(
        None,
        description="Structured lifecycle summary with end-to-end workflow and stages"
    )
    spotlight_stories: Optional[List[SpotlightStory]] = Field(
        None,
        description="Deep-dive spotlight stories for 1-2 critical lifecycle stages"
    )
    
    # Core Signals fields (for highlighting 2-3 most important themes)
    core_signals: List[CoreSignal] = Field(
        default_factory=list,
        description="为这个 JD 提炼出的 2–3 个核心主题"
    )
    core_narrative: Optional[str] = Field(
        default=None,
        description="一段总结性的短文：这个 JD 真正在找什么样的战士、打什么仗。"
    )


# Graph Step Model for Engineering View
class GraphStep(BaseModel):
    """
    Graph step model for tracking LangGraph node execution.
    
    Used to provide engineering/debug view of which nodes were executed
    during JD analysis workflow.
    """
    name: str = Field(..., description="Node name (e.g., 'check_constraints', 'interpret_jd')")
    status: Literal["pending", "in_progress", "completed", "failed", "skipped"] = Field(
        ..., description="Step execution status"
    )
    started_at: Optional[str] = Field(None, description="ISO timestamp when step started")
    finished_at: Optional[str] = Field(None, description="ISO timestamp when step finished")
    duration_ms: Optional[float] = Field(None, description="Step duration in milliseconds")
    extra_info: Optional[Dict[str, Any]] = Field(
        None, description="Optional extra information (lightweight, avoid large objects)"
    )


# LangGraph State Models for JobHunter Flows
class JDAnalysisState(TypedDict, total=False):
    """
    LangGraph state for Flow 1: JD Analysis + Fit Assessment (single analysis loop)
    
    Used for one-time JD interpretation and fit analysis flow.
    
    [Quick Filter] Added skip_deep_analysis flag to short-circuit heavy LLM nodes.
    """
    jd_input: JobJDInput  # Input JD information
    jd_summary: Optional[JobJDSummary]  # JD interpretation result
    fit_summary: Optional[Any]  # Fit analysis result (JobFitSummary, using Any to avoid circular import)
    candidate_profile: Optional[str]  # Candidate profile text
    profile_id: Optional[str]  # Profile identifier (e.g., "data_engineer_gcp", "llm_agent")
    constraints: Optional[ConstraintCheckResult]  # Constraint checking result (hard blocks, soft flags)
    lifecycle: Optional[LifecycleSummary]  # Lifecycle summary (from lifecycle_reflection node)
    spotlight_stories: List[SpotlightStory]  # Spotlight stories (from spotlight_story node)
    core_signals: List[CoreSignal]  # Core signals (from core_signals node)
    graph_steps: Annotated[List[GraphStep], add]  # [Engineering View] Graph execution steps for debugging (uses reducer to append)
    skip_deep_analysis: bool  # [Quick Filter] If True, skip heavy LLM nodes and return early with low match score


class JDChatState(TypedDict, total=False):
    """
    LangGraph state for Flow 2: JD 职业教练多轮对话（多轮对话闭环）
    
    用于多轮对话场景，支持基于 JD 分析和适配度分析进行问答。
    """
    jd_input: JobJDInput  # JD 输入
    jd_summary: JobJDSummary  # JD 解读结果（必需）
    fit_summary: Optional[Any]  # 适配度分析结果（可选，JobFitSummary）
    candidate_profile: Optional[str]  # 候选人画像
    history: List[Dict[str, str]]  # 对话历史，格式: [{"role": "user"|"assistant", "content": "..."}]
    last_user_message: Optional[str]  # 最后一轮用户消息
    last_response: Optional[str]  # 最后一轮助手回复


class JobHistoryState(TypedDict, total=False):
    """
    LangGraph state for Flow 3: 偏好 & 历史经验闭环（影响排序和建议）
    
    用于整合用户偏好评分和历史经验，计算最终排序分数。
    """
    job_id: str  # 职位 ID
    job_meta: Dict[str, Any]  # 职位元信息（公司、title、match_score 等）
    user_rating: Optional[int]  # 用户评分（1-5）
    model_preference_score: Optional[float]  # 模型偏好分数
    final_score: Optional[float]  # 最终综合分数（用于排序）


# HTTP API Models for Chat Endpoint
class ChatMessage(BaseModel):
    """Chat message model for multi-turn conversations."""
    role: Literal["user", "assistant"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")


class JobHunterChatRequest(BaseModel):
    """Request model for JobHunter chat endpoint."""
    jd_summary: JobJDSummary = Field(..., description="Job JD summary from Flow1")
    fit_summary: Optional[Any] = Field(None, description="Job fit summary (optional)")
    messages: List[ChatMessage] = Field(..., description="Chat message history, last one is user question")
    use_default_profile: bool = Field(True, description="Whether to use default candidate profile")
    profile_text: Optional[str] = Field(None, description="Custom candidate profile text")
    profile_mode: Optional[str] = Field(
        default=None,
        description="Which candidate profile to use. e.g. 'agent' or 'data_eng'. If omitted, defaults to original agent profile."
    )


class JobHunterChatResponse(BaseModel):
    """Response model for JobHunter chat endpoint."""
    reply: str = Field(..., description="Assistant reply")
    messages: List[ChatMessage] = Field(..., description="Updated complete chat history")


__all__ = [
    "JobPosting",
    "JobScore",
    "JobApplicationStatus",
    "JobApplicationRecord",
    "JobPreferenceRecord",
    "JobJDInput",
    "JobJDSummary",
    "ConstraintCheckResult",
    "LifecycleSummary",
    "SpotlightStory",
    "CoreSignal",
    "GraphStep",
    "JDAnalysisState",
    "JDChatState",
    "JobHistoryState",
    "ChatMessage",
    "JobHunterChatRequest",
    "JobHunterChatResponse",
]
