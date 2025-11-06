"""
best.py - Best Config Route Handler
====================================
Handles /api/best endpoint for managing best.yaml configuration file.
Implements concurrent-safe read/write operations with file locking.

Features:
- GET /api/best: Read and return best.yaml contents (with default skeleton if missing)
- PUT /api/best: Deep merge updates into best.yaml with UTC timestamps
- Portalocker-based file locking for concurrent access safety
- Pydantic schema validation for best.yaml structure
- Retry mechanism with exponential backoff
"""

import logging
import yaml
import portalocker
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, ContextManager, TextIO, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ========================================
# Router Setup
# ========================================

router = APIRouter(prefix="/api", tags=["Best Config"])

# ========================================
# Constants
# ========================================

# Project root is 3 levels up from this file
# services/fiqa_api/routes/best.py -> services/fiqa_api/routes -> services/fiqa_api -> services -> project_root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.resolve()
BEST_YAML_PATH = PROJECT_ROOT / "reports" / "_latest" / "best.yaml"


# ========================================
# Pydantic Models (Schema Validation)
# ========================================

class GatedRerankConfig(BaseModel):
    """Schema for gated rerank configuration."""
    top_k: int = Field(default=20, description="Number of candidates to rerank")
    margin: float = Field(default=0.12, description="Margin threshold for triggering rerank")
    trigger_rate_cap: float = Field(default=0.25, description="Maximum rerank trigger rate")
    budget_ms: int = Field(default=25, description="Rerank budget in milliseconds")


class PipelineConfig(BaseModel):
    """Schema for pipeline configuration."""
    use_hybrid: bool = Field(default=False, description="Whether to use hybrid search (BM25 + vector)")
    top_k: Optional[int] = Field(default=50, description="Number of results to return")
    rrf_k: Optional[int] = Field(default=None, description="RRF reciprocal rank fusion k parameter")
    rerank: bool = Field(default=False, description="Whether to enable reranking")
    rerank_top_k: Optional[int] = Field(default=None, description="Number of candidates to rerank")
    gated_rerank: Optional[GatedRerankConfig] = Field(default=None, description="Gated rerank configuration")


class BestConfigSchema(BaseModel):
    """Schema for best.yaml configuration file."""
    version: str = Field(default="", description="Version identifier")
    dataset: str = Field(default="", description="Dataset name")
    sla: Dict[str, Any] = Field(default_factory=dict, description="SLA configuration")
    pipeline: Dict[str, Any] = Field(default_factory=dict, description="Pipeline configuration (can include hybrid, rrf_k, gated_rerank)")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics")
    updated_at: Optional[str] = Field(default=None, description="ISO 8601 UTC timestamp")
    
    class Config:
        # Allow extra fields for flexible schema (pipeline can contain hybrid, rrf_k, gated_rerank)
        extra = "allow"


def get_default_skeleton() -> BestConfigSchema:
    """Return default skeleton with all required fields."""
    return BestConfigSchema(
        version="v1",
        dataset="FiQA",
        sla={},
        pipeline={
            "use_hybrid": False,
            "top_k": 50,
            "rrf_k": None,
            "rerank": False,
            "rerank_top_k": None,
            "gated_rerank": False,
        },
        metrics={},
        updated_at=None
    )


def validate_or_fill_skeleton(data: Dict[str, Any]) -> BestConfigSchema:
    """
    Validate data against BestConfigSchema, or return default skeleton if validation fails.
    
    Args:
        data: Dictionary to validate
    
    Returns:
        Validated BestConfigSchema instance
    """
    try:
        return BestConfigSchema(**data)
    except Exception as e:
        logger.warning(f"[BEST] Schema validation failed: {e}. Using default skeleton.")
        return get_default_skeleton()


# ========================================
# Configuration
# ========================================

LOCK_TIMEOUT = 5.0  # seconds
MAX_RETRIES = 5
MIN_BACKOFF_MS = 200
MAX_BACKOFF_MS = 1000


# ========================================
# Helper Functions
# ========================================

def locked_open(path: Path, mode: str, timeout: float = LOCK_TIMEOUT) -> ContextManager[TextIO]:
    """
    Acquire a file lock with retry mechanism and exponential backoff.
    
    Args:
        path: Path to the file
        mode: File mode ('r', 'r+', 'w', 'w+')
        timeout: Lock timeout per attempt in seconds
    
    Returns:
        Context manager for the locked file
    
    Raises:
        portalocker.LockException: If all retry attempts fail
    """
    last_exception = None
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Calculate backoff for this attempt: exponential growth from MIN to MAX
            backoff_ms = min(
                MIN_BACKOFF_MS * (2 ** (attempt - 1)),
                MAX_BACKOFF_MS
            )
            
            logger.info(f"[BEST][lock-retry] attempt={attempt} timeout={timeout}s backoff_ms={backoff_ms}")
            
            # Try to acquire lock
            return portalocker.Lock(path, mode=mode, timeout=timeout)
            
        except portalocker.LockException as e:
            last_exception = e
            
            # If this is the last attempt, raise
            if attempt == MAX_RETRIES:
                logger.error(f"[BEST][lock-retry] All {MAX_RETRIES} attempts failed")
                raise
            
            # Calculate backoff for next retry
            backoff_ms = min(
                MIN_BACKOFF_MS * (2 ** (attempt - 1)),
                MAX_BACKOFF_MS
            )
            
            # Wait before retry
            logger.warning(f"[BEST][lock-retry] attempt={attempt} failed: {e}, retrying in {backoff_ms}ms...")
            time.sleep(backoff_ms / 1000.0)
    
    # Should not reach here, but just in case
    raise last_exception


