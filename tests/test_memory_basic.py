"""
AutoTuner Brain - 记忆层基础测试

测试记忆系统的基本功能：环形缓冲、EWMA计算、甜点发现
"""

import pytest
import sys
import os
import time

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.autotuner.brain.memory import Memory
from modules.autotuner.brain.contracts import MemorySample


class TestMemoryBasic:
    """测试记忆系统基础功能"""
    
    def setup_method(self):
        """测试前的设置"""
        # 设置环境变量
        os.environ['MEMORY_ENABLED'] = '1'
        os.environ['MEMORY_RING_SIZE'] = '10'  # 小缓冲区便于测试
        os.environ['MEMORY_ALPHA'] = '0.5'    # 高alpha便于测试
        os.environ['MEMORY_TTL_SEC'] = '60'   # 短TTL便于测试
        
        self.memory = Memory()
    
    def teardown_method(self):
        """测试后的清理"""
        # 清理环境变量
        for key in ['MEMORY_ENABLED', 'MEMORY_RING_SIZE', 'MEMORY_ALPHA', 'MEMORY_TTL_SEC']:
            if key in os.environ:
                del os.environ[key]
    
    def test_memory_sample_creation(self):
        """测试记忆样本创建"""
        sample = MemorySample(
            bucket_id="test_bucket",
            ef=128,
            T=500,
            Ncand_max=1000,
            p95_ms=150.0,
            recall_at10=0.87,
            ts=time.time()
        )
        
        assert sample.bucket_id == "test_bucket"
        assert sample.ef == 128
        assert sample.p95_ms == 150.0
        assert sample.recall_at10 == 0.87
    
    def test_observe_and_ring_buffer(self):
        """测试观测和环形缓冲"""
        # 添加多个样本
        for i in range(15):  # 超过缓冲区大小
            sample = MemorySample(
                bucket_id="test_bucket",
                ef=128 + i,
                T=500,
                Ncand_max=1000,
                p95_ms=150.0 + i,
                recall_at10=0.87,
                ts=time.time()
            )
            self.memory.observe(sample)
        
        # 检查缓冲区大小
        assert len(self.memory.ring_buffer) == 10  # 环形缓冲大小限制
        
        # 检查最后一个样本
        last_sample = self.memory.ring_buffer[-1]
        assert last_sample.ef == 142  # 128 + 14
    
    def test_ewma_calculation(self):
        """测试EWMA计算"""
        bucket_id = "test_bucket"
        ef = 128
        
        # 添加多个相同ef的样本
        samples = [
            MemorySample(bucket_id, ef, 500, 1000, 200.0, 0.80, time.time()),
            MemorySample(bucket_id, ef, 500, 1000, 180.0, 0.85, time.time()),
            MemorySample(bucket_id, ef, 500, 1000, 160.0, 0.90, time.time()),
        ]
        
        for sample in samples:
            self.memory.observe(sample)
        
        # 检查EWMA数据
        assert ef in self.memory.ewma_data[bucket_id]
        ewma_p95, ewma_recall, count = self.memory.ewma_data[bucket_id][ef]
        
        # EWMA应该收敛到较小的值
        assert ewma_p95 < 200.0
        assert ewma_recall > 0.80
        assert count == 3
    
    def test_sweet_spot_discovery(self):
        """测试甜点发现"""
        bucket_id = "test_bucket"
        
        # 添加满足SLO的样本（p95 <= 200, recall >= 0.85）
        good_samples = [
            MemorySample(bucket_id, 160, 500, 1000, 180.0, 0.87, time.time()),
            MemorySample(bucket_id, 192, 500, 1000, 190.0, 0.88, time.time()),
            MemorySample(bucket_id, 128, 500, 1000, 170.0, 0.86, time.time()),
        ]
        
        for sample in good_samples:
            self.memory.observe(sample)
        
        # 查询甜点
        sweet_spot = self.memory.query(bucket_id)
        
        assert sweet_spot is not None
        assert sweet_spot.meets_slo is True
        assert sweet_spot.ef == 128  # 应该选择最小的ef
    
    def test_sweet_spot_no_valid_ef(self):
        """测试没有满足SLO的ef时甜点处理"""
        bucket_id = "test_bucket"
        
        # 添加不满足SLO的样本
        bad_samples = [
            MemorySample(bucket_id, 128, 500, 1000, 250.0, 0.80, time.time()),  # 延迟过高
            MemorySample(bucket_id, 160, 500, 1000, 180.0, 0.70, time.time()),  # 召回过低
        ]
        
        for sample in bad_samples:
            self.memory.observe(sample)
        
        # 查询甜点
        sweet_spot = self.memory.query(bucket_id)
        
        # 应该没有有效的甜点
        assert sweet_spot is None
    
    def test_sweet_spot_staleness(self):
        """测试甜点过期"""
        bucket_id = "test_bucket"
        
        # 添加样本
        sample = MemorySample(bucket_id, 128, 500, 1000, 180.0, 0.87, time.time())
        self.memory.observe(sample)
        
        # 立即查询应该有效
        sweet_spot = self.memory.query(bucket_id)
        assert sweet_spot is not None
        assert sweet_spot.meets_slo is True
        
        # 模拟时间过期
        self.memory.last_update[bucket_id] = time.time() - 120  # 2分钟前
        
        # 查询应该过期
        sweet_spot = self.memory.query(bucket_id)
        assert sweet_spot is None
    
    def test_bucket_id_calculation(self):
        """测试流量桶ID计算"""
        # 模拟TuningInput
        class MockTuningInput:
            def __init__(self, ncand):
                self.params = {'Ncand_max': ncand}
        
        # 测试不同候选数量的分桶
        small_input = MockTuningInput(600)
        medium_input = MockTuningInput(1000)
        large_input = MockTuningInput(1500)
        
        assert self.memory.default_bucket_of(small_input) == "small_candidates"
        assert self.memory.default_bucket_of(medium_input) == "medium_candidates"
        assert self.memory.default_bucket_of(large_input) == "large_candidates"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

