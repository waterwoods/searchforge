"""
preset_manager.py - Preset Configuration Manager
==================================================
V10: Manages preset configurations for experiments.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from services.fiqa_api.utils.fs import read_json, write_json_atomic
from services.fiqa_api.models.experiment_models import ExperimentConfig

logger = logging.getLogger(__name__)


class PresetManager:
    """Manages experiment preset configurations."""
    
    def __init__(self, presets_file: Optional[str] = None):
        """
        Initialize preset manager.
        
        Args:
            presets_file: Optional path to presets.json file (defaults to RAGLAB_DIR/presets.json)
        """
        if presets_file is None:
            # Use same directory as jobs.json
            base_dir = os.getenv("RAGLAB_DIR", "/tmp/raglab")
            presets_file = str(Path(base_dir) / "presets.json")
        self.presets_file = Path(presets_file)
        self._ensure_presets_dir()
        self._init_default_presets()
    
    def _ensure_presets_dir(self):
        """Ensure presets directory exists."""
        self.presets_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _init_default_presets(self):
        """Initialize with default presets if file doesn't exist."""
        if not self.presets_file.exists():
            logger.info(f"Creating default presets.json at {self.presets_file}")
            default_presets = self._get_default_presets()
            write_json_atomic(str(self.presets_file), default_presets)
            logger.info(f"Initialized {len(default_presets)} default presets")
    
    def _get_default_presets(self) -> Dict[str, Dict]:
        """Get default preset configurations."""
        now = datetime.now().isoformat()
        return {
            "fiqa-fast-baseline": {
                "name": "FIQA Fast - Baseline",
                "description": "Fast mode baseline (vector only)",
                "config": {
                    "base_url": "http://localhost:8011",
                    "dataset_name": "fiqa",
                    "data_dir": "experiments/data/fiqa",
                    "top_k": 40,
                    "repeats": 1,
                    "warmup": 5,
                    "concurrency": 16,
                    "sample": 200,
                    "fast_mode": True,
                    "fast_rrf_k": 40,
                    "fast_topk": 40,
                    "fast_rerank_topk": 10,
                    "groups": [
                        {
                            "name": "Baseline",
                            "use_hybrid": False,
                            "rerank": False,
                            "description": "Pure vector search baseline"
                        }
                    ]
                },
                "created_at": now,
                "updated_at": now
            },
            "fiqa-fast-rrf": {
                "name": "FIQA Fast - RRF",
                "description": "Fast mode with RRF hybrid search",
                "config": {
                    "base_url": "http://localhost:8011",
                    "dataset_name": "fiqa",
                    "data_dir": "experiments/data/fiqa",
                    "top_k": 40,
                    "repeats": 1,
                    "warmup": 5,
                    "concurrency": 16,
                    "sample": 200,
                    "fast_mode": True,
                    "fast_rrf_k": 40,
                    "fast_topk": 40,
                    "fast_rerank_topk": 10,
                    "groups": [
                        {
                            "name": "+RRF",
                            "use_hybrid": True,
                            "rrf_k": 40,
                            "rerank": False,
                            "description": "Hybrid RRF (BM25 + vector fusion)"
                        }
                    ]
                },
                "created_at": now,
                "updated_at": now
            },
            "fiqa-fast-full": {
                "name": "FIQA Fast - Full Suite",
                "description": "Fast mode all three configurations",
                "config": {
                    "base_url": "http://localhost:8011",
                    "dataset_name": "fiqa",
                    "data_dir": "experiments/data/fiqa",
                    "top_k": 40,
                    "repeats": 1,
                    "warmup": 5,
                    "concurrency": 16,
                    "sample": 200,
                    "fast_mode": True,
                    "fast_rrf_k": 40,
                    "fast_topk": 40,
                    "fast_rerank_topk": 10,
                    "groups": [
                        {
                            "name": "Baseline",
                            "use_hybrid": False,
                            "rerank": False,
                            "description": "Pure vector search baseline"
                        },
                        {
                            "name": "+RRF",
                            "use_hybrid": True,
                            "rrf_k": 40,
                            "rerank": False,
                            "description": "Hybrid RRF (BM25 + vector fusion)"
                        },
                        {
                            "name": "+Gated Rerank",
                            "use_hybrid": True,
                            "rrf_k": 40,
                            "rerank": True,
                            "rerank_top_k": 10,
                            "rerank_if_margin_below": 0.12,
                            "max_rerank_trigger_rate": 0.25,
                            "rerank_budget_ms": 25,
                            "description": "Hybrid RRF + gated reranking"
                        }
                    ]
                },
                "created_at": now,
                "updated_at": now
            },
            "fiqa-full": {
                "name": "FIQA Full",
                "description": "Full run all configurations",
                "config": {
                    "base_url": "http://localhost:8011",
                    "dataset_name": "fiqa",
                    "data_dir": "experiments/data/fiqa",
                    "top_k": 50,
                    "repeats": 3,
                    "warmup": 5,
                    "concurrency": 16,
                    "sample": None,
                    "fast_mode": False,
                    "fast_rrf_k": 60,
                    "fast_topk": 50,
                    "fast_rerank_topk": 20,
                    "groups": [
                        {
                            "name": "Baseline",
                            "use_hybrid": False,
                            "rerank": False,
                            "description": "Pure vector search baseline"
                        },
                        {
                            "name": "+RRF",
                            "use_hybrid": True,
                            "rrf_k": 60,
                            "rerank": False,
                            "description": "Hybrid RRF (BM25 + vector fusion)"
                        },
                        {
                            "name": "+Gated Rerank",
                            "use_hybrid": True,
                            "rrf_k": 60,
                            "rerank": True,
                            "rerank_top_k": 20,
                            "rerank_if_margin_below": 0.12,
                            "max_rerank_trigger_rate": 0.25,
                            "rerank_budget_ms": 25,
                            "description": "Hybrid RRF + gated reranking"
                        }
                    ]
                },
                "created_at": now,
                "updated_at": now
            }
        }
    
    def list_presets(self) -> Dict[str, Dict]:
        """
        List all available presets.
        
        Returns:
            Dictionary mapping preset names to metadata
        """
        presets_data = read_json(str(self.presets_file), {})
        result = {}
        for name, preset in presets_data.items():
            result[name] = {
                "name": preset.get("name", name),
                "description": preset.get("description", ""),
                "created_at": preset.get("created_at"),
                "updated_at": preset.get("updated_at")
            }
        return result
    
    def get_preset(self, name: str) -> Optional[ExperimentConfig]:
        """
        Get a preset configuration by name.
        
        Args:
            name: Preset name
            
        Returns:
            ExperimentConfig or None if not found
        """
        presets_data = read_json(str(self.presets_file), {})
        preset = presets_data.get(name)
        
        if preset is None:
            return None
        
        config_dict = preset.get("config")
        if config_dict is None:
            logger.error(f"Preset {name} missing 'config' field")
            return None
        
        try:
            return ExperimentConfig(**config_dict)
        except Exception as e:
            logger.error(f"Failed to parse preset {name}: {e}")
            return None
    
    def save_preset(self, name: str, config: ExperimentConfig, description: str = "") -> bool:
        """
        Save or update a preset.
        
        Args:
            name: Preset name
            config: Experiment configuration
            description: Optional description
            
        Returns:
            True if successful
        """
        try:
            presets_data = read_json(str(self.presets_file), {})
            
            # Get or create preset entry
            preset = presets_data.get(name, {})
            preset.update({
                "name": name,
                "description": description or preset.get("description", ""),
                "config": config.model_dump(),
                "updated_at": datetime.now().isoformat()
            })
            
            if "created_at" not in preset:
                preset["created_at"] = datetime.now().isoformat()
            
            presets_data[name] = preset
            
            write_json_atomic(str(self.presets_file), presets_data)
            logger.info(f"Saved preset: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save preset {name}: {e}")
            return False
    
    def delete_preset(self, name: str) -> bool:
        """
        Delete a preset.
        
        Args:
            name: Preset name
            
        Returns:
            True if successful
        """
        try:
            presets_data = read_json(str(self.presets_file), {})
            
            if name not in presets_data:
                return False
            
            del presets_data[name]
            write_json_atomic(str(self.presets_file), presets_data)
            logger.info(f"Deleted preset: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete preset {name}: {e}")
            return False


# Global singleton instance
_preset_manager: Optional[PresetManager] = None


def get_preset_manager() -> PresetManager:
    """Get PresetManager singleton instance."""
    global _preset_manager
    if _preset_manager is None:
        _preset_manager = PresetManager()
    return _preset_manager