def deep_merge(source: Dict[str, Any], destination: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge source dictionary into destination dictionary.
    
    Merge Strategy:
        - Dictionaries: Recursive deep merge (nested dicts are merged)
        - Arrays/Lists: Complete replacement (not merged, overwrites entirely)
        - Primitives (str, int, bool, etc.): Overwrite
    
    Args:
        source: New data to merge in
        destination: Existing data to merge into
    
    Returns:
        Deeply merged dictionary
    
    Example:
        >>> deep_merge({"a": [1, 2]}, {"a": [3, 4], "b": {"c": 5}})
        {"a": [1, 2], "b": {"c": 5}}
        
        >>> deep_merge({"b": {"d": 6}}, {"b": {"c": 5}})
        {"b": {"c": 5, "d": 6}}
    """
    result = destination.copy()
    
    for key, value in source.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(value, result[key])
        else:
            # Arrays/lists and primitives: complete replacement
            result[key] = value
    
    return result


# ========================================
# Route Handlers
# ========================================

@router.get("/best")
async def get_best_config():
    """
    GET /api/best
    
    Read best.yaml configuration file with concurrent-safe file locking.
    Returns default skeleton if file doesn't exist.
    
    Returns:
        JSON representation of best.yaml contents (or default skeleton)
    
    Raises:
        HTTPException: 503 if file is locked after all retries
        HTTPException: 500 if read/parse error
    """
    try:
        # If file doesn't exist, return default skeleton
        if not BEST_YAML_PATH.exists():
            logger.info("[BEST] File not found, returning default skeleton")
            return get_default_skeleton().model_dump()
        
        # Read with shared lock for concurrent readers (with retry)
        with locked_open(BEST_YAML_PATH, "r") as f:
            content = f.read()
            if not content:
                return get_default_skeleton().model_dump()
            
            data = yaml.safe_load(content)
            if data is None:
                return get_default_skeleton().model_dump()
            
            # Validate and return (with skeleton fallback if invalid)
            validated = validate_or_fill_skeleton(data)
            return validated.model_dump()
        
    except portalocker.LockException as e:
        logger.error(f"[BEST] File lock timeout after retries: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "best_yaml_lock_timeout",
                "message": "file lock timeout after retries"
            }
        )
    except yaml.YAMLError as e:
        logger.error(f"[BEST] YAML parse error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Invalid YAML format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[BEST] Read error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read best.yaml: {str(e)}"
        )


@router.put("/best")
async def update_best_config(payload: Dict[str, Any]):
    """
    PUT /api/best
    
    Deep merge updates into best.yaml with concurrent-safe file locking and UTC timestamps.
    Uses atomic write (temp file + rename) to prevent partial writes.
    
    Request body:
        JSON object with configuration updates to merge
    
    Behavior:
        1. Ensures parent directories exist
        2. Acquires exclusive file lock (with retry/backoff)
        3. Reads existing data (or uses default skeleton)
        4. Deep merges payload into existing data
        5. Updates 'updated_at' field with UTC ISO timestamp
        6. Validates final structure against BestConfigSchema
        7. Writes to temporary file (atomic operation)
        8. Renames temp file to final location (atomic on POSIX)
    
    Deep merge rules:
        - Dictionaries: Recursive merge (nested dicts are merged)
        - Arrays/Lists: Complete replacement (not merged)
        - Primitives: Overwrite
    
    Returns:
        Updated and validated configuration data
    
    Raises:
        HTTPException: 503 if file is locked after retries
        HTTPException: 500 if write/merge/validation error
    """
    try:
        # Ensure parent directories exist
        BEST_YAML_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing data with lock (for file consistency)
        file_exists = BEST_YAML_PATH.exists()
        
        # Lock and read existing data
        if file_exists:
            with locked_open(BEST_YAML_PATH, "r+") as f:
                content = f.read()
                current_data = yaml.safe_load(content) if content else {}
        else:
            # No file exists, start with empty dict
            current_data = {}
        
        # Prepare merged data
        new_data = deep_merge(payload, current_data)
        
        # Update timestamp with UTC
        new_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Validate final structure
        validated = BestConfigSchema(**new_data)
        
        # Atomic write: Write to temp file, then rename
        # This prevents partial writes if process crashes during write
        temp_path = BEST_YAML_PATH.with_suffix(".yaml.tmp")
        
        try:
            # Write validated data to temp file
            with temp_path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(
                    validated.model_dump(),
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True
                )
            
            # Atomic rename on POSIX (single system call)
            temp_path.replace(BEST_YAML_PATH)
            
        except Exception as write_error:
            # Clean up temp file if it exists
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise write_error
        
        logger.info(f"[BEST] Successfully updated {BEST_YAML_PATH}")
        return validated.model_dump()
        
    except portalocker.LockException as e:
        logger.error(f"[BEST] File lock timeout after retries: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "best_yaml_lock_timeout",
                "message": "file lock timeout after retries"
            }
        )
    except yaml.YAMLError as e:
        logger.error(f"[BEST] YAML dump error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"YAML serialization error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[BEST] Write error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update best.yaml: {str(e)}"
        )


@router.post("/snapshot")
async def create_snapshot():
    """
    POST /api/snapshot
    
    Create a snapshot of the current Best Pack configuration.
    
    Saves best.yaml + environment context to reports/_snapshots/
    
    Returns:
        Snapshot metadata with path and timestamp
    """
    try:
        import subprocess
        import time as time_module
        
        # Get git SHA
        git_sha = "unknown"
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=2,
                cwd=str(PROJECT_ROOT)
            )
            if result.returncode == 0:
                git_sha = result.stdout.strip()[:8]
        except:
            pass
        
        # Read current best.yaml
        best_data = {}
        if BEST_YAML_PATH.exists():
            try:
                with locked_open(BEST_YAML_PATH, "r") as f:
                    content = f.read()
                    if content:
                        best_data = yaml.safe_load(content) or {}
            except:
                pass
        
        # Build snapshot
        timestamp = int(time_module.time())
        snapshot = {
            "timestamp": timestamp,
            "timestamp_human": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "git_sha": git_sha,
            "best_config": best_data,
            "trigger": "manual"
        }
        
        # Write to reports/_snapshots/
        snapshots_dir = PROJECT_ROOT / "reports" / "_snapshots"
        snapshots_dir.mkdir(parents=True, exist_ok=True)
        
        snapshot_file = snapshots_dir / f"{timestamp}_snapshot.json"
        import json
        with open(snapshot_file, "w") as f:
            json.dump(snapshot, f, indent=2)
        
        logger.info(f"[SNAPSHOT] Created: {snapshot_file}")
        
        return {
            "ok": True,
            "path": str(snapshot_file.relative_to(PROJECT_ROOT)),
            "timestamp": timestamp
        }
        
    except Exception as e:
        logger.error(f"[SNAPSHOT] Error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create snapshot: {str(e)}"
        )


@router.get("/artifacts/{job_id}")
async def get_artifacts(job_id: str):
    """
    GET /api/artifacts/{job_id}
    
    V6: Get artifacts bound to the specific job_id.
    Returns artifacts parsed from the subprocess output via ARTIFACTS_JSON.
    
    Returns:
        Artifacts metadata with paths to YAML report and charts
    """
    try:
        # V6: Validate job_id to prevent path traversal
        import re
        if not re.match(r'^[a-zA-Z0-9_-]{1,200}$', job_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid job_id format"
            )
        
        # Try new registry system first
        from services.fiqa_api.routes.experiment import _JOB_REGISTRY, _JOBS, _RUNS_DIR, _LOCK
        from pathlib import Path
        import json
        
        artifacts = None
        
        # Check if job exists in new system - try to parse from log regardless
        log_path = _RUNS_DIR / f"{job_id}.log"
        if log_path.exists():
            try:
                log_content = log_path.read_text(errors="ignore")
                # Search for [ARTIFACTS_JSON] marker
                for line in log_content.splitlines():
                    if '[ARTIFACTS_JSON]' in line:
                        marker_start = line.find('[ARTIFACTS_JSON]') + len('[ARTIFACTS_JSON]')
                        json_str = line[marker_start:].strip()
                        artifacts = json.loads(json_str)
                        break
            except Exception as e:
                logger.warning(f"Failed to parse artifacts from log for {job_id}: {e}")
        
        # If not found in new system, try old JobManager
        if artifacts is None:
            try:
                from services.fiqa_api.job_runner import get_job_manager
                
                manager = get_job_manager()
                job = manager.get_status(job_id)
                
                if job and job.artifacts:
                    artifacts = job.artifacts.copy()
            except Exception as e:
                logger.debug(f"JobManager lookup failed for {job_id}: {e}")
        
        # If still no artifacts found, return empty response (not 404)
        if artifacts is None:
            return {
                "ok": False,
                "artifacts": {
                    "job_id": job_id,
                    "timestamp": None,
                    "report_dir": None,
                    "yaml_report": None,
                    "combined_plot": None
                }
            }
        
        artifacts["job_id"] = job_id
        
        # Load YAML data if available
        yaml_report_path = artifacts.get("yaml_report")
        if yaml_report_path:
            full_yaml_path = PROJECT_ROOT / yaml_report_path
            if full_yaml_path.exists():
                try:
                    with open(full_yaml_path, 'r') as f:
                        artifacts["report_data"] = yaml.safe_load(f)
                except:
                    pass
        
        return {
            "ok": True,
            "artifacts": artifacts
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ARTIFACTS] Error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get artifacts: {str(e)}"
        )
