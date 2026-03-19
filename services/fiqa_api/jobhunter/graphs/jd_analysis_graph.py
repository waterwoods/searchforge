"""
jd_analysis_graph.py - Flow 1: JD Analysis + Fit Assessment LangGraph

This is Flow 1: JD interpretation + fit assessment (single analysis loop) LangGraph implementation.
Reuses existing modules (jd_interpreter.py, job_fit_analyzer.py) to provide a minimal usable analysis flow.

[改动标记 - Step 2]
- 新增 node_attach_evidence 节点（证据对齐/反幻觉）
- 更新流程顺序：check_constraints → interpret_jd → lifecycle_reflection → spotlight_story → evidence_align → analyze_fit
"""

import logging
import time
import json
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

from langgraph.graph import StateGraph, END

from services.fiqa_api.jobhunter.schemas import JDAnalysisState, JobJDInput, JobJDSummary, GraphStep
from services.fiqa_api.jobhunter.jd_interpreter import interpret_job_jd, DEFAULT_MODEL
from services.fiqa_api.jobhunter.job_fit_analyzer import analyze_job_fit, JobFitSummary
from services.fiqa_api.jobhunter.jd_constraints import check_basic_constraints
from services.fiqa_api.jobhunter.jd_story_reflection import (
    node_lifecycle_reflection as _node_lifecycle_reflection,
    node_spotlight_story as _node_spotlight_story,
)
from services.fiqa_api.jobhunter.jd_evidence_align import attach_evidence_snippets
from services.fiqa_api.jobhunter.jd_core_signals import run_core_signals
from services.fiqa_api.clients import get_openai_client
from services.fiqa_api.telemetry.langsmith_config import (
    is_langsmith_enabled,
    default_langsmith_run_config,
)
from services.fiqa_api.jobhunter.sqlite_cache import (
    init_db,
    compute_jd_hash,
    get_cached_analysis,
    save_analysis,
    update_auto_skip_flags,
    get_cache_id_by_hash,
)

logger = logging.getLogger(__name__)


def _create_graph_step(
    node_name: str,
    status: str,
    started_at: Optional[str] = None,
    finished_at: Optional[str] = None,
    duration_ms: Optional[float] = None,
    extra_info: Optional[Dict[str, Any]] = None,
) -> GraphStep:
    """
    Helper function to create a graph step.
    
    Args:
        node_name: Name of the node (e.g., "check_constraints")
        status: Step status ("pending", "in_progress", "completed", "failed", "skipped")
        started_at: ISO timestamp when step started
        finished_at: ISO timestamp when step finished
        duration_ms: Optional duration in milliseconds
        extra_info: Optional extra information dict
    
    Returns:
        GraphStep instance
    """
    return GraphStep(
        name=node_name,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=duration_ms,
        extra_info=extra_info,
    )


