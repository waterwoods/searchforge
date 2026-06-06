# Vitals Viewer Cloud Run Service

A simple Cloud Run service that displays real-time vitals data from GCP Pub/Sub.

## Overview

The vitals viewer service pulls the latest vitals messages from Pub/Sub subscription `vital-events-sub` and displays them in a human-readable HTML format or as JSON.

## Deployment

### Prerequisites

- GCP Project: `optimal-disk-472305-e2`
- Pub/Sub topic `vital-events` and subscription `vital-events-sub` must exist
- Application Default Credentials configured (for local testing)

### Deploy to Cloud Run

```bash
# Option 1: Use the deployment script
./scripts/deploy_vitals_viewer.sh

# Option 2: Manual deployment
gcloud config set project optimal-disk-472305-e2
gcloud run deploy vitals-viewer \
  --source services/vitals_viewer \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated
```

After deployment, Cloud Run will print a public HTTPS URL like:
```
https://vitals-viewer-xxxxx-uc.a.run.app
```

## Usage

### View in Browser

1. Open the Cloud Run service URL in any browser (desktop or mobile)
2. The page displays a table with the latest 20 vitals readings:
   - Time (formatted)
   - Heart Rate (bpm)
   - SpO2 (%)
   - Source device
3. **Refresh the page** to pull the latest data from Pub/Sub

### View as JSON

Add `?format=json` to the URL:
```
https://vitals-viewer-xxxxx-uc.a.run.app/?format=json
```

Returns:
```json
{
  "count": 20,
  "messages": [
    {
      "hr": 72.5,
      "spo2": 97.2,
      "time_ms": 1704067200000,
      "time_str": "2024-01-01 12:00:00",
      "source": "e2e-gcp"
    },
    ...
  ]
}
```

### Mobile / iPhone Access

The service is fully responsive and works on mobile devices:
- Open the Cloud Run URL in Safari or any mobile browser
- The table is optimized for mobile viewing
- Refresh to see latest data

## How It Works

1. **Request**: User visits the Cloud Run service URL
2. **Pull**: Service pulls up to 20 latest messages from Pub/Sub subscription `vital-events-sub`
3. **Parse**: Messages are parsed as JSON
4. **Sort**: Messages are sorted by `time_ms` descending (newest first)
5. **Render**: Data is displayed as an HTML table or returned as JSON
6. **Ack**: Messages are acknowledged after reading (they won't appear again)

## Architecture

```
Vitals Generator → Pub/Sub Topic (vital-events) → Subscription (vital-events-sub) → Cloud Run Service → Browser
```

## Local Testing

To test locally before deploying:

```bash
cd services/vitals_viewer
pip install -r requirements.txt
python main.py
```

Then visit `http://localhost:8080` in your browser.

## Endpoints

- `GET /` - Main page (HTML or JSON based on `?format=json` parameter)
- `GET /health` - Health check endpoint

## Notes

- This is a **demo/visualization service**, not production-hardened
- No authentication required (public access)
- Messages are acknowledged after reading (they won't appear on next pull)
- Each page refresh pulls fresh data from Pub/Sub
- The service uses Application Default Credentials (no keys needed)

## Troubleshooting

### No data showing

1. Verify messages are being published to Pub/Sub:
   ```bash
   gcloud pubsub subscriptions pull vital-events-sub --limit=5
   ```

2. Check Cloud Run logs:
   ```bash
   gcloud run services logs read vitals-viewer --region us-central1
   ```

### Service not accessible

- Ensure `--allow-unauthenticated` flag was used during deployment
- Check Cloud Run service status in GCP Console

## Related Files

- `services/vitals_viewer/main.py` - Main FastAPI application
- `services/vitals_viewer/Dockerfile` - Container image definition
- `services/vitals_viewer/requirements.txt` - Python dependencies
- `scripts/deploy_vitals_viewer.sh` - Deployment script
