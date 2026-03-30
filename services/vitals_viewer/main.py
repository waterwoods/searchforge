#!/usr/bin/env python3
"""
vitals_viewer/main.py - Cloud Run service to display real-time vitals from Pub/Sub

Simple demo service that pulls latest vitals messages from GCP Pub/Sub
and displays them in a readable HTML format or JSON.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from google.cloud import pubsub_v1
import time

app = FastAPI(title="Vitals Viewer")

# Pub/Sub configuration
PROJECT_ID = "optimal-disk-472305-e2"
SUBSCRIPTION_ID = "vital-events-sub"

# Simple in-memory cache (TTL = 3 seconds)
_cache = {
    "messages": [],
    "cache_time": 0,
    "ttl": 3.0
}


def pull_messages(limit: int = 20) -> List[dict]:
    """
    Pull latest messages from Pub/Sub subscription.
    
    Args:
        limit: Maximum number of messages to pull
        
    Returns:
        List of parsed JSON messages
    """
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)
    
    messages = []
    
    try:
        # Pull messages with immediate return (no waiting)
        response = subscriber.pull(
            request={
                "subscription": subscription_path,
                "max_messages": limit,
            }
        )
        
        ack_ids = []
        for received_message in response.received_messages:
            try:
                # Parse JSON message
                import json
                data = json.loads(received_message.message.data.decode('utf-8'))
                messages.append(data)
                ack_ids.append(received_message.ack_id)
            except (json.JSONDecodeError, KeyError) as e:
                # Skip invalid messages but still ack them
                ack_ids.append(received_message.ack_id)
        
        # Acknowledge messages
        if ack_ids:
            subscriber.acknowledge(
                request={
                    "subscription": subscription_path,
                    "ack_ids": ack_ids,
                }
            )
    except Exception as e:
        # Log error but don't crash
        print(f"Error pulling messages: {e}")
    
    return messages


def format_display_time(msg: dict) -> str:
    """
    Format display time from message with priority:
    1) time_str if present and non-empty
    2) server_time_str if present
    3) time_ms if epoch-ms (>= 1e12): convert to UTC
    4) time_ms if small (ESP32 boot ms): show "boot_ms:<time_ms>"
    5) "N/A"
    """
    # Priority 1: time_str
    if 'time_str' in msg and msg['time_str']:
        return msg['time_str']
    
    # Priority 2: server_time_str
    if 'server_time_str' in msg and msg['server_time_str']:
        return msg['server_time_str']
    
    # Priority 3: time_ms as epoch milliseconds
    if 'time_ms' in msg and msg['time_ms'] is not None:
        time_ms = msg['time_ms']
        # Check if it's epoch milliseconds (>= 1e12 means >= year 2001)
        if time_ms >= 1e12:
            try:
                dt = datetime.utcfromtimestamp(time_ms / 1000.0)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, OSError):
                pass
        # Priority 4: Small time_ms (ESP32 boot milliseconds)
        else:
            return f"boot_ms:{time_ms}"
    
    # Priority 5: N/A
    return "N/A"


def render_html(messages: List[dict]) -> str:
    """Render messages as HTML table."""
    # Sort by time_ms descending (newest first)
    sorted_messages = sorted(
        messages,
        key=lambda x: x.get('time_ms', 0),
        reverse=True
    )
    
    last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Live Vital Monitor</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 20px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        .last-update {{
            text-align: center;
            color: #666;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{
            background-color: #4CAF50;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .hr-value {{
            font-weight: bold;
            color: #e74c3c;
        }}
        .spo2-value {{
            font-weight: bold;
            color: #3498db;
        }}
        .no-data {{
            text-align: center;
            padding: 40px;
            color: #999;
        }}
    </style>
</head>
<body>
    <h1>Live Vital Monitor</h1>
    <div class="last-update">
        Last updated: {last_update}
    </div>
"""
    
    if sorted_messages:
        html += """    <table>
        <thead>
            <tr>
                <th>Time</th>
                <th>Heart Rate (bpm)</th>
                <th>SpO2 (%)</th>
                <th>Source</th>
            </tr>
        </thead>
        <tbody>
"""
        for msg in sorted_messages:
            display_time = format_display_time(msg)
            hr = msg.get('hr', 'N/A')
            spo2 = msg.get('spo2', 'N/A')
            source = msg.get('source', 'N/A')
            
            html += f"""            <tr>
                <td>{display_time}</td>
                <td class="hr-value">{hr}</td>
                <td class="spo2-value">{spo2}</td>
                <td>{source}</td>
            </tr>
"""
        html += """        </tbody>
    </table>
"""
    else:
        html += """    <div class="no-data">
        <p>No vitals data available.</p>
        <p>Make sure messages are being published to Pub/Sub.</p>
    </div>
"""
    
    html += """    <div style="text-align: center; margin-top: 20px; color: #666;">
        <p>Refresh the page to see latest data</p>
        <p><a href="?format=json">View as JSON</a></p>
    </div>
</body>
</html>"""
    
    return html


@app.get("/", response_class=HTMLResponse)
async def root(format: Optional[str] = Query(None, description="Output format: json or html")):
    """
    Main endpoint to display vitals data.
    
    Query params:
        format: 'json' for JSON output, otherwise HTML
    """
    # Check cache (TTL = 3 seconds)
    current_time = time.time()
    if current_time - _cache["cache_time"] < _cache["ttl"]:
        messages = _cache["messages"]
    else:
        # Pull fresh messages from Pub/Sub
        messages = pull_messages(limit=20)
        # Update cache
        _cache["messages"] = messages
        _cache["cache_time"] = current_time
    
    if format == "json":
        # Sort by time_ms descending
        sorted_messages = sorted(
            messages,
            key=lambda x: x.get('time_ms', x.get('server_time_ms', 0)),
            reverse=True
        )
        # Add computed display time to each message
        for msg in sorted_messages:
            msg['computed_display_time'] = format_display_time(msg)
        return JSONResponse(content={
            "count": len(sorted_messages),
            "messages": sorted_messages
        })
    else:
        html = render_html(messages)
        return HTMLResponse(content=html)


@app.get("/json")
async def json_redirect():
    """Redirect /json to /?format=json for convenience."""
    return RedirectResponse(url="/?format=json")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