def _convert_to_dict(obj: Any) -> Any:
    """
    Helper to convert Pydantic models and nested structures to plain dicts/lists.
    """
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, list):
        return [_convert_to_dict(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _convert_to_dict(v) for k, v in obj.items()}
    return obj


def calculate_auto_skip(analysis_result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Calculate auto_skip flag and reasons based on analysis result.
    
    This function implements Lv0 auto-skip logic to mark "obviously unsuitable" jobs
    based on existing analysis fields (fit_summary, constraints) without additional LLM calls.
    
    Rules:
    1. Category C (low fit grade)
    2. Match score < 5 (out of 10)
    3. Visa sponsorship unavailable (hard constraint)
    4. Location restriction (soft constraint, conservative - only marks as reason, not auto-skip)
    
    Args:
        analysis_result: Complete analysis result dict with fit_summary, constraints, etc.
    
    Returns:
        Tuple of (auto_skip: bool, reasons: list[str])
    """
    auto_skip = False
    reasons = []
    
    # Extract fit_summary and constraints
    fit_summary = analysis_result.get("fit_summary") or {}
    constraints = analysis_result.get("constraints") or {}
    
    # Rule 1: Category C (low fit grade)
    category = fit_summary.get("category")
    if category == "C":
        auto_skip = True
        reasons.append("low_fit_grade")
    
    # Rule 2: Match score < 5 (out of 10)
    match_score = fit_summary.get("match_score")
    if match_score is not None and match_score < 5:
        auto_skip = True
        reasons.append("low_match_score")
    
    # Rule 3: Visa sponsorship unavailable (hard constraint)
    soft_flags = constraints.get("soft_flags") or []
    if isinstance(soft_flags, list):
        if "visa_sponsorship_unavailable" in soft_flags:
            auto_skip = True
            reasons.append("visa_unavailable")
    
    # Rule 4: Location restriction (conservative - only add as reason, don't auto-skip)
    # This is a soft constraint that may be negotiable, so we mark it but don't auto-skip
    if isinstance(soft_flags, list):
        if "location_restriction" in soft_flags:
            reasons.append("location_restriction")
            # Note: We don't set auto_skip = True here, as location restrictions may be negotiable
    
    return auto_skip, reasons


def generate_cn_fast_read(analysis_result: Dict[str, Any]) -> str:
    """
    Given a structured analysis_result, generate a concise Chinese fast-read summary.

    The summary should help candidates quickly understand:
    - 核心职责 / Core Signals
    - 关键技能 / 技术栈要求
    - Lifecycle：角色在团队中的位置与上下游
    - Spotlight Stories：1–2 个典型工作场景
    - 对什么背景的候选人更合适 / 不太合适

    NOTE:
        - Only uses structured fields (jd_summary, core_signals, lifecycle, spotlight_stories,
          constraints, fit_summary, graph_steps).
        - Does NOT include raw JD text to keep tokens under control.
    """
    try:
        client = get_openai_client()
        if client is None:
            logger.warning("OpenAI client not available, skipping cn_fast_read generation")
            return ""

        # Extract and normalize structured fields only
        jd_summary = _convert_to_dict(analysis_result.get("jd_summary") or {})
        fit_summary = _convert_to_dict(analysis_result.get("fit_summary") or {})
        constraints = _convert_to_dict(analysis_result.get("constraints") or {})
        lifecycle = _convert_to_dict(analysis_result.get("lifecycle") or {})
        spotlight_stories = _convert_to_dict(analysis_result.get("spotlight_stories") or [])
        core_signals = _convert_to_dict(analysis_result.get("core_signals") or [])

        payload = {
            "meta": {
                "title": (jd_summary or {}).get("title"),
                "company": (jd_summary or {}).get("company"),
                "location": (jd_summary or {}).get("location"),
            },
            "jd_summary": {
                "gold_points": (jd_summary or {}).get("gold_points") or [],
                "silver_points": (jd_summary or {}).get("silver_points") or [],
                "bronze_points": (jd_summary or {}).get("bronze_points") or [],
                "core_skills": (jd_summary or {}).get("core_skills") or [],
                "nice_to_have_skills": (jd_summary or {}).get("nice_to_have_skills") or [],
                "risks_or_red_flags": (jd_summary or {}).get("risks_or_red_flags") or [],
                "reflection_problem_summary": (jd_summary or {}).get("reflection_problem_summary"),
                "reflection_day_in_life": (jd_summary or {}).get("reflection_day_in_life"),
                "reflection_pros_for_candidate": (jd_summary or {}).get("reflection_pros_for_candidate"),
                "reflection_risks_for_candidate": (jd_summary or {}).get("reflection_risks_for_candidate"),
                "lifecycle_summary": (jd_summary or {}).get("lifecycle_summary"),
            },
            "core_signals": core_signals or [],
            "lifecycle": lifecycle or {},
            "spotlight_stories": spotlight_stories or [],
            "constraints": {
                "hard_block": (constraints or {}).get("hard_block"),
                "hard_reasons": (constraints or {}).get("hard_reasons") or [],
                "soft_flags": (constraints or {}).get("soft_flags") or [],
                "reasons": (constraints or {}).get("reasons") or [],
                "profile_mismatch_reasons": (constraints or {}).get("profile_mismatch_reasons") or [],
                "skip_deep_analysis": (constraints or {}).get("skip_deep_analysis"),
            },
            "fit_summary": {
                "recommendation_for_candidate": (fit_summary or {}).get("recommendation_for_candidate")
                or (fit_summary or {}).get("recommendation"),
                "strengths": (fit_summary or {}).get("strengths") or [],
                "gaps": (fit_summary or {}).get("gaps") or [],
                "action_items": (fit_summary or {}).get("action_items") or (fit_summary or {}).get("next_actions") or [],
                "reasoning_summary": (fit_summary or {}).get("reasoning_summary"),
            },
        }

        payload_text = json.dumps(payload, ensure_ascii=False)
        
        system_prompt = (
            "你是一名资深求职教练，目标读者是正在找工作的数据 / 算法 / 工程类候选人。\n"
            "你现在拿到的是某个岗位已经整理好的结构化分析结果（jd_summary、core_signals、lifecycle、spotlight_stories、constraints、fit_summary 等），"
            "而不是原始 JD 文本。\n"
            "你的任务是：用简洁、结构化的中文，一句一句点出每个关键点，帮助候选人在几分钟内读完并做出是否要认真投递的判断。"
        )
        
        # 重要：说明固定小节结构、“每点一句”的写法，以及各字段缺失时的处理方式
        user_prompt = (
            "下面是某个职位的结构化分析结果（JSON，仅供你阅读理解，不要在答案中提到 JSON 或字段名）：\n\n"
            f"{payload_text}\n\n"
            "请严格使用 **中文自然语言** 输出一份 200–400 字左右的结构化速读总结，总共分为 5 个小节，标题和顺序必须是：\n"
            "1. 【总览】\n"
            "2. 【核心信号】\n"
            "3. 【生命周期】\n"
            "4. 【场景故事】\n"
            "5. 【适合度 & 建议】\n\n"
            "具体写法要求如下：\n\n"
            "【总览】\n"
            "- 用 2–3 句中文说清楚：这份工作的公司/业务场景、岗位的职责核心、主要涉及的技术或领域。\n"
            "- 语气面向“在找工作的数据/算法/工程类候选人”，可以适度点出这是偏数据平台、偏应用工程、还是偏 AI/LLM 等方向。\n\n"
            "【核心信号】\n"
            "- 只从 core_signals 和 jd_summary 里挑出最多 3 条最关键的信号，不要列太多。\n"
            "- 如果 core_signals 里有 importance / severity 等字段，就按重要程度从高到低排序；否则按原有顺序取前 3 条即可（排序逻辑由你推断，不需要在答案中说明）。\n"
            "- 对每条信号，用 1 句中文概括，建议采用类似格式：\n"
            "  \"1）这个岗位最看重 XXX（例如：大规模 ELT 管道 + 数据质量治理），说明团队非常在意 YYY。\"\n"
            "- 只在已有信息的基础上总结，不要凭空捏造新的技术栈或职责。\n"
            "- 如果确实找不到任何核心信号，就写一行：\"暂无明确的核心信号，可从整体 JD 理解为偏重 XXX。\"（XXX 用已有 jd_summary 的整体方向做非常简短的归纳，不要编造具体技术名词）。\n\n"
            "【生命周期】\n"
            "- 结合 lifecycle 结构和 jd_summary.lifecycle_summary，在 1–2 句内概括“一个项目 / 数据流的典型步骤”，例如：\n"
            "  \"从多源系统采集数据 → 通过 ETL/ELT 清洗建模 → 落地到数仓或服务层 → 通过报表/API 提供给业务，并持续监控质量。\"\n"
            "- 如果 lifecycle 相关信息非常有限，可以只写 1 句高层概括；如果完全缺失，就写：\"暂无相关信息。\"。\n\n"
            "【场景故事】\n"
            "- 如果 spotlight_stories 是非空列表（哪怕内部字段结构有些奇怪），你必须从中选出 1–3 条最有代表性的故事，每条用 1 句中文总结，格式类似：\n"
            "  \"1）描述业务场景 + 要解决的问题或关键指标 + 使用的大致技术或数据手段。\"\n"
            "- 只有在 spotlight_stories 完全缺失或为空（null / []）时，才可以写一行：\"暂无具体场景故事，但整体可以理解为围绕 XXX 的典型数据平台建设与治理。\"（XXX 用已有信息中的领域词做非常简短概括）。\n"
            "- 当 spotlight_stories 是非空列表时，严禁输出“暂无具体场景故事”或类似占位语，一定要根据列表中的英文描述写出 1–3 条一句话故事。\n\n"
            "【适合度 & 建议】\n"
            "- 结合 fit_summary.strengths、gaps、recommendation_for_candidate 和 constraints，用 1–2 句说明：什么背景的人会比较吃香（例如：强 SQL + ETL 经验、有云平台和 Airflow 经验、做过生产级 LLM 应用等）。\n"
            "- 再用 1–2 句给出客观的行动建议，例如：需要补哪块短板，简历/面试中应该重点强调哪些经验。\n"
            "- 语气偏职业教练，但尽量使用第三人称、客观表述，不要用“我觉得”“我建议你一定要”这类主观口吻。\n\n"
            "统一要求：\n"
            "1. 全文必须使用中文，可以保留少量必要的英文技术名词（如 Airflow、BigQuery、Snowflake、Python、RAG 等）。\n"
            "2. 总字数控制在 200–400 字以内，每个要点尽量 1 句，最多不要超过 2 句，整体偏速读而不是长篇报告。\n"
            "3. 严禁凭空捏造结构化分析中不存在的公司名称、技术栈或职责；遇到缺字段时，用“暂无相关信息”或非常简短的高层概括带过即可。\n"
            "4. 只输出上述五个小节的中文正文，不要输出任何代码、JSON、表格、字段名或额外说明文字。"
        )

        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=600,
        )

        content = (response.choices[0].message.content or "").strip()
        return content
    except Exception as e:
        logger.warning(f"Failed to generate cn_fast_read summary: {e}")
        return ""


def run_jd_quick_analysis(
    jd_text: str,
    title: Optional[str] = None,
    company: Optional[str] = None,
    location: Optional[str] = None,
    profile_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Lv1 轻量分析：单次 LLM 调用，直接从 JD 文本生成 Quick View 结构。
    
    输出示例：
    {
      "cn_overview": "一句话总结...",
      "responsibilities": ["...", "..."],
      "requirements": ["...", "..."],
      "red_flags": ["hybrid_required", "location_restriction"],
    }
    
    Args:
        jd_text: Job description text (required)
        title: Optional job title
        company: Optional company name
        location: Optional location
        profile_id: Optional profile identifier
    
    Returns:
        Dict with cn_overview, responsibilities, requirements, red_flags fields.
        Returns empty structure on error.
    """
    try:
        client = get_openai_client()
        if client is None:
            logger.warning("OpenAI client not available, skipping quick analysis")
            return {
                "cn_overview": "",
                "responsibilities": [],
                "requirements": [],
                "red_flags": [],
            }
        
        # Build prompt with JD text and metadata
        meta_info = []
        if title:
            meta_info.append(f"职位：{title}")
        if company:
            meta_info.append(f"公司：{company}")
        if location:
            meta_info.append(f"地点：{location}")
        
        meta_text = "\n".join(meta_info) if meta_info else ""
        
        system_prompt = (
            "你是一名资深求职教练，目标读者是正在找工作的数据 / 算法 / 工程类候选人。\n"
            "你的任务是从 JD 原文中快速提取关键信息，生成一个轻量级的快速概览。"
        )
        
        user_prompt = (
            "请分析以下职位描述，生成一个结构化的快速概览。\n\n"
            f"{meta_text}\n\n" if meta_text else ""
            f"【职位描述】\n{jd_text}\n\n"
            "请严格按照以下 JSON 格式输出（不要包含任何其他文字）：\n"
            "{\n"
            '  "cn_overview": "1-2 句中文，总共不超过 80 字，说明这份工作的核心是什么（团队使命 + 场景）",\n'
            '  "responsibilities": ["最多 3 条，每条不超过 40 字，主要职责/工作内容"],\n'
            '  "requirements": ["最多 3 条，每条不超过 40 字，硬性要求（技能/年限/地点/must-have）"],\n'
            '  "red_flags": ["0-3 个短标签，如 hybrid_required, on_call, must_relocate, visa_restriction, on_site_only"]\n'
            "}\n\n"
            "要求：\n"
            "- cn_overview 必须控制在 80 字以内\n"
            "- responsibilities 和 requirements 各最多 3 条，每条不超过 40 字\n"
            "- red_flags 只在有明显限制时填写（如必须 on-site、必须 relocation、需要政府 clearance 等）\n"
            "- 总字数约 120-200 字\n"
            "- 只输出 JSON，不要包含任何解释文字"
        )
        
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=300,
            response_format={"type": "json_object"},
        )
        
        content = (response.choices[0].message.content or "").strip()
        
        # Parse JSON response
        try:
            quick_view = json.loads(content)
            # Ensure all required fields exist
            result = {
                "cn_overview": quick_view.get("cn_overview", ""),
                "responsibilities": quick_view.get("responsibilities", []),
                "requirements": quick_view.get("requirements", []),
                "red_flags": quick_view.get("red_flags", []),
            }
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse quick analysis JSON: {e}, content: {content[:200]}")
            return {
                "cn_overview": "",
                "responsibilities": [],
                "requirements": [],
                "red_flags": [],
            }
            
    except Exception as e:
        logger.warning(f"Failed to run quick analysis: {e}")
        return {
            "cn_overview": "",
            "responsibilities": [],
            "requirements": [],
            "red_flags": [],
        }


def generate_quick_view_cn(analysis_result: Dict[str, Any]) -> str:
    """
    Lv1 轻量分析：从已有的 analysis_result 生成 QuickView（3–4 句中文）。
    
    这是 Lv1 低成本的中文 QuickView，目标是给求职者 3 秒钟判断"要不要往下深挖"。
    输出结构关注 4 件事：岗位本质 / 技术主轴 / 资历门槛 / 工作形态。
    
    这是一个轻量级的摘要生成函数，基于已有的 analysis_json 进行二次压缩。
    设计目标是快速且低成本，不需要重新分析原始 JD 文本。
    
    输出要求：
        - 最多 4 句，每句 20–40 字左右，总长约 80–160 字
        - 纯文本输出，不要编号、不要 markdown、不要列表
        - 固定结构（4 个信息点）：
            1. 岗位本质 + 所在团队（第 1 句）
            2. 核心技术栈 / 工作方式（第 2 句）
            3. 资历门槛 + 角色级别（第 3 句）
            4. 工作形态 + 地域 / 行业特殊要求（第 4 句，可选）
        - 如果 JD 没写，就用"未明确"式的保守说法，不要硬编公司没说的细节
        - 严禁编造公司名、薪资、地点，只用 jd_summary / fit_summary / core_signals 等已有字段
    """
    try:
        client = get_openai_client()
        if client is None:
            logger.warning("OpenAI client not available, skipping quick_view_cn generation")
            return ""

        # Extract and normalize structured fields only
        jd_summary = _convert_to_dict(analysis_result.get("jd_summary") or {})
        fit_summary = _convert_to_dict(analysis_result.get("fit_summary") or {})
        core_signals = _convert_to_dict(analysis_result.get("core_signals") or [])
        lifecycle = _convert_to_dict(analysis_result.get("lifecycle") or {})
        constraints = _convert_to_dict(analysis_result.get("constraints") or {})

        # Build minimal payload for quick view
        payload = {
            "meta": {
                "title": (jd_summary or {}).get("title"),
                "company": (jd_summary or {}).get("company"),
                "location": (jd_summary or {}).get("location"),
            },
            "jd_summary": {
                "core_skills": (jd_summary or {}).get("core_skills") or [],
                "reflection_problem_summary": (jd_summary or {}).get("reflection_problem_summary"),
                "lifecycle_summary": (jd_summary or {}).get("lifecycle_summary"),
            },
            "core_signals": core_signals[:3] if core_signals else [],  # Only first 1-3 signals
            "lifecycle": lifecycle or {},
            "fit_summary": {
                "match_score": (fit_summary or {}).get("match_score"),
                "category": (fit_summary or {}).get("category"),
                "recommendation_for_candidate": (fit_summary or {}).get("recommendation_for_candidate")
                or (fit_summary or {}).get("recommendation"),
                "strengths": (fit_summary or {}).get("strengths") or [],
            },
            "constraints": {
                "soft_flags": (constraints or {}).get("soft_flags") or [],
            },
        }

        payload_text = json.dumps(payload, ensure_ascii=False)
        
        system_prompt = (
            "你是一名资深求职教练，目标读者是正在找工作的数据 / 算法 / 工程类候选人。\n"
            "你现在拿到的是某个岗位已经整理好的结构化分析结果（jd_summary、core_signals、lifecycle、fit_summary 等），"
            "而不是原始 JD 文本。\n"
            "你的任务是：用固定的信息结构，让每个 JD 都能在 3–4 句里说清楚：这岗位干嘛 / 用什么技术 / 资历门槛 / 工作形态。"
        )
        
        user_prompt = (
            "下面是某个职位的结构化分析结果（JSON，仅供你阅读理解，不要在答案中提到 JSON 或字段名）：\n\n"
            f"{payload_text}\n\n"
            "请生成一个 3–4 句的中文\"快速概览\"，严格贴合以下模板结构：\n\n"
            "第 1 句：岗位本质 + 所在团队\n"
            "  例如：\"这是一个隶属于 XX 团队的数据工程岗位，主要负责 YY 场景的数据平台建设和支持。\"\n"
            "  如果信息缺失，用\"未明确\"式的保守说法，不要硬编。\n\n"
            "第 2 句：核心技术栈 / 工作方式\n"
            "  例如：\"日常主要使用 Python/SQL + 云数仓（如 BigQuery/Snowflake）+ 调度工具（如 Airflow），处理批处理和部分实时数据管道。\"\n"
            "  从 core_signals 和 core_skills 中提取，最多 2–3 个技术点。\n\n"
            "第 3 句：资历门槛 + 角色级别\n"
            "  例如：\"岗位偏 Senior/Manager 级别，通常希望候选人有 5–8 年以上数据工程/数据平台相关经验，并具备跨团队沟通能力。\"\n"
            "  如果信息缺失，用更泛的描述（如\"中高级\"），不要硬编具体年限。\n\n"
            "第 4 句（可选）：工作形态 + 地域 / 行业特殊要求\n"
            "  例如：\"工作地点在洛杉矶地区，采用混合办公模式，对电力/能源行业经验有加分。\"\n"
            "  如果 constraints.soft_flags 中有 location_restriction、hybrid_required 等信息，可以提及。\n"
            "  如果完全没有相关信息，可以省略第 4 句。\n\n"
            "输出要求：\n"
            "- 最多 4 句，每句 20–40 字左右，总长约 80–160 字\n"
            "- 纯文本输出，不要编号、不要 markdown、不要列表符号，只要连续的自然中文句子\n"
            "- 如果 JD 没写，就用\"未明确\"式的保守说法，不要硬编公司没说的细节\n"
            "- 严禁编造公司名、薪资、地点，只用已有字段\n"
            "- 语气自然流畅，像在跟候选人快速介绍这个岗位"
        )

        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=256,
        )

        content = (response.choices[0].message.content or "").strip()
        return content
    except Exception as e:
        logger.warning(f"Failed to generate quick_view_cn summary: {e}")
        return ""


