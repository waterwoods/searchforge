"""
semantic_tools.py - Semantic Ops Tools for Ops Copilot
=======================================================
LLM-grounded tools for operational data: logs, runbooks, and incidents.

These tools provide "realistic-looking" interfaces that would normally connect
to real systems (Splunk, Datadog, CMDB, etc.), but currently use mock data.
"""

from typing import Dict, List, Optional, Literal, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import random


# ========================================
# Pydantic Models
# ========================================

class LogEntry(BaseModel):
    """A single log entry from a service."""
    timestamp: datetime = Field(..., description="Log entry timestamp")
    level: Literal["INFO", "WARN", "ERROR"] = Field(..., description="Log level")
    message: str = Field(..., description="Log message content")
    source: Optional[str] = Field(None, description="Module or component name")


class LogSummary(BaseModel):
    """Summary of logs from a service over a time window."""
    service_name: str = Field(..., description="Service name")
    window_minutes: int = Field(..., description="Time window in minutes")
    total_lines: int = Field(..., description="Total log lines in window")
    error_count: int = Field(..., description="Number of ERROR level logs")
    warn_count: int = Field(..., description="Number of WARN level logs")
    sample_entries: List[LogEntry] = Field(
        default_factory=list,
        description="Sample log entries (max 5)",
    )


class RunbookStep(BaseModel):
    """A single step in a runbook procedure."""
    order: int = Field(..., description="Step order (1-based)")
    action: str = Field(..., description="Action to perform")
    notes: Optional[str] = Field(None, description="Additional notes or context")


class RunbookEntry(BaseModel):
    """A runbook entry for a specific service and symptom."""
    service_name: str = Field(..., description="Service name")
    symptom: str = Field(..., description="Symptom identifier (e.g., 'high_latency')")
    title: str = Field(..., description="Runbook title")
    summary: str = Field(..., description="Brief summary of the issue and remediation")
    steps: List[RunbookStep] = Field(
        default_factory=list,
        description="Remediation steps",
    )


class IncidentRecord(BaseModel):
    """A single incident record."""
    id: str = Field(..., description="Incident identifier")
    service_name: str = Field(..., description="Service name")
    started_at: datetime = Field(..., description="Incident start time")
    resolved_at: Optional[datetime] = Field(None, description="Incident resolution time")
    severity: Literal["low", "medium", "high", "critical"] = Field(
        ...,
        description="Incident severity level",
    )
    root_cause: Optional[str] = Field(None, description="Root cause analysis")
    summary: str = Field(..., description="Incident summary")


class IncidentSummary(BaseModel):
    """Summary of recent incidents for a service."""
    service_name: str = Field(..., description="Service name")
    window_days: int = Field(..., description="Time window in days")
    total_incidents: int = Field(..., description="Total incidents in window")
    critical_count: int = Field(..., description="Number of critical incidents")
    high_count: int = Field(..., description="Number of high severity incidents")
    recent_incidents: List[IncidentRecord] = Field(
        default_factory=list,
        description="Recent incident records (max 5)",
    )


# ========================================
# Mock Data Templates
# ========================================

