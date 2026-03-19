"""
health_monitor.py - Health Monitoring Route Handler
====================================================
Handles /api/vitals/ingest and /api/vitals/latest endpoints for ESP32 health data.
"""

import json
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Optional: google.cloud.pubsub_v1 (may not be available in all deployments)
try:
    from google.cloud import pubsub_v1
    PUBSUB_AVAILABLE = True
except ImportError:
    pubsub_v1 = None
    PUBSUB_AVAILABLE = False

from services.fiqa_api.health.health_db import (
    init_health_db,
    insert_health_reading,
    get_latest_health_readings,
)

logger = logging.getLogger(__name__)

# Pub/Sub configuration (must match vitals-viewer)
PROJECT_ID = "optimal-disk-472305-e2"
TOPIC_ID = "vital-events"

# ========================================
# Router Setup
# ========================================

router = APIRouter(prefix="/api/vitals", tags=["health-monitor"])

# ========================================
# Request/Response Models
# ========================================


class HealthIngestRequest(BaseModel):
    """Request model for health data ingestion endpoint."""
    hr: float = Field(..., description="Heart rate (beats per minute)")
    spo2: float = Field(..., description="Blood oxygen saturation (percentage)")
    time_ms: Optional[int] = Field(None, description="Timestamp in milliseconds from ESP32")
    time_str: Optional[str] = Field(None, description="Timestamp string from ESP32 (YYYY-MM-DD HH:MM:SS)")
    source: Optional[str] = Field(None, description="Device identifier (default: 'esp32-default')")
    
    class Config:
        """Pydantic model configuration."""
        extra = "ignore"  # Ignore unknown fields (e.g., battery, device_id) for forward compatibility


class HealthIngestResponse(BaseModel):
    """Response model for health data ingestion endpoint."""
    ok: bool


class HealthReading(BaseModel):
    """Single health reading item."""
    id: int
    source: str
    hr: float
    spo2: float
    time_ms: Optional[int] = None
    time_str: Optional[str] = None
    created_at: str


class HealthLatestResponse(BaseModel):
    """Response model for latest health readings endpoint."""
    readings: List[HealthReading]


# ========================================
# Endpoints
# ========================================


@router.post("/ingest", response_model=HealthIngestResponse)
async def ingest_health_reading(request: HealthIngestRequest):
    """
    Ingest a health reading from ESP32 device.
    
    Stores heart rate and SpO2 data along with optional timestamps and device source.
    Also publishes to Pub/Sub topic for real-time viewing.
    """
    try:
        source = request.source or "esp32-default"
        
        # Store to SQLite (existing behavior)
        insert_health_reading(
            hr=request.hr,
            spo2=request.spo2,
            time_ms=request.time_ms,
            time_str=request.time_str,
            source=source,
        )
        
        # Publish to Pub/Sub for vitals-viewer
        try:
            if not PUBSUB_AVAILABLE:
                logger.warning("Pub/Sub not available, skipping event publish")
                return {"status": "ingested", "pubsub": "unavailable"}
            publisher = pubsub_v1.PublisherClient()
            topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
            
            # Create message payload matching viewer's expected format
            message_data = {
                "hr": request.hr,
                "spo2": request.spo2,
                "time_ms": request.time_ms,
                "time_str": request.time_str,
                "source": source,
            }
            
            # Publish message
            message_bytes = json.dumps(message_data).encode("utf-8")
            future = publisher.publish(topic_path, message_bytes)
            message_id = future.result()  # Wait for publish to complete
            
            logger.debug(f"Published vitals to Pub/Sub topic {TOPIC_ID}: message_id={message_id}")
        except Exception as pubsub_error:
            # Log but don't fail the request if Pub/Sub fails
            logger.warning(f"Failed to publish to Pub/Sub (non-fatal): {pubsub_error}")
        
        return HealthIngestResponse(ok=True)
    except Exception as e:
        logger.error(f"Failed to ingest health reading: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest health reading: {str(e)}")


@router.get("/latest", response_model=HealthLatestResponse)
async def get_latest_readings(limit: int = Query(20, ge=1, le=1000, description="Maximum number of readings to return")):
    """
    Get the latest health readings.
    
    Returns the most recent health readings ordered by creation time (newest first).
    """
    try:
        readings_data = get_latest_health_readings(limit=limit)
        readings = [HealthReading(**r) for r in readings_data]
        return HealthLatestResponse(readings=readings)
    except Exception as e:
        logger.error(f"Failed to get latest health readings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get latest health readings: {str(e)}")
