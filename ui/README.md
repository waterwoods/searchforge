# Mini Dashboard Frontend

Read-only dashboard for Lab experiment metrics.

## Features

- Single button to fetch latest report
- Displays 3 key metrics: ΔP95%, ΔQPS%, Err%
- No polling, manual refresh only
- Graceful error handling (no white screen)
- Type-safe API adapters

## Quick Start

```bash
# Install dependencies
npm install

# Run dev server (with proxy to backend)
npm run dev

# Build for production
npm run build
```

## Environment

Create `.env` file:

```bash
VITE_API_BASE=http://localhost:8011
```

## Architecture

- **Pages**: `MiniDashboard.tsx` - Main UI
- **Adapters**: Type-safe API layer with error handling
  - `types.generated.ts` - Generated from backend
  - `apiAdapters.ts` - Safe defaults and converters
- **Utils**: `toStringSafe()` prevents React object rendering errors

## API Contract

`GET /ops/lab/report?mini=1` returns:

```json
{
  "ok": boolean,
  "delta_p95_pct": number,
  "delta_qps_pct": number,
  "error_rate_pct": number,
  "message": string,
  "generated_at": string | null
}
```

Always returns 200, even when no report exists.


