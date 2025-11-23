"""
risk_assessment.py - Risk Assessment / Risk Control Fence Module
================================================================
风险评估/风控护栏模块：集中所有规则判断。

【最简洁用法】A → B → C
----------------------
A (输入): StressCheckResponse 或 CaseState
   ↓
B (处理): assess_risk(stress_response=...) 
   ↓
C (输出): RiskAssessment {
   - risk_flags: List[str]        # 风险标识，如 ['high_dti', 'negative_cashflow']
   - hard_block: bool              # True = 强烈不建议继续（硬拦截）
   - soft_warning: bool            # True = 需要谨慎（软警告）
}

【护栏是怎么起效的？】
--------------------

护栏作用方式：在业务流程关键节点进行检查，根据风险级别采取不同行动。

1️⃣ 【在 stress check 后检查】- 最常用
   ```
   业务流: run_stress_check() → 得到 StressCheckResponse
           ↓
           调用 assess_risk(stress_response=stress_response)
           ↓
           if result.hard_block:
               # 🚫 硬拦截：强烈不建议继续
               # 可以：阻止继续、显示警告、建议更安全的方案
           elif result.soft_warning:
               # ⚠️  软警告：需要谨慎
               # 可以：显示提示、询问用户确认、建议优化
   ```

2️⃣ 【在 LLM 生成解释前检查】
   ```
   业务流: 获取 stress_result
           ↓
           risk = assess_risk(stress_response=stress_result)
           ↓
           if risk.hard_block:
               # 告诉 LLM：必须强调高风险，不建议继续
               llm_prompt += f"⚠️ 高风险警告：{risk.risk_flags}"
           elif risk.soft_warning:
               # 告诉 LLM：需要提醒用户谨慎考虑
               llm_prompt += f"注意：{risk.risk_flags}"
   ```

3️⃣ 【在生成推荐前检查】
   ```
   业务流: 计算 affordability / 生成 mortgage plans
           ↓
           for plan in plans:
               risk = assess_risk_from_plan(dti_ratio=plan.dti_ratio, ...)
               if risk.hard_block:
                   # 过滤掉或标记为"不推荐"
                   plan.mark_as_not_recommended()
   ```

4️⃣ 【在前端展示时使用】
   ```
   API 返回: StressCheckResponse { ..., risk_assessment: RiskAssessment }
           ↓
   前端检查: if response.risk_assessment?.hard_block:
               // 显示红色警告框："强烈不建议继续此方案"
               // 禁用"继续申请"按钮
            elif response.risk_assessment?.soft_warning:
               // 显示黄色提示："需要谨慎评估"
               // "继续申请"按钮变为警告样式
   ```

【集成示例代码】
---------------
# 在 mortgage_agent_runtime.py 的 run_stress_check() 函数中：
from services.fiqa_api.mortgage.risk_assessment import assess_risk

# ... 生成 stress_response 后 ...

# 调用风险评估护栏
try:
    risk_assessment = assess_risk(stress_response=stress_response)
    # 可选：将风险评估结果附加到 response（不破坏向后兼容）
    # stress_response.risk_assessment = risk_assessment  # 暂时不暴露，先内部使用
    
    # 根据风险评估记录日志
    if risk_assessment.hard_block:
        logger.warning(
            f"level=WARN risk_hard_block_triggered "
            f"risk_flags={risk_assessment.risk_flags} "
            f"dti={stress_response.dti_ratio:.2%}"
        )
except Exception as e:
    logger.warning(f"level=WARN risk_assessment_failed error='{str(e)}'")
    # 不阻断主流程，仅记录警告

【设计原则】
-----------
1. 集中管理：所有风险规则统一在这里
2. 向后兼容：不改变现有 API，仅内部使用
3. 易于扩展：方便添加新的风险标识
4. 非阻断性：护栏检查失败不影响主流程，仅记录警告
"""

import logging
from typing import List, Optional, Union

from services.fiqa_api.mortgage.mortgage_profile import MORTGAGE_RULES
from services.fiqa_api.mortgage.schemas import (
    CaseState,
    RiskAssessment,
    StressCheckResponse,
    StressBand,
)

logger = logging.getLogger(__name__)