def generate_quick_view_from_raw(jd_text: str, meta: Dict[str, Any]) -> str:
    """
    Lv1 轻量分析：从原始 JD 文本生成 QuickView（3–4 句中文），用于尚未跑全量分析的情况。
    
    这是 Lv1 低成本的中文 QuickView，目标是给求职者 3 秒钟判断"要不要往下深挖"。
    输出结构关注 4 件事：岗位本质 / 技术主轴 / 资历门槛 / 工作形态。
    
    这是一个轻量级的摘要生成函数，直接从 raw JD 文本生成中文概览。
    设计目标是便宜、快，但比 1–2 句更有信息量。
    
    Args:
        jd_text: 原始 JD 文本（英文）
        meta: 可选的元数据字典，可包含 title / company / location 等
    
    Returns:
        3–4 句中文，80–160 字。如果生成失败，返回空字符串。
    
    输出要求：
        - 最多 4 句，每句 20–40 字左右，总长约 80–160 字
        - 纯文本输出，不要编号、不要 markdown、不要列表
        - 固定结构（4 个信息点）：
            1. 岗位本质 + 所在团队（第 1 句）
            2. 核心技术栈 / 工作方式（第 2 句）
            3. 资历门槛 + 角色级别（第 3 句）
            4. 工作形态 + 地域 / 行业特殊要求（第 4 句，可选）
        - 如果 JD 没写，就用"未明确"式的保守说法，不要硬编公司没说的细节
        - 禁止瞎编公司名和薪资，地点不确定就别写
    """
    try:
        client = get_openai_client()
        if client is None:
            logger.warning("OpenAI client not available, skipping quick_view_from_raw generation")
            return ""
        
        # Build meta info string
        meta_parts = []
        if meta.get("title"):
            meta_parts.append(f"职位：{meta['title']}")
        if meta.get("company"):
            meta_parts.append(f"公司：{meta['company']}")
        if meta.get("location"):
            meta_parts.append(f"地点：{meta['location']}")
        meta_text = "\n".join(meta_parts) if meta_parts else ""
        
        system_prompt = (
            "你是一名资深求职教练，目标读者是正在找工作的数据 / 算法 / 工程类候选人。\n"
            "你的任务是从原始 JD 文本中快速提取关键信息，生成一个轻量的中文快速概览。\n"
            "使用固定的信息结构，让每个 JD 都能在 3–4 句里说清楚：这岗位干嘛 / 用什么技术 / 资历门槛 / 工作形态。"
        )
        
        user_prompt = (
            "请分析以下职位描述，生成一个 3–4 句的中文\"快速概览\"，严格贴合以下模板结构：\n\n"
            f"{meta_text}\n\n" if meta_text else ""
            f"【职位描述】\n{jd_text}\n\n"
            "第 1 句：岗位本质 + 所在团队\n"
            "  例如：\"这是一个隶属于 XX 团队的数据工程岗位，主要负责 YY 场景的数据平台建设和支持。\"\n"
            "  如果信息缺失，用\"未明确\"式的保守说法，不要硬编。\n\n"
            "第 2 句：核心技术栈 / 工作方式\n"
            "  例如：\"日常主要使用 Python/SQL + 云数仓（如 BigQuery/Snowflake）+ 调度工具（如 Airflow），处理批处理和部分实时数据管道。\"\n"
            "  从 JD 中提取核心技术，最多 2–3 个技术点。\n\n"
            "第 3 句：资历门槛 + 角色级别\n"
            "  例如：\"岗位偏 Senior/Manager 级别，通常希望候选人有 5–8 年以上数据工程/数据平台相关经验，并具备跨团队沟通能力。\"\n"
            "  如果信息缺失，用更泛的描述（如\"中高级\"），不要硬编具体年限。\n\n"
            "第 4 句（可选）：工作形态 + 地域 / 行业特殊要求\n"
            "  例如：\"工作地点在洛杉矶地区，采用混合办公模式，对电力/能源行业经验有加分。\"\n"
            "  如果 JD 中明确提到工作地点、远程/混合/现场、行业要求等，可以提及。\n"
            "  如果完全没有相关信息，可以省略第 4 句。\n\n"
            "输出要求：\n"
            "- 最多 4 句，每句 20–40 字左右，总长约 80–160 字\n"
            "- 纯文本输出，不要编号、不要 markdown、不要列表符号，只要连续的自然中文句子\n"
            "- 如果 JD 没写，就用\"未明确\"式的保守说法，不要硬编公司没说的细节\n"
            "- 禁止瞎编公司名和薪资，地点不确定就别写\n"
            "- 语气自然流畅，像在跟候选人快速介绍这个岗位"
        )
        
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=256,
        )
        
        content = (response.choices[0].message.content or "").strip()
        return content
    except Exception as e:
        logger.warning(f"Failed to generate quick_view_from_raw: {e}")
        return ""


