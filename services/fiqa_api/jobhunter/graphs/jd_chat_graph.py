"""
jd_chat_graph.py - Flow 2: JD 职业教练多轮对话 LangGraph

这是 Flow 2：JD 职业教练对话（多轮对话闭环）的 LangGraph 实现。
基于 JD 分析和适配度分析结果，提供多轮对话能力。
"""

import logging
from typing import Dict, Any, Optional, List

from langgraph.graph import StateGraph, END

from services.fiqa_api.jobhunter.schemas import JDChatState, JobJDInput, JobJDSummary, ChatMessage
from services.fiqa_api.clients import get_openai_client
from services.fiqa_api.telemetry.langsmith_config import (
    is_langsmith_enabled,
    default_langsmith_run_config,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o-mini"


def node_answer_user(state: JDChatState) -> Dict[str, Any]:
    """
    节点：回答用户问题
    
    基于 JD 分析结果、适配度分析和对话历史，使用 LLM 生成回答。
    """
    jd_summary = state.get("jd_summary")
    fit_summary = state.get("fit_summary")
    candidate_profile = state.get("candidate_profile")
    history = state.get("history", [])
    last_user_message = state.get("last_user_message")
    
    if not jd_summary:
        raise ValueError("Missing jd_summary in state")
    
    if not last_user_message:
        raise ValueError("Missing last_user_message in state")
    
    # 构建上下文
    context_parts = []
    
    # JD 信息
    context_parts.append(f"职位: {jd_summary.title or 'Unknown'} @ {jd_summary.company or 'Unknown'}")
    context_parts.append(f"地点: {jd_summary.location or 'Unknown'}")
    context_parts.append("")
    
    # JD 分析结果
    context_parts.append("## JD 分析结果:")
    context_parts.append(f"推荐: {jd_summary.recommendation}")
    context_parts.append(f"理由: {jd_summary.reasoning_summary}")
    context_parts.append("")
    
    if jd_summary.gold_points:
        context_parts.append("核心要点:")
        for point in jd_summary.gold_points:
            context_parts.append(f"- {point}")
        context_parts.append("")
    
    if jd_summary.silver_points:
        context_parts.append("Key skill requirements:")
        for point in jd_summary.silver_points:
            context_parts.append(f"- {point}")
        context_parts.append("")
    
    if jd_summary.core_skills:
        context_parts.append(f"核心技能: {', '.join(jd_summary.core_skills)}")
        context_parts.append("")
    
    if jd_summary.risks_or_red_flags:
        context_parts.append("风险/注意事项:")
        for risk in jd_summary.risks_or_red_flags:
            context_parts.append(f"- {risk}")
        context_parts.append("")
    
    # 适配度分析结果（如果有）
    if fit_summary:
        context_parts.append("## 适配分析:")
        context_parts.append(f"推荐: {fit_summary.recommendation_for_candidate}")
        context_parts.append("")
        
        if hasattr(fit_summary, "strengths") and fit_summary.strengths:
            context_parts.append("优势:")
            for strength in fit_summary.strengths:
                context_parts.append(f"- {strength}")
            context_parts.append("")
        
        if hasattr(fit_summary, "gaps") and fit_summary.gaps:
            context_parts.append("缺口:")
            for gap in fit_summary.gaps:
                context_parts.append(f"- {gap}")
            context_parts.append("")
        
        if hasattr(fit_summary, "action_items") and fit_summary.action_items:
            context_parts.append("行动建议:")
            for action in fit_summary.action_items:
                context_parts.append(f"- {action}")
            context_parts.append("")
    
    context_text = "\n".join(context_parts)
    
    # 构建系统 prompt
    system_prompt = """你是一个专业的求职教练，帮助候选人理解职位要求、评估适配度，并提供实用的建议。

你的回答应该：
1. 基于提供的 JD 分析和适配分析结果
2. 针对候选人的具体问题给出实用建议
3. 回答要简洁、具体、可操作
4. 可以涉及：简历修改、技能缺口解释、面试准备、职业规划等

如果用户问的问题超出了当前 JD 的范围，可以礼貌地说明，并基于现有信息给出最相关的建议。"""
    
    # 构建消息列表
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    
    # 添加对话历史（只取最后 N 条，避免 token 过多）
    history_limit = 10  # 只保留最后 10 轮对话
    recent_history = history[-history_limit:] if len(history) > history_limit else history
    for msg in recent_history:
        if isinstance(msg, dict) and "role" in msg and "content" in msg:
            messages.append({"role": msg["role"], "content": msg["content"]})
    
    # 添加当前用户消息
    user_message = f"""以下是这个职位的分析结果：

{context_text}

---

用户问题: {last_user_message}

请基于以上分析结果，回答用户的问题。回答要简洁、具体、可操作。"""
    
    messages.append({"role": "user", "content": user_message})
    
    # 调用 LLM
    client = get_openai_client()
    if client is None:
        raise RuntimeError("OpenAI client not available. Make sure OPENAI_API_KEY is set.")
    
    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            temperature=0.7,
        )
        assistant_response = response.choices[0].message.content or "抱歉，无法生成回答。"
    except Exception as e:
        logger.error(f"Failed to generate chat response: {e}", exc_info=True)
        assistant_response = f"抱歉，生成回答时出错: {str(e)}"
    
    # 更新对话历史
    updated_history = list(history)  # 创建副本
    updated_history.append({"role": "user", "content": last_user_message})
    updated_history.append({"role": "assistant", "content": assistant_response})
    
    return {
        "last_response": assistant_response,
        "history": updated_history,
    }


