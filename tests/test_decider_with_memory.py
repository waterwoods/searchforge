"""
AutoTuner Brain - 记忆驱动决策测试

测试记忆钩子在决策过程中的作用
"""

import pytest
import sys
import os
import time

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.autotuner.brain.contracts import TuningInput, SLO, Guards, MemorySample
from modules.autotuner.brain.decider import decide_tuning_action
from modules.autotuner.brain.memory import get_memory


class TestDeciderWithMemory:
    """测试记忆驱动的决策"""
    
    def setup_method(self):
        """测试前的设置"""
        # 设置环境变量
        os.environ['MEMORY_ENABLED'] = '1'
        os.environ['MEMORY_TTL_SEC'] = '3600'  # 1小时，避免过期
        
        self.base_slo = SLO(p95_ms=200.0, recall_at10=0.85)
        self.base_params = {
            'ef': 128,
            'T': 500,
            'Ncand_max': 1000,
            'rerank_mult': 3
        }
        
        # 清空全局记忆
        self.memory = get_memory()
        self.memory.ring_buffer.clear()
        self.memory.ewma_data.clear()
        self.memory.sweet_spots.clear()
        self.memory.last_update.clear()
    
    def teardown_method(self):
        """测试后的清理"""
        # 清理环境变量
        if 'MEMORY_ENABLED' in os.environ:
            del os.environ['MEMORY_ENABLED']
        if 'MEMORY_TTL_SEC' in os.environ:
            del os.environ['MEMORY_TTL_SEC']
    
    def _train_memory_with_ef(self, ef: int, count: int = 5):
        """训练记忆，使用指定的ef值"""
        bucket_id = "medium_candidates"  # 对应Ncand_max=1000
        
        for i in range(count):
            sample = MemorySample(
                bucket_id=bucket_id,
                ef=ef,
                T=500,
                Ncand_max=1000,
                p95_ms=150.0,  # 满足SLO
                recall_at10=0.87,  # 满足SLO
                ts=time.time()
            )
            self.memory.observe(sample)
    
    def test_scenario1_memory_hit_nudge_towards_sweet_spot(self):
        """场景1：记忆命中，小步靠拢甜点"""
        # 训练记忆：甜点ef=160
        self._train_memory_with_ef(160, 10)
        
        # 当前ef=128，应该小步靠拢到160
        inp = TuningInput(
            p95_ms=90.0,  # 低延迟
            recall_at10=0.80,  # 低召回
            qps=100.0,
            params=self.base_params.copy(),
            slo=self.base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=False,
            last_action=None,
            adjustment_count=0
        )
        
        action = decide_tuning_action(inp)
        
        # 应该返回记忆驱动的动作
        assert action.kind == "bump_ef"
        assert action.step == 16  # 小步长
        assert "memory" in action.reason.lower()
    
    def test_scenario2_memory_hit_nudge_down_towards_sweet_spot(self):
        """场景2：记忆命中，从高ef小步靠拢甜点"""
        # 训练记忆：甜点ef=160
        self._train_memory_with_ef(160, 10)
        
        # 当前ef=192，应该小步靠拢到160
        params = self.base_params.copy()
        params['ef'] = 192
        
        inp = TuningInput(
            p95_ms=90.0,  # 低延迟
            recall_at10=0.80,  # 低召回
            qps=100.0,
            params=params,
            slo=self.base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=False,
            last_action=None,
            adjustment_count=0
        )
        
        action = decide_tuning_action(inp)
        
        # 应该返回记忆驱动的动作
        assert action.kind == "drop_ef"
        assert action.step == -16  # 小步长
        assert "memory" in action.reason.lower()
    
    def test_scenario3_memory_expired_fallback_to_original_logic(self):
        """场景3：记忆过期，回退到原逻辑"""
        # 训练记忆但让它过期
        self._train_memory_with_ef(160, 10)
        self.memory.last_update["medium_candidates"] = time.time() - 7200  # 2小时前
        
        inp = TuningInput(
            p95_ms=90.0,  # 低延迟
            recall_at10=0.80,  # 低召回
            qps=100.0,
            params=self.base_params.copy(),
            slo=self.base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=False,
            last_action=None,
            adjustment_count=0
        )
        
        action = decide_tuning_action(inp)
        
        # 应该回退到原逻辑
        assert action.kind == "bump_ef"
        assert action.step == 32  # 常规步长
        assert "latency_margin" in action.reason.lower()
    
    def test_scenario4_memory_disabled_fallback_to_original_logic(self):
        """场景4：记忆功能禁用，回退到原逻辑"""
        # 禁用记忆功能
        os.environ['MEMORY_ENABLED'] = '0'
        
        # 训练记忆
        self._train_memory_with_ef(160, 10)
        
        inp = TuningInput(
            p95_ms=90.0,  # 低延迟
            recall_at10=0.80,  # 低召回
            qps=100.0,
            params=self.base_params.copy(),
            slo=self.base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=False,
            last_action=None,
            adjustment_count=0
        )
        
        action = decide_tuning_action(inp)
        
        # 应该回退到原逻辑
        assert action.kind == "bump_ef"
        assert action.step == 32  # 常规步长
        assert "latency_margin" in action.reason.lower()
    
    def test_scenario5_at_sweet_spot_noop(self):
        """场景5：已在甜点位置，返回noop"""
        # 训练记忆：甜点ef=160
        self._train_memory_with_ef(160, 10)
        
        # 当前ef=160，已经在甜点位置
        params = self.base_params.copy()
        params['ef'] = 160
        
        inp = TuningInput(
            p95_ms=90.0,  # 低延迟
            recall_at10=0.80,  # 低召回
            qps=100.0,
            params=params,
            slo=self.base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=False,
            last_action=None,
            adjustment_count=0
        )
        
        action = decide_tuning_action(inp)
        
        # 应该返回noop
        assert action.kind == "noop"
        assert action.step == 0.0
        assert "sweet_spot" in action.reason.lower()
    
    def test_scenario6_memory_invalid_sweet_spot_fallback(self):
        """场景6：记忆中的甜点无效，回退到原逻辑"""
        # 训练记忆但甜点不满足SLO
        bucket_id = "medium_candidates"
        for i in range(5):
            sample = MemorySample(
                bucket_id=bucket_id,
                ef=128,
                T=500,
                Ncand_max=1000,
                p95_ms=250.0,  # 不满足SLO
                recall_at10=0.70,  # 不满足SLO
                ts=time.time()
            )
            self.memory.observe(sample)
        
        inp = TuningInput(
            p95_ms=90.0,  # 低延迟
            recall_at10=0.80,  # 低召回
            qps=100.0,
            params=self.base_params.copy(),
            slo=self.base_slo,
            guards=Guards(cooldown=False, stable=True),
            near_T=False,
            last_action=None,
            adjustment_count=0
        )
        
        action = decide_tuning_action(inp)
        
        # 应该回退到原逻辑
        assert action.kind == "bump_ef"
        assert action.step == 32  # 常规步长
        assert "latency_margin" in action.reason.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

