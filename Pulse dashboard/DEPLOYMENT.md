# Deploying Pulse (step by step)

You'll deploy the backend first (so you have its live URL), then the frontend
pointing at that URL. Both platforms have a free tier that's enough for this
capstone.

---

## Part 0 — Push this project to GitHub

Both Vercel and Render deploy from a GitHub repo.

```bash
cd pulse-fullstack
git init
git add .
git commit -m "Pulse capstone: React + Flask + JWT + PostgreSQL"
```

Create a new **empty** repo on github.com (no README/gitignore — you already
have files), then:

```bash
git remote add origin https://github.com/<your-username>/pulse-capstone.git
git branch -M main
git push -u origin main
```

---

## Part 1 — Backend on Render

1. Go to render.com → sign in with GitHub → **New +** → **Blueprint**.
2. Pick your `pulse-capstone` repo. Render will detect `pulse-backend/render.yaml`
   automatically and propose:
   - A **PostgreSQL** database (`pulse-db`)
   - A **Web Service** (`pulse-backend`) with build/start commands already set
3. Click **Apply**. Render will provision the database and deploy the service.
   `DATABASE_URL` and `JWT_SECRET_KEY` are generated automatically from the
   blueprint — you don't need to type those in.
4. One env var needs your input: **CORS_ORIGIN**. For now, set it to
   `http://localhost:5173` (you'll update it to your real Vercel URL in Part 3).
5. Wait for the first deploy to finish, then open the service URL + `/api/health`
   (e.g. `https://pulse-backend-xxxx.onrender.com/api/health`) — you should see
   `{"status": "ok"}`.

> Free-tier Render services spin down after inactivity and take ~30s to wake up
> on the first request — that's normal, not a bug.

---

## Part 2 — Frontend on Vercel

1. Go to vercel.com → sign in with GitHub → **Add New** → **Project**.
2. Import the same `pulse-capstone` repo.
3. Set **Root Directory** to `pulse-dashboard`.
4. Framework preset should auto-detect as **Vite**.
5. Under **Environment Variables**, add:
   - `VITE_API_URL` = your Render backend URL from Part 1 (no trailing slash,
     e.g. `https://pulse-backend-xxxx.onrender.com`)
6. Click **Deploy**.

---

## Part 3 — Connect them

1. Copy your live Vercel URL (e.g. `https://pulse-capstone.vercel.app`).
2. Back in Render → your `pulse-backend` service → **Environment** → update
   `CORS_ORIGIN` to that Vercel URL exactly (no trailing slash).
3. Render will auto-redeploy with the new value.

---

## Part 4 — Test the live app

Open your Vercel URL and run through the full flow:
1. Sign up (use an email containing "admin" for admin access)
2. Create a post with an image
3. Like it
4. Comment, then reply to your own comment (nested)
5. Search by the hashtag you used
6. Go to the Admin Panel and delete a post

If any step fails, open your browser's dev tools → Network tab, find the
failed request, and paste the error here — most issues at this stage are a
CORS_ORIGIN mismatch or a stale VITE_API_URL.

---

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Frontend loads but API calls fail with a CORS error | `CORS_ORIGIN` on Render doesn't exactly match your Vercel URL |
| "Failed to fetch" on every request | `VITE_API_URL` in Vercel is wrong, or missing `https://` |
| 401 on every request after login | `JWT_SECRET_KEY` changed between deploys (e.g. redeployed without the blueprint) — old tokens are invalidated, just log in again |
| Images don't persist after a Render redeploy | Local disk storage (`IMAGE_STORAGE=local`) doesn't survive redeploys/restarts on Render — switch to S3 for anything beyond a demo (see `pulse-backend/README.md`) |
| First request after inactivity is slow | Normal on Render's free tier — the service was asleep |
