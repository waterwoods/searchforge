# Deploying the Single Home Mortgage Agent Frontend to Vercel

## Prerequisites

- A GitHub repository containing this project.
- The backend API already deployed, e.g. on GCP Cloud Run:
  - Example: `https://mortgage-agent-api-xxxx.us-west1.run.app`

## Step 1 – Connect the project to Vercel

1. Go to https://vercel.com and log in.
2. Click "New Project" and import your GitHub repo.
3. In the project settings:
   - Set the **root directory** to `ui/`.
   - Set the **framework** to "Vite" or "Other" if needed.
   - Build command: `npm run build`
   - Output directory: `dist`

## Step 2 – Configure environment variables

In Vercel Project Settings → Environment Variables:

- `VITE_API_BASE_URL` = `https://mortgage-agent-api-xxxx.us-west1.run.app`

(Replace with your actual Cloud Run URL.)

Trigger a new deployment after setting the env var.

## Step 3 – Test the deployed frontend

1. Open the Vercel URL (e.g. `https://your-project-name.vercel.app`).
2. Navigate to `/workbench/single-home-stress` if needed.
3. Use one of the demo presets:
   - "SoCal High Price, Feels Tight"
   - "Texas Starter Home, Comfortable"
   - "Extreme High Risk, Hard Block"
4. Click "Run Mortgage Agent on this plan" and verify that results load correctly.

If you see CORS errors, ensure:
- The backend `ALLOWED_ORIGINS` env var includes the Vercel domain.

## SPA routing / deep links

To support deep linking (e.g., directly accessing `/workbench/single-home-stress`), we use Vercel rewrites configured in `ui/vercel.json`. This file lives under `ui/` since `ui/` is the Vercel project root.

The configuration rewrites all routes (including `/workbench/*`) to `/`, allowing the frontend router to handle the routing client-side. This ensures that deep links work correctly and return the SPA instead of a 404 error.

