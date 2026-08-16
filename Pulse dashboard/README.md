# Pulse — Full-Stack Social Dashboard

A full-stack social media dashboard with the **Orbit glassmorphic UI** (React + Vite + Tailwind + Framer Motion) wired to a **Flask + PostgreSQL** backend. Features real-time feed, hashtag search, nested comments, like toggling with confetti burst, image uploads to AWS S3, JWT auth with silent token refresh, and a role-protected admin panel.

---

## Project Structure

```
Pulse dashboard/
├── backend/                      Flask API (source of truth — do not modify)
│   ├── app/
│   │   ├── __init__.py           Application factory
│   │   ├── extensions.py         db, jwt, bcrypt, cors, migrate
│   │   ├── models.py             User, Post, Comment, Like, Hashtag
│   │   └── routes/
│   │       ├── auth.py           POST /api/auth/signup|login|refresh, GET /api/auth/me
│   │       ├── posts.py          GET|POST /api/posts, POST /api/posts/:id/like
│   │       ├── comments.py       GET|POST /api/posts/:id/comments
│   │       └── admin.py          DELETE /api/admin/posts/:id, GET /api/admin/stats|posts
│   ├── run.py                    Dev entrypoint
│   ├── wsgi.py                   Gunicorn/Render entrypoint
│   ├── requirements.txt
│   ├── render.yaml               Render deploy config
│   └── .env.example
│
└── orbit-dashboard/              Orbit glassmorphic frontend (React + Vite)
    ├── src/
    │   ├── data/api.js           Fetch wrapper — all calls wired to real backend
    │   ├── context/AuthContext.jsx
    │   ├── pages/                Login, Signup, DashboardLayout, Feed, SearchPage, AdminPanel
    │   └── components/           PostCard, CommentSection, CreatePostModal,
    │                             LikeButton (confetti), GradientRing, BackgroundBlobs,
    │                             PostSkeleton, Sidebar, Topbar, TrendsPanel, Toast
    ├── tailwind.config.js        Orbit design tokens (coral, violet, sky, mint, amber, glass)
    ├── vite.config.js            Dev proxy: /api/* → http://localhost:5000
    ├── vercel.json               SPA rewrite for Vercel
    ├── index.html                Loads Sora + Inter from Google Fonts
    └── .env.local                Set VITE_API_URL for production only
```

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (or use the SQLite fallback — no setup required)

---

### 1 — Backend

```powershell
cd backend

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows PowerShell
# source .venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env — set DATABASE_URL and JWT_SECRET_KEY at minimum.
# Leave AWS_* blank to disable image uploads (posts still work without images).

# Initialise the database
flask --app run:app db upgrade

# Start the dev server (port 5000)
python run.py
```

Confirm it's running: `GET http://localhost:5000/api/health` → `{"status": "ok"}`

> **SQLite fallback** — the default `DATABASE_URL=sqlite:///pulse_dev.db` creates a local
> SQLite file. No PostgreSQL needed for quick testing.

---

### 2 — Frontend (orbit-dashboard)

```powershell
cd orbit-dashboard

npm install
npm run dev      # starts on http://localhost:5173
```

The Vite dev server **proxies all `/api/*` requests to `http://localhost:5000`** automatically — no CORS issues, no env var needed for local development.

> **First run note**: if `npm run dev` says `vite` is not found, use
> `.\node_modules\.bin\vite dev` directly. This happens when Node's PATH isn't
> refreshed after first install; opening a new terminal fixes it.

---

### 3 — First user = admin

The **first account** created via `/signup` is automatically assigned `role = "admin"`.
All subsequent accounts are `role = "user"`. The Admin Panel (`/dashboard/admin`) is
hidden from non-admin users in both the UI and at the API level.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection string or `sqlite:///pulse_dev.db` |
| `JWT_SECRET_KEY` | Yes | Long random string for signing JWTs |
| `JWT_ACCESS_EXPIRES` | No | Access token TTL in seconds (default 900) |
| `JWT_REFRESH_EXPIRES` | No | Refresh token TTL in seconds (default 2592000) |
| `CORS_ORIGIN` | Yes | Frontend origin, e.g. `https://your-app.vercel.app` |
| `AWS_ACCESS_KEY_ID` | No | AWS credential for S3 image uploads |
| `AWS_SECRET_ACCESS_KEY` | No | AWS credential for S3 image uploads |
| `AWS_S3_BUCKET` | No | S3 bucket name |
| `AWS_REGION` | No | AWS region (default `us-east-1`) |

### Frontend (`orbit-dashboard/.env.local`)

| Variable | Description |
|---|---|
| `VITE_API_URL` | **Leave unset for local dev** (Vite proxy handles it). Set to your Render URL for production, e.g. `https://pulse-backend.onrender.com` |

---

## API Reference

All endpoints are on the Flask backend. The frontend calls them through the Vite proxy in
dev, or via `VITE_API_URL` in production.

### Auth

| Method | Path | Auth | Body / Notes |
|---|---|---|---|
| POST | `/api/auth/signup` | — | `{ name, email, password }` → `{ access_token, refresh_token, user }` |
| POST | `/api/auth/login` | — | `{ email, password }` → `{ access_token, refresh_token, user }` |
| POST | `/api/auth/refresh` | Refresh JWT | → `{ access_token, user }` |
| GET | `/api/auth/me` | Access JWT | → `{ user }` |

