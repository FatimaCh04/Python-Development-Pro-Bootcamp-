# Pulse — Full-Stack Social Media Dashboard

Capstone project: React frontend + Flask backend, JWT auth, PostgreSQL-ready,
image upload, nested comments, hashtag search, admin moderation.

## Folders
- `pulse-dashboard/` — React frontend (Vite + Tailwind + Framer Motion)
- `pulse-backend/` — Flask API (SQLAlchemy + JWT + bcrypt, S3-ready image upload)

## Quickest way to run it locally

Terminal 1 (backend):
```bash
cd pulse-backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

Terminal 2 (frontend):
```bash
cd pulse-dashboard
npm install
cp .env.example .env
npm run dev
```

Open http://localhost:5173 — sign up (use an email containing "admin" for admin access)
and the whole app — feed, likes, nested comments, hashtag search, image upload, admin
delete — runs against the real backend.

See each folder's own README for endpoint docs, PostgreSQL/S3 switch-over, and
Vercel/Render deployment steps.
