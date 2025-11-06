"""
Ops Client - Interface to /api/* endpoints and scripts
======================================================
Minimal HTTP client for lab operations and flag management.

Dependencies: stdlib + requests
"""

import json
import subprocess
import time
from typing import Dict, Any, Optional
from pathlib import Path

try:
    import requests
except ImportError:
    import urllib.request
    import urllib.error
    requests = None  # Fallback to urllib


class OpsClient:
    """Client for /api API endpoints and lab scripts."""
    
    def __init__(self, base_url: str = "http://localhost:8011", timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.use_requests = requests is not None
    
    def _get(self, endpoint: str) -> Dict[str, Any]:
        """HTTP GET request.
        HTTP GET 请求：调用 /api/* API
        """
        url = f"{self.base_url}{endpoint}"
        
        if self.use_requests:
            resp = requests.get(url, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        else:
            # Fallback to urllib
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode())
    
    def _post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """HTTP POST request.
        HTTP POST 请求：写入配置或标志
        """
        url = f"{self.base_url}{endpoint}"
        
        if self.use_requests:
            resp = requests.post(url, json=data or {}, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        else:
            # Fallback to urllib
            body = json.dumps(data or {}).encode('utf-8')
            req = urllib.request.Request(
                url, 
                data=body,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode())
    
    # Health & Config
    def check_health(self) -> Dict[str, Any]:
        """Check system health via /api/lab/config.
        健康检查：确认 Redis 和 Qdrant 可用
        """
        return self._get("/api/lab/config")
    
    # Lab Experiment Operations
    def get_lab_status(self) -> Dict[str, Any]:
        """Get current lab experiment status."""
        return self._get("/api/lab/status")
    
    def get_lab_report_mini(self) -> Dict[str, Any]:
        """Get mini report with key metrics."""
        return self._get("/api/lab/report?mini=1")
    
    def get_lab_report_full(self) -> Dict[str, Any]:
        """Get full text report."""
        return self._get("/api/lab/report")
    
    # Flag Management
    def apply_flags(self, control: Optional[Dict[str, Any]] = None, 
                    routing: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Apply feature flags via POST /api/flags.
        
        Args:
            control: Control flags (policy, target_p95_ms, max_concurrency, max_batch_size)
            routing: Routing flags (enabled, policy, topk_threshold, manual_backend)
        
        Returns:
            Application result
        """
        payload = {}
        if control:
            payload["control"] = control
        if routing:
            payload["routing"] = routing
        
        return self._post("/api/flags", payload)
    
    def get_flags(self) -> Dict[str, Any]:
        """Get current flags."""
        return self._get("/api/flags")
    
    # Script Execution
    def run_lab_script(self, script_args: str, cwd: Optional[Path] = None,
                       time_budget: int = 0, dry_run: bool = False) -> Dict[str, Any]:
        """
        Run ./scripts/run_lab_headless.sh with given arguments.
        
        Args:
            script_args: Full command line args (e.g., "combo --with-load --qps 10 ...")
            cwd: Working directory (defaults to project root)
            time_budget: Max execution time in seconds (0 = no limit)
            dry_run: If True, only print command
        
        Returns:
            {"ok": bool, "stdout": str, "stderr": str, "returncode": int}
        """
        if cwd is None:
            cwd = Path(__file__).parent.parent.parent.parent
        
        script_path = cwd / "scripts" / "run_lab_headless.sh"
        if not script_path.exists():
            return {
                "ok": False,
                "error": f"Script not found: {script_path}",
                "returncode": -1
            }
        
        cmd = f"bash {script_path} {script_args}"
        
        if dry_run:
            return {
                "ok": True,
                "dry_run": True,
                "command": cmd,
                "message": "DRY-RUN: Command not executed"
            }
        
        try:
            timeout = time_budget if time_budget > 0 else None
            proc = subprocess.run(
                cmd,
                shell=True,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "ok": proc.returncode == 0,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "returncode": proc.returncode
            }
        
        except subprocess.TimeoutExpired as e:
            return {
                "ok": False,
                "error": f"Script timeout after {time_budget}s",
                "stdout": e.stdout.decode() if e.stdout else "",
                "stderr": e.stderr.decode() if e.stderr else "",
                "returncode": -2
            }
        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
                "returncode": -3
            }
    
    # Report File Fallback
    def read_report_file(self, report_type: str = "combo") -> Optional[str]:
        """
        Read report file as fallback if API fails.
        
        Args:
            report_type: "combo", "routing", or "flow"
        
        Returns:
            Report text or None
        """
        project_root = Path(__file__).parent.parent.parent.parent
        reports_dir = project_root / "reports"
        
        filename_map = {
            "combo": "LAB_COMBO_REPORT_MINI.txt",
            "routing": "LAB_ROUTE_REPORT_MINI.txt",
            "flow": "LAB_FLOW_REPORT_MINI.txt"
        }
        
        filename = filename_map.get(report_type, "LAB_COMBO_REPORT_MINI.txt")
        report_path = reports_dir / filename
        
        if report_path.exists():
            return report_path.read_text()
        
        return None