def build_jd_chat_graph() -> StateGraph:
    """
    构建 JD 职业教练多轮对话的 LangGraph。
    
    Returns:
        编译后的 StateGraph
    
    注意：这个 graph 是单步对话，多轮由 CLI 反复调用实现。
    """
    graph = StateGraph(JDChatState)
    
    # 添加节点
    graph.add_node("answer_user", node_answer_user)
    
    # 设置入口点
    graph.set_entry_point("answer_user")
    
    # 添加边：单步对话，直接结束
    graph.add_edge("answer_user", END)
    
    return graph


def run_jd_chat_turn(
    jd_summary: JobJDSummary,
    fit_summary: Optional[Any],
    messages: List[ChatMessage],
    candidate_profile: Optional[str],
) -> List[ChatMessage]:
    """
    Run a single turn of JD chat conversation.
    
    This is a helper function that wraps the LangGraph chat flow for use in HTTP endpoints.
    It takes the chat history, extracts the last user message, runs the graph, and returns
    the updated message history.
    
    Args:
        jd_summary: Job JD summary from Flow1
        fit_summary: Optional job fit summary
        messages: Chat message history (last one should be user message)
        candidate_profile: Optional candidate profile text
    
    Returns:
        Updated list of ChatMessage objects with the assistant reply appended
    
    Raises:
        ValueError: If messages list is empty or last message is not from user
    """
    if not messages:
        raise ValueError("Messages list cannot be empty")
    
    # Extract last user message
    last_user_msg = messages[-1]
    if last_user_msg.role != "user":
        raise ValueError("Last message in history must be from user")
    
    # Convert ChatMessage list to dict format for LangGraph state
    history_dict = [{"role": msg.role, "content": msg.content} for msg in messages[:-1]]
    
    # Build chat state
    chat_state: JDChatState = {
        "jd_input": JobJDInput(
            job_id=jd_summary.job_id,
            company=jd_summary.company,
            title=jd_summary.title,
            location=jd_summary.location,
            description="",  # Not needed for chat, already in jd_summary
            candidate_profile=candidate_profile,
        ),
        "jd_summary": jd_summary,
        "fit_summary": fit_summary,
        "candidate_profile": candidate_profile,
        "history": history_dict,
        "last_user_message": last_user_msg.content,
        "last_response": None,
    }
    
    # Run the graph
    graph = build_jd_chat_graph().compile()
    if is_langsmith_enabled():
        config = default_langsmith_run_config("jobhunter_jd_chat")
        result_state = graph.invoke(chat_state, config=config)
    else:
        result_state = graph.invoke(chat_state)
    
    # Extract updated history and convert back to ChatMessage list
    updated_history_dict = result_state.get("history", history_dict)
    updated_messages: List[ChatMessage] = []
    
    # Add all previous messages (except the last user message which we already processed)
    for msg in messages[:-1]:
        updated_messages.append(msg)
    
    # Add the last user message
    updated_messages.append(ChatMessage(role="user", content=last_user_msg.content))
    
    # Add the assistant reply
    assistant_reply = result_state.get("last_response", "抱歉，无法生成回答。")
    updated_messages.append(ChatMessage(role="assistant", content=assistant_reply))
    
    return updated_messages


if __name__ == "__main__":
    # 简单的 smoke test
    import sys
    from pathlib import Path
    
    # 添加项目根路径
    project_root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    from services.fiqa_api.jobhunter.schemas import JobJDInput, JobJDSummary
    
    # 创建一个假的 JD 摘要用于测试
    test_jd_summary = JobJDSummary(
        job_id="test_123",
        company="Test Company",
        title="Senior Engineer",
        location="Remote",
        gold_points=["需要 Python 和 GCP 经验", "LLM 系统开发经验"],
        silver_points=["分布式系统", "Kubernetes"],
        bronze_points=["前端经验"],
        core_skills=["python", "gcp", "llm"],
        nice_to_have_skills=["react", "typescript"],
        risks_or_red_flags=[],
        recommendation="APPLY",
        reasoning_summary="这是一个很好的匹配",
        evidence_snippets=["JD 中提到需要 Python 和 GCP"],
    )
    
    print("Testing Flow 2: JD Chat Graph")
    print("=" * 60)
    
    graph = build_jd_chat_graph().compile()
    
    initial_state: JDChatState = {
        "jd_input": JobJDInput(
            job_id="test_123",
            company="Test Company",
            title="Senior Engineer",
            location="Remote",
            description="Test description",
        ),
        "jd_summary": test_jd_summary,
        "fit_summary": None,
        "candidate_profile": None,
        "history": [],
        "last_user_message": "这个职位需要哪些核心技能？",
        "last_response": None,
    }
    
    result = graph.invoke(initial_state)
    
    print("\nResults:")
    print(f"- Last response: {result.get('last_response') is not None}")
    print(f"- History length: {len(result.get('history', []))}")
    
    if result.get("last_response"):
        print(f"\nResponse preview: {result['last_response'][:200]}...")