### Posts

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/api/posts` | Access JWT | `?tag=reactjs&page=1&per_page=20` — tag without `#` |
| POST | `/api/posts` | Access JWT | `multipart/form-data`: `content` + optional `image` file |
| POST | `/api/posts/:id/like` | Access JWT | Toggle; returns `{ liked, likes }` |

### Comments

| Method | Path | Auth | Body |
|---|---|---|---|
| GET | `/api/posts/:id/comments` | Access JWT | Returns `{ comments }` — top-level only; replies nested inside each comment |
| POST | `/api/posts/:id/comments` | Access JWT | `{ content, parent_id? }` → `{ comment }` |

### Admin (`role = "admin"` required)

| Method | Path | Notes |
|---|---|---|
| DELETE | `/api/admin/posts/:id` | Hard-deletes post + all its comments/likes |
| GET | `/api/admin/stats` | `{ total_posts, total_users, total_likes, total_comments }` |
| GET | `/api/admin/posts` | Paginated full post list |

---

## Backend ↔ Frontend Field Mapping

Key differences between the raw backend response and what the Orbit UI consumes:

| Backend field | Frontend alias | Where normalised |
|---|---|---|
| `user.avatar_url` | `user.avatar` | `AuthContext.normaliseUser()` |
| `post.image` | `post.image` | Same — no change |
| `post.author.avatar` | `post.author.avatar` | Set in `Post.to_dict()` |
| `GET /api/posts` → `post.comments: []` | Fetched on-demand | `PostCard` calls `api.getComments(id)` on expand |
| `GET /api/admin/stats` → `total_users` | Displayed as "Total Users" | `AdminPanel` — not `active_users` |

---

## Deployment

### Backend → Render

1. Push your `backend/` directory to GitHub.
2. Go to [render.com](https://render.com) → **New → Blueprint** → point at your repo.
   Render detects `backend/render.yaml` and creates the PostgreSQL database + web service.
3. Set environment variables in the Render dashboard (see table above).
4. Open the **Shell** tab and run migrations:
   ```bash
   flask --app wsgi:app db upgrade
   ```
5. Verify: `https://<your-service>.onrender.com/api/health` → `{"status": "ok"}`

### Frontend → Vercel

1. Go to [vercel.com](https://vercel.com) → **Add New Project** → import your repo.
2. Set **Root Directory** to `orbit-dashboard`.
3. Add environment variable:
   - `VITE_API_URL` = `https://<your-backend>.onrender.com`
4. Deploy. The `vercel.json` rewrites all routes to `index.html` for React Router.
5. After deploy, update `CORS_ORIGIN` on the Render backend to your Vercel URL and redeploy.

---

## AWS S3 Setup (optional — for image uploads)

1. Create an S3 bucket in your chosen region.
2. Keep **Block all public access** enabled (backend generates presigned URLs).
3. Create an IAM user with this inline policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:PutObject", "s3:GetObject"],
    "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/posts/*"
  }]
}
```

4. Set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_BUCKET` in your backend env.

If S3 is not configured, post creation still works — `image_url` stays `null` and the
frontend renders no image.

---

## Flow Verification Checklist

Run through these after starting both servers locally:

- [ ] **Signup** — first user becomes admin; redirected to feed
- [ ] **Login** — JWT stored in `localStorage` as `pulse_tokens`
- [ ] **Token refresh** — access token expires → silent refresh → request retried
- [ ] **Create post** — text only; text + image (check S3 bucket)
- [ ] **Hashtag extraction** — `#flask` in content → tag chip shown on card
- [ ] **Like toggle** — confetti burst on first like; optimistic update reconciled with server
- [ ] **Expand comments** — click comment count → skeleton → comment list loads
- [ ] **Add comment** — appears immediately after submit
- [ ] **Nested reply** — click Reply → indented under parent
- [ ] **Hashtag search** — type `#flask` → debounced API call → filtered results
- [ ] **Admin delete** — Admin Panel → Remove button → post disappears, toast shown
- [ ] **Admin stats** — counts reflect actual DB state
- [ ] **Non-admin guard** — regular user → `/dashboard/admin` redirects to feed
- [ ] **Forced logout** — delete tokens from localStorage → next request fires `pulse:logout` → redirect to login

---

## Tech Stack

| Layer | Tech |
|---|---|
| Frontend | React 18, Vite 5, Tailwind CSS 3, Framer Motion 11, React Router v6 |
| UI design | Orbit glassmorphic theme — frosted glass cards, gradient blobs, confetti like effect |
| API client | Custom `fetch` wrapper with silent JWT refresh and `pulse:logout` event |
| Backend | Flask 3, Flask-JWT-Extended, Flask-Bcrypt, Flask-CORS |
| ORM | SQLAlchemy 3 + Flask-Migrate (Alembic) |
| Database | PostgreSQL (SQLite for local dev) |
| File storage | AWS S3 via boto3 (presigned URLs) |
| Frontend deploy | Vercel |
| Backend deploy | Render |
