"""
Audit Logger for Canary Deployments

This module provides comprehensive audit logging for all canary deployment
operations, including configuration changes, rollbacks, and system events.
"""

import os
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""
    CANARY_START = "canary_start"
    CANARY_PROMOTE = "canary_promote"
    CANARY_ROLLBACK = "canary_rollback"
    CANARY_STOP = "canary_stop"
    CONFIG_CREATE = "config_create"
    CONFIG_UPDATE = "config_update"
    CONFIG_DELETE = "config_delete"
    SLO_VIOLATION = "slo_violation"
    MANUAL_ROLLBACK = "manual_rollback"
    SYSTEM_ERROR = "system_error"


@dataclass
class AuditEvent:
    """Represents an audit log event."""
    event_id: str
    event_type: AuditEventType
    timestamp: str
    deployment_id: Optional[str]
    user_id: Optional[str]
    config_name: Optional[str]
    details: Dict[str, Any]
    success: bool
    error_message: Optional[str]


class AuditLogger:
    """
    Comprehensive audit logging for canary deployments.
    
    Features:
    - Structured audit events for all operations
    - JSON-based log format for easy parsing
    - Automatic log rotation and archival
    - Search and filtering capabilities
    - Integration with all canary components
    """
    
    def __init__(self, audit_log_dir: str = "reports/canary"):
        """
        Initialize the audit logger.
        
        Args:
            audit_log_dir: Directory for audit log files
        """
        self.audit_log_dir = Path(audit_log_dir)
        self.audit_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Main audit log file
        self.audit_log_file = self.audit_log_dir / "audit.log"
        
        # Current session log file (for easier analysis)
        self.session_log_file = self.audit_log_dir / f"session_{int(time.time())}.log"
        
        logger.info(f"AuditLogger initialized with log_dir={self.audit_log_dir}")
    
    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        return f"audit_{int(time.time() * 1000)}_{hash(str(time.time())) % 10000}"
    
    def _write_audit_event(self, event: AuditEvent) -> None:
        """
        Write an audit event to the log files.
        
        Args:
            event: Audit event to write
        """
        event_dict = asdict(event)
        event_dict["event_type"] = event.event_type.value  # Convert enum to string
        event_json = json.dumps(event_dict, ensure_ascii=False)
        
        try:
            # Write to main audit log (append mode)
            with open(self.audit_log_file, 'a', encoding='utf-8') as f:
                f.write(event_json + '\n')
            
            # Write to session log
            with open(self.session_log_file, 'a', encoding='utf-8') as f:
                f.write(event_json + '\n')
            
            logger.debug(f"Logged audit event: {event.event_type.value} - {event.event_id}")
            
        except Exception as e:
            logger.error(f"Failed to write audit event: {e}")
    
    def log_canary_start(self, deployment_id: str, candidate_config: str, 
                        traffic_split: Dict[str, float], user_id: Optional[str] = None) -> None:
        """
        Log the start of a canary deployment.
        
        Args:
            deployment_id: Unique deployment ID
            candidate_config: Name of the candidate configuration
            traffic_split: Traffic split configuration
            user_id: Optional user ID who initiated the deployment
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.CANARY_START,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            deployment_id=deployment_id,
            user_id=user_id,
            config_name=candidate_config,
            details={
                "candidate_config": candidate_config,
                "traffic_split": traffic_split,
                "action": "start_canary_deployment"
            },
            success=True,
            error_message=None
        )
        
        self._write_audit_event(event)
    
    def log_canary_promote(self, deployment_id: str, candidate_config: str, 
                          metrics_summary: Dict[str, Any], user_id: Optional[str] = None) -> None:
        """
        Log the promotion of a candidate configuration.
        
        Args:
            deployment_id: Unique deployment ID
            candidate_config: Name of the promoted configuration
            metrics_summary: Summary of deployment metrics
            user_id: Optional user ID who initiated the promotion
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.CANARY_PROMOTE,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            deployment_id=deployment_id,
            user_id=user_id,
            config_name=candidate_config,
            details={
                "candidate_config": candidate_config,
                "metrics_summary": metrics_summary,
                "action": "promote_candidate_configuration"
            },
            success=True,
            error_message=None
        )
        
        self._write_audit_event(event)
    
    def log_canary_rollback(self, deployment_id: str, candidate_config: str, 
                           reason: str, metrics_summary: Dict[str, Any], 
                           user_id: Optional[str] = None) -> None:
        """
        Log a canary rollback.
        
        Args:
            deployment_id: Unique deployment ID
            candidate_config: Name of the rolled back configuration
            reason: Reason for the rollback
            metrics_summary: Summary of deployment metrics
            user_id: Optional user ID who initiated the rollback
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.CANARY_ROLLBACK,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            deployment_id=deployment_id,
            user_id=user_id,
            config_name=candidate_config,
            details={
                "candidate_config": candidate_config,
                "rollback_reason": reason,
                "metrics_summary": metrics_summary,
                "action": "rollback_candidate_configuration"
            },
            success=True,
            error_message=None
        )
        
        self._write_audit_event(event)
    
    def log_slo_violation(self, deployment_id: str, config_name: str, 
                         violation_details: Dict[str, Any]) -> None:
        """
        Log an SLO violation.
        
        Args:
            deployment_id: Unique deployment ID
            config_name: Configuration name that violated SLO
            violation_details: Details of the SLO violation
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.SLO_VIOLATION,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            deployment_id=deployment_id,
            user_id="system",
            config_name=config_name,
            details={
                "config_name": config_name,
                "violation_details": violation_details,
                "action": "slo_violation_detected"
            },
            success=False,
            error_message=f"SLO violation in {config_name}"
        )
        
        self._write_audit_event(event)
    
    def log_config_operation(self, operation_type: AuditEventType, config_name: str, 
                           config_details: Dict[str, Any], success: bool = True, 
                           error_message: Optional[str] = None, user_id: Optional[str] = None) -> None:
        """
        Log a configuration operation.
        
        Args:
            operation_type: Type of configuration operation
            config_name: Name of the configuration
            config_details: Details of the configuration
            success: Whether the operation was successful
            error_message: Error message if operation failed
            user_id: Optional user ID who performed the operation
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=operation_type,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            deployment_id=None,
            user_id=user_id,
            config_name=config_name,
            details={
                "config_name": config_name,
                "config_details": config_details,
                "action": f"{operation_type.value}_configuration"
            },
            success=success,
            error_message=error_message
        )
        
        self._write_audit_event(event)
    
    def log_system_error(self, error_message: str, error_details: Dict[str, Any], 
                        component: Optional[str] = None) -> None:
        """
        Log a system error.
        
        Args:
            error_message: Error message
            error_details: Additional error details
            component: Optional component name where error occurred
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.SYSTEM_ERROR,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            deployment_id=None,
            user_id="system",
            config_name=component,
            details={
                "component": component,
                "error_details": error_details,
                "action": "system_error"
            },
            success=False,
            error_message=error_message
        )
        
        self._write_audit_event(event)
    
    def read_audit_events(self, log_file: Optional[str] = None, 
                         event_types: Optional[List[AuditEventType]] = None,
                         deployment_id: Optional[str] = None,
                         config_name: Optional[str] = None,
                         limit: Optional[int] = None) -> List[AuditEvent]:
        """
        Read and filter audit events from log files.
        
        Args:
            log_file: Specific log file to read (default: main audit log)
            event_types: Optional list of event types to filter by
            deployment_id: Optional deployment ID to filter by
            config_name: Optional configuration name to filter by
            limit: Optional limit on number of events to return
            
        Returns:
            List of AuditEvent objects
        """
        if log_file is None:
            log_file = self.audit_log_file
        
        if not Path(log_file).exists():
            return []
        
        events = []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        event_dict = json.loads(line.strip())
                        
                        # Convert event_type string back to enum
                        event_dict["event_type"] = AuditEventType(event_dict["event_type"])
                        
                        event = AuditEvent(**event_dict)
                        
                        # Apply filters
                        if event_types and event.event_type not in event_types:
                            continue
                        
                        if deployment_id and event.deployment_id != deployment_id:
                            continue
                        
                        if config_name and event.config_name != config_name:
                            continue
                        
                        events.append(event)
                        
                        # Apply limit
                        if limit and len(events) >= limit:
                            break
                    
                    except (json.JSONDecodeError, ValueError, TypeError) as e:
                        logger.warning(f"Failed to parse audit event line: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Failed to read audit events from {log_file}: {e}")
        
        return events
    
    def export_audit_events(self, output_file: str, **filter_kwargs) -> None:
        """
        Export filtered audit events to a JSON file.
        
        Args:
            output_file: Output file path
            **filter_kwargs: Filter arguments for read_audit_events
        """
        events = self.read_audit_events(**filter_kwargs)
        
        export_data = {
            "export_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_events": len(events),
            "filters": filter_kwargs,
            "events": [asdict(event) for event in events]
        }
        
        # Convert enum to string for JSON serialization
        for event_dict in export_data["events"]:
            event_dict["event_type"] = event_dict["event_type"].value
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Exported {len(events)} audit events to {output_file}")
        except Exception as e:
            logger.error(f"Failed to export audit events to {output_file}: {e}")
            raise
    
    def get_deployment_audit_trail(self, deployment_id: str) -> List[AuditEvent]:
        """
        Get the complete audit trail for a deployment.
        
        Args:
            deployment_id: Deployment ID to get audit trail for
            
        Returns:
            List of AuditEvent objects for the deployment
        """
        return self.read_audit_events(deployment_id=deployment_id)
    
    def get_recent_events(self, hours: int = 24, limit: int = 100) -> List[AuditEvent]:
        """
        Get recent audit events.
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of events to return
            
        Returns:
            List of recent AuditEvent objects
        """
        cutoff_time = time.time() - (hours * 3600)
        cutoff_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(cutoff_time))
        
        events = self.read_audit_events(limit=limit)
        
        # Filter by timestamp
        recent_events = []
        for event in events:
            event_time = time.mktime(time.strptime(event.timestamp, "%Y-%m-%dT%H:%M:%SZ"))
            if event_time >= cutoff_time:
                recent_events.append(event)
        
        return recent_events


# Global audit logger instance
_global_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _global_audit_logger
    if _global_audit_logger is None:
        _global_audit_logger = AuditLogger()
    return _global_audit_logger