def node_check_constraints(state: JDAnalysisState) -> Dict[str, Any]:
    """
    Node: Check constraints
    
    Calls check_basic_constraints to identify hard blocks and soft flags
    (work mode, location restrictions, travel requirements) and writes
    the result to state["constraints"].
    """
    node_name = "check_constraints"
    started_at = datetime.utcnow().isoformat()
    start_time = time.perf_counter()
    
    try:
        jd_input = state.get("jd_input")
        if not jd_input:
            raise ValueError("Missing jd_input in state")
        
        candidate_profile = state.get("candidate_profile")
        profile_id = state.get("profile_id")
        
        # Ensure jd_input is JobJDInput type
        if isinstance(jd_input, dict):
            jd_input = JobJDInput(**jd_input)
        elif not isinstance(jd_input, JobJDInput):
            jd_input = JobJDInput.model_validate(jd_input)
        
        # Call constraint checking (with profile_id for mismatch detection)
        logger.info("Checking constraints...")
        constraints = check_basic_constraints(jd_input, candidate_profile=candidate_profile, profile_id=profile_id)
        
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        
        # Record completed step (reducer will append this to existing list)
        new_step = _create_graph_step(
            node_name, "completed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms
        )
        
        # [Quick Filter] Propagate skip_deep_analysis flag to state
        return {
            "constraints": constraints,
            "skip_deep_analysis": constraints.skip_deep_analysis,
            "graph_steps": [new_step],  # Return only new step, reducer will append
        }
    except Exception as e:
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        
        # Record failed step (reducer will append this to existing list)
        new_step = _create_graph_step(
            node_name, "failed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"error": str(e)[:200]}
        )
        
        return {
            "graph_steps": [new_step],  # Return only new step, reducer will append
        }


