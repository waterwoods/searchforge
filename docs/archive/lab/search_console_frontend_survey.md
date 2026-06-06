# Search Lab Frontend Survey

**Date:** 2025-01-16  
**Purpose:** Survey existing front-end structure to plan new "Search Lab" page with Playground and KV & Streaming tabs

---

## 1. Project Structure & Routing

### Front-end Location
- **Path:** `/home/andy/searchforge/ui/`
- **Framework:** React 18.3.1 + Vite + TypeScript
- **UI Library:** Ant Design 5.28.1
- **Routing:** React Router DOM 7.9.5

### Main Layout & Sidebar
- **Layout Component:** `ui/src/components/layout/AppLayout.tsx`
  - Provides the main application shell with Header, Left Sider (sidebar), Content, and Right Sider (context panels)
  - Uses Ant Design `Layout` components
  - Conditionally renders different right panels based on route

- **Sidebar Component:** `ui/src/components/layout/AppSider.tsx`
  - Defines the left navigation menu
  - Uses Ant Design `Menu` component with nested items
  - Menu items are defined in `menuItems` array (lines 18-98)
  - Current structure:
    - Showtime (root `/`)
    - Experiment Lab (`/workbench`)
    - Code Map (`/codemap`)
    - RAG Lab (submenu with multiple pages)
    - **AI Workbench** (submenu) - This is where we'll add "Search Lab"
      - Agent Studio
      - Code Intelligence Lab
      - Retriever Lab
      - Ranker Lab
      - Index Explorer
      - **SLA Tuner Lab** (`/workbench/sla-tuner-lab`) ← Similar page to what we're building

### Routing Configuration
- **File:** `ui/src/App.tsx`
- **Pattern:** Uses React Router `Routes` and `Route` components
- All routes are nested under `<AppLayout />` (line 37)
- Workbench routes are defined starting at line 41:
  ```tsx
  <Route path="workbench" element={<WorkbenchPage />} />
  <Route path="workbench/agent-studio" element={<AgentStudioPage />} />
  <Route path="workbench/retriever-lab" element={<RetrieverLabPage />} />
  <Route path="workbench/ranker-lab" element={<RankerLabPage />} />
  <Route path="workbench/index-explorer" element={<IndexExplorerPage />} />
  <Route path="workbench/sla-tuner-lab" element={<SLATunerLabPage />} />
  ```

### SLA Tuner Lab Page
- **File:** `ui/src/pages/SLATunerLabPage.tsx`
- **Component Name:** `SLATunerLabPage`
- **Route:** `/workbench/sla-tuner-lab`
- **Structure:**
  - Three-column layout using Ant Design `Row` and `Col`
  - Left column (span=6): Experiment Controls card
  - Middle column (span=10): Real-time Performance chart
  - Right column (span=8): Auto-Tuner Recommendations timeline

---

## 2. Reusable Components

### Experiment Controls Components

#### 1. **Card** (Ant Design)
- **Path:** Imported from `antd`
- **Usage:** Used throughout SLA Tuner Lab for section containers
- **Props:** `title`, `bordered`, `children`
- **Example:** `<Card title="Experiment Controls" bordered={false}>`

#### 2. **Button** (Ant Design)
- **Path:** Imported from `antd`
- **Usage:** Start/Stop controls, form submissions
- **Props:** `type`, `icon`, `onClick`, `disabled`, `loading`
- **Example:** `<Button type="primary" icon={<PlayCircleOutlined />} onClick={handleStart}>`

#### 3. **Form Controls** (Ant Design)
- **Select:** Dropdown for configuration options
  - Props: `size`, `value`, `onChange`, `options`, `style`
- **InputNumber:** Numeric input with validation
  - Props: `size`, `value`, `onChange`, `min`, `max`, `step`, `addonAfter`
- **Space:** Layout wrapper for form elements
  - Props: `direction`, `style`

#### 4. **Status Display Components**
- **Tag:** Status badges (e.g., "RUNNING", "IDLE")
  - Props: `color` (e.g., 'processing', 'success', 'error')
- **Progress:** Progress bar for job status
  - Props: `percent`, `size`, `status`, `strokeColor`
- **Statistic:** Metric display cards
  - Props: `title`, `value`, `suffix`, `valueStyle`, `precision`

### Real-time Performance Charts

#### **RealTimePerfChart**
- **Path:** `ui/src/components/charts/RealTimePerfChart.tsx`
- **Component Name:** `RealTimePerfChart`
- **Purpose:** Displays real-time P95 latency and QPS metrics over time
- **Props:**
  - `expId?: string | null` - Experiment ID (default: 'monitor_demo')
  - `windowSec?: number` - Time window in seconds (default: 300)
  - `refreshIntervalMs?: number` - Polling interval (default: 2000)
