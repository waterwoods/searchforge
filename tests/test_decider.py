"""
AutoTuner Brain - 单元测试

测试核心决策逻辑，覆盖主要路径和边界情况。
"""

import pytest
import sys
import os

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.autotuner.brain.contracts import TuningInput, SLO, Guards, Action
from modules.autotuner.brain.decider import decide_tuning_action, analyze_tuning_input
from modules.autotuner.brain.constraints import clip_params, is_param_valid
from modules.autotuner.brain.apply import apply_action


class TestDecider:
    """测试决策逻辑"""
    
    def setup_method(self):
        """测试前的设置"""
        self.base_slo = SLO(p95_ms=200.0, recall_at10=0.85)
        self.base_params = {
            'ef': 128,
            'T': 500,
            'Ncand_max': 1000,
            'rerank_mult': 3
        }
    
    def test_cooldown_returns_noop(self):
        """测试冷却期返回 noop"""
        inp = TuningInput(
            p95_ms=300.0,  # 严重超标
            recall_at10=0.70,  # 严重不达标
            qps=100.0,
            params=self.base_params.copy(),
            slo=self.base_slo,
            guards=Guards(cooldown=True, stable=True),
            near_T=False
        )
        
        action = decide_tuning_action(inp)
        
        assert action.kind == "noop"
        assert action.step == 0.0
        assert "cooldown" in action.reason.lower()
    
    def test_high_latency_recall_redundant_drops_ef(self):
        """测试高延迟且召回富余时降 ef"""
        inp = TuningInput(
            p95_ms=250.0,  # 超出SLO
            recall_at10=0.92,  # 有富余
            qps=100.0,
            params=self.base_params.copy(),
            slo=self.base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=False
        )
        
        action = decide_tuning_action(inp)
        
        assert action.kind == "drop_ef"
        assert action.step == -32.0
        assert "latency" in action.reason.lower()
        assert "recall" in action.reason.lower()
    
    def test_low_recall_latency_margin_bumps_ef(self):
        """测试低召回且延迟富余时升 ef"""
        inp = TuningInput(
            p95_ms=90.0,  # 有富余 (90 <= 200-100)
            recall_at10=0.80,  # 低于SLO
            qps=100.0,
            params=self.base_params.copy(),
            slo=self.base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=False
        )
        
        action = decide_tuning_action(inp)
        
        assert action.kind == "bump_ef"
        assert action.step == 32.0
        assert "recall" in action.reason.lower()
        assert "latency" in action.reason.lower()
    
    def test_near_T_boundary_optimization_bumps_T(self):
        """测试临界区优化时升 T"""
        inp = TuningInput(
            p95_ms=220.0,  # 超出SLO
            recall_at10=0.87,  # 满足SLO
            qps=100.0,
            params=self.base_params.copy(),
            slo=self.base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=True
        )
        
        action = decide_tuning_action(inp)
        
        assert action.kind == "bump_T"
        assert action.step == 100.0
        assert "boundary" in action.reason.lower() or "near" in action.reason.lower()
    
    def test_ef_at_min_drops_ncand(self):
        """测试 ef 已达最小值时降 ncand"""
        min_ef_params = self.base_params.copy()
        min_ef_params['ef'] = 64
        
        inp = TuningInput(
            p95_ms=240.0,  # 超出SLO
            recall_at10=0.90,  # 有富余
            qps=100.0,
            params=min_ef_params,
            slo=self.base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=False
        )
        
        action = decide_tuning_action(inp)
        
        assert action.kind == "drop_ncand"
        assert action.step == -200.0
        assert "ncand" in action.reason.lower()
    
    def test_ef_at_max_bumps_rerank(self):
        """测试 ef 已达最大值时升 rerank"""
        max_ef_params = self.base_params.copy()
        max_ef_params['ef'] = 256
        
        inp = TuningInput(
            p95_ms=90.0,  # 有富余 (90 <= 200-100)
            recall_at10=0.82,  # 低于SLO
            qps=100.0,
            params=max_ef_params,
            slo=self.base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=False
        )
        
        action = decide_tuning_action(inp)
        
        assert action.kind == "bump_rerank"
        assert action.step == 1.0
        assert "rerank" in action.reason.lower()
    
    def test_within_slo_returns_noop(self):
        """测试在 SLO 范围内时返回 noop"""
        inp = TuningInput(
            p95_ms=180.0,  # 满足SLO
            recall_at10=0.87,  # 满足SLO
            qps=100.0,
            params=self.base_params.copy(),
            slo=self.base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=False
        )
        
        action = decide_tuning_action(inp)
        
        assert action.kind == "noop"
        assert action.step == 0.0
        assert "slo" in action.reason.lower() or "uncertain" in action.reason.lower()
    
    def test_near_T_unstable_returns_noop(self):
        """测试 near_T 但不稳定时返回 noop"""
        inp = TuningInput(
            p95_ms=220.0,  # 超出SLO
            recall_at10=0.87,  # 满足SLO
            qps=100.0,
            params=self.base_params.copy(),
            slo=self.base_slo,
            guards=Guards(cooldown=False, stable=False),  # 不稳定
            near_T=True
        )
        
        action = decide_tuning_action(inp)
        
        assert action.kind == "noop"
        assert action.step == 0.0