def node_interpret_jd(state: JDAnalysisState) -> Dict[str, Any]:
    """
    Node: Interpret JD
    
    Calls interpret_job_jd to interpret the JD and writes the result to state["jd_summary"].
    
    [Quick Filter] Short-circuits if skip_deep_analysis=True to avoid heavy LLM calls.
    """
    node_name = "interpret_jd"
    started_at = datetime.utcnow().isoformat()
    start_time = time.perf_counter()
    
    # [Quick Filter] Short-circuit if skip_deep_analysis is True
    if state.get("skip_deep_analysis"):
        logger.info("Skipping interpret_jd: skip_deep_analysis=True (quick filter active)")
        finished_at = datetime.utcnow().isoformat()
        duration_ms = 0.0  # SKIPPED nodes don't need duration
        new_step = _create_graph_step(
            node_name, "skipped",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"skipped": "Quick filter: profile mismatch detected"}
        )
        
        # Create a minimal jd_summary for compatibility (CLI and UI expect it)
        jd_input = state.get("jd_input")
        if isinstance(jd_input, dict):
            jd_input = JobJDInput(**jd_input)
        elif not isinstance(jd_input, JobJDInput):
            jd_input = JobJDInput.model_validate(jd_input)
        
        minimal_summary = JobJDSummary(
            job_id=jd_input.job_id,
            company=jd_input.company,
            title=jd_input.title,
            location=jd_input.location,
            gold_points=[],
            silver_points=[],
            bronze_points=[],
            core_skills=[],
            nice_to_have_skills=[],
            risks_or_red_flags=["Profile/JD mismatch: role type does not align with candidate profile"],
            recommendation="SKIP",
            reasoning_summary="Quick filter: This role appears to be primarily a sales/financial-advisory position, which does not align with the selected profile.",
            evidence_snippets=[],
        )
        
        return {
            "jd_summary": minimal_summary,
            "graph_steps": [new_step],  # Return only new step, reducer will append
        }
    
    try:
        jd_input = state.get("jd_input")
        if not jd_input:
            raise ValueError("Missing jd_input in state")
        
        candidate_profile = state.get("candidate_profile")
        
        # Ensure jd_input is JobJDInput type
        # LangGraph may serialize objects as dict, need to convert back
        if isinstance(jd_input, dict):
            jd_input = JobJDInput(**jd_input)
        elif not isinstance(jd_input, JobJDInput):
            # If not JobJDInput and not dict, try to convert
            jd_input = JobJDInput.model_validate(jd_input)
        
        # Set candidate_profile (if provided)
        if candidate_profile:
            jd_input.candidate_profile = candidate_profile
        
        # Call JD interpretation
        logger.info("Interpreting JD...")
        jd_summary = interpret_job_jd(jd_input, client=None)
        
        # Check if interpret_job_jd returned None (should not happen, but handle gracefully)
        if jd_summary is None:
            logger.error("interpret_job_jd returned None, creating fallback summary")
            jd_summary = JobJDSummary(
                job_id=jd_input.job_id,
                company=jd_input.company,
                title=jd_input.title,
                location=jd_input.location,
                gold_points=[],
                silver_points=[],
                bronze_points=[],
                core_skills=[],
                nice_to_have_skills=[],
                risks_or_red_flags=[],
                recommendation="MAYBE",
                reasoning_summary="JD interpretation returned None (internal error)",
                evidence_snippets=[],
            )
        
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        
        # Record completed step (reducer will append this to existing list)
        new_step = _create_graph_step(
            node_name, "completed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms
        )
        
        return {
            "jd_summary": jd_summary,
            "graph_steps": [new_step],  # Return only new step, reducer will append
        }
    except Exception as e:
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        
        logger.error(f"Failed to interpret JD in node: {e}", exc_info=True)
        
        # Record failed step (reducer will append this to existing list)
        new_step = _create_graph_step(
            node_name, "failed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"error": str(e)[:200]}
        )
        
        # Create a minimal fallback jd_summary so the graph can continue
        # This matches the fallback behavior in interpret_job_jd
        minimal_summary = JobJDSummary(
            job_id=jd_input.job_id,
            company=jd_input.company,
            title=jd_input.title,
            location=jd_input.location,
            gold_points=[],
            silver_points=[],
            bronze_points=[],
            core_skills=[],
            nice_to_have_skills=[],
            risks_or_red_flags=[],
            recommendation="MAYBE",
            reasoning_summary=f"Analysis failed: {str(e)[:200]}",
            evidence_snippets=[],
        )
        
        return {
            "jd_summary": minimal_summary,
            "graph_steps": [new_step],  # Return only new step, reducer will append
        }


