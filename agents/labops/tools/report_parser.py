"""
Report Parser - Extract metrics from mini reports and text files
================================================================
Parses /api/lab/report?mini=1 responses and LAB_*_REPORT_MINI.txt files.
"""

import re
from typing import Dict, Any, Optional


class ReportParser:
    """Parser for lab experiment reports."""
    
    @staticmethod
    def parse_mini_endpoint(response: Dict[str, Any]) -> Dict[str, float]:
        """
        Parse /api/lab/report?mini=1 response.
        解析报告：从 API 响应提取指标
        
        Args:
            response: API response dict
        
        Returns:
            {"delta_p95_pct": float, "delta_qps_pct": float, "error_rate_pct": float}
        """
        return {
            "delta_p95_pct": response.get("delta_p95_pct", 0.0),
            "delta_qps_pct": response.get("delta_qps_pct", 0.0),
            "error_rate_pct": response.get("error_rate_pct", 0.0),
            "faiss_share_pct": response.get("faiss_share_pct", 0.0),
            "fallback_count": response.get("fallback_count", 0)
        }
    
    @staticmethod
    def parse_text_report(report_text: str) -> Dict[str, float]:
        """
        Parse LAB_*_REPORT_MINI.txt file content.
        
        Extracts:
        - ΔP95: -8.1ms (-0.8%)
        - ΔQPS: -1.1 (-24.2%)
        - Error Rate: 0.12%
        - FAISS: 123 (45.6%)
        - Fallbacks: 5
        
        Args:
            report_text: Full report text
        
        Returns:
            Metrics dict
        """
        metrics = {
            "delta_p95_pct": 0.0,
            "delta_qps_pct": 0.0,
            "error_rate_pct": 0.0,
            "faiss_share_pct": 0.0,
            "fallback_count": 0
        }
        
        for line in report_text.split('\n'):
            # ΔP95: -8.1ms (-0.8%)
            if 'ΔP95:' in line or 'deltaP95:' in line:
                match = re.search(r'\(([+-]?\d+\.?\d*)%\)', line)
                if match:
                    metrics["delta_p95_pct"] = float(match.group(1))
            
            # ΔQPS: -1.1 (-24.2%)
            elif 'ΔQPS:' in line or 'deltaQPS:' in line:
                match = re.search(r'\(([+-]?\d+\.?\d*)%\)', line)
                if match:
                    metrics["delta_qps_pct"] = float(match.group(1))
            
            # Error Rate: 0.12%
            elif 'Error Rate:' in line or 'error_rate' in line:
                match = re.search(r'([0-9.]+)%', line)
                if match:
                    metrics["error_rate_pct"] = float(match.group(1))
            
            # FAISS: 123 (45.6%)
            elif 'FAISS:' in line and '(' in line:
                match = re.search(r'FAISS:\s*\d+\s*\(([0-9.]+)%\)', line)
                if match:
                    metrics["faiss_share_pct"] = float(match.group(1))
            
            # Fallbacks (FAISS→Qdrant): 5
            elif 'Fallbacks' in line or 'fallback' in line:
                match = re.search(r':\s*(\d+)', line)
                if match:
                    metrics["fallback_count"] = int(match.group(1))
        
        return metrics
    
    @staticmethod
    def validate_metrics(metrics: Dict[str, float]) -> bool:
        """
        Validate that metrics contain required fields with reasonable values.
        
        Args:
            metrics: Parsed metrics
        
        Returns:
            True if valid (all three core metrics present)
        """
        required = ["delta_p95_pct", "delta_qps_pct", "error_rate_pct"]
        
        for field in required:
            if field not in metrics:
                return False
            
            # Check if value is a valid number
            val = metrics[field]
            if not isinstance(val, (int, float)):
                return False
            
            # Sanity checks
            if abs(val) > 1000:  # Extreme values
                return False
        
        return True
    
    @staticmethod
    def extract_ab_balance(report_text: str) -> Optional[float]:
        """
        Extract A/B sample balance from report.
        
        Looks for patterns like:
        - "Valid A Windows: 10"
        - "Valid B Windows: 11"
        - "Balance: 47.6% / 52.4%"
        
        Args:
            report_text: Full report text
        
        Returns:
            AB imbalance percentage (0-100) or None
        """
        a_count = None
        b_count = None
        
        for line in report_text.split('\n'):
            if 'Valid A Windows:' in line or 'A windows:' in line:
                match = re.search(r':\s*(\d+)', line)
                if match:
                    a_count = int(match.group(1))
            
            elif 'Valid B Windows:' in line or 'B windows:' in line:
                match = re.search(r':\s*(\d+)', line)
                if match:
                    b_count = int(match.group(1))
        
        if a_count is not None and b_count is not None:
            total = a_count + b_count
            if total == 0:
                return None
            
            balance_a = a_count / total * 100
            balance_b = b_count / total * 100
            
            # Return max deviation from 50%
            imbalance = max(abs(balance_a - 50), abs(balance_b - 50))
            return imbalance
        
        return None

