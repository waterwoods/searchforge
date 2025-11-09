"""
Orchestrator package exposing high-level APIs for experiment automation.

Modules are implemented incrementally following the milestones described in the
master orchestrator prompt. Consumers should interact with the public helpers
in `flow.py`.
"""

from .flow import ExperimentPlan, ExperimentReport, OrchestratorFlow  # noqa: F401