def node_attach_evidence(state: JDAnalysisState) -> Dict[str, Any]:
    """
    Node: Attach Evidence Snippets (Step 2)
    
    Attaches evidence snippets from JD text to spotlight stories to reduce hallucinations.
    Reads jd_input.description and jd_summary, calls attach_evidence_snippets(),
    and updates jd_summary with evidence_snippets for each spotlight story.
    
    [Quick Filter] Short-circuits if skip_deep_analysis=True.
    """
    node_name = "evidence_align"
    started_at = datetime.utcnow().isoformat()
    start_time = time.perf_counter()
    
    # [Quick Filter] Short-circuit if skip_deep_analysis is True
    if state.get("skip_deep_analysis"):
        logger.info("Skipping evidence_align: skip_deep_analysis=True (quick filter active)")
        finished_at = datetime.utcnow().isoformat()
        duration_ms = 0.0  # SKIPPED nodes don't need duration
        new_step = _create_graph_step(
            node_name, "skipped",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"skipped": "Quick filter: profile mismatch detected"}
        )
        return {"graph_steps": [new_step]}  # Return only new step, reducer will append
    
    try:
        jd_input = state.get("jd_input")
        jd_summary = state.get("jd_summary")
        
        if not jd_input or not jd_summary:
            logger.warning("Missing jd_input or jd_summary, skipping evidence attachment")
            finished_at = datetime.utcnow().isoformat()
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            new_step = _create_graph_step(
                node_name, "completed",
                started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
                extra_info={"skipped": "Missing jd_input or jd_summary"}
            )
            return {"graph_steps": [new_step]}  # Return only new step, reducer will append
        
        # Ensure types
        if isinstance(jd_input, dict):
            jd_input = JobJDInput(**jd_input)
        elif not isinstance(jd_input, JobJDInput):
            jd_input = JobJDInput.model_validate(jd_input)
        
        if isinstance(jd_summary, dict):
            jd_summary = JobJDSummary(**jd_summary)
        elif not isinstance(jd_summary, JobJDSummary):
            jd_summary = JobJDSummary.model_validate(jd_summary)
        
        # Skip if no spotlight stories
        if not jd_summary.spotlight_stories:
            logger.debug("No spotlight stories found, skipping evidence attachment")
            finished_at = datetime.utcnow().isoformat()
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            new_step = _create_graph_step(
                node_name, "completed",
                started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
                extra_info={"skipped": "No spotlight stories"}
            )
            return {"graph_steps": [new_step]}  # Return only new step, reducer will append
        
        # Attach evidence snippets
        logger.info("Attaching evidence snippets to spotlight stories...")
        updated_summary = attach_evidence_snippets(
            jd_text=jd_input.description,
            summary=jd_summary,
        )
        
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        new_step = _create_graph_step(
            node_name, "completed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms
        )
        
        return {
            "jd_summary": updated_summary,
            "graph_steps": [new_step],  # Return only new step, reducer will append
        }
    except Exception as e:
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        new_step = _create_graph_step(
            node_name, "failed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"error": str(e)[:200]}
        )
        return {"graph_steps": [new_step]}  # Return only new step, reducer will append


def node_analyze_fit(state: JDAnalysisState) -> Dict[str, Any]:
    """
    Node: Analyze fit
    
    If candidate_profile and jd_summary are not None, calls analyze_job_fit to perform fit analysis.
    
    [Quick Filter] If skip_deep_analysis=True, returns early with low match score (1/10) and SKIP recommendation.
    """
    node_name = "analyze_fit"
    started_at = datetime.utcnow().isoformat()
    start_time = time.perf_counter()
    
    try:
        jd_summary = state.get("jd_summary")
        candidate_profile = state.get("candidate_profile")
        profile_id = state.get("profile_id")
        skip_deep_analysis = state.get("skip_deep_analysis", False)
        constraints = state.get("constraints")
        
        fit_summary = None
        
        # [Quick Filter] If skip_deep_analysis is True, return early with low score
        if skip_deep_analysis:
            logger.info("Quick filter active: returning low match score (1/10) due to profile mismatch")
            
            # Build reasoning from profile_mismatch_reasons
            reasons = []
            if constraints and hasattr(constraints, "profile_mismatch_reasons"):
                reasons = constraints.profile_mismatch_reasons or []
            
            # Create a minimal fit summary with SKIP recommendation
            # The route handler will set match_score=1 and category="C" for SKIP when skip_deep_analysis=True
            # The route handler will also build reasoning_summary from constraints.profile_mismatch_reasons
            fit_summary = JobFitSummary(
                recommendation_for_candidate="SKIP",
                strengths=[],
                gaps=reasons if reasons else ["Quick role filter detected this is a sales/financial advisor role, not a data engineering position, so deep analysis was skipped."],
                action_items=[],
            )
            
        elif candidate_profile and jd_summary:
            logger.info("Analyzing job fit...")
            fit_summary = analyze_job_fit(jd_summary, candidate_profile, profile_id=profile_id)
        else:
            logger.debug("Skipping fit analysis: missing candidate_profile or jd_summary")
        
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        new_step = _create_graph_step(
            node_name, "completed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"fit_analyzed": fit_summary is not None}
        )
        
        return {
            "fit_summary": fit_summary,
            "graph_steps": [new_step],  # Return only new step, reducer will append
        }
    except Exception as e:
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        new_step = _create_graph_step(
            node_name, "failed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"error": str(e)[:200]}
        )
        return {"graph_steps": [new_step]}  # Return only new step, reducer will append


