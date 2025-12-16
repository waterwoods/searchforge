"""
graphs/ - LangGraph Flows for JobHunter

这是三个可复用的 LangGraph flow，方便以后挂到 Web / K8s / 评估系统上。

Flow 1: JD 解读 + 适配度（单次分析闭环）
Flow 2: JD 职业教练对话（多轮对话闭环）
Flow 3: 偏好 & 历史经验闭环（影响排序和建议）
"""

from .jd_analysis_graph import build_jd_analysis_graph, run_jd_analysis
from .jd_chat_graph import build_jd_chat_graph
from .preferences_graph import build_preferences_graph, run_preferences_analysis

__all__ = [
    "build_jd_analysis_graph",
    "run_jd_analysis",
    "build_jd_chat_graph",
    "build_preferences_graph",
    "run_preferences_analysis",
]