- **Data Source:** Fetches from `/api/metrics/mini?exp_id={expId}&window_sec={windowSec}`
- **Chart Library:** Recharts (`LineChart`, `Line`, `XAxis`, `YAxis`)
- **Features:**
  - Dual Y-axis (left: P95 ms, right: QPS)
  - Auto-refresh every 2 seconds
  - Falls back to demo data if API unavailable
  - Shows loading spinner on initial load

### Metric Cards

#### **Statistic** (Ant Design)
- **Path:** Imported from `antd`
- **Usage:** Display key metrics (P95, QPS, Recall)
- **Props:**
  - `title: string` - Label (e.g., "P95 Latency")
  - `value: number` - Metric value
  - `suffix: string` - Unit (e.g., "ms", "%")
  - `valueStyle: object` - Styling (e.g., `{ color: '#cf1322' }`)
  - `precision: number` - Decimal places
- **Example Usage in SLA Tuner Lab:**
  ```tsx
  <Statistic
    title="P95 Latency"
    value={120.4}
    suffix="ms"
    valueStyle={{ color: '#cf1322' }}
  />
  <Statistic
    title="QPS"
    value={3.2}
    valueStyle={{ color: '#3f8600' }}
  />
  <Statistic
    title="Recall"
    value={82.0}
    suffix="%"
    valueStyle={{ color: '#1890ff' }}
  />
  ```

#### **KpiBar** (Custom Component)
- **Path:** `ui/src/components/kpi/KpiBar.tsx`
- **Component Name:** `KpiBar`
- **Purpose:** Global KPI bar displayed in the header
- **Props:** None (uses Zustand store `useAppStore` for metrics)
- **Displays:** P95 Latency, Recall, QPS
- **Features:** Color-coded based on thresholds (red for poor, green for good)

### Layout Components

#### **Row & Col** (Ant Design Grid)
- **Path:** Imported from `antd`
- **Usage:** Responsive grid layout
- **Props:**
  - `Row`: `gutter` (spacing between columns)
  - `Col`: `span` (column width, 1-24)

#### **Typography** (Ant Design)
- **Path:** Imported from `antd`
- **Components:** `Title`, `Text`, `Paragraph`, `Link`
- **Usage:** Consistent text styling throughout

---

## 3. API Integration

### Existing `/api/query` Usage

#### **QueryConsole Component**
- **Path:** `ui/src/components/console/QueryConsole.tsx`
- **Component Name:** `QueryConsole`
- **Current Request Payload:**
  ```typescript
  {
    question: string,      // User's query
    top_k: number,         // Number of results (from store)
    rerank: boolean        // Whether to rerank (from store)
  }
  ```
- **Endpoint:** `POST /api/query`
- **Response Handling:**
  - Updates `result` state with `ApiQueryResponse`
  - Sets `trace_id` in global store
  - Updates global metrics (P95, Recall, QPS)
  - Displays answer text and sources list

#### **Backend API Support** (from `services/fiqa_api/routes/query.py`)

The backend `QueryRequest` model supports additional fields that are **not currently used** in the frontend:

```python
class QueryRequest(BaseModel):
    question: str                    # ✅ Currently used
    top_k: int                       # ✅ Currently used
    rerank: bool                     # ✅ Currently used
    stream: bool = False             # ❌ Not used in frontend yet
    generate_answer: bool = False    # ❌ Not used in frontend yet
    use_kv_cache: bool = False      # ❌ Not used in frontend yet
    session_id: Optional[str] = None # ❌ Not used in frontend yet
    use_hybrid: bool = False
    rrf_k: Optional[int] = None
    rerank_top_k: Optional[int] = None
    collection: Optional[str] = "fiqa"
    budget_ms: Optional[int] = None
    # ... other fields
```

**Response Structure:**
```typescript
{
  ok: boolean
  trace_id: string
  question: string
  answer: string              // Empty if generate_answer=false
  latency_ms: number
  route: string
  params: {
    top_k: number
    rerank: boolean
    use_hybrid: boolean
    rrf_k?: number
  }
  sources: Array<{
    doc_id: string
    title: string
    url: string
    score: number
  }>
  metrics: {
    // Various metrics
  }
  ts: string  // ISO8601 timestamp
}
```

### Other API Endpoints Used

- **Metrics:** `GET /api/metrics/mini?exp_id={id}&window_sec={sec}` - Used by RealTimePerfChart
- **AutoTuner:** 
  - `GET /api/autotuner/status` - Status polling
  - `GET /api/autotuner/recommendations` - Recommendations list
  - `POST /api/autotuner/start` - Start tuning job
  - `POST /api/autotuner/stop` - Stop tuning job
- **Traffic Generation:** `POST /api/demo/generate-traffic?high_qps={bool}&duration={sec}`

---

## 4. Proposal for New "Search Lab" Page

### File Structure

**New Page Component:**
- **Path:** `ui/src/pages/SearchLabPage.tsx`
- **Component Name:** `SearchLabPage`
- **Route Path:** `/workbench/search-lab`

### Routing Changes