def assess_risk(
    stress_response: Optional[StressCheckResponse] = None,
    case_state: Optional[CaseState] = None,
) -> RiskAssessment:
    """
    Assess risk based on stress check response or case state.
    
    This is the main entry point for risk assessment. It consolidates all
    risk rules from stress_band, approval_score, and hard_warning logic.
    
    Args:
        stress_response: Optional StressCheckResponse instance
        case_state: Optional CaseState instance
    
    Returns:
        RiskAssessment with risk_flags, hard_block, and soft_warning
    
    Note:
        At least one of stress_response or case_state must be provided.
        If both are provided, stress_response takes precedence.
    """
    if stress_response is None and case_state is None:
        raise ValueError("At least one of stress_response or case_state must be provided")
    
    # Extract data from stress_response or case_state
    if stress_response is not None:
        dti_ratio = stress_response.dti_ratio
        stress_band = stress_response.stress_band
        hard_warning = stress_response.hard_warning
        total_monthly_payment = stress_response.total_monthly_payment
        wallet_snapshot = stress_response.wallet_snapshot or {}
        home_snapshot = stress_response.home_snapshot or {}
        approval_score = stress_response.approval_score
    else:
        # Extract from case_state
        risk_summary = case_state.risk_summary if case_state else {}
        dti_ratio = risk_summary.get("dti_ratio", 0.0)
        stress_band = risk_summary.get("stress_band", "ok")
        hard_warning = risk_summary.get("hard_warning")
        # Try to reconstruct from plans if available
        plans = case_state.plans if case_state else []
        if plans and plans[0].dti_ratio is not None:
            dti_ratio = plans[0].dti_ratio
        total_monthly_payment = plans[0].monthly_payment if plans else 0.0
        wallet_snapshot = {}
        home_snapshot = {}
        approval_score = None
    
    # Collect risk flags
    risk_flags: List[str] = []
    
    # Rule 1: High DTI ratio
    if dti_ratio > 0.43:
        risk_flags.append("high_dti")
    if dti_ratio > 0.80:
        risk_flags.append("very_high_dti")
    
    # Rule 2: Stress band classification
    if stress_band == "high_risk":
        risk_flags.append("high_risk_band")
    elif stress_band == "tight":
        risk_flags.append("tight_band")
    
    # Rule 3: Check if payment exceeds safe band
    safe_payment_band = wallet_snapshot.get("safe_payment_band", {})
    max_safe = safe_payment_band.get("max_safe", 0.0)
    if max_safe > 0 and total_monthly_payment > max_safe:
        excess_pct = (total_monthly_payment - max_safe) / max_safe
        if excess_pct > 0.20:  # More than 20% over safe band
            risk_flags.append("payment_way_above_safe_band")
        else:
            risk_flags.append("payment_above_safe_band")
    
    # Rule 4: Negative cashflow check
    monthly_income = wallet_snapshot.get("monthly_income", 0.0)
    other_debts = wallet_snapshot.get("other_debts_monthly", 0.0)
    if monthly_income > 0:
        remaining_income = monthly_income - total_monthly_payment - other_debts
        if remaining_income < 0:
            risk_flags.append("negative_cashflow")
        elif remaining_income < monthly_income * 0.1:  # Less than 10% buffer
            risk_flags.append("very_low_cashflow_buffer")
    
    # Rule 5: High LTV (Loan-to-Value)
    list_price = home_snapshot.get("list_price", 0.0)
    loan_amount = home_snapshot.get("loan_amount", 0.0)
    if list_price > 0 and loan_amount > 0:
        ltv_ratio = loan_amount / list_price
        if ltv_ratio > 0.90:
            risk_flags.append("very_high_ltv")
        elif ltv_ratio > 0.80:
            risk_flags.append("high_ltv")
    
    # Rule 6: Low down payment
    down_payment_pct = home_snapshot.get("down_payment_pct", 0.20)
    if down_payment_pct < 0.10:
        risk_flags.append("low_down_payment")
    elif down_payment_pct < 0.20:
        risk_flags.append("below_standard_down_payment")
    
    # Rule 7: Approval score indicators
    if approval_score:
        if approval_score.bucket == "unlikely":
            risk_flags.append("unlikely_approval")
        elif approval_score.bucket == "borderline":
            risk_flags.append("borderline_approval")
        
        # Add specific reasons from approval_score if available
        for reason in approval_score.reasons:
            if reason not in risk_flags:
                risk_flags.append(f"approval_{reason}")
    
    # Rule 8: Max affordability gap (from hard_warning logic)
    if hard_warning:
        # If hard_warning exists, it indicates a serious issue
        risk_flags.append("affordability_gap")
    
    # Determine hard_block: Cases that should be strongly discouraged
    hard_block = False
    # Hard block conditions (consolidated from build_hard_warning_if_needed)
    if dti_ratio > 0.80:
        hard_block = True
    if stress_band == "high_risk":
        hard_block = True
    if hard_warning is not None:
        hard_block = True
    if "negative_cashflow" in risk_flags:
        hard_block = True
    if max_safe > 0 and total_monthly_payment > max_safe * 1.20:  # >20% over safe band
        hard_block = True
    
    # Determine soft_warning: Cases that need caution
    soft_warning = False
    if not hard_block:  # Only set soft_warning if not hard_block
        if stress_band in ("tight", "high_risk"):
            soft_warning = True
        if dti_ratio > MORTGAGE_RULES["dti_medium_threshold"]:
            soft_warning = True
        if "payment_above_safe_band" in risk_flags:
            soft_warning = True
        if "very_low_cashflow_buffer" in risk_flags:
            soft_warning = True
        if approval_score and approval_score.bucket == "borderline":
            soft_warning = True
    
    return RiskAssessment(
        risk_flags=risk_flags,
        hard_block=hard_block,
        soft_warning=soft_warning,
    )


