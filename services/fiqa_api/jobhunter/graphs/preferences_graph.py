"""
preferences_graph.py - Flow 3: 偏好 & 历史经验闭环 LangGraph

这是 Flow 3：偏好 & 历史经验闭环（影响排序和建议）的 LangGraph 实现。
整合用户偏好评分和历史经验，计算最终排序分数。
"""

import logging
from typing import Dict, Any, Optional

from langgraph.graph import StateGraph, END

from services.fiqa_api.jobhunter.schemas import JobHistoryState
from services.fiqa_api.jobhunter.preferences_store import load_preferences
from services.fiqa_api.telemetry.langsmith_config import (
    is_langsmith_enabled,
    default_langsmith_run_config,
)

logger = logging.getLogger(__name__)


def node_load_preference(state: JobHistoryState) -> Dict[str, Any]:
    """
    节点：加载用户偏好
    
    从 preferences.json 读取已有评分，写入 state["user_rating"]。
    """
    job_id = state.get("job_id")
    if not job_id:
        raise ValueError("Missing job_id in state")
    
    # 加载所有偏好记录
    preferences = load_preferences()
    
    # 查找当前 job_id 的偏好记录
    user_rating = None
    if job_id in preferences:
        preference_record = preferences[job_id]
        user_rating = preference_record.user_rating
        logger.info(f"Found user rating {user_rating} for job {job_id}")
    else:
        logger.debug(f"No user rating found for job {job_id}")
    
    return {
        "user_rating": user_rating,
    }


def node_compute_final_score(state: JobHistoryState) -> Dict[str, Any]:
    """
    节点：计算最终分数
    
    使用公式：final_score = match_score + (rating - 3) * 0.7
    如果没有 rating，使用原 match_score。
    """
    job_meta = state.get("job_meta", {})
    user_rating = state.get("user_rating")
    model_preference_score = state.get("model_preference_score")
    
    # 从 job_meta 中获取 match_score
    match_score = job_meta.get("match_score", 0)
    
    # 如果没有 model_preference_score，使用 match_score
    base_score = model_preference_score if model_preference_score is not None else match_score
    
    # 计算最终分数
    # 公式：final_score = base_score + (rating - 3) * 0.7
    # rating 1-5，中位数是 3，所以 (rating - 3) * 0.7 会在 -1.4 到 +1.4 之间
    if user_rating is not None:
        final_score = base_score + (user_rating - 3) * 0.7
        logger.info(f"Computed final_score: {base_score} + ({user_rating} - 3) * 0.7 = {final_score}")
    else:
        final_score = base_score
        logger.debug(f"No user rating, using base_score: {final_score}")
    
    return {
        "final_score": final_score,
    }


def build_preferences_graph() -> StateGraph:
    """
    构建偏好 & 历史经验闭环的 LangGraph。
    
    Returns:
        编译后的 StateGraph
    """
    graph = StateGraph(JobHistoryState)
    
    # 添加节点
    graph.add_node("load_preference", node_load_preference)
    graph.add_node("compute_final_score", node_compute_final_score)
    
    # 设置入口点
    graph.set_entry_point("load_preference")
    
    # 添加边：线性流程
    graph.add_edge("load_preference", "compute_final_score")
    graph.add_edge("compute_final_score", END)
    
    return graph


def run_preferences_analysis(
    job_id: str,
    job_meta: Dict[str, Any],
    model_preference_score: Optional[float] = None,
) -> Dict[str, Any]:
    """
    运行偏好 & 历史经验分析的 helper 函数。
    
    Args:
        job_id: 职位 ID
        job_meta: 职位元信息（包含 match_score 等）
        model_preference_score: 可选的模型偏好分数（如果提供，将替代 job_meta 中的 match_score）
    
    Returns:
        完成后的 JobHistoryState（字典格式）
    """
    graph = build_preferences_graph().compile()
    
    initial_state: JobHistoryState = {
        "job_id": job_id,
        "job_meta": job_meta,
        "model_preference_score": model_preference_score,
    }
    
    if is_langsmith_enabled():
        config = default_langsmith_run_config("jobhunter_preferences")
        result = graph.invoke(initial_state, config=config)
    else:
        result = graph.invoke(initial_state)
    
    return result


if __name__ == "__main__":
    # 简单的 smoke test
    import sys
    from pathlib import Path
    
    # 添加项目根路径
    project_root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    print("Testing Flow 3: Preferences Graph")
    print("=" * 60)
    
    # 创建一个假的 job_meta
    test_job_meta = {
        "company": "Test Company",
        "title": "Senior Engineer",
        "match_score": 8.5,
        "category": "A",
    }
    
    result = run_preferences_analysis(
        job_id="test_123",
        job_meta=test_job_meta,
    )
    
    print("\nResults:")
    print(f"- User rating: {result.get('user_rating')}")
    print(f"- Final score: {result.get('final_score')}")
    
    # 测试有 rating 的情况
    print("\nTesting with user_rating=5:")
    test_state: JobHistoryState = {
        "job_id": "test_456",
        "job_meta": test_job_meta,
        "user_rating": 5,  # 直接设置 rating，跳过 load_preference
    }
    
    # 手动运行 compute_final_score
    result2 = node_compute_final_score(test_state)
    
    print(f"- Final score (with rating=5): {result2.get('final_score')}")
    print(f"  Expected: 8.5 + (5-3)*0.7 = 8.5 + 1.4 = 9.9")



