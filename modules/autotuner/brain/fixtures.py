"""
AutoTuner Brain - 测试样例集

构造各种场景的 TuningInput 样例，用于测试和验证决策逻辑。
"""

from typing import List, NamedTuple
from .contracts import TuningInput, SLO, Guards


class NamedFixture(NamedTuple):
    """带名称的测试样例"""
    name: str
    tuning_input: TuningInput


def create_fixtures() -> List[NamedFixture]:
    """
    创建测试样例集
    
    Returns:
        包含各种场景的 NamedFixture 列表
    """
    fixtures = []
    
    # 基础SLO和参数配置
    base_slo = SLO(p95_ms=200.0, recall_at10=0.85)
    base_params = {
        'ef': 128,
        'T': 500, 
        'Ncand_max': 1000,
        'rerank_mult': 3
    }
    
    # 1. 高延迟 + 召回富余 -> 应该降ef
    fixtures.append(NamedFixture(
        name="high_latency_recall_redundant",
        tuning_input=TuningInput(
            p95_ms=250.0,  # 超出SLO
            recall_at10=0.92,  # 有富余
            qps=100.0,
            params=base_params.copy(),
            slo=base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=False,
            last_action=None,
            adjustment_count=0
        )
    ))
    
    # 2. 低召回 + 延迟富余 -> 应该升ef
    fixtures.append(NamedFixture(
        name="low_recall_latency_margin",
        tuning_input=TuningInput(
            p95_ms=90.0,  # 有富余 (90 <= 200-100)
            recall_at10=0.80,  # 低于SLO
            qps=100.0,
            params=base_params.copy(),
            slo=base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=False,
            last_action=None,
            adjustment_count=0
        )
    ))
    
    # 3. near_T + 超标 + 稳定 -> 应该升T
    fixtures.append(NamedFixture(
        name="near_T_boundary_optimization",
        tuning_input=TuningInput(
            p95_ms=220.0,  # 超出SLO
            recall_at10=0.87,  # 满足SLO
            qps=100.0,
            params=base_params.copy(),
            slo=base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=True,
            last_action=None,
            adjustment_count=0
        )
    ))
    
    # 4. 冷却期 -> 应该noop
    fixtures.append(NamedFixture(
        name="cooldown_active",
        tuning_input=TuningInput(
            p95_ms=250.0,  # 超出SLO
            recall_at10=0.80,  # 低于SLO
            qps=100.0,
            params=base_params.copy(),
            slo=base_slo,
            guards=Guards(cooldown=True, stable=True),
            near_T=False,
            last_action=None,
            adjustment_count=0
        )
    ))
    
    # 5. 都达标 -> 应该noop
    fixtures.append(NamedFixture(
        name="within_slo",
        tuning_input=TuningInput(
            p95_ms=180.0,  # 满足SLO
            recall_at10=0.87,  # 满足SLO
            qps=100.0,
            params=base_params.copy(),
            slo=base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=False,
            last_action=None,
            adjustment_count=0
        )
    ))
    
    # 6. ef已达最小值 + 高延迟 -> 应该降ncand
    min_ef_params = base_params.copy()
    min_ef_params['ef'] = 64
    fixtures.append(NamedFixture(
        name="ef_at_min_drop_ncand",
        tuning_input=TuningInput(
            p95_ms=240.0,  # 超出SLO
            recall_at10=0.90,  # 有富余
            qps=100.0,
            params=min_ef_params,
            slo=base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=False,
            last_action=None,
            adjustment_count=0
        )
    ))
    
    # 7. ef已达最大值 + 低召回 -> 应该升rerank
    max_ef_params = base_params.copy()
    max_ef_params['ef'] = 256
    fixtures.append(NamedFixture(
        name="ef_at_max_bump_rerank",
        tuning_input=TuningInput(
            p95_ms=90.0,  # 有富余 (90 <= 200-100)
            recall_at10=0.82,  # 低于SLO
            qps=100.0,
            params=max_ef_params,
            slo=base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=False,
            last_action=None,
            adjustment_count=0
        )
    ))
    
    # 8. 边界值测试 - 刚好在SLO边界
    fixtures.append(NamedFixture(
        name="slo_boundary",
        tuning_input=TuningInput(
            p95_ms=200.0,  # 刚好等于SLO
            recall_at10=0.85,  # 刚好等于SLO
            qps=100.0,
            params=base_params.copy(),
            slo=base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=False,
            last_action=None,
            adjustment_count=0
        )
    ))
    
    # 9. 不确定状态 - 不稳定
    fixtures.append(NamedFixture(
        name="unstable_state",
        tuning_input=TuningInput(
            p95_ms=210.0,  # 略微超出SLO
            recall_at10=0.86,  # 略微超出SLO
            qps=100.0,
            params=base_params.copy(),
            slo=base_slo,
            guards=Guards(cooldown=False, stable=False),
            near_T=False,
            last_action=None,
            adjustment_count=0
        )
    ))
    
    # 10. 极端高延迟
    fixtures.append(NamedFixture(
        name="extreme_high_latency",
        tuning_input=TuningInput(
            p95_ms=400.0,  # 严重超出SLO
            recall_at10=0.95,  # 有富余
            qps=100.0,
            params=base_params.copy(),
            slo=base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=False,
            last_action=None,
            adjustment_count=0
        )
    ))
    
    # 11. 极端低召回
    fixtures.append(NamedFixture(
        name="extreme_low_recall",
        tuning_input=TuningInput(
            p95_ms=120.0,  # 有富余
            recall_at10=0.70,  # 严重低于SLO
            qps=100.0,
            params=base_params.copy(),
            slo=base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=False,
            last_action=None,
            adjustment_count=0
        )
    ))
    
    # 12. 临界区 + 不稳定 -> 应该noop
    fixtures.append(NamedFixture(
        name="near_T_unstable",
        tuning_input=TuningInput(
            p95_ms=220.0,  # 超出SLO
            recall_at10=0.87,  # 满足SLO
            qps=100.0,
            params=base_params.copy(),
            slo=base_slo,
            guards=Guards(cooldown=False, stable=False),  # 不稳定
            near_T=True,
            last_action=None,
            adjustment_count=0
        )
    ))
    
    return fixtures


def get_fixture_by_name(name: str) -> TuningInput:
    """
    根据名称获取特定的测试样例
    
    Args:
        name: 样例名称
        
    Returns:
        对应的 TuningInput 样例
    """
    fixtures = create_fixtures()
    for fixture in fixtures:
        if fixture.name == name:
            return fixture.tuning_input
    raise ValueError(f"Fixture '{name}' not found")


def get_all_fixture_names() -> List[str]:
    """
    获取所有测试样例的名称列表
    
    Returns:
        样例名称列表
    """
    fixtures = create_fixtures()
    return [fixture.name for fixture in fixtures]
