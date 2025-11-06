"""
Code Navigator for V3 - 轻量"代码指路"功能
==========================================
支持 git grep + 行号，帮助用户快速定位代码位置。
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class CodeNavigator:
    """轻量代码导航，支持关键词搜索定位。"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
    
    def find_code(self, keyword: str, file_pattern: str = "*.py", max_results: int = 5) -> List[Dict[str, any]]:
        """
        使用 git grep 查找代码位置。
        
        Args:
            keyword: 搜索关键词
            file_pattern: 文件模式（默认 *.py）
            max_results: 最多返回结果数
        
        Returns:
            List of {"file": str, "line": int, "content": str}
        """
        results = []
        
        try:
            # Try git grep first (faster and respects .gitignore)
            cmd = [
                "git", "grep", "-n", "-i",  # -n for line numbers, -i for case-insensitive
                keyword,
                "--", file_pattern
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[:max_results]:
                    # Format: "file:line:content"
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        file_path = parts[0]
                        line_num = parts[1]
                        content = parts[2].strip()
                        
                        results.append({
                            "file": file_path,
                            "line": int(line_num) if line_num.isdigit() else 0,
                            "content": content[:100]  # Limit content length
                        })
        
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            # Fallback: No results if git grep fails
            pass
        
        return results
    
    def find_metric_computation(self, metric_name: str) -> List[Dict[str, any]]:
        """查找指标计算相关代码。"""
        keywords = {
            "delta_p95": ["delta_p95", "p95", "latency"],
            "delta_qps": ["delta_qps", "qps", "throughput"],
            "error_rate": ["error_rate", "error", "failed"]
        }
        
        search_terms = keywords.get(metric_name.lower(), [metric_name])
        all_results = []
        
        for term in search_terms:
            results = self.find_code(term, "core/metrics.py", max_results=2)
            all_results.extend(results)
        
        # Deduplicate by (file, line)
        seen = set()
        unique_results = []
        for r in all_results:
            key = (r["file"], r["line"])
            if key not in seen:
                seen.add(key)
                unique_results.append(r)
        
        return unique_results[:3]  # Return top 3
    
    def find_decision_logic(self) -> List[Dict[str, any]]:
        """查找决策逻辑代码位置。"""
        return self.find_code("verdict", "agents/labops/policies/*.py", max_results=3)
    
    def find_report_parser(self) -> List[Dict[str, any]]:
        """查找报告解析代码。"""
        return self.find_code("parse", "agents/labops/tools/report_parser.py", max_results=3)
    
    def suggest_locations(self, result: Dict) -> List[Dict[str, any]]:
        """
        根据实验结果推荐相关代码位置。
        
        Args:
            result: Agent execution result
        
        Returns:
            List of code location suggestions with context
        """
        suggestions = []
        
        # 1. 如果有判断阶段的结果，指向决策逻辑
        if result.get("judgment"):
            decision_locs = self.find_decision_logic()
            for loc in decision_locs[:1]:  # Top 1
                suggestions.append({
                    "context": "判断逻辑",
                    **loc
                })
        
        # 2. 如果有指标，指向指标计算
        metrics = result.get("judgment", {}).get("metrics", {})
        if metrics:
            metric_locs = self.find_metric_computation("delta_p95")
            for loc in metric_locs[:1]:  # Top 1
                suggestions.append({
                    "context": "P95 计算",
                    **loc
                })
        
        # 3. 如果有错误，指向相关错误处理
        if result.get("error") or not result.get("ok"):
            error_type = result.get("error", "unknown")
            error_locs = self.find_code(error_type, "agents/labops/**/*.py", max_results=2)
            for loc in error_locs[:1]:
                suggestions.append({
                    "context": f"错误处理 ({error_type})",
                    **loc
                })
        
        return suggestions[:5]  # Max 5 suggestions


def create_code_link(file_path: str, line: int) -> str:
    """创建可点击的代码链接（VS Code 格式）。"""
    return f"{file_path}:{line}"


def format_code_nav(nav_results: List[Dict[str, any]]) -> str:
    """格式化代码导航结果为人类可读文本。"""
    if not nav_results:
        return "（无相关代码位置）"
    
    lines = []
    for i, result in enumerate(nav_results, 1):
        context = result.get("context", "相关代码")
        file_path = result.get("file", "unknown")
        line_num = result.get("line", 0)
        content = result.get("content", "")
        
        lines.append(f"{i}. [{context}] {file_path}:{line_num}")
        if content:
            lines.append(f"   → {content[:80]}")
    
    return "\n".join(lines)