**File:** `ui/src/App.tsx`
- **Add route:** After line 50 (after SLA Tuner Lab route)
  ```tsx
  <Route path="workbench/search-lab" element={<SearchLabPage />} />
  ```

**File:** `ui/src/components/layout/AppSider.tsx`
- **Add menu item:** In the "AI Workbench" submenu (after SLA Tuner Lab, around line 95)
  ```tsx
  {
    key: '/workbench/search-lab',
    icon: <SearchOutlined />,  // or another appropriate icon
    label: <Link to="/workbench/search-lab">Search Lab</Link>,
  },
  ```

### Page Layout Sketch

#### **Overall Structure**
- Follow the same pattern as `SLATunerLabPage.tsx`
- Use Ant Design `Tabs` component for the two tabs
- Reuse the three-column layout pattern (or adapt as needed)

#### **Tab 1: Playground**
- **Purpose:** Interactive query testing with answer generation
- **Layout:**
  - Left Column: Query input form
    - Text input for question
    - Checkboxes/toggles for:
      - `generate_answer: boolean`
      - `stream: boolean` (if streaming is implemented)
      - `use_kv_cache: boolean`
    - Input for `session_id: string` (optional)
    - `top_k` slider/input
    - `rerank` toggle
    - Submit button
  - Middle Column: Results display
    - Answer text (if `generate_answer=true`)
    - Sources list
    - Latency metrics
  - Right Column: Real-time metrics
    - Reuse `RealTimePerfChart` component
    - Metric cards (P95, QPS, Recall) using `Statistic` components

#### **Tab 2: KV & Streaming**
- **Purpose:** Test KV cache behavior and streaming responses
- **Layout:**
  - Left Column: Configuration
    - Session management controls
    - KV cache toggle
    - Streaming toggle
    - Query input
  - Middle Column: Streaming output
    - Real-time answer text display (for streaming)
    - Session history/conversation view
  - Right Column: Performance metrics
    - Reuse `RealTimePerfChart` for latency/first-token metrics
    - KV cache hit rate statistics
    - Streaming metrics (tokens/sec, time to first token)

### Component Reuse Plan

| Component | Source | Reuse For |
|-----------|--------|-----------|
| `RealTimePerfChart` | `components/charts/RealTimePerfChart.tsx` | Both tabs - latency/QPS charts |
| `Statistic` | Ant Design | Both tabs - metric cards |
| `Card` | Ant Design | Both tabs - section containers |
| `Button` | Ant Design | Both tabs - form controls |
| `Input.Search` | Ant Design | Playground tab - query input |
| `Form` | Ant Design | Both tabs - form layouts |
| `Tabs` | Ant Design | Main page - tab navigation |
| `Row` / `Col` | Ant Design | Both tabs - grid layouts |

### API Integration Plan

**Playground Tab:**
- Use `POST /api/query` with extended payload:
  ```typescript
  {
    question: string
    top_k: number
    rerank: boolean
    generate_answer: boolean  // NEW
    stream: boolean           // NEW (if implemented)
    use_kv_cache: boolean     // NEW
    session_id?: string       // NEW
  }
  ```
- Handle streaming responses if `stream=true` (may require SSE or WebSocket)

**KV & Streaming Tab:**
- Same endpoint with focus on:
  - `use_kv_cache=true` for cache testing
  - `session_id` for multi-turn conversations
  - `stream=true` for streaming responses
- May need additional endpoints for:
  - Session management
  - Cache statistics
  - Streaming metrics

---

## 5. Summary

### Current Architecture
- **Layout:** Centralized `AppLayout` with context-aware right panels
- **Navigation:** `AppSider` with nested menu structure
- **Routing:** React Router with nested routes under `/workbench`
- **State Management:** Zustand store (`useAppStore`) for global state
- **Styling:** Ant Design components with dark theme

### Key Reusable Components
1. **RealTimePerfChart** - Real-time metrics visualization
2. **Statistic** - Metric display cards
3. **Card, Button, Form** - Standard UI controls
4. **Row/Col** - Grid layout system

### Implementation Checklist
- [ ] Create `SearchLabPage.tsx` component
- [ ] Add route in `App.tsx`
- [ ] Add menu item in `AppSider.tsx`
- [ ] Implement Playground tab with query form
- [ ] Implement KV & Streaming tab
- [ ] Integrate `/api/query` with new parameters
- [ ] Add streaming response handling (if needed)
- [ ] Reuse `RealTimePerfChart` for metrics
- [ ] Add metric cards using `Statistic` components
- [ ] Test with backend API

### Notes
- The backend already supports `stream`, `generate_answer`, `use_kv_cache`, and `session_id` parameters
- Frontend currently only uses `question`, `top_k`, and `rerank`
- Streaming may require additional frontend implementation (SSE or WebSocket)
- KV cache behavior testing will need session management UI
- Consider adding error handling and loading states similar to SLA Tuner Lab

---

**Next Steps:** Implementation phase (after approval of this survey)




