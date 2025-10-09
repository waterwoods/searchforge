"""
AutoTuner Brain - 记忆层

实现轻量级内存驻留的记忆系统：
- 环形缓冲保存观测数据
- EWMA计算性能指标
- 甜点发现和缓存

⚠️ Feature Freeze: Redis 和文件持久化已禁用，仅使用内存缓存
"""

import os
import json
import time
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque

from .contracts import TuningInput, MemorySample, SweetSpot, SLO
from .autotuner_config import ENABLE_REDIS, ENABLE_PERSISTENCE


class Memory:
    """
    记忆系统
    
    提供环形缓冲、EWMA计算和甜点发现功能
    
    ⚠️ Feature Freeze: 仅使用内存缓存，Redis 和文件持久化已禁用
    """
    
    def __init__(self):
        # 配置参数（从环境变量读取，带默认值）
        self.ring_size = int(os.environ.get('MEMORY_RING_SIZE', '100'))
        self.alpha = float(os.environ.get('MEMORY_ALPHA', '0.2'))
        self.ttl_sec = int(os.environ.get('MEMORY_TTL_SEC', '900'))  # 15分钟
        
        # 环形缓冲：保存最近的观测样本
        self.ring_buffer: deque = deque(maxlen=self.ring_size)
        
        # 每个bucket的EWMA数据：bucket_id -> {ef: (ewma_p95, ewma_recall, count)}
        self.ewma_data: Dict[str, Dict[int, Tuple[float, float, int]]] = defaultdict(dict)
        
        # 甜点缓存：bucket_id -> SweetSpot
        self.sweet_spots: Dict[str, SweetSpot] = {}
        
        # 每个bucket的最后更新时间
        self.last_update: Dict[str, float] = {}
        
        # ⚠️ Feature Freeze: Redis 和持久化连接已禁用
        self.redis_client = None
        self.persistence_enabled = False
    
    def _log_event(self, event_type: str, **kwargs):
        """打印JSON格式的事件日志"""
        log_entry = {"event": event_type, "timestamp": time.time()}
        log_entry.update(kwargs)
        print(json.dumps(log_entry, separators=(',', ':')))
    
    def default_bucket_of(self, inp: TuningInput) -> str:
        """
        计算流量桶ID
        
        使用filter_signature和top_k进行粗粒度分桶
        """
        # 简化的分桶策略：基于候选数量范围
        ncand = inp.params.get('Ncand_max', 1000)
        if ncand <= 800:
            bucket = "small_candidates"
        elif ncand <= 1200:
            bucket = "medium_candidates"
        else:
            bucket = "large_candidates"
        
        # 可以进一步细分，这里保持简单
        return bucket
    
    def observe(self, sample: MemorySample):
        """
        添加观测样本
        
        Args:
            sample: 记忆样本
        """
        bucket_id = sample.bucket_id
        ef = sample.ef
        current_time = time.time()
        
        # 添加到环形缓冲
        self.ring_buffer.append(sample)
        
        # 更新EWMA数据
        if ef not in self.ewma_data[bucket_id]:
            # 首次观测该ef值
            self.ewma_data[bucket_id][ef] = (sample.p95_ms, sample.recall_at10, 1)
        else:
            # 更新EWMA
            old_p95, old_recall, count = self.ewma_data[bucket_id][ef]
            new_p95 = self.alpha * sample.p95_ms + (1 - self.alpha) * old_p95
            new_recall = self.alpha * sample.recall_at10 + (1 - self.alpha) * old_recall
            self.ewma_data[bucket_id][ef] = (new_p95, new_recall, count + 1)
        
        # 更新最后更新时间
        self.last_update[bucket_id] = current_time
        
        # ⚠️ Feature Freeze: Redis 持久化已禁用
        # if ENABLE_REDIS and self.redis_client:
        #     self._persist_to_redis(sample)
        
        # ⚠️ Feature Freeze: 文件持久化已禁用
        # if ENABLE_PERSISTENCE:
        #     self._persist_to_disk(sample)
        
        # 尝试更新甜点
        self._update_sweet_spot(bucket_id, current_time)
    
    def _update_sweet_spot(self, bucket_id: str, current_time: float):
        """
        更新甜点
        
        在满足SLO的ef集合中选择最小的ef作为甜点
        """
        if bucket_id not in self.ewma_data:
            return
        
        # 假设使用标准的SLO（这里可以从外部传入）
        slo_p95 = 200.0
        slo_recall = 0.85
        
        # 找到所有满足SLO的ef值
        valid_efs = []
        for ef, (ewma_p95, ewma_recall, _) in self.ewma_data[bucket_id].items():
            if ewma_p95 <= slo_p95 and ewma_recall >= slo_recall:
                valid_efs.append((ef, ewma_p95, ewma_recall))
        
        if not valid_efs:
            # 没有满足SLO的ef值
            if bucket_id in self.sweet_spots:
                # 标记当前甜点为无效
                self.sweet_spots[bucket_id].meets_slo = False
            return
        
        # 选择最小的ef作为甜点
        valid_efs.sort(key=lambda x: x[0])  # 按ef排序
        sweet_ef, sweet_p95, sweet_recall = valid_efs[0]
        
        # 获取对应的T值（从最近的观测中获取）
        sweet_T = self._get_representative_T(bucket_id, sweet_ef)
        
        # 更新甜点
        age_s = current_time - self.last_update.get(bucket_id, current_time)
        sweet_spot = SweetSpot(
            ef=sweet_ef,
            T=sweet_T,
            meets_slo=True,
            age_s=age_s,
            ewma_p95=sweet_p95,
            ewma_recall=sweet_recall
        )
        
        self.sweet_spots[bucket_id] = sweet_spot
        
        # 打印更新事件
        self._log_event(
            "MEMORY_UPDATE",
            bucket=bucket_id,
            sweet_ef=sweet_ef,
            meets_slo=True,
            ewma_p95=round(sweet_p95, 2),
            ewma_recall=round(sweet_recall, 3)
        )
    
    def _get_representative_T(self, bucket_id: str, ef: int) -> int:
        """
        获取某个ef值的代表性T值
        
        从最近的观测中查找
        """
        # 从环形缓冲中查找最近的匹配样本
        for sample in reversed(self.ring_buffer):
            if sample.bucket_id == bucket_id and sample.ef == ef:
                return sample.T
        
        # 如果没找到，返回默认值
        return 500
    
    def query(self, bucket_id: str) -> Optional[SweetSpot]:
        """
        查询甜点
        
        Args:
            bucket_id: 流量桶ID
            
        Returns:
            甜点信息，如果不存在或过期则返回None
        """
        if bucket_id not in self.sweet_spots:
            return None
        
        sweet_spot = self.sweet_spots[bucket_id]
        
        # 检查是否过期
        if self.is_stale(bucket_id):
            sweet_spot.meets_slo = False
            return None
        
        return sweet_spot
    
    def is_stale(self, bucket_id: str, ttl_s: Optional[int] = None) -> bool:
        """
        检查甜点是否过期
        
        Args:
            bucket_id: 流量桶ID
            ttl_s: 过期时间（秒），默认使用配置值
            
        Returns:
            是否过期
        """
        if ttl_s is None:
            ttl_s = self.ttl_sec
        
        if bucket_id not in self.last_update:
            return True
        
        age = time.time() - self.last_update[bucket_id]
        return age > ttl_s
    
    def _persist_to_redis(self, sample: MemorySample):
        """
        持久化样本到 Redis（已禁用）
        
        ⚠️ Feature Freeze: Redis 持久化已禁用，此方法为空实现
        """
        if not ENABLE_REDIS:
            return
        # Redis persistence code would go here
        pass
    
    def _persist_to_disk(self, sample: MemorySample):
        """
        持久化样本到磁盘（已禁用）
        
        ⚠️ Feature Freeze: 文件持久化已禁用，此方法为空实现
        """
        if not ENABLE_PERSISTENCE:
            return
        # File persistence code would go here
        pass
    
    def load_from_redis(self, bucket_id: str) -> Optional[Dict]:
        """
        从 Redis 加载数据（已禁用）
        
        ⚠️ Feature Freeze: Redis 持久化已禁用，始终返回 None
        """
        if not ENABLE_REDIS:
            return None
        # Redis load code would go here
        return None
    
    def load_from_disk(self, bucket_id: str) -> Optional[Dict]:
        """
        从磁盘加载数据（已禁用）
        
        ⚠️ Feature Freeze: 文件持久化已禁用，始终返回 None
        """
        if not ENABLE_PERSISTENCE:
            return None
        # File load code would go here
        return None


# 全局记忆实例
_global_memory = Memory()


def get_memory() -> Memory:
    """获取全局记忆实例"""
    return _global_memory

