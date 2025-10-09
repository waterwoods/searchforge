"""
Configuration Version Manager for Canary Deployments

This module manages configuration versions, presets, and state tracking
for the canary deployment system.
"""

import os
import yaml
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConfigVersion:
    """Represents a configuration version with metadata."""
    name: str
    description: str
    created_at: str
    version: str
    tags: List[str]
    macro_knobs: Dict[str, float]
    derived_params: Dict[str, Any]
    retriever: Dict[str, Any]
    reranker: Dict[str, Any]
    slo: Dict[str, float]


@dataclass
class ConfigState:
    """Represents the current state of configuration deployment."""
    active_config: str
    last_good_config: str
    candidate_config: Optional[str]
    canary_start_time: Optional[str]
    canary_status: str  # "idle", "running", "rolled_back", "promoted"


class ConfigManager:
    """
    Manages configuration versions and deployment state.
    
    Features:
    - Load/save configuration presets
    - Track active, last_good, and candidate configurations
    - Manage deployment state
    - Provide configuration snapshots
    """
    
    def __init__(self, presets_dir: str = "configs/presets", state_file: str = "configs/canary_state.json"):
        """
        Initialize the configuration manager.
        
        Args:
            presets_dir: Directory containing configuration presets
            state_file: File to store deployment state
        """
        self.presets_dir = Path(presets_dir)
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load current state
        self.state = self._load_state()
        
        # Ensure presets directory exists
        self.presets_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ConfigManager initialized with presets_dir={self.presets_dir}, state_file={self.state_file}")
    
    def _load_state(self) -> ConfigState:
        """Load deployment state from file."""
        if not self.state_file.exists():
            # Initialize with default state
            return ConfigState(
                active_config="last_good",
                last_good_config="last_good",
                candidate_config=None,
                canary_start_time=None,
                canary_status="idle"
            )
        
        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
            return ConfigState(**data)
        except Exception as e:
            logger.error(f"Failed to load state from {self.state_file}: {e}")
            return ConfigState(
                active_config="last_good",
                last_good_config="last_good",
                candidate_config=None,
                canary_start_time=None,
                canary_status="idle"
            )
    
    def _save_state(self) -> None:
        """Save deployment state to file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(asdict(self.state), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state to {self.state_file}: {e}")
    
    def list_presets(self) -> List[str]:
        """List all available configuration presets."""
        preset_files = list(self.presets_dir.glob("*.yaml"))
        return [f.stem for f in preset_files]
    
    def load_preset(self, preset_name: str) -> ConfigVersion:
        """
        Load a configuration preset.
        
        Args:
            preset_name: Name of the preset to load
            
        Returns:
            ConfigVersion object
            
        Raises:
            FileNotFoundError: If preset doesn't exist
            ValueError: If preset format is invalid
        """
        preset_file = self.presets_dir / f"{preset_name}.yaml"
        if not preset_file.exists():
            raise FileNotFoundError(f"Preset '{preset_name}' not found in {self.presets_dir}")
        
        try:
            with open(preset_file, 'r') as f:
                data = yaml.safe_load(f)
            
            # Validate required fields
            required_fields = ['metadata', 'macro_knobs', 'derived_params', 'retriever', 'reranker', 'slo']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field '{field}' in preset '{preset_name}'")
            
            metadata = data['metadata']
            return ConfigVersion(
                name=metadata['name'],
                description=metadata['description'],
                created_at=metadata['created_at'],
                version=metadata['version'],
                tags=metadata.get('tags', []),
                macro_knobs=data['macro_knobs'],
                derived_params=data['derived_params'],
                retriever=data['retriever'],
                reranker=data['reranker'],
                slo=data['slo']
            )
        except Exception as e:
            raise ValueError(f"Failed to load preset '{preset_name}': {e}")
    
    def save_preset(self, config: ConfigVersion) -> None:
        """
        Save a configuration preset.
        
        Args:
            config: ConfigVersion object to save
        """
        preset_file = self.presets_dir / f"{config.name}.yaml"
        
        data = {
            'metadata': {
                'name': config.name,
                'description': config.description,
                'created_at': config.created_at,
                'version': config.version,
                'tags': config.tags
            },
            'macro_knobs': config.macro_knobs,
            'derived_params': config.derived_params,
            'retriever': config.retriever,
            'reranker': config.reranker,
            'slo': config.slo
        }
        
        try:
            with open(preset_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Saved preset '{config.name}' to {preset_file}")
        except Exception as e:
            logger.error(f"Failed to save preset '{config.name}': {e}")
            raise
    
    def get_current_configs(self) -> Tuple[ConfigVersion, Optional[ConfigVersion]]:
        """
        Get current active and candidate configurations.
        
        Returns:
            Tuple of (active_config, candidate_config)
        """
        active_config = self.load_preset(self.state.active_config)
        candidate_config = None
        
        if self.state.candidate_config:
            try:
                candidate_config = self.load_preset(self.state.candidate_config)
            except Exception as e:
                logger.warning(f"Failed to load candidate config '{self.state.candidate_config}': {e}")
        
        return active_config, candidate_config
    
    def get_last_good_config(self) -> ConfigVersion:
        """Get the last good configuration."""
        return self.load_preset(self.state.last_good_config)
    
    def start_canary(self, candidate_name: str) -> None:
        """
        Start a canary deployment with the specified candidate configuration.
        
        Args:
            candidate_name: Name of the candidate configuration to deploy
        """
        if not (self.presets_dir / f"{candidate_name}.yaml").exists():
            raise FileNotFoundError(f"Candidate configuration '{candidate_name}' not found")
        
        if self.state.canary_status == "running":
            # Allow restarting if the same candidate
            if self.state.candidate_config == candidate_name:
                logger.info(f"Restarting canary deployment with same candidate: {candidate_name}")
            else:
                raise ValueError("Canary deployment is already running")
        
        # Update state
        self.state.candidate_config = candidate_name
        self.state.canary_start_time = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.state.canary_status = "running"
        
        self._save_state()
        logger.info(f"Started canary deployment with candidate '{candidate_name}'")
    
    def promote_candidate(self) -> None:
        """Promote the candidate configuration to active and update last_good."""
        if not self.state.candidate_config:
            raise ValueError("No candidate configuration to promote")
        
        # Update last_good to current active
        self.state.last_good_config = self.state.active_config
        
        # Promote candidate to active
        self.state.active_config = self.state.candidate_config
        
        # Clear canary state
        self.state.candidate_config = None
        self.state.canary_start_time = None
        self.state.canary_status = "promoted"
        
        self._save_state()
        logger.info(f"Promoted candidate configuration to active")
    
    def rollback_candidate(self, reason: str = "SLO violation") -> None:
        """
        Rollback to the last good configuration.
        
        Args:
            reason: Reason for rollback
        """
        if not self.state.candidate_config:
            logger.warning("No candidate configuration to rollback")
            return
        
        # Clear canary state
        self.state.candidate_config = None
        self.state.canary_start_time = None
        self.state.canary_status = "rolled_back"
        
        self._save_state()
        logger.info(f"Rolled back candidate configuration. Reason: {reason}")
    
    def get_canary_status(self) -> Dict[str, Any]:
        """Get current canary deployment status."""
        return {
            "status": self.state.canary_status,
            "active_config": self.state.active_config,
            "last_good_config": self.state.last_good_config,
            "candidate_config": self.state.candidate_config,
            "canary_start_time": self.state.canary_start_time
        }
    
    def create_config_from_current(self, name: str, description: str = "") -> ConfigVersion:
        """
        Create a new configuration preset from current macro knobs and derived parameters.
        
        Args:
            name: Name for the new preset
            description: Description for the new preset
            
        Returns:
            ConfigVersion object
        """
        from modules.autotune.macros import get_macro_config, derive_params
        
        # Get current macro configuration
        macro_config = get_macro_config()
        derived_params = derive_params(macro_config["latency_guard"], macro_config["recall_bias"])
        
        # Load a base configuration template
        try:
            base_config = self.load_preset("last_good")
        except:
            # Create a minimal base configuration if last_good doesn't exist
            base_config = ConfigVersion(
                name="base",
                description="Base configuration",
                created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                version="1.0.0",
                tags=[],
                macro_knobs=macro_config,
                derived_params=derived_params,
                retriever={"type": "hybrid", "alpha": 0.6, "vector_top_k": 200, "bm25_top_k": 200, "top_k": 50},
                reranker={"type": "cross_encoder", "model": "cross-encoder/ms-marco-MiniLM-L-6-v2", "top_k": 50},
                slo={"p95_ms": 1200, "recall_at_10": 0.30}
            )
        
        # Create new configuration with current parameters
        new_config = ConfigVersion(
            name=name,
            description=description or f"Configuration created from current parameters at {time.strftime('%Y-%m-%d %H:%M:%S')}",
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            version="1.0.0",
            tags=["auto-generated"],
            macro_knobs=macro_config,
            derived_params=derived_params,
            retriever=base_config.retriever,
            reranker=base_config.reranker,
            slo=base_config.slo
        )
        
        return new_config