class TestConstraints:
    """测试参数约束"""
    
    def test_clip_params_within_range(self):
        """测试参数在范围内时不被裁剪"""
        params = {'ef': 128, 'T': 500, 'Ncand_max': 1000, 'rerank_mult': 3}
        clipped = clip_params(params)
        assert clipped == params
    
    def test_clip_params_out_of_range(self):
        """测试参数超出范围时被裁剪"""
        params = {'ef': 32, 'T': 50, 'Ncand_max': 100, 'rerank_mult': 1}
        clipped = clip_params(params)
        assert clipped['ef'] == 64  # 最小值
        assert clipped['T'] == 200  # 最小值
        assert clipped['Ncand_max'] == 500  # 最小值
        assert clipped['rerank_mult'] == 2  # 最小值
    
    def test_is_param_valid(self):
        """测试参数有效性检查"""
        valid_params = {'ef': 128, 'T': 500, 'Ncand_max': 1000, 'rerank_mult': 3}
        invalid_params = {'ef': 32, 'T': 50, 'Ncand_max': 100, 'rerank_mult': 1}
        
        assert is_param_valid(valid_params) is True
        assert is_param_valid(invalid_params) is False


class TestApply:
    """测试动作应用"""
    
    def test_apply_bump_ef(self):
        """测试应用 bump_ef 动作"""
        params = {'ef': 128, 'T': 500, 'Ncand_max': 1000, 'rerank_mult': 3}
        action = Action(kind="bump_ef", step=32.0, reason="test")
        
        new_params = apply_action(params, action)
        
        assert new_params['ef'] == 160
        assert new_params['T'] == 500  # 不变
        assert new_params['Ncand_max'] == 1000  # 不变
        assert new_params['rerank_mult'] == 3  # 不变
    
    def test_apply_drop_ef(self):
        """测试应用 drop_ef 动作"""
        params = {'ef': 128, 'T': 500, 'Ncand_max': 1000, 'rerank_mult': 3}
        action = Action(kind="drop_ef", step=-32.0, reason="test")
        
        new_params = apply_action(params, action)
        
        assert new_params['ef'] == 96
        assert new_params['T'] == 500  # 不变
        assert new_params['Ncand_max'] == 1000  # 不变
        assert new_params['rerank_mult'] == 3  # 不变
    
    def test_apply_bump_T(self):
        """测试应用 bump_T 动作"""
        params = {'ef': 128, 'T': 500, 'Ncand_max': 1000, 'rerank_mult': 3}
        action = Action(kind="bump_T", step=100.0, reason="test")
        
        new_params = apply_action(params, action)
        
        assert new_params['ef'] == 128  # 不变
        assert new_params['T'] == 600
        assert new_params['Ncand_max'] == 1000  # 不变
        assert new_params['rerank_mult'] == 3  # 不变
    
    def test_apply_noop(self):
        """测试应用 noop 动作"""
        params = {'ef': 128, 'T': 500, 'Ncand_max': 1000, 'rerank_mult': 3}
        action = Action(kind="noop", step=0.0, reason="test")
        
        new_params = apply_action(params, action)
        
        assert new_params == params  # 完全不变
    
    def test_apply_with_clipping(self):
        """测试动作应用后的参数裁剪"""
        params = {'ef': 240, 'T': 500, 'Ncand_max': 1000, 'rerank_mult': 3}
        action = Action(kind="bump_ef", step=32.0, reason="test")
        
        new_params = apply_action(params, action)
        
        # ef 应该是 272，但被裁剪到最大值 256
        assert new_params['ef'] == 256
        assert is_param_valid(new_params) is True


