<div align="center">

# 🔐 CipherVAULT

**A master-password-protected, Fernet-encrypted password manager —
web app, REST API, and CLI, all sharing one encrypted core.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)
![Fernet](https://img.shields.io/badge/Encryption-Fernet%20(AES--128)-C9A227)
![No plaintext](https://img.shields.io/badge/Plaintext%20on%20disk-Never-45D9C7)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

</div>

---

## What it is

You end up with dozens of accounts and one brain. VAULT trades that for
**one master password** — everything else is encrypted independently and
decrypted only for as long as you need it.

- 🔑 One master password, hashed — never stored, never recoverable by anyone but you
- 🔒 Every website / username / password encrypted **independently** with Fernet
- 🕵️ Search-and-decrypt: look up a site, get the credential back, nothing else exposed
- ⏱️ Auto-logout after 5 idle minutes — enforced by the **server**, not just the browser tab
- 🖥️ Use it as a web app, hit the API directly, or drop into the terminal CLI

---

## Table of contents

- [Architecture](#architecture)
- [Quick start](#quick-start)
- [Project structure](#project-structure)
- [API reference](#api-reference)
- [How the encryption actually works](#how-the-encryption-actually-works)
- [Security notes & limitations](#security-notes--limitations)
- [Roadmap](#roadmap)

---

## Architecture

```
┌─────────────────┐        HTTPS/JSON        ┌──────────────────┐
│  frontend/       │ ───────────────────────▶ │  backend/api.py   │
│  (HTML/CSS/JS)   │ ◀─────────────────────── │  (FastAPI)        │
└─────────────────┘                           └────────┬─────────┘
                                                          │
                                               ┌──────────▼─────────┐
                                               │ backend/vault_core.py│
                                               │  MasterAuth          │
                                               │  CryptoService        │
                                               │  VaultManager          │
                                               └──────────┬─────────┘
                                                           │
                                                  ┌────────▼────────┐
                                                  │   vault.json     │
                                                  │ (encrypted only) │
                                                  └──────────────────┘
                       ▲
                       │  same core, different entry point
              ┌────────┴────────┐
              │ backend/vault_cli.py │
              │  (terminal + pyperclip) │
              └─────────────────────┘
```

The web app and the CLI both call into the exact same `VaultManager` —
add a password from the terminal, find it in the browser, and vice versa.

---

## Quick start

### 1. Start the backend
```bash
cd backend
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```
`vault.json` is created automatically — but stays empty until you set a
master password from the app.

### 2. Serve the frontend
```bash
cd frontend
python3 -m http.server 8080
```
Open **http://localhost:8080**. Scroll to **"Unlock Vault"** — the first
password you type there *becomes* your master password. Every time after
that, it verifies against it.

> Backend running somewhere other than `127.0.0.1:8000`? Update
> `API_BASE` at the top of `frontend/js/script.js`.

### 3. (Optional) Use the CLI instead
```bash
cd backend
python3 vault_cli.py
```
Same `vault.json`, same encryption — just a terminal menu instead of a
browser.

---

## Project structure

```
vault-project/
├── frontend/
│   ├── index.html          Landing page, login gate, dashboard
│   ├── css/style.css        Design system (dark/brass "vault door" theme)
│   └── js/script.js         All API calls, animations, session handling
│
└── backend/
    ├── vault_core.py        MasterAuth · CryptoService · VaultEntry · VaultManager
    ├── api.py                FastAPI routes + server-enforced session timeout
    ├── vault_cli.py           Terminal entry point (getpass + pyperclip)
    └── requirements.txt
```

---

## API reference

| Method | Endpoint | What it does |
|---|---|---|
| `GET` | `/status` | Is a master password already configured? |
| `POST` | `/setup` | First-run only — sets the master password |
| `POST` | `/unlock` | Verifies the master password, returns a session token |
| `POST` | `/logout` | Invalidates the current session token |
| `POST` | `/activity` | Heartbeat — resets the 5-minute idle timer |
| `GET` | `/entries` | Lists saved site names (decrypted, needs a valid session) |
| `GET` | `/entries/search?q=` | Decrypts and returns full matches for a query |
| `POST` | `/entries` | Adds a new encrypted entry |
| `DELETE` | `/entries/{id}` | Removes an entry |

Every route except `/status`, `/setup`, and `/unlock` requires an
`Authorization: Bearer <token>` header from a live, non-expired session.

---

## How the encryption actually works

1. You type a master password → it's run through **PBKDF2-HMAC-SHA256**
   (390,000 iterations) and only the resulting **hash** is saved. The
   password itself is never written anywhere.
2. That same master password also derives a separate **Fernet key** (via
   its own PBKDF2 salt) — this key exists only in memory for the length
   of your session, never on disk.
3. Every entry's `site`, `username`, and `password` fields are encrypted
   **independently**. A compromised single record never exposes the rest
   of the vault.
4. Fernet's authenticated encryption means tampered ciphertext is
   **rejected**, not silently corrupted or misread.

```python
# roughly what happens on add:
key = pbkdf2(master_password, salt_key)          # never stored
fernet = Fernet(key)
entry = {
    "site": fernet.encrypt(b"github.com"),
    "username": fernet.encrypt(b"hamza_dev"),
    "password": fernet.encrypt(b"Gh#9kLp2!vQ"),
}
```

---

## Security notes & limitations

- This is a **local, single-user** vault — `vault.json` lives on one
  machine, there's no multi-user or cloud sync built in.
- Session tokens are held in server memory — restarting the API drops
  active sessions (your saved entries are untouched, they're on disk).
- CORS is wide open by default for local development. **Tighten
  `allow_origins` in `api.py` before running this anywhere but
  localhost.**
- Lose your master password and the vault is unrecoverable **by design**
  — that's the trade-off of real encryption, not a bug.

---

## Roadmap

- [ ] Edit existing entries (`PATCH /entries/{id}`)
- [ ] Encrypted vault export/import for backups
- [ ] Password strength meter in the add-entry modal
- [ ] Duplicate-entry detection per site+username

---

<div align="center">

Built with Python OOP · `cryptography.fernet` · FastAPI · vanilla JS

</div>