# Runbook templates: (service_name, symptom) -> runbook data
RUNBOOK_TEMPLATES: Dict[str, Dict[str, Any]] = {
    # API Gateway runbooks
    ("api-gateway", "high_latency"): {
        "title": "API Gateway High Latency Remediation",
        "summary": "High latency in API gateway often caused by downstream service degradation or rate limiting. Check downstream services and adjust connection pools.",
        "steps": [
            {"order": 1, "action": "Check downstream service health metrics", "notes": "Focus on database and cache response times"},
            {"order": 2, "action": "Review connection pool settings", "notes": "Increase pool size if utilization > 80%"},
            {"order": 3, "action": "Enable circuit breakers for slow downstream services", "notes": "Use timeout = 2x p99 latency"},
            {"order": 4, "action": "Scale horizontally if CPU > 70%", "notes": "Add 2-3 replicas gradually"},
        ],
    },
    ("api-gateway", "high_error_rate"): {
        "title": "API Gateway High Error Rate Investigation",
        "summary": "Elevated error rates typically indicate downstream service failures, rate limiting, or request validation issues.",
        "steps": [
            {"order": 1, "action": "Check error logs for 5xx vs 4xx breakdown", "notes": "5xx = downstream, 4xx = client/validation"},
            {"order": 2, "action": "Verify downstream service availability", "notes": "Check health endpoints and response codes"},
            {"order": 3, "action": "Review rate limiting configuration", "notes": "Check if legitimate traffic is being throttled"},
            {"order": 4, "action": "Enable graceful degradation for non-critical features", "notes": "Return cached or default responses"},
        ],
    },
    ("api-gateway", "high_cpu"): {
        "title": "API Gateway High CPU Usage",
        "summary": "High CPU usage in API gateway can be caused by traffic spikes, inefficient request processing, or insufficient horizontal scaling.",
        "steps": [
            {"order": 1, "action": "Check QPS against baseline", "notes": "Compare with last 7-day average"},
            {"order": 2, "action": "Review CPU profiler traces", "notes": "Look for hot code paths"},
            {"order": 3, "action": "Add horizontal replicas", "notes": "Target CPU < 70% after scaling"},
            {"order": 4, "action": "Enable request caching for read-heavy endpoints", "notes": "Cache TTL = 60-300s depending on data freshness"},
        ],
    },
    
    # Search Service runbooks
    ("search-service", "high_latency"): {
        "title": "Search Service High Latency Troubleshooting",
        "summary": "Search latency spikes usually caused by index bloat, cache misses, or query complexity. Check vector DB performance and cache hit rates.",
        "steps": [
            {"order": 1, "action": "Check vector DB query latency metrics", "notes": "Target p95 < 100ms"},
            {"order": 2, "action": "Review cache hit rate", "notes": "Should be > 60% for production traffic"},
            {"order": 3, "action": "Analyze slow queries in last 15 minutes", "notes": "Identify queries with > 500ms latency"},
            {"order": 4, "action": "Consider index optimization or replication", "notes": "Add read replicas if query load > 1000 QPS"},
        ],
    },
    ("search-service", "high_error_rate"): {
        "title": "Search Service Error Rate Investigation",
        "summary": "Search errors often stem from vector DB connection issues, malformed queries, or index corruption.",
        "steps": [
            {"order": 1, "action": "Check vector DB connection pool health", "notes": "Look for connection timeouts"},
            {"order": 2, "action": "Review query validation errors", "notes": "Check for malformed embedding vectors"},
            {"order": 3, "action": "Verify index integrity", "notes": "Run index health check command"},
            {"order": 4, "action": "Enable fallback to BM25 if vector search fails", "notes": "Graceful degradation strategy"},
        ],
    },
    
    # Payment Service runbooks
    ("payment-service", "high_error_rate"): {
        "title": "Payment Service Error Rate Spike",
        "summary": "Payment errors are critical. Check external payment gateway health, network connectivity, and retry mechanisms.",
        "steps": [
            {"order": 1, "action": "Check payment gateway API status page", "notes": "Verify external service availability"},
            {"order": 2, "action": "Review 5xx vs 4xx error breakdown", "notes": "5xx = gateway issues, 4xx = validation"},
            {"order": 3, "action": "Verify retry logic and exponential backoff", "notes": "Max retries should be 3 with jitter"},
            {"order": 4, "action": "Enable circuit breaker if gateway is down", "notes": "Return cached payment methods"},
            {"order": 5, "action": "Page on-call if error rate > 5% for > 5 minutes", "notes": "Critical service - immediate escalation"},
        ],
    },
    ("payment-service", "high_cpu"): {
        "title": "Payment Service CPU Saturation",
        "summary": "CPU spikes in payment service can indicate fraud detection overhead or transaction processing bottlenecks.",
        "steps": [
            {"order": 1, "action": "Check fraud detection service CPU", "notes": "ML models can be CPU-intensive"},
            {"order": 2, "action": "Review transaction processing queue depth", "notes": "Target queue depth < 100"},
            {"order": 3, "action": "Scale horizontally", "notes": "Add 2 replicas immediately"},
            {"order": 4, "action": "Consider offloading fraud detection to dedicated service", "notes": "Long-term optimization"},
        ],
    },
    
    # User Service runbooks
    ("user-service", "high_memory"): {
        "title": "User Service Memory Pressure",
        "summary": "Memory issues in user service often caused by session caching, connection leaks, or unbounded in-memory data structures.",
        "steps": [
            {"order": 1, "action": "Check active session count", "notes": "Should match active user count"},
            {"order": 2, "action": "Review memory profiler snapshots", "notes": "Look for memory leaks in heap"},
            {"order": 3, "action": "Verify cache eviction policies", "notes": "LRU cache should evict entries after TTL"},
            {"order": 4, "action": "Restart service if memory > 90%", "notes": "Temporary fix while investigating"},
        ],
    },
    
    # Auth Service runbooks
    ("auth-service", "high_latency"): {
        "title": "Auth Service Latency Issues",
        "summary": "Auth latency impacts all services. Check token validation, session lookup, and database connection pool.",
        "steps": [
            {"order": 1, "action": "Check session store (Redis) latency", "notes": "Target p95 < 10ms"},
            {"order": 2, "action": "Review token validation logic", "notes": "JWT validation should be < 5ms"},
            {"order": 3, "action": "Verify database connection pool is not exhausted", "notes": "Max connections should be > 50"},
            {"order": 4, "action": "Enable token caching if not already enabled", "notes": "Cache validated tokens for 60s"},
        ],
    },
    
    # Generic fallback
    ("generic-service", "high_latency"): {
        "title": "Generic Service High Latency",
        "summary": "High latency can be caused by various factors. Follow general troubleshooting steps.",
        "steps": [
            {"order": 1, "action": "Check service health endpoint", "notes": "Verify service is responding"},
            {"order": 2, "action": "Review recent deployments", "notes": "Check if latency spike correlates with deployment"},
            {"order": 3, "action": "Analyze database query performance", "notes": "Look for slow queries"},
            {"order": 4, "action": "Scale horizontally if resource-constrained", "notes": "Add 1-2 replicas"},
        ],
    },
    ("generic-service", "high_error_rate"): {
        "title": "Generic Service High Error Rate",
        "summary": "Elevated error rates require immediate investigation. Check logs and downstream dependencies.",
        "steps": [
            {"order": 1, "action": "Check recent error logs", "notes": "Look for patterns in error messages"},
            {"order": 2, "action": "Verify downstream service health", "notes": "Check dependencies"},
            {"order": 3, "action": "Review recent code changes", "notes": "Rollback if issue started after deployment"},
            {"order": 4, "action": "Enable circuit breakers for failing dependencies", "notes": "Prevent cascading failures"},
        ],
    },
    ("generic-service", "high_cpu"): {
        "title": "Generic Service High CPU",
        "summary": "High CPU usage indicates performance bottleneck. Investigate hot code paths and scale if needed.",
        "steps": [
            {"order": 1, "action": "Check QPS and traffic patterns", "notes": "Compare with baseline"},
            {"order": 2, "action": "Review CPU profiler data", "notes": "Identify hot code paths"},
            {"order": 3, "action": "Scale horizontally", "notes": "Add 1-2 replicas"},
        ],
    },
    ("generic-service", "high_memory"): {
        "title": "Generic Service Memory Issues",
        "summary": "Memory pressure can lead to OOM kills. Check for memory leaks and optimize data structures.",
        "steps": [
            {"order": 1, "action": "Review memory usage trends", "notes": "Check for gradual increase (leak)"},
            {"order": 2, "action": "Analyze heap dumps", "notes": "Look for large objects"},
            {"order": 3, "action": "Restart service if memory > 90%", "notes": "Temporary mitigation"},
        ],
    },
    ("generic-service", "disk_near_full"): {
        "title": "Generic Service Disk Full",
        "summary": "Disk full can cause service crashes. Clean up logs and temporary files immediately.",
        "steps": [
            {"order": 1, "action": "Check disk usage by directory", "notes": "Use du -sh command"},
            {"order": 2, "action": "Rotate and compress old log files", "notes": "Keep last 7 days only"},
            {"order": 3, "action": "Clear temporary files and caches", "notes": "Safe to delete /tmp contents"},
            {"order": 4, "action": "Increase disk size or add volume", "notes": "Long-term fix"},
        ],
    },
}


# Incident templates: service_name -> list of recent incident templates
INCIDENT_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "api-gateway": [
        {
            "id": "INC-2024-001",
            "severity": "high",
            "started_at_offset_days": 2,
            "duration_hours": 1.5,
            "root_cause": "Downstream database connection pool exhaustion during traffic spike",
            "summary": "API gateway experienced elevated latency (p95 > 800ms) during peak traffic. Mitigated by increasing connection pool size.",
        },
        {
            "id": "INC-2024-012",
            "severity": "medium",
            "started_at_offset_days": 10,
            "duration_hours": 0.5,
            "root_cause": "Rate limiting misconfiguration blocking legitimate traffic",
            "summary": "Elevated 429 error rate due to overly aggressive rate limiting. Fixed by adjusting rate limit to 1000 req/min per client.",
        },
        {
            "id": "INC-2023-245",
            "severity": "critical",
            "started_at_offset_days": 45,
            "duration_hours": 3.0,
            "root_cause": "Memory leak in request middleware caused OOM crashes",
            "summary": "API gateway pods crashing every 4 hours due to memory leak. Fixed by upgrading middleware library to v2.3.1.",
        },
    ],
    "search-service": [
        {
            "id": "INC-2024-005",
            "severity": "high",
            "started_at_offset_days": 5,
            "duration_hours": 2.0,
            "root_cause": "Vector DB index corruption after unclean shutdown",
            "summary": "Search queries returning stale results. Reindexed vector DB from snapshot, restored service.",
        },
        {
            "id": "INC-2024-018",
            "severity": "medium",
            "started_at_offset_days": 15,
            "duration_hours": 1.0,
            "root_cause": "Cache invalidation bug causing cache stampede",
            "summary": "Search latency spike to p95 600ms. Fixed by implementing cache warming strategy.",
        },
    ],
    "payment-service": [
        {
            "id": "INC-2024-003",
            "severity": "critical",
            "started_at_offset_days": 3,
            "duration_hours": 0.75,
            "root_cause": "External payment gateway API outage",
            "summary": "Payment processing failed for all transactions. Enabled fallback to secondary gateway, restored service within 45 minutes.",
        },
        {
            "id": "INC-2024-022",
            "severity": "high",
            "started_at_offset_days": 18,
            "duration_hours": 1.5,
            "root_cause": "Fraud detection model causing CPU saturation",
            "summary": "Payment service CPU at 95%, causing timeouts. Offloaded fraud detection to dedicated service.",
        },
        {
            "id": "INC-2023-289",
            "severity": "medium",
            "started_at_offset_days": 60,
            "duration_hours": 0.5,
            "root_cause": "Transaction retry logic missing exponential backoff",
            "summary": "Elevated error rate during transient gateway failures. Implemented retry with exponential backoff + jitter.",
        },
    ],
    "user-service": [
        {
            "id": "INC-2024-008",
            "severity": "medium",
            "started_at_offset_days": 7,
            "duration_hours": 1.0,
            "root_cause": "Session cache memory leak",
            "summary": "User service memory usage at 92%, causing pod evictions. Fixed cache eviction policy.",
        },
    ],
    "auth-service": [
        {
            "id": "INC-2024-014",
            "severity": "high",
            "started_at_offset_days": 12,
            "duration_hours": 0.5,
            "root_cause": "Redis session store failover latency",
            "summary": "Auth latency spike to p95 450ms during Redis failover. Added Redis Sentinel for faster failover.",
        },
    ],
}