class TestAnalyzeTuningInput:
    """测试输入分析功能"""
    
    def setup_method(self):
        """测试前的设置"""
        self.base_slo = SLO(p95_ms=200.0, recall_at10=0.85)
        self.base_params = {
            'ef': 128,
            'T': 500,
            'Ncand_max': 1000,
            'rerank_mult': 3
        }
    
    def test_analyze_tuning_input(self):
        """测试调优输入分析"""
        inp = TuningInput(
            p95_ms=250.0,  # 超出SLO
            recall_at10=0.92,  # 有富余
            qps=100.0,
            params={'ef': 128, 'T': 500, 'Ncand_max': 1000, 'rerank_mult': 3},
            slo=SLO(p95_ms=200.0, recall_at10=0.85),
            guards=Guards(cooldown=False, stable=True),
            near_T=False,
            last_action=None,
            adjustment_count=0
        )
        
        analysis = analyze_tuning_input(inp)
        
        assert analysis['latency_violation'] is True
        assert analysis['recall_violation'] is False
        assert analysis['recall_redundancy'] is True
        assert analysis['latency_margin'] is False
        assert analysis['cooldown_active'] is False
        assert analysis['stable_state'] is True
        assert analysis['near_boundary'] is False
        assert analysis['ef_at_min'] is False
        assert analysis['ef_at_max'] is False

    def test_hysteresis_noop(self):
        """测试滞回带：小误差时应返回 noop"""
        # 误差在滞回带内：p95误差 < 100ms, recall误差 < 0.02
        inp = TuningInput(
            p95_ms=210.0,  # 误差 = 10ms < 100ms
            recall_at10=0.86,  # 误差 = 0.01 < 0.02
            qps=100.0,
            params=self.base_params.copy(),
            slo=self.base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=False,
            last_action=None,
            adjustment_count=0
        )
        
        action = decide_tuning_action(inp)
        
        assert action.kind == "noop"
        assert action.step == 0.0
        assert "hysteresis" in action.reason.lower()
    
    def test_cooldown_block_repeat_action(self):
        """测试冷却时间：短间隔重复动作应跳过"""
        # 上一轮执行了 bump_ef，间隔 < 10 秒
        last_action = Action(
            kind="bump_ef",
            step=32.0,
            reason="test",
            age_sec=5.0  # 间隔 5 秒 < 10 秒
        )
        
        inp = TuningInput(
            p95_ms=90.0,  # 低延迟
            recall_at10=0.80,  # 低召回
            qps=100.0,
            params=self.base_params.copy(),
            slo=self.base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=False,
            last_action=last_action,
            adjustment_count=1
        )
        
        action = decide_tuning_action(inp)
        
        assert action.kind == "noop"
        assert action.step == 0.0
        assert "cooldown" in action.reason.lower()
    
    def test_adaptive_step_halved(self):
        """测试自适应步长：连续同方向动作步长减半"""
        # 连续两次同方向调整
        inp = TuningInput(
            p95_ms=250.0,  # 高延迟
            recall_at10=0.92,  # 召回富余
            qps=100.0,
            params=self.base_params.copy(),
            slo=self.base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=False,
            last_action=None,
            adjustment_count=2  # 连续两次调整
        )
        
        action = decide_tuning_action(inp)
        
        assert action.kind == "drop_ef"
        assert action.step == -16.0  # 原始 -32.0 减半
        assert "high_latency" in action.reason.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
