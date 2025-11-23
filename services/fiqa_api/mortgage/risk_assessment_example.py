"""
risk_assessment_example.py - 护栏起效方式示例
=============================================
展示风险评估护栏在实际业务流程中如何起效。

这个文件仅作为示例参考，展示护栏的集成方式。
"""

from services.fiqa_api.mortgage.risk_assessment import assess_risk
from services.fiqa_api.mortgage.schemas import StressCheckResponse


def example_1_guardrail_in_stress_check(stress_response: StressCheckResponse):
    """
    示例 1: 在 stress check 后检查护栏
    
    这是最常用的方式：在生成 stress check 结果后立即评估风险。
    """
    # A → B → C
    risk = assess_risk(stress_response=stress_response)
    
    # 根据护栏结果采取行动
    if risk.hard_block:
        # 🚫 硬拦截：强烈不建议继续
        print(f"🚫 硬拦截触发！风险标识: {risk.risk_flags}")
        print("行动：")
        print("  - 显示强烈警告信息")
        print("  - 建议用户降低价格或增加首付")
        print("  - 在前端禁用'继续申请'按钮")
        print("  - 记录高风险日志")
        
    elif risk.soft_warning:
        # ⚠️  软警告：需要谨慎
        print(f"⚠️  软警告触发！风险标识: {risk.risk_flags}")
        print("行动：")
        print("  - 显示黄色提示信息")
        print("  - 询问用户是否确认继续")
        print("  - '继续申请'按钮变为警告样式")
        
    else:
        # ✅ 低风险：可以继续
        print("✅ 风险评估通过，可以继续")
    
    return risk


def example_2_guardrail_before_llm_prompt(stress_response: StressCheckResponse):
    """
    示例 2: 在 LLM 生成解释前检查护栏
    
    根据风险评估结果，调整给 LLM 的提示词。
    """
    risk = assess_risk(stress_response=stress_response)
    
    # 构建 LLM 提示词
    base_prompt = f"用户的贷款方案：DTI={stress_response.dti_ratio:.1%}, stress_band={stress_response.stress_band}"
    
    if risk.hard_block:
        # 硬拦截：要求 LLM 必须强调高风险
        llm_prompt = f"""
{base_prompt}

⚠️ 高风险警告（必须强调）：
- 风险标识: {', '.join(risk.risk_flags)}
- 这是一个高风险案例，强烈不建议用户继续此方案。
- 你必须：
  1. 明确警告用户风险
  2. 建议降低购买价格或增加首付
  3. 提醒用户咨询专业贷款顾问
"""
    elif risk.soft_warning:
        # 软警告：要求 LLM 提醒谨慎
        llm_prompt = f"""
{base_prompt}

⚠️ 需要谨慎评估：
- 风险标识: {', '.join(risk.risk_flags)}
- 这个方案有一定风险，提醒用户谨慎考虑。
- 建议优化方案或增加财务缓冲。
"""
    else:
        # 低风险：正常解释
        llm_prompt = base_prompt
    
    return llm_prompt


def example_3_guardrail_filter_plans(plans: list):
    """
    示例 3: 在生成推荐前检查护栏
    
    过滤掉高风险的计划，或标记为"不推荐"。
    """
    from services.fiqa_api.mortgage.risk_assessment import assess_risk_from_plan
    
    safe_plans = []
    risky_plans = []
    
    for plan in plans:
        # 为每个计划评估风险
        risk = assess_risk_from_plan(
            dti_ratio=plan.dti_ratio,
            stress_band=None,  # 如果没有 stress_band，可以传入 None
            monthly_payment=plan.monthly_payment,
        )
        
        if risk.hard_block:
            # 🚫 硬拦截：不推荐这个计划
            risky_plans.append({
                "plan": plan,
                "risk": risk,
                "reason": "高风险，不推荐",
            })
        elif risk.soft_warning:
            # ⚠️  软警告：标记为需谨慎
            safe_plans.append({
                "plan": plan,
                "risk": risk,
                "tag": "需谨慎评估",
            })
        else:
            # ✅ 低风险：推荐
            safe_plans.append({
                "plan": plan,
                "risk": risk,
                "tag": "推荐",
            })
    
    return {
        "recommended": safe_plans,
        "not_recommended": risky_plans,
    }


def example_4_guardrail_in_api_response(stress_response: StressCheckResponse):
    """
    示例 4: 在 API 返回中包含风险评估（前端展示用）
    
    将风险评估结果附加到 API 响应中，供前端使用。
    """
    # 计算风险评估
    risk = assess_risk(stress_response=stress_response)
    
    # 构建增强的响应（向后兼容：可选字段）
    enhanced_response = {
        # 原有字段保持不变
        "total_monthly_payment": stress_response.total_monthly_payment,
        "dti_ratio": stress_response.dti_ratio,
        "stress_band": stress_response.stress_band,
        "hard_warning": stress_response.hard_warning,
        
        # 新增：结构化风险评估（前端可以轻松使用）
        "risk_assessment": {
            "risk_flags": risk.risk_flags,
            "hard_block": risk.hard_block,
            "soft_warning": risk.soft_warning,
        }
    }
    
    # 前端使用示例（伪代码）：
    # if (response.risk_assessment?.hard_block) {
    #   showRedWarning("强烈不建议继续此方案")
    #   disableButton("continue_apply")
    # } else if (response.risk_assessment?.soft_warning) {
    #   showYellowWarning("需要谨慎评估")
    #   setButtonStyle("continue_apply", "warning")
    # }
    
    return enhanced_response


if __name__ == "__main__":
    print("=" * 60)
    print("风险评估护栏 - 使用示例")
    print("=" * 60)
    print()
    print("这些示例展示了护栏在业务流程中的不同使用场景。")
    print("详见：risk_assessment.py 文档注释")
    print()

