# Fake Vitals Stream Generator

A continuous fake vitals data generator for simulating ESP32 device data streams.

## Overview

The `generate_vitals_stream.py` script generates realistic vitals data (heart rate and SpO2) with smooth drift, noise, and optional spikes. It supports two output modes:

- **stdout**: Print newline-delimited JSON to stdout (for piping/redirection)
- **post**: HTTP POST each reading to the ingest endpoint

## Features

- **Realistic data generation**: Smooth baseline drift with small noise variations
- **Optional spikes**: Configurable probability for rare HR spikes (simulating events)
- **Jitter support**: Random interval jitter to simulate real-world timing variations
- **Graceful shutdown**: Handles Ctrl+C cleanly with summary statistics
- **Retry logic**: Automatic retry (max 3 attempts) for HTTP POST failures
- **Zero dependencies**: Uses only Python standard library

## Usage

### Basic Examples

```bash
# Print JSON lines to stdout for 5 seconds
python3 scripts/generate_vitals_stream.py --mode stdout --duration-sec 5

# POST to API for 60 seconds (default endpoint)
python3 scripts/generate_vitals_stream.py --mode post --duration-sec 60

# Run forever until Ctrl+C
python3 scripts/generate_vitals_stream.py --mode stdout --duration-sec 0

# Custom interval and source
python3 scripts/generate_vitals_stream.py \
  --mode stdout \
  --interval-sec 1.0 \
  --source esp32-bedroom \
  --duration-sec 30
```

### Makefile Target

```bash
# Quick test: 60 seconds, 2s interval, stdout mode
make vitals-stream
```

### Advanced Examples

```bash
# Reproducible run with seed
python3 scripts/generate_vitals_stream.py \
  --mode stdout \
  --duration-sec 10 \
  --seed 42

# High-frequency stream with more spikes
python3 scripts/generate_vitals_stream.py \
  --mode post \
  --interval-sec 0.5 \
  --spike-prob 0.05 \
  --endpoint http://localhost:8000/api/vitals/ingest

# Low jitter (more consistent timing)
python3 scripts/generate_vitals_stream.py \
  --mode stdout \
  --jitter 0.05 \
  --duration-sec 20
```

## Command-Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--interval-sec` | float | 2.0 | Base interval between readings (seconds) |
| `--duration-sec` | float | 60.0 | Total duration (0 = run forever) |
| `--source` | string | "esp32-livingroom" | Device source identifier |
| `--mode` | choice | "stdout" | Output mode: `stdout` or `post` |
| `--endpoint` | string | `http://localhost:8000/api/vitals/ingest` | HTTP endpoint for post mode |
| `--seed` | int | None | Random seed for reproducibility (optional) |
| `--jitter` | float | 0.2 | Random jitter factor (0.0-1.0) |
| `--spike-prob` | float | 0.01 | Probability of spike events (0.0-1.0) |

## Output Format

Each reading is a JSON object with the following fields:

```json
{
  "hr": 72.5,
  "spo2": 97.2,
  "time_ms": 1704067200000,
  "time_str": "2024-01-01 12:00:00",
  "source": "esp32-livingroom"
}
```

- `hr`: Heart rate in beats per minute (float, typically 60-95 bpm)
- `spo2`: Blood oxygen saturation percentage (float, typically 94-99%)
- `time_ms`: Unix timestamp in milliseconds (int)
- `time_str`: Human-readable timestamp (string, format: "YYYY-MM-DD HH:MM:SS")
- `source`: Device identifier (string)

## Data Generation Details

### Heart Rate (HR)
- Baseline: 60-95 bpm (random initial value)
- Slow drift: ±0.5 bpm per second
- Noise: Gaussian noise with σ=2.0 bpm
- Spikes: Optional 30-60% increase (configurable probability)
- Clamped: Final values constrained to 50-120 bpm

### SpO2
- Baseline: 94-99% (random initial value)
- Slow drift: ±0.02% per second
- Noise: Gaussian noise with σ=0.5%
- Clamped: Final values constrained to 90-100%

## Integration with Ingest API

The script is compatible with the `/api/vitals/ingest` endpoint:

```bash
# Ensure API is running
# Then generate and POST data
python3 scripts/generate_vitals_stream.py \
  --mode post \
  --duration-sec 300 \
  --endpoint http://localhost:8000/api/vitals/ingest
```

The endpoint expects:
- Required: `hr` (float), `spo2` (float)
- Optional: `time_ms` (int), `time_str` (str), `source` (str)
- Extra fields are ignored (forward compatibility)

## Error Handling

- **HTTP errors**: Automatic retry with exponential backoff (max 3 attempts)
- **Network errors**: Retry logic handles connection failures
- **Graceful shutdown**: Ctrl+C prints summary and exits cleanly

## Summary Output

On exit (normal or Ctrl+C), the script prints a summary to stderr:

```
============================================================
Vitals Stream Summary
============================================================
Total readings sent: 30
Mode: stdout
Duration: 60.02 seconds
Average interval: 2.01 seconds
============================================================
```

## Use Cases

1. **Development/Testing**: Generate test data without hardware
2. **Load Testing**: Simulate multiple devices sending data
3. **Dashboard Development**: Populate dashboards with realistic data
4. **Pipeline Testing**: Verify ingest endpoint behavior
5. **Data Analysis**: Generate datasets for algorithm development

## Examples

### Pipe to file
```bash
python3 scripts/generate_vitals_stream.py --mode stdout --duration-sec 60 > vitals.jsonl
```

### Pipe to jq for inspection
```bash
python3 scripts/generate_vitals_stream.py --mode stdout --duration-sec 5 | jq '.'
```

### Multiple devices simulation
```bash
# Terminal 1
python3 scripts/generate_vitals_stream.py --mode post --source esp32-livingroom

# Terminal 2
python3 scripts/generate_vitals_stream.py --mode post --source esp32-bedroom

# Terminal 3
python3 scripts/generate_vitals_stream.py --mode post --source esp32-kitchen
```

## End-to-End Verification

To verify that the POST mode works correctly with a running API, use the verification script:

### Starting the API

First, ensure the backend API is running. Common ways to start it:

```bash
# Option 1: Using docker compose (if configured)
docker compose up -d rag-api

# Option 2: Direct uvicorn (from services/fiqa_api directory)
cd services/fiqa_api
python -m uvicorn app_main:app --host 0.0.0.0 --port 8000

# Option 3: Using existing start scripts
./scripts/start_app_main.sh
```

Wait for the API to be ready (check `http://localhost:8000/healthz`).

### Running Verification

```bash
# Using Makefile (recommended)
make vitals-e2e

# Or directly
python3 scripts/verify_vitals_e2e_post.py \
  --endpoint-base http://localhost:8000 \
  --duration-sec 10 \
  --interval-sec 1
```

### Expected Output

**Success case (API running):**
```
[Step A] Getting baseline from http://localhost:8000/api/vitals/latest...
   Baseline: id=42, time_ms=1704067200000

[Step B] Running generator (POST mode, 10s, interval 1s)...
   Generator completed successfully

[Step C] Polling for new readings (source=e2e-test)...
   Found 10 new readings (min required: 5)

[Step D] Verification Result:
============================================================
✅ PASS
   New readings: 10 (required: 5)
   Newest reading: id=52, hr=72.5, spo2=97.2, source=e2e-test
============================================================
```

**Failure case (API down):**
```
[Step A] Getting baseline from http://localhost:8000/api/vitals/latest...
❌ FAIL: Cannot connect to API: URL error: Connection refused
   Make sure the API is running at http://localhost:8000
```

The verification script:
1. Gets a baseline (newest reading ID and timestamp)
2. Runs the generator in POST mode for the specified duration
3. Polls the API to count new readings matching the test source
4. Reports PASS if at least `--min-new` readings are found

## Related Files

- `scripts/generate_vitals_stream.py`: Main generator script
- `scripts/verify_vitals_e2e_post.py`: End-to-end verification script
- `experiments/health/seed_fake_health_data.py`: One-time seed script (5 records)
- `services/fiqa_api/routes/health_monitor.py`: Ingest endpoint implementation