# ========================================
# Tool Functions
# ========================================

def query_logs(
    service_name: str,
    window_minutes: int = 15,
    max_samples: int = 5,
) -> LogSummary:
    """
    Query recent logs for a service (mock implementation with synthetic data).
    
    In a real system, this would query Splunk, Elasticsearch, or CloudWatch Logs.
    
    Args:
        service_name: Service name (e.g., "api-gateway")
        window_minutes: Time window to query in minutes (default: 15)
        max_samples: Maximum number of sample log entries to return (default: 5)
    
    Returns:
        LogSummary with aggregated log statistics and sample entries
    """
    # Simulate log query latency
    import time
    time.sleep(0.01)  # 10ms latency
    
    # Generate synthetic log statistics
    # Use service_name as seed for reproducibility
    seed = sum(ord(c) for c in service_name)
    rng = random.Random(seed + window_minutes)
    
    # Total lines: 100-10000 depending on service and window
    base_lines = 1000
    total_lines = base_lines + rng.randint(0, min(window_minutes * 100, 9000))
    
    # Error rate: 0.1% - 5% depending on service health
    error_rate = rng.uniform(0.001, 0.05)
    error_count = int(total_lines * error_rate)
    
    # Warn rate: 0.5% - 10%
    warn_rate = rng.uniform(0.005, 0.10)
    warn_count = int(total_lines * warn_rate)
    
    # Generate sample log entries
    sample_entries: List[LogEntry] = []
    now = datetime.utcnow()
    
    # Generate a mix of ERROR, WARN, and INFO logs
    log_templates = {
        "ERROR": [
            "Timeout connecting to downstream service: connection timeout after 5000ms",
            "Database query failed: connection pool exhausted",
            "Failed to process request: internal server error (500)",
            "Circuit breaker open for service: {service_name}-db",
            "Request validation failed: invalid request parameters",
        ],
        "WARN": [
            "High memory usage detected: 85% of heap allocated",
            "Slow query detected: query took 1250ms to complete",
            "Retry attempt 3/3 for failed request",
            "Connection pool utilization at 90%",
            "Cache miss rate elevated: 45% misses in last 5 minutes",
        ],
        "INFO": [
            "Request processed successfully in 125ms",
            "Cache hit for key: user_profile_12345",
            "Health check passed: all dependencies healthy",
            "Metrics published to monitoring system",
        ],
    }
    
    # Add ERROR samples
    for i in range(min(error_count, max_samples // 2 + 1)):
        log_msg = rng.choice(log_templates["ERROR"]).replace("{service_name}", service_name)
        sample_entries.append(LogEntry(
            timestamp=now - timedelta(minutes=rng.randint(0, window_minutes)),
            level="ERROR",
            message=log_msg,
            source=f"{service_name}.core.handler" if rng.random() > 0.5 else f"{service_name}.downstream.client",
        ))
    
    # Add WARN samples
    remaining_slots = max_samples - len(sample_entries)
    for i in range(min(warn_count, remaining_slots // 2 + 1)):
        log_msg = rng.choice(log_templates["WARN"])
        sample_entries.append(LogEntry(
            timestamp=now - timedelta(minutes=rng.randint(0, window_minutes)),
            level="WARN",
            message=log_msg,
            source=f"{service_name}.monitoring" if rng.random() > 0.5 else f"{service_name}.cache",
        ))
    
    # Fill remaining with INFO
    remaining_slots = max_samples - len(sample_entries)
    for i in range(remaining_slots):
        log_msg = rng.choice(log_templates["INFO"])
        sample_entries.append(LogEntry(
            timestamp=now - timedelta(minutes=rng.randint(0, window_minutes)),
            level="INFO",
            message=log_msg,
            source=f"{service_name}.handler",
        ))
    
    # Sort by timestamp descending (most recent first)
    sample_entries.sort(key=lambda x: x.timestamp, reverse=True)
    
    return LogSummary(
        service_name=service_name,
        window_minutes=window_minutes,
        total_lines=total_lines,
        error_count=error_count,
        warn_count=warn_count,
        sample_entries=sample_entries[:max_samples],
    )


def get_runbook(
    service_name: str,
    symptom: str,
) -> RunbookEntry:
    """
    Fetch runbook for a specific service and symptom (mock implementation).
    
    In a real system, this would query a runbook database, Confluence, or PagerDuty.
    
    Args:
        service_name: Service name (e.g., "api-gateway")
        symptom: Symptom identifier (e.g., "high_latency", "high_error_rate", "high_cpu")
    
    Returns:
        RunbookEntry with remediation steps
    """
    # Simulate runbook query latency
    import time
    time.sleep(0.005)  # 5ms latency
    
    # Try exact match first
    key = (service_name, symptom)
    if key in RUNBOOK_TEMPLATES:
        template = RUNBOOK_TEMPLATES[key]
    else:
        # Fallback to generic runbook
        generic_key = ("generic-service", symptom)
        if generic_key in RUNBOOK_TEMPLATES:
            template = RUNBOOK_TEMPLATES[generic_key]
        else:
            # Ultimate fallback
            template = {
                "title": f"Generic Troubleshooting for {symptom}",
                "summary": f"No specific runbook found for {service_name} / {symptom}. Follow general troubleshooting steps.",
                "steps": [
                    {"order": 1, "action": "Check service logs for errors", "notes": "Look for recent ERROR/WARN messages"},
                    {"order": 2, "action": "Review recent changes and deployments", "notes": "Rollback if issue correlates with deployment"},
                    {"order": 3, "action": "Check resource utilization (CPU/memory/disk)", "notes": "Scale if resources are constrained"},
                    {"order": 4, "action": "Verify downstream dependencies", "notes": "Check health of databases, caches, external APIs"},
                ],
            }
    
    # Build RunbookEntry from template
    steps = [
        RunbookStep(
            order=step["order"],
            action=step["action"],
            notes=step.get("notes"),
        )
        for step in template["steps"]
    ]
    
    return RunbookEntry(
        service_name=service_name,
        symptom=symptom,
        title=template["title"],
        summary=template["summary"],
        steps=steps,
    )


def summarize_recent_incidents(
    service_name: str,
    window_days: int = 30,
    max_items: int = 5,
) -> IncidentSummary:
    """
    Summarize recent incidents for a service (mock implementation).
    
    In a real system, this would query PagerDuty, Jira, or an internal incident management system.
    
    Args:
        service_name: Service name (e.g., "api-gateway")
        window_days: Time window in days (default: 30)
        max_items: Maximum number of incident records to return (default: 5)
    
    Returns:
        IncidentSummary with aggregated incident statistics and recent records
    """
    # Simulate incident query latency
    import time
    time.sleep(0.01)  # 10ms latency
    
    # Get incident templates for this service, or use empty list if none
    incident_templates = INCIDENT_TEMPLATES.get(service_name, [])
    
    # Filter incidents within window
    now = datetime.utcnow()
    recent_incidents: List[IncidentRecord] = []
    
    for template in incident_templates:
        offset_days = template.get("started_at_offset_days", 0)
        if offset_days > window_days:
            continue  # Outside window
        
        started_at = now - timedelta(days=offset_days)
        duration_hours = template.get("duration_hours", 1.0)
        resolved_at = started_at + timedelta(hours=duration_hours)
        
        incident = IncidentRecord(
            id=template["id"],
            service_name=service_name,
            started_at=started_at,
            resolved_at=resolved_at,
            severity=template["severity"],
            root_cause=template.get("root_cause"),
            summary=template["summary"],
        )
        recent_incidents.append(incident)
    
    # Count by severity
    critical_count = sum(1 for inc in recent_incidents if inc.severity == "critical")
    high_count = sum(1 for inc in recent_incidents if inc.severity == "high")
    
    # Sort by started_at descending (most recent first)
    recent_incidents.sort(key=lambda x: x.started_at, reverse=True)
    
    return IncidentSummary(
        service_name=service_name,
        window_days=window_days,
        total_incidents=len(recent_incidents),
        critical_count=critical_count,
        high_count=high_count,
        recent_incidents=recent_incidents[:max_items],
    )


__all__ = [
    "LogEntry",
    "LogSummary",
    "RunbookStep",
    "RunbookEntry",
    "IncidentRecord",
    "IncidentSummary",
    "query_logs",
    "get_runbook",
    "summarize_recent_incidents",
]

