from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any
import time
import yaml

from modules.metrics.sla_monitor import SlaMonitor, SlaTargets
from modules.executors.parameter_executor import ParameterExecutor, ParamChange

@dataclass
class AutoTunerPolicy:
    min_top_k: int = 20
    max_top_k: int = 100
    min_batch_size: int = 8
    max_batch_size: int = 512
    cooldown_seconds: int = 30
    # 软/硬违约时的步长（示例策略：降低 top_k、降低 batch_size 来控时延）
    soft_top_k_step: int = -10
    soft_batch_step: int = -16
    hard_top_k_step: int = -20
    hard_batch_step: int = -64

def _clip(v: Optional[int], lo: int, hi: int) -> Optional[int]:
    if v is None: return None
    return max(lo, min(hi, v))

class AutoTuner:
    """
    最小可运行版：
    - 调用 monitor.evaluate() 识别违约等级
    - 依据 policy 生成参数变更建议 ParamChange
    - 通过 executor.apply() 执行（默认 dry-run）
    - 冷却窗口内不重复动作
    """
    def __init__(self, policy: AutoTunerPolicy, monitor: SlaMonitor, executor: ParameterExecutor):
        self.policy = policy
        self.monitor = monitor
        self.executor = executor
        self._last_action_ts: float = 0.0
        self._last_params: Dict[str, Any] = {"top_k": 80, "batch_size": 64}

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "AutoTuner":
        import yaml
        from modules.metrics.sla_monitor import SlaMonitor, SlaTargets

        with open(yaml_path, "r") as f:
            cfg = yaml.safe_load(f) or {}

        tcfg = cfg.get("targets", {}) or {}
        enabled = bool(tcfg.get("enabled", True))  # default ON unless explicitly disabled

        monitor = SlaMonitor(SlaTargets(
            p95_target_ms=float(tcfg.get("p95_target_ms", 120)),
            p99_hard_ms=float(tcfg.get("p99_hard_ms", 250)),
            window_seconds=int(tcfg.get("window_seconds", 30)),
            min_samples=int(tcfg.get("min_samples", 30)),
            enabled=enabled,
        ))

        # keep other policy/tuning fields unchanged
        pcfg = cfg.get("policy", {}) or {}
        policy = AutoTunerPolicy(
            min_top_k=int(pcfg.get("min_top_k", 20)),
            max_top_k=int(pcfg.get("max_top_k", 100)),
            min_batch_size=int(pcfg.get("min_batch_size", 8)),
            max_batch_size=int(pcfg.get("max_batch_size", 512)),
            cooldown_seconds=int(pcfg.get("cooldown_seconds", 30)),
            soft_top_k_step=int(pcfg.get("soft_top_k_step", -10)),
            soft_batch_step=int(pcfg.get("soft_batch_step", -16)),
            hard_top_k_step=int(pcfg.get("hard_top_k_step", -20)),
            hard_batch_step=int(pcfg.get("hard_batch_step", -64)),
        )
        executor = ParameterExecutor(mode="local", dry_run=True)
        return cls(policy, monitor, executor)

    def tick(self) -> Optional[ParamChange]:
        """
        在外部循环中周期调用（例如每 1s）。
        返回产生的 ParamChange（若无则 None）。
        """
        level, p95, p99, n = self.monitor.evaluate()
        now = time.time()
        if level == "none":
            return None
        if now - self._last_action_ts < self.policy.cooldown_seconds:
            return None

        # 依据软/硬违约生成建议
        d_top = self.policy.soft_top_k_step if level == "soft" else self.policy.hard_top_k_step
        d_bat = self.policy.soft_batch_step if level == "soft" else self.policy.hard_batch_step

        new_top = _clip(self._last_params.get("top_k", 80) + d_top, self.policy.min_top_k, self.policy.max_top_k)
        new_bat = _clip(self._last_params.get("batch_size", 64) + d_bat, self.policy.min_batch_size, self.policy.max_batch_size)

        change = ParamChange(top_k=new_top, batch_size=new_bat,
                             note=f"{level}-breach p95={p95:.1f} p99={p99:.1f} n={n}")
        ok = self.executor.apply(change)
        if ok:
            self._last_action_ts = now
            if new_top is not None: self._last_params["top_k"] = new_top
            if new_bat is not None: self._last_params["batch_size"] = new_bat
            return change
        return None
