"""
LLM Explainer for V3 - 支持离线降级 + 缓存 + 日志
=====================================================
优先尝试 LLM（便宜模型如 gpt-4o-mini），失败时自动回退到规则解释。

环境变量配置：
- OPENAI_API_KEY: OpenAI API Key
- AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint
- AZURE_OPENAI_API_KEY: Azure API Key
- LLM_MODEL: 模型名称（默认 gpt-4o-mini）
- LLM_TIMEOUT: 超时秒数（默认 8）

新增功能：
- 轻量缓存：hash-based JSON 缓存（≤1 MB）
- 日志记录：轮换日志（≤200 条）
"""

import os
import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import deque
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from agents.labops.v2.explainers.rules import RuleBasedExplainer


class LLMExplainer:
    """LLM-powered explainer with automatic fallback to rules, caching, and logging."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.rule_explainer = RuleBasedExplainer(project_root)
        
        # LLM configuration
        self.llm_enabled = self._check_llm_available()
        self.llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.llm_timeout = float(os.getenv("LLM_TIMEOUT", "8.0"))
        
        # Cache configuration
        self.cache_dir = project_root / "cache"
        self.cache_file = self.cache_dir / "llm_explain_cache.json"
        self.cache_max_size = 1 * 1024 * 1024  # 1 MB
        self._cache = None
        
        # Log configuration
        self.log_dir = project_root / "logs"
        self.log_file = self.log_dir / "agent_v3_explainer.log"
        self.log_max_entries = 200
        
        # Initialize cache and log
        self._init_cache()
        self._init_log()
        
        # Initialize LLM client if available
        self.client = None
        self.use_azure = False
        
        if self.llm_enabled:
            self._init_llm_client()
    
    def _check_llm_available(self) -> bool:
        """检查是否有可用的 LLM API Key。"""
        openai_key = os.getenv("OPENAI_API_KEY")
        azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        return bool(openai_key or (azure_key and azure_endpoint))
    
    def _init_llm_client(self):
        """初始化 LLM 客户端（OpenAI 或 Azure）。"""
        try:
            # Try Azure first
            azure_key = os.getenv("AZURE_OPENAI_API_KEY")
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            
            if azure_key and azure_endpoint:
                from openai import AzureOpenAI
                self.client = AzureOpenAI(
                    api_key=azure_key,
                    api_version="2024-02-15-preview",
                    azure_endpoint=azure_endpoint
                )
                self.use_azure = True
                print(f"  ✓ LLM: Azure OpenAI ({self.llm_model})")
                return
            
            # Fallback to OpenAI
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                from openai import OpenAI
                self.client = OpenAI(api_key=openai_key)
                self.use_azure = False
                print(f"  ✓ LLM: OpenAI ({self.llm_model})")
                return
        
        except ImportError:
            # openai package not installed, fallback to rules
            print(f"  ⚠️  openai package not installed, using rule-based fallback")
            self.llm_enabled = False
            self.client = None
        
        except Exception as e:
            print(f"  ⚠️  LLM init failed: {e}, using rule-based fallback")
            self.llm_enabled = False
            self.client = None
    
    def _init_cache(self):
        """初始化缓存（JSON 文件）。"""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            if self.cache_file.exists():
                # Load existing cache
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
                
                # Check size
                file_size = self.cache_file.stat().st_size
                if file_size > self.cache_max_size:
                    # Cache too large, clear it
                    self._cache = {}
                    self._save_cache()
            else:
                self._cache = {}
        
        except Exception as e:
            # Fallback: no cache
            self._cache = {}
    
    def _init_log(self):
        """初始化日志文件。"""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
            if not self.log_file.exists():
                self.log_file.touch()
        
        except Exception:
            # Fallback: no logging
            pass
    
    def _compute_cache_key(self, context: Dict[str, Any]) -> str:
        """计算缓存键（基于关键指标的 hash）。"""
        # Extract key metrics for hashing
        metrics = context.get("metrics", {})
        verdict = context.get("verdict", "unknown")
        
        key_data = {
            "delta_p95": round(metrics.get("delta_p95_pct", 0.0), 1),
            "delta_qps": round(metrics.get("delta_qps_pct", 0.0), 1),
            "error_rate": round(metrics.get("error_rate_pct", 0.0), 2),
            "verdict": verdict
        }
        
        # Hash to get cache key
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取解释。"""
        if not self._cache:
            return None
        
        cached = self._cache.get(cache_key)
        if cached:
            # Check if cache is still fresh (optional: add TTL later)
            return cached
        
        return None
    
    def _save_to_cache(self, cache_key: str, explanation: Dict[str, Any]):
        """保存解释到缓存。"""
        try:
            if not self._cache:
                return
            
            self._cache[cache_key] = {
                "explanation": explanation,
                "cached_at": datetime.now().isoformat()
            }
            
            self._save_cache()
        
        except Exception:
            # Non-critical: cache save failed
            pass
    
    def _save_cache(self):
        """将缓存写入文件。"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        
        except Exception:
            pass
    
    def _log_explanation(self, mode: str, verdict: str, bullets_count: int, cached: bool):
        """记录解释日志（轮换，≤200 条）。"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"[{timestamp}] mode={mode} verdict={verdict} bullets={bullets_count} cached={cached}\n"
            
            # Read existing log
            lines = []
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            
            # Append new line
            lines.append(log_line)
            
            # Keep only last N entries
            lines = lines[-self.log_max_entries:]
            
            # Write back
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        
        except Exception:
            # Non-critical: logging failed
            pass
    
    def explain(self, result: Dict[str, Any], include_code_nav: bool = True) -> Dict[str, Any]:
        """
        生成解释（优先 LLM，失败时回退到规则）。
        带缓存和日志功能。
        
        Args:
            result: Agent execution result
            include_code_nav: 是否包含代码导航
        
        Returns:
            {
                "bullets": List[str],  # ≤6 bullet points
                "sources": List[str],
                "mode": "llm" | "rules" | "fallback",
                "cached": bool,  # NEW: 是否来自缓存
                "code_nav": List[Dict] (optional)
            }
        """
        # Prepare context for cache key
        context = self._prepare_llm_context(result)
        cache_key = self._compute_cache_key(context)
        
        # Try cache first
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            explanation = cached_result["explanation"]
            explanation["cached"] = True
            
            # Log cache hit
            verdict = context.get("verdict", "unknown")
            bullets_count = len(explanation.get("bullets", []))
            mode = explanation.get("mode", "unknown")
            self._log_explanation(mode, verdict, bullets_count, cached=True)
            
            return explanation
        
        # No cache, generate new explanation
        cached = False
        
        # Try LLM first
        if self.llm_enabled and self.client:
            try:
                llm_result = self._explain_with_llm(result, include_code_nav)
                if llm_result:
                    llm_result["cached"] = False
                    
                    # Save to cache
                    self._save_to_cache(cache_key, llm_result)
                    
                    # Log
                    verdict = context.get("verdict", "unknown")
                    bullets_count = len(llm_result.get("bullets", []))
                    self._log_explanation("llm", verdict, bullets_count, cached=False)
                    
                    return llm_result
            except Exception as e:
                print(f"  ⚠️  LLM explain failed: {e}, falling back to rules")
        
        # Fallback to rules
        rule_result = self.rule_explainer.explain(result)
        rule_result["mode"] = "fallback" if self.llm_enabled else "rules"
        rule_result["cached"] = False
        
        # Add code navigation if requested
        if include_code_nav:
            from agents.labops.v3.code_nav import CodeNavigator
            navigator = CodeNavigator(self.project_root)
            code_nav = navigator.suggest_locations(result)
            rule_result["code_nav"] = code_nav[:3]  # Max 3 locations
        
        # Limit bullets to 6
        rule_result["bullets"] = rule_result.get("bullets", [])[:6]
        
        # Save to cache
        self._save_to_cache(cache_key, rule_result)
        
        # Log
        verdict = context.get("verdict", "unknown")
        bullets_count = len(rule_result.get("bullets", []))
        mode = rule_result.get("mode", "rules")
        self._log_explanation(mode, verdict, bullets_count, cached=False)
        
        return rule_result
    
    def _explain_with_llm(self, result: Dict[str, Any], include_code_nav: bool) -> Optional[Dict[str, Any]]:
        """使用 LLM 生成解释（带超时）。"""
        if not self.client:
            return None
        
        # Prepare context for LLM
        context = self._prepare_llm_context(result)
        
        # Build prompt
        prompt = self._build_prompt(context)
        
        # Call LLM with timeout
        start_time = time.time()
        try:
            # Set a timeout by wrapping in async or using signal (simplified here)
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "你是一个实验结果分析专家，善于用简洁的中文解释 A/B 测试结果。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
                timeout=self.llm_timeout
            )
            
            elapsed = time.time() - start_time
            
            if elapsed > self.llm_timeout:
                print(f"  ⚠️  LLM timeout ({elapsed:.1f}s > {self.llm_timeout}s)")
                return None
            
            # Parse response
            content = response.choices[0].message.content.strip()
            bullets = self._parse_bullets(content)
            
            # Add code navigation if requested
            code_nav = []
            if include_code_nav:
                from agents.labops.v3.code_nav import CodeNavigator
                navigator = CodeNavigator(self.project_root)
                code_nav = navigator.suggest_locations(result)[:3]
            
            return {
                "bullets": bullets[:6],  # Limit to 6
                "sources": ["llm"],
                "mode": "llm",
                "model": self.llm_model,
                "latency_ms": round(elapsed * 1000, 2),
                "code_nav": code_nav
            }
        
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ⚠️  LLM call failed after {elapsed:.1f}s: {e}")
            return None
    
    def _prepare_llm_context(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """准备 LLM 上下文（提取关键信息）。"""
        context = {
            "ok": result.get("ok", False),
            "phase": result.get("phase", "unknown")
        }
        
        # Extract metrics
        judgment = result.get("judgment", {})
        if judgment.get("ok"):
            metrics = judgment.get("metrics", {})
            context["metrics"] = {
                "delta_p95_pct": metrics.get("delta_p95_pct", 0.0),
                "delta_qps_pct": metrics.get("delta_qps_pct", 0.0),
                "error_rate_pct": metrics.get("error_rate_pct", 0.0)
            }
            
            decision = judgment.get("decision", {})
            context["verdict"] = decision.get("verdict", "unknown")
            context["reason"] = decision.get("reason", "")
            context["warnings"] = decision.get("warnings", [])
        
        # Extract config
        config = result.get("config", {})
        exp_cfg = config.get("experiment", {})
        context["config"] = {
            "flow_policy": exp_cfg.get("flow_policy", ""),
            "routing_mode": exp_cfg.get("routing_mode", ""),
            "target_p95": exp_cfg.get("target_p95", 0)
        }
        
        # Extract error if any
        if not result.get("ok"):
            context["error"] = result.get("error", "")
            context["error_reason"] = result.get("reason", "")
        
        return context
    
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """构建 LLM prompt。"""
        prompt_lines = [
            "请分析以下 COMBO 实验结果，生成 ≤6 条简洁的中文解释（每条 ≤30 字）：",
            "",
            "实验结果："
        ]
        
        if context.get("metrics"):
            metrics = context["metrics"]
            prompt_lines.append(f"- ΔP95: {metrics['delta_p95_pct']:+.1f}%")
            prompt_lines.append(f"- ΔQPS: {metrics['delta_qps_pct']:+.1f}%")
            prompt_lines.append(f"- 错误率: {metrics['error_rate_pct']:.2f}%")
            prompt_lines.append(f"- 判定: {context.get('verdict', 'unknown').upper()}")
            prompt_lines.append(f"- 原因: {context.get('reason', 'N/A')}")
        else:
            prompt_lines.append(f"- 状态: {context.get('phase', 'unknown')} 阶段")
            if not context.get("ok"):
                prompt_lines.append(f"- 错误: {context.get('error', 'unknown')}")
                prompt_lines.append(f"- 原因: {context.get('error_reason', 'N/A')}")
        
        prompt_lines.extend([
            "",
            "配置：",
            f"- 流控策略: {context.get('config', {}).get('flow_policy', 'N/A')}",
            f"- 路由模式: {context.get('config', {}).get('routing_mode', 'N/A')}",
            f"- 目标 P95: {context.get('config', {}).get('target_p95', 'N/A')} ms",
            "",
            "要求：",
            "1. 每条解释 ≤30 字",
            "2. 使用 ✓ / ⚠ / ✗ 图标表示状态",
            "3. 重点关注：延迟改善、错误率、QPS 变化",
            "4. 给出可操作建议",
            "5. 最多 6 条",
            "",
            "请以纯文本列表格式输出，每行一条，格式：",
            "- 第一条解释",
            "- 第二条解释",
            "..."
        ])
        
        return "\n".join(prompt_lines)
    
    def _parse_bullets(self, content: str) -> List[str]:
        """从 LLM 响应中提取 bullet points。"""
        bullets = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Remove bullet markers (-, *, •, numbers)
            if line.startswith(('-', '*', '•', '→')):
                line = line[1:].strip()
            elif line[0].isdigit() and line[1:3] in ['. ', ') ']:
                line = line[3:].strip()
            
            if line:
                bullets.append(line)
        
        return bullets


def explain_with_llm(result: Dict[str, Any], project_root: Path = None) -> Dict[str, Any]:
    """
    便捷函数：使用 LLM 解释结果（自动回退）。
    
    Args:
        result: Agent execution result
        project_root: Project root path (auto-detected if None)
    
    Returns:
        Explanation with bullets, mode, and code navigation
    """
    if project_root is None:
        project_root = Path(__file__).parent.parent.parent.parent.parent
    
    explainer = LLMExplainer(project_root)
    return explainer.explain(result, include_code_nav=True)