def node_lifecycle_reflection(state: JDAnalysisState) -> Dict[str, Any]:
    """
    Wrapper for lifecycle_reflection node with step tracking.
    
    [Quick Filter] Short-circuits if skip_deep_analysis=True.
    """
    node_name = "lifecycle_reflection"
    started_at = datetime.utcnow().isoformat()
    start_time = time.perf_counter()
    
    # [Quick Filter] Short-circuit if skip_deep_analysis is True
    if state.get("skip_deep_analysis"):
        logger.info("Skipping lifecycle_reflection: skip_deep_analysis=True (quick filter active)")
        finished_at = datetime.utcnow().isoformat()
        duration_ms = 0.0  # SKIPPED nodes don't need duration
        new_step = _create_graph_step(
            node_name, "skipped",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"skipped": "Quick filter: profile mismatch detected"}
        )
        return {"graph_steps": [new_step]}  # Return only new step, reducer will append
    
    try:
        result = _node_lifecycle_reflection(state)
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        new_step = _create_graph_step(
            node_name, "completed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms
        )
        # Add new step to result (reducer will append)
        result["graph_steps"] = [new_step]
        return result
    except Exception as e:
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        new_step = _create_graph_step(
            node_name, "failed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"error": str(e)[:200]}
        )
        return {"graph_steps": [new_step]}  # Return only new step, reducer will append


def node_spotlight_story(state: JDAnalysisState) -> Dict[str, Any]:
    """
    Wrapper for spotlight_story node with step tracking.
    
    [Quick Filter] Short-circuits if skip_deep_analysis=True.
    """
    node_name = "spotlight_story"
    started_at = datetime.utcnow().isoformat()
    start_time = time.perf_counter()
    
    # [Quick Filter] Short-circuit if skip_deep_analysis is True
    if state.get("skip_deep_analysis"):
        logger.info("Skipping spotlight_story: skip_deep_analysis=True (quick filter active)")
        finished_at = datetime.utcnow().isoformat()
        duration_ms = 0.0  # SKIPPED nodes don't need duration
        new_step = _create_graph_step(
            node_name, "skipped",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"skipped": "Quick filter: profile mismatch detected"}
        )
        return {"graph_steps": [new_step]}  # Return only new step, reducer will append
    
    try:
        result = _node_spotlight_story(state)
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        new_step = _create_graph_step(
            node_name, "completed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms
        )
        # Add new step to result (reducer will append)
        result["graph_steps"] = [new_step]
        return result
    except Exception as e:
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        new_step = _create_graph_step(
            node_name, "failed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"error": str(e)[:200]}
        )
        return {"graph_steps": [new_step]}  # Return only new step, reducer will append


def node_core_signals(state: JDAnalysisState) -> Dict[str, Any]:
    """
    Node: Core Signals Extraction
    
    Extracts 2-3 core themes from lifecycle + spotlight stories + evidence.
    Updates state.core_signals and state.jd_summary.core_signals/core_narrative.
    
    [Quick Filter] Short-circuits if skip_deep_analysis=True.
    """
    node_name = "core_signals"
    started_at = datetime.utcnow().isoformat()
    start_time = time.perf_counter()
    
    # [Quick Filter] Short-circuit if skip_deep_analysis is True
    if state.get("skip_deep_analysis"):
        logger.info("Skipping core_signals: skip_deep_analysis=True (quick filter active)")
        finished_at = datetime.utcnow().isoformat()
        duration_ms = 0.0  # SKIPPED nodes don't need duration
        new_step = _create_graph_step(
            node_name, "skipped",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"skipped": "Quick filter: profile mismatch detected"}
        )
        return {"graph_steps": [new_step]}  # Return only new step, reducer will append
    
    try:
        new_state = run_core_signals(state)
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        
        # Extract updated fields from new_state
        core_signals = new_state.get("core_signals", [])
        jd_summary = new_state.get("jd_summary")
        
        new_step = _create_graph_step(
            node_name, "completed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"signals_count": len(core_signals) if core_signals else 0}
        )
        
        return {
            "core_signals": core_signals,
            "jd_summary": jd_summary,
            "graph_steps": [new_step],  # Return only new step, reducer will append
        }
    except Exception as e:
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        new_step = _create_graph_step(
            node_name, "failed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"error": str(e)[:200]}
        )
        return {"graph_steps": [new_step]}  # Return only new step, reducer will append


def build_jd_analysis_graph() -> StateGraph:
    """
    Build LangGraph for JD interpretation + fit analysis.
    
    Flow: check_constraints -> interpret_jd -> lifecycle_reflection -> spotlight_story -> core_signals -> evidence_align -> analyze_fit
    
    Returns:
        Compiled StateGraph
    """
    graph = StateGraph(JDAnalysisState)
    
    # Add nodes
    graph.add_node("check_constraints", node_check_constraints)
    graph.add_node("interpret_jd", node_interpret_jd)
    graph.add_node("lifecycle_reflection", node_lifecycle_reflection)
    graph.add_node("spotlight_story", node_spotlight_story)
    graph.add_node("core_signals", node_core_signals)  # [Core Signals] 新增核心信号提取节点
    graph.add_node("evidence_align", node_attach_evidence)  # [Step 2] 新增证据对齐节点
    graph.add_node("analyze_fit", node_analyze_fit)
    
    # Set entry point
    graph.set_entry_point("check_constraints")
    
    # Add edges: linear flow (updated for Core Signals)
    graph.add_edge("check_constraints", "interpret_jd")
    graph.add_edge("interpret_jd", "lifecycle_reflection")
    graph.add_edge("lifecycle_reflection", "spotlight_story")
    graph.add_edge("spotlight_story", "core_signals")  # [Core Signals] 添加核心信号提取步骤
    graph.add_edge("core_signals", "evidence_align")  # [Core Signals] 更新流程顺序
    graph.add_edge("evidence_align", "analyze_fit")
    graph.add_edge("analyze_fit", END)
    
    return graph


