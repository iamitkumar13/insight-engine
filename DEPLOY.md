# Deployment guide — Render (backend) + Vercel (frontend)

One public link for judges: **`https://<your-project>.vercel.app`**.
Vercel serves the React app and proxies `/api/*` to the Render backend, so there
is **no CORS** to configure and the frontend code needs no changes.

```
Browser ──> Vercel (React build + /api proxy) ──> Render (FastAPI + SQLite)
```

> Free-tier note: the Render backend **sleeps after ~15 min idle** and cold-starts
> in ~50 s. Hit the live link once a minute before judging to keep it warm, or
> open it ~1 min before the demo.

---

## Step 1 — Deploy the backend on Render

1. Create a free account at <https://render.com> and connect your GitHub.
2. **New → Blueprint** → pick the `insight-engine` repo. Render reads
   `render.yaml` and proposes the `insight-engine-api` web service.
3. When prompted, set the secret env var:
   - `HF_TOKEN` = your Hugging Face token (`hf_...`)
   - (`LLM_PROVIDER`, `HF_MODEL`, `PYTHON_VERSION` are already in the blueprint.)
4. Click **Apply / Create**. Wait for the build, then the deploy to go live.
5. Confirm it works: open `https://insight-engine-api-XXXX.onrender.com/health`
   → should return `{"status":"ok",...}`.
6. **Copy the backend URL** (e.g. `https://insight-engine-api-xxxx.onrender.com`).

## Step 2 — Point the frontend proxy at the backend

1. Edit `frontend/vercel.json` and replace `REPLACE_WITH_RENDER_URL` with your
   backend host **without** the `https://` scheme duplicated — keep the form:

   ```json
   "destination": "https://insight-engine-api-xxxx.onrender.com/:path*"
   ```
2. Commit & push:

   ```powershell
   git add frontend/vercel.json
   git commit -m "chore: point vercel proxy at render backend"
   git push
   ```

## Step 3 — Deploy the frontend on Vercel

1. Create a free account at <https://vercel.com> and connect GitHub.
2. **Add New → Project** → import the `insight-engine` repo.
3. Set **Root Directory** = `frontend` (click *Edit* next to root directory).
   Vercel auto-detects Vite (build `npm run build`, output `dist`).
4. Click **Deploy**. When it finishes you get
   `https://<your-project>.vercel.app` — **this is your live link.**

## Step 4 — Verify end to end

1. Open the Vercel URL.
2. Upload `backend/data/messy_sales.csv` (the sample ships in the repo).
3. Ask: *"Which regions have the highest total sales?"*
4. You should see the cleaning summary, SQL, a table, a chart, and an insight.
   (First request may be slow if the Render backend was asleep.)

## Submission checklist (deliverable #4)

- [ ] Backend `/health` returns ok on Render
- [ ] `frontend/vercel.json` destination points at the real Render URL
- [ ] Vercel root directory is `frontend`
- [ ] Live link loads and a full upload→query works
- [ ] No login required (the app is open) — note this for the judges
