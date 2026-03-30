#!/usr/bin/env python3
"""
vitals_ingest_lite/main.py - Minimal Cloud Run service for ESP32 vitals ingestion

Single responsibility: POST /ingest → publish to Pub/Sub topic vital-events
No database, no background jobs, no heavy dependencies.
"""

import json
import logging
import time
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from google.cloud import pubsub_v1

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Pub/Sub configuration
PROJECT_ID = "optimal-disk-472305-e2"
TOPIC_ID = "vital-events"

# Initialize FastAPI app
app = FastAPI(title="Vitals Ingest Lite", version="1.0.0")

# Initialize Pub/Sub publisher (reused across requests)
_publisher = None


def get_publisher():
    """Get or create Pub/Sub publisher client."""
    global _publisher
    if _publisher is None:
        _publisher = pubsub_v1.PublisherClient()
        logger.info(f"Initialized Pub/Sub publisher for topic {TOPIC_ID}")
    return _publisher


# ========================================
# Request/Response Models
# ========================================


class VitalsIngestRequest(BaseModel):
    """Request model for vitals ingestion."""
    hr: float = Field(..., description="Heart rate (beats per minute)")
    spo2: float = Field(..., description="Blood oxygen saturation (percentage)")
    time_ms: Optional[int] = Field(None, description="Timestamp in milliseconds")
    time_str: Optional[str] = Field(None, description="Timestamp string (YYYY-MM-DD HH:MM:SS)")
    source: Optional[str] = Field(None, description="Device identifier")


class VitalsIngestResponse(BaseModel):
    """Response model for vitals ingestion."""
    ok: bool


# ========================================
# Endpoints
# ========================================


@app.post("/ingest", response_model=VitalsIngestResponse)
async def ingest_vitals(request: VitalsIngestRequest):
    """
    Ingest vitals data from ESP32 and publish to Pub/Sub.
    
    Required fields: hr, spo2
    Optional fields: time_ms, time_str, source
    """
    try:
        # Get publisher client
        publisher = get_publisher()
        topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
        
        # Always create server timestamp
        server_time_ms = int(time.time() * 1000)
        server_time_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare message payload
        message_data = {
            "hr": request.hr,
            "spo2": request.spo2,
            "server_time_ms": server_time_ms,
            "server_time_str": server_time_str,
        }
        
        # Add optional fields if present
        if request.time_ms is not None:
            message_data["time_ms"] = request.time_ms
        
        # Ensure time_str exists: use provided, or server_time_str
        if request.time_str is not None and request.time_str:
            message_data["time_str"] = request.time_str
        else:
            # If missing or empty, use server_time_str
            # Also handle case where time_ms is boot millis (< 1e12)
            if request.time_ms is not None and request.time_ms < 1e12:
                # Keep boot millis but ensure time_str is server time
                message_data["time_str"] = server_time_str
            else:
                # No time_ms or epoch ms: use server time
                message_data["time_str"] = server_time_str
        
        if request.source is not None:
            message_data["source"] = request.source
        else:
            message_data["source"] = "esp32-unknown"
        
        # Publish to Pub/Sub
        try:
            message_bytes = json.dumps(message_data).encode("utf-8")
            future = publisher.publish(topic_path, message_bytes)
            message_id = future.result(timeout=5.0)  # Wait max 5 seconds
            
            logger.info(f"Published vitals to Pub/Sub: message_id={message_id}, hr={request.hr}, spo2={request.spo2}")
        except Exception as pubsub_error:
            logger.warning(f"Pub/Sub publish failed (non-fatal): {pubsub_error}")
            # Still return success to client (non-blocking)
        
        return VitalsIngestResponse(ok=True)
        
    except Exception as e:
        logger.error(f"Failed to ingest vitals: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to ingest vitals: {str(e)}"
        )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "vitals-ingest-lite"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "vitals-ingest-lite",
        "version": "1.0.0",
        "endpoint": "/ingest",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