def run_jd_analysis(
    jd_input: JobJDInput,
    candidate_profile: str | None = None,
    profile_id: str | None = None,
    job_url: str | None = None,
    job_title: str | None = None,
) -> Dict[str, Any]:
    """
    Helper function to run JD interpretation + fit analysis with caching support.
    
    This function:
    1. Checks cache before running analysis
    2. Runs LangGraph analysis if cache miss
    3. Saves result to cache after analysis
    
    Args:
        jd_input: JobJDInput instance
        candidate_profile: Optional candidate profile text
        profile_id: Optional profile identifier (e.g., "data_engineer_gcp", "llm_agent")
        job_url: Optional job posting URL (for cache storage)
        job_title: Optional job title (for cache storage, defaults to jd_input.title)
    
    Returns:
        Completed JDAnalysisState (as dict) with graph_steps populated
    """
    # ========================================
    # Cache Integration: Check cache before analysis
    # ========================================
    user_id = "andy_local"  # Use consistent user_id with routes
    full_jd_text = jd_input.description  # Use the full JD text for hashing
    cached_result = None
    cache_hit = False
    
    # Only check cache if we have valid JD text and profile_id
    if full_jd_text and profile_id:
        try:
            # Initialize DB (idempotent)
            init_db()
            
            # Compute hash for cache key
            jd_hash = compute_jd_hash(full_jd_text)
            
            # Try to get cached analysis
            cached_result = get_cached_analysis(
                user_id=user_id,
                profile_id=profile_id,
                jd_hash=jd_hash,
            )
            
            if cached_result:
                cache_hit = True
                logger.info(f"Cache HIT for job: {jd_input.title or 'Untitled'} (profile_id={profile_id}, jd_hash={jd_hash[:8]}...)")
            else:
                logger.info(f"Cache MISS for job: {jd_input.title or 'Untitled'} (profile_id={profile_id}, jd_hash={jd_hash[:8]}...)")
        except Exception as e:
            # Graceful degradation: if cache fails, continue with normal analysis
            logger.warning(f"Cache lookup failed: {e}, continuing with normal analysis")
    
    # If cache hit, use cached result; otherwise run analysis
    if cache_hit and cached_result:
        # Reconstruct result dict from cached analysis
        # cached_result should be the analysis_result dict saved by save_analysis
        result = cached_result
        logger.info("Using cached analysis result")
    else:
        # Run JD analysis graph
        logger.info(f"Running JD analysis for job: {jd_input.title or 'Untitled'} at {jd_input.company or 'Unknown'}")
        
        graph = build_jd_analysis_graph().compile()
        
        initial_state: JDAnalysisState = {
            "jd_input": jd_input,
            "candidate_profile": candidate_profile,
            "profile_id": profile_id,
            "graph_steps": [],  # Initialize graph_steps list
            "skip_deep_analysis": False,  # [Quick Filter] Initialize skip flag
        }
        
        if is_langsmith_enabled():
            config = default_langsmith_run_config("jobhunter_jd_analysis")
            result = graph.invoke(initial_state, config=config)
        else:
            result = graph.invoke(initial_state)
        
        # Ensure graph_steps is in result (convert GraphStep objects to dicts)
        # LangGraph merges state updates, so graph_steps should be accumulated from all nodes
        if "graph_steps" in result and result["graph_steps"]:
            # Convert GraphStep objects to dicts for JSON serialization
            graph_steps_list = []
            for step in result["graph_steps"]:
                if hasattr(step, "model_dump"):
                    graph_steps_list.append(step.model_dump())
                elif isinstance(step, dict):
                    graph_steps_list.append(step)
                else:
                    # Fallback: try to convert to dict
                    try:
                        graph_steps_list.append({
                            "name": getattr(step, "name", ""),
                            "status": getattr(step, "status", ""),
                            "started_at": getattr(step, "started_at", None),
                            "finished_at": getattr(step, "finished_at", None),
                            "duration_ms": getattr(step, "duration_ms", None),
                            "extra_info": getattr(step, "extra_info", None),
                        })
                    except Exception as e:
                        logger.warning(f"Failed to convert graph step to dict: {e}")
                        continue
            result["graph_steps"] = graph_steps_list
            logger.info(f"Collected {len(graph_steps_list)} graph steps")
        else:
            logger.warning("No graph_steps found in result")
            result["graph_steps"] = []
        
        # Build a normalized snapshot of structured analysis fields for downstream use
        analysis_result = {
            "jd_summary": _convert_to_dict(result.get("jd_summary")),
            "fit_summary": _convert_to_dict(result.get("fit_summary")),
            "constraints": _convert_to_dict(result.get("constraints")),
            "lifecycle": _convert_to_dict(result.get("lifecycle")),
            "spotlight_stories": _convert_to_dict(result.get("spotlight_stories")),
            "core_signals": _convert_to_dict(result.get("core_signals")),
            "graph_steps": result.get("graph_steps", []),
        }

        # Generate Chinese fast-read summary from structured fields only.
        # This intentionally avoids sending raw JD text again to control token usage.
        cn_fast_read = generate_cn_fast_read(analysis_result)
        analysis_result["cn_fast_read"] = cn_fast_read
        # Attach cn_fast_read to in-memory result so online responses can use it
        result["cn_fast_read"] = cn_fast_read

        # ========================================
        # Cache Integration: Save result after analysis
        # ========================================
        if full_jd_text and profile_id and not cache_hit:
            try:
                jd_hash = compute_jd_hash(full_jd_text)
                job_url_final = job_url or ""
                job_title_final = job_title or jd_input.title or ""
                
                save_analysis(
                    user_id=user_id,
                    profile_id=profile_id,
                    job_url=job_url_final,
                    job_title=job_title_final,
                    jd_hash=jd_hash,
                    raw_text=full_jd_text,
                    analysis=analysis_result,
                )
                logger.info(f"Cached complete analysis result (profile_id={profile_id}, jd_hash={jd_hash[:8]}...)")
                
                # Calculate and save auto_skip flags (Lv0 auto-filter)
                try:
                    cache_id = get_cache_id_by_hash(user_id, profile_id, jd_hash)
                    if cache_id:
                        auto_skip, reasons = calculate_auto_skip(analysis_result)
                        update_auto_skip_flags(
                            cache_id=cache_id,
                            auto_skip=1 if auto_skip else 0,
                            reasons=reasons if reasons else None,
                        )
                        logger.info(f"Updated auto_skip flags for cache_id={cache_id}: auto_skip={auto_skip}, reasons={reasons}")
                    else:
                        logger.warning(f"Could not find cache_id for jd_hash={jd_hash[:8]}... to update auto_skip flags")
                except Exception as e:
                    # Graceful degradation: if auto_skip calculation fails, log warning but don't fail the request
                    logger.warning(f"Failed to calculate/update auto_skip flags: {e}")
            except Exception as e:
                # Graceful degradation: if save fails, log warning but don't fail the request
                logger.warning(f"Failed to save analysis to cache: {e}")
    
    return result


if __name__ == "__main__":
    # 简单的 smoke test
    import sys
    from pathlib import Path
    
    # 添加项目根路径
    project_root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # 创建一个假的 JD 输入用于测试
    from services.fiqa_api.jobhunter.schemas import JobJDInput
    
    test_jd = JobJDInput(
        job_id="test_123",
        company="Test Company",
        title="Senior Engineer",
        location="Remote",
        description="We are looking for a senior engineer with experience in Python, GCP, and LLM systems.",
    )
    
    print("Testing Flow 1: JD Analysis Graph")
    print("=" * 60)
    
    result = run_jd_analysis(test_jd)
    
    print("\nResults:")
    print(f"- JD Summary: {result.get('jd_summary') is not None}")
    print(f"- Fit Summary: {result.get('fit_summary') is not None}")
    
    if result.get("jd_summary"):
        summary = result["jd_summary"]
        print(f"\nRecommendation: {summary.recommendation}")
        print(f"Gold points: {len(summary.gold_points)}")
        print(f"Core skills: {summary.core_skills}")