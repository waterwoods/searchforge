# SearchForge UI

Frontend application for SearchForge platform.

## 🚀 Quick Start - Demo Page

### Option 1: Use Dev Script (Recommended)

The easiest way to start both backend and frontend:

```bash
# From repo root
./scripts/dev_local.sh
```

This script will:
- Start backend on `http://localhost:8000`
- Start frontend on `http://localhost:5173`
- Create `.env.local` automatically if needed
- Perform readiness checks
- Show you the URLs to access

### Option 2: Manual Setup

To run the demo page manually:

1. **Ensure backend is running:**
   ```bash
   # From repo root
   python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Copy environment file:**
   ```bash
   cd ui
   cp .env.example .env.local
   ```

3. **Edit `.env.local` and set backend URL:**
   ```bash
   # For local development
   VITE_API_BASE_URL=http://localhost:8000
   
   # For production (Cloud Run)
   # VITE_API_BASE_URL=https://your-cloud-run-url
   ```

4. **Install dependencies:**
   ```bash
   npm install
   ```

5. **Start the dev server:**
   ```bash
   npm run dev
   ```

6. **Configure translation (optional):**
   ```bash
   # Backend environment variables (in .env.cloudrun or environment)
   export TRANSLATION_ENABLED=1
   export TRANSLATION_PROVIDER=argos
   export TRANSLATE_SOURCES_TO_ZH=1
   
   # Install Argos Translate language packages (first time only)
   pip install argostranslate
   python -m argostranslate.argostranslate --install-packages zh en
   ```

7. **Open the demo page:**
   - Navigate to: `http://localhost:5173/demo`
   - Or access from your network: `http://<YOUR_IP>:5173/demo`

### Demo Features

The demo page allows you to:
- Ask questions in Chinese or English
- **Toggle "Translate results to Chinese"** for Chinese-friendly experience
- View Top-K search results with scores
- See request latency and translation status
- Click source URLs to view original documents
- Show/hide original English text when translations are available

### Troubleshooting

**"Failed to fetch" error:**
1. Ensure backend is running: `curl http://localhost:8000/healthz`
2. Check `.env.local` has correct `VITE_API_BASE_URL`
3. Check browser console for CORS errors (backend should allow all origins in dev)
4. Try using the dev script: `./scripts/dev_local.sh`

## 🌐 Translation Feature

The demo supports automatic translation for Chinese queries:

1. **Enable translation in backend:**
   ```bash
   export TRANSLATION_ENABLED=1
   export TRANSLATION_PROVIDER=argos
   export TRANSLATE_SOURCES_TO_ZH=1
   ```

2. **Install translation packages:**
   ```bash
   pip install argostranslate
   python -m argostranslate.argostranslate --install-packages zh en
   ```

3. **Use in demo:**
   - Toggle "Translate results to Chinese" checkbox
   - Enter a Chinese question (e.g., "加州最低汽车保险要求是什么？")
   - Results will show Chinese translations when available
   - Click "显示原文" to view original English text

### Verification Steps

1. **Start backend and frontend:**
   ```bash
   ./scripts/dev_local.sh
   ```

2. **Test Chinese query with translation:**
   - Open `http://localhost:5173/demo`
   - Enable "Translate results to Chinese" toggle
   - Enter: "加州最低汽车保险要求是什么？"
   - Verify:
     - Response shows `translation_applied: true` badge
     - Results display Chinese text (title_zh, text_zh)
     - "显示原文" button appears for each result

3. **Test English query:**
   - Enter: "What are the minimum auto insurance requirements in California?"
   - Verify:
     - `translation_applied: false` (or no badge)
     - Results show English text

4. **Test without translation toggle:**
   - Disable translation toggle
   - Enter Chinese query
   - Verify results show English (no translation applied)

## 📖 Demo Documentation

For detailed demo scripts and talking points, see:
- `docs/DEMO_SCRIPT.md` - Demo questions and presentation guide
- `docs/supporting/PROMPT3_ACCEPTANCE_CHECKLIST.md` - Acceptance checklist
- `docs/supporting/PROMPT5_TRANSLATION_PLAN.md` - Translation feature documentation

## [vitals-lan] How to view vitals dashboard on iPad / iPhone

To access the vitals dashboard (`/vitals` page) from your iPhone or iPad on the same Wi-Fi network:

1. **Start the dev server with LAN access** on your Alienware machine:
   ```bash
   cd ui
   pnpm dev:lan
   # or
   npm run dev:lan
   ```

2. **Find your machine's IPv4 address**:
   - On Windows: Open Command Prompt and run `ipconfig`
   - Look for "IPv4 Address" under your active network adapter (usually Wi-Fi)
   - Example: `10.0.1.50` or `192.168.1.100`

3. **Access from your mobile device**:
   - Open Safari or any browser on your iPhone/iPad
   - Navigate to: `http://<YOUR_IP_ADDRESS>:5173/vitals`
   - Example: `http://10.0.1.50:5173/vitals`

**Note**: Make sure your Windows firewall allows incoming connections on port 5173, or temporarily disable the firewall for testing.

The API calls will automatically use relative paths (`/api/vitals/latest`) which are proxied through the Vite dev server to your backend, so no additional configuration is needed.

## Production Deployment (Vercel)

### Environment Variables

For production deployment on Vercel, you need to set the Cloud Run backend URL:

1. **Set environment variable in Vercel dashboard:**
   - Go to your Vercel project settings → Environment Variables
   - Add: `VITE_API_BASE_URL` = your Cloud Run URL (e.g. `https://fiqa-api-xxx.run.app`)

2. **Or use Vercel CLI:**
   ```bash
   vercel env add VITE_API_BASE_URL production
   # When prompted, paste your Cloud Run backend URL
   ```

3. **Redeploy after setting env var:**
   ```bash
   vercel --prod
   ```

### Local Development

For local development, create a `.env.local` file (see `.env.local.example`):
```bash
# .env.local
VITE_API_BASE_URL=http://localhost:8000
```

If `VITE_API_BASE_URL` is not set, it defaults to `http://localhost:8000` and uses Vite's proxy for `/api` routes.

### Verification After Deployment

After setting the environment variable and redeploying:

1. **Open the deployed frontend URL** (e.g., `https://your-app.vercel.app`)
2. **Open browser DevTools** (F12) → Console tab
3. **Verify no CORS errors** when navigating to MetricsHub page
4. **Test a query** in the search playground
5. **Check MetricsHub demo mode** - should fetch demo summary without errors

If you see CORS errors, verify:
- `VITE_API_BASE_URL` is set correctly in Vercel
- Frontend was redeployed after setting the env var
- Cloud Run CORS is configured (should allow all origins for demo)
