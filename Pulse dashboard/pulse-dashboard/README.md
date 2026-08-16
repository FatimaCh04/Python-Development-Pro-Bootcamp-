# Pulse — Social Dashboard (Frontend)

A fully designed, animated React frontend for a social media dashboard capstone project.
Currently wired to **mock data** (see `src/data/mockData.js` and `src/context/AuthContext.jsx`)
so you can see and click through the entire UI before the backend exists.

## Stack
- React 18 + Vite
- React Router v6
- Tailwind CSS (custom "Pulse" design tokens in `tailwind.config.js`)
- Framer Motion (page/element animations)
- Lucide React (icons)

## Run it locally

```bash
npm install
npm run dev
```

Open http://localhost:5173. Log in with **any email/password** — use an email containing
"admin" (e.g. `admin@pulse.app`) to unlock the Admin Panel.

## What's built (frontend only, mock data)
- Login / Signup pages with animated hero
- Dashboard shell: sidebar nav, top search bar, trends rail
- Feed with post cards, animated like button, image support
- Nested comments (reply-to-reply)
- Hashtag search page
- Admin panel with stats + delete post

## Where the backend plugs in
Every place that needs a real API call is marked with `// TODO(backend): ...` comments, in:
- `src/context/AuthContext.jsx` — signup/login/JWT
- `src/pages/DashboardLayout.jsx` — create post, like, comment, delete (admin)
- `src/components/CreatePostModal.jsx` — image upload → S3

See the accompanying build prompt for wiring this up to Flask + PostgreSQL + JWT + S3.
