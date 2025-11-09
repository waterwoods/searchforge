"""Tests for policy guard and alignment validation."""

import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from agents.orchestrator.flow import AlignmentBlockError, DatasetBlockError


class TestPolicyGuard:
    """Test policy guard validation."""

    @pytest.fixture
    def config_path(self):
        """Path to config.yaml."""
        return Path(__file__).parent.parent.parent / "agents" / "orchestrator" / "config.yaml"

    @pytest.fixture
    def policies_path(self):
        """Path to policies.json."""
        return Path(__file__).parent.parent.parent / "configs" / "policies.json"

    @pytest.fixture
    def config(self, config_path):
        """Load config.yaml."""
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    @pytest.fixture
    def policies(self, policies_path):
        """Load policies.json."""
        with open(policies_path, encoding="utf-8") as f:
            return json.load(f)

    def test_positive_all_policies_valid(self, config, policies):
        """Test that all current policies pass validation."""
        whitelist = set(config.get("datasets", {}).get("whitelist", []))
        disabled = set(config.get("datasets", {}).get("disabled", []))
        qmap = config.get("datasets", {}).get("queries_map", {})
        rmap = config.get("datasets", {}).get("qrels_map", {})

        repo_root = Path(__file__).parent.parent.parent

        policies_data = policies.get("policies", {})
        for policy_name, policy in policies_data.items():
            dataset = policy.get("dataset")
            assert dataset is not None, f"Policy {policy_name} missing dataset"

            # Check whitelist/disabled
            assert dataset in whitelist, f"Policy {policy_name} dataset {dataset} not in whitelist"
            assert dataset not in disabled, f"Policy {policy_name} dataset {dataset} is disabled"

            # Check paths
            queries_path = policy.get("queries_path") or qmap.get(dataset)
            qrels_path = policy.get("qrels_path") or rmap.get(dataset)

            assert queries_path is not None, f"Policy {policy_name} missing queries_path"
            assert qrels_path is not None, f"Policy {policy_name} missing qrels_path"

            # Check files exist
            queries_full = repo_root / queries_path if not Path(queries_path).is_absolute() else Path(queries_path)
            qrels_full = repo_root / qrels_path if not Path(qrels_path).is_absolute() else Path(qrels_path)

            assert queries_full.exists(), f"Policy {policy_name} queries_path {queries_path} not found"
            assert qrels_full.exists(), f"Policy {policy_name} qrels_path {qrels_path} not found"

    def test_negative_dataset_disabled(self, config, policies, policies_path):
        """Test that using a disabled dataset fails."""
        # Create a temporary copy of policies.json
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            tmp_policies = policies.copy()
            # Modify one policy to use disabled dataset
            policies_data = tmp_policies.get("policies", {})
            first_policy_name = list(policies_data.keys())[0]
            policies_data[first_policy_name] = policies_data[first_policy_name].copy()
            policies_data[first_policy_name]["dataset"] = "fiqa_50k_v1"  # This should be disabled

            json.dump(tmp_policies, tmp)
            tmp_path = tmp.name

        try:
            # Run CI guard
            result = subprocess.run(
                ["make", "ci:policy-guard"],
                cwd=Path(__file__).parent.parent.parent,
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Should fail with DATASET_BLOCK
            assert result.returncode != 0, "CI guard should fail with disabled dataset"
            assert "DATASET_BLOCK" in result.stdout or "DATASET_BLOCK" in result.stderr
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_negative_missing_qrels_path(self, config, policies, policies_path):
        """Test that missing qrels_path fails."""
        # Create a temporary copy of policies.json
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            tmp_policies = policies.copy()
            # Modify one policy to remove qrels_path
            policies_data = tmp_policies.get("policies", {})
            first_policy_name = list(policies_data.keys())[0]
            policies_data[first_policy_name] = policies_data[first_policy_name].copy()
            del policies_data[first_policy_name]["qrels_path"]

            json.dump(tmp_policies, tmp)
            tmp_path = tmp.name

        try:
            # Temporarily replace policies.json
            backup_path = policies_path.with_suffix('.json.bak')
            policies_path.rename(backup_path)
            Path(tmp_path).rename(policies_path)

            try:
                # Run CI guard
                result = subprocess.run(
                    ["make", "ci:policy-guard"],
                    cwd=Path(__file__).parent.parent.parent,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                # Should fail with ALIGNMENT_BLOCK
                assert result.returncode != 0, "CI guard should fail with missing qrels_path"
                assert "ALIGNMENT_BLOCK" in result.stdout or "ALIGNMENT_BLOCK" in result.stderr
            finally:
                # Restore original
                if policies_path.exists():
                    policies_path.unlink()
                backup_path.rename(policies_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_flow_dataset_block_error(self):
        """Test that DatasetBlockError is raised correctly."""
        error = DatasetBlockError(
            "Dataset is disabled",
            code="DATASET_BLOCK",
            payload={"dataset": "fiqa_50k_v1", "hint": "Use whitelisted dataset"},
        )
        assert error.code == "DATASET_BLOCK"
        assert "fiqa_50k_v1" in str(error)
        assert error.payload["dataset"] == "fiqa_50k_v1"

    def test_flow_alignment_block_error(self):
        """Test that AlignmentBlockError is raised correctly."""
        error = AlignmentBlockError(
            "Alignment check failed",
            code="ALIGNMENT_BLOCK",
            payload={"dataset": "fiqa_para_50k", "mismatch_rate": 0.1},
        )
        assert error.code == "ALIGNMENT_BLOCK"
        assert "Alignment check failed" in str(error)
        assert error.payload["mismatch_rate"] == 0.1