def assess_risk_from_plan(
    dti_ratio: float,
    stress_band: Optional[StressBand] = None,
    monthly_payment: Optional[float] = None,
    max_affordability: Optional[dict] = None,
    target_purchase_price: Optional[float] = None,
) -> RiskAssessment:
    """
    Assess risk from individual plan data (convenience function for mortgage plans).
    
    This is a simplified version for cases where we only have plan-level data
    (like in the mortgage agent response).
    
    Args:
        dti_ratio: Debt-to-income ratio
        stress_band: Optional stress band classification
        monthly_payment: Optional monthly payment amount
        max_affordability: Optional max affordability dict with max_home_price
        target_purchase_price: Optional target purchase price for affordability comparison
    
    Returns:
        RiskAssessment with risk_flags, hard_block, and soft_warning
    """
    risk_flags: List[str] = []
    
    # Rule 1: High DTI
    if dti_ratio > 0.43:
        risk_flags.append("high_dti")
    if dti_ratio > 0.80:
        risk_flags.append("very_high_dti")
    
    # Rule 2: Stress band
    if stress_band == "high_risk":
        risk_flags.append("high_risk_band")
    elif stress_band == "tight":
        risk_flags.append("tight_band")
    
    # Rule 3: Affordability gap (from build_hard_warning_if_needed logic)
    if max_affordability and target_purchase_price:
        max_home_price = max_affordability.get("max_home_price", 0.0)
        if max_home_price > 0:
            gap_ratio = (target_purchase_price - max_home_price) / target_purchase_price
            if gap_ratio > 0.30:  # Gap > 30%
                risk_flags.append("affordability_gap")
    
    # Determine hard_block
    hard_block = False
    if dti_ratio > 0.80:
        hard_block = True
    if stress_band == "high_risk":
        hard_block = True
    if max_affordability and target_purchase_price:
        max_home_price = max_affordability.get("max_home_price", 0.0)
        if max_home_price > 0:
            gap_ratio = (target_purchase_price - max_home_price) / target_purchase_price
            if gap_ratio > 0.30:
                hard_block = True
    
    # Determine soft_warning
    soft_warning = False
    if not hard_block:
        if stress_band in ("tight", "high_risk"):
            soft_warning = True
        if dti_ratio > MORTGAGE_RULES["dti_medium_threshold"]:
            soft_warning = True
    
    return RiskAssessment(
        risk_flags=risk_flags,
        hard_block=hard_block,
        soft_warning=soft_warning,
    )


__all__ = [
    "assess_risk",
    "assess_risk_from_plan",
    "RiskAssessment",
]

