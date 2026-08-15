# VAULT Backend — Deployment Checklist

## ✅ Pre-Deployment Verification

### 1. Environment Configuration
- [ ] Copy `.env.example` to `.env` (local dev) or set environment variables (production)
- [ ] Set `ALLOWED_ORIGINS` to your frontend domain(s)
- [ ] Configure `SESSION_TIMEOUT_SECONDS` (default: 300 = 5 minutes)
- [ ] Set `VAULT_PATH` to a secure location
- [ ] Configure `RATE_LIMIT_MAX_ATTEMPTS` and `RATE_LIMIT_WINDOW_SECONDS`
- [ ] Set `LOG_LEVEL` (INFO for dev, WARNING for production)

### 2. Dependencies
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Verify Python >= 3.10
- [ ] Check `python-dotenv` is installed (for .env loading)

### 3. Security Review
- [ ] Confirm `ALLOWED_ORIGINS` does NOT contain wildcards or `*`
- [ ] Verify `vault.json` has restrictive permissions (chmod 600)
- [ ] Ensure `.env` is gitignored (never commit secrets)
- [ ] Test rate limiting works (see test_hardening.py)
- [ ] Confirm logs don't contain plaintext passwords

### 4. Run Tests
```powershell
# Full test suite (40+ tests)
powershell -NoProfile -ExecutionPolicy Bypass -File run_tests.ps1

# Hardening verification (requires running server)
python test_hardening.py
```

---

## 🚀 Local Development Deployment

### Quick Start
```powershell
cd backend
powershell -NoProfile -ExecutionPolicy Bypass -File start.ps1
```

### Manual Start
```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### Verify Server
```bash
curl http://localhost:8000/api/status
# Expected: {"initialized": false}
```

### Test Rate Limiting
```powershell
python test_hardening.py
```

---

## 🏭 Production Deployment

### 1. Environment Setup
```bash
# Set environment variables (don't use .env file in production)
export ALLOWED_ORIGINS=https://vault.yourdomain.com
export SESSION_TIMEOUT_SECONDS=300
export VAULT_PATH=/var/lib/vault/vault.json
export RATE_LIMIT_MAX_ATTEMPTS=5
export RATE_LIMIT_WINDOW_SECONDS=300
export LOG_LEVEL=WARNING
```

### 2. File Permissions
```bash
# Create vault directory
mkdir -p /var/lib/vault
chown vault-user:vault-user /var/lib/vault
chmod 700 /var/lib/vault

# Set vault file permissions (after first run)
chmod 600 /var/lib/vault/vault.json
```

### 3. Reverse Proxy (Nginx Example)
```nginx
server {
    listen 443 ssl http2;
    server_name vault.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/vault.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/vault.yourdomain.com/privkey.pem;
    
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location / {
        root /var/www/vault-frontend;
        try_files $uri $uri/ /index.html;
    }
}
```

### 4. Systemd Service (Linux)
```ini
# /etc/systemd/system/vault-backend.service
[Unit]
Description=VAULT Password Manager Backend
After=network.target

[Service]
Type=simple
User=vault-user
WorkingDirectory=/opt/vault/backend
Environment="ALLOWED_ORIGINS=https://vault.yourdomain.com"
Environment="SESSION_TIMEOUT_SECONDS=300"
Environment="VAULT_PATH=/var/lib/vault/vault.json"
Environment="LOG_LEVEL=WARNING"
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable vault-backend
sudo systemctl start vault-backend
sudo systemctl status vault-backend
```

### 5. Logging
```bash
# View logs
sudo journalctl -u vault-backend -f

# Monitor failed auth attempts
sudo journalctl -u vault-backend | grep "Failed unlock\|Rate limit"
```

---

## 🔒 Security Checklist

### Pre-Production
- [ ] HTTPS enabled (via reverse proxy)
- [ ] `ALLOWED_ORIGINS` set to production domain only
- [ ] Rate limiting configured (5 attempts per 5 min)
- [ ] Session timeout appropriate for use case
- [ ] Logs reviewed (no plaintext passwords)
- [ ] File permissions restrictive (vault.json = 600)
- [ ] Reverse proxy headers configured (`X-Forwarded-For`)

### Post-Deployment
- [ ] Test CORS with browser DevTools (verify only allowed origins accepted)
- [ ] Test rate limiting (6 rapid unlock attempts → 429 on 6th)
- [ ] Test timing consistency (response times ~100-300ms due to PBKDF2)
- [ ] Verify logs don't leak sensitive data
- [ ] Test session expiry (5 minutes idle → 401)
- [ ] Test vault existence leak (missing vault → 401, wrong password → 401)

---

## 🧪 Testing Checklist

### Automated Tests
```powershell
# Run pytest suite (40+ tests)
cd backend
powershell -NoProfile -ExecutionPolicy Bypass -File run_tests.ps1
```

Expected output:
```
test_vault.py::TestCrypto::test_salt_generation_is_random PASSED
test_vault.py::TestCrypto::test_derive_key_deterministic PASSED
...
test_vault.py::TestAPIEndpoints::test_post_lock_destroys_session PASSED
========== 40+ passed in X.XXs ==========
```

### Hardening Verification (Requires Running Server)
```powershell
python test_hardening.py
```

Expected output:
```
=== Test 1: Rate Limiting ===
  Attempt 1: HTTP 401
  Attempt 2: HTTP 401
  ...
  Attempt 6: HTTP 429
  ✅ Rate limiting active! Retry-After: 300s

=== Test 2: CORS Allowlist ===
  Allowed origin (localhost:8000): http://localhost:8000
  ✅ CORS configured

=== Test 3: Timing Consistency ===
  Average response time: 0.150s
  Variance (max-min): 0.025s
  ✅ PBKDF2 computation dominates timing
  ✅ Consistent timing across attempts

=== Test 4: Vault Existence Leak Prevention ===
  HTTP Status: 401
  Error Message: Incorrect master password.
  ✅ Generic 401 returned (no info leak)
```

---

## 📊 Monitoring

### Key Metrics to Track
1. **Failed unlock attempts per IP** (detect brute-force)
2. **Rate limit violations** (429 responses)
3. **Session creation rate** (detect credential stuffing)
4. **Average response time for /unlock** (should be ~100-300ms)

### Log Queries
```bash
# Count failed unlock attempts
grep "Failed unlock attempt" /var/log/vault.log | wc -l

# Show rate-limited IPs
grep "Rate limit exceeded" /var/log/vault.log | awk '{print $NF}' | sort | uniq -c

# Monitor response times (if using structured logging)
grep "Successful unlock" /var/log/vault.log
```

### Alerts to Configure
- More than 10 failed unlocks from single IP in 1 hour
- Rate limit exceeded more than 5 times per hour
- Unusual spike in 401 responses

---

## 🆘 Troubleshooting

### Issue: CORS errors in browser
**Symptom:** Frontend shows "CORS policy blocked" error

**Solution:**
1. Check `.env` has correct `ALLOWED_ORIGINS`:
   ```bash
   ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
   ```
2. Verify server logs show: `ALLOWED_ORIGINS: ['http://localhost:8000', ...]`
3. Restart server after changing `.env`

### Issue: Rate limiting not working
**Symptom:** Can make unlimited unlock attempts

**Solution:**
1. Check `.env` has:
   ```bash
   RATE_LIMIT_MAX_ATTEMPTS=5
   RATE_LIMIT_WINDOW_SECONDS=300
   ```
2. Verify `X-Forwarded-For` header is set (if behind proxy)
3. Run `test_hardening.py` to verify

### Issue: Logs show plaintext passwords
**Symptom:** Master password appears in logs

**Solution:**
1. **This should NEVER happen** — immediately review code
2. Check `main.py` logger calls don't include `body.master_password`
3. Rotate all passwords in the vault (security breach)

### Issue: Session expires too quickly
**Symptom:** Users logged out before 5 minutes

**Solution:**
1. Check `SESSION_TIMEOUT_SECONDS` in `.env` (default: 300)
2. Verify frontend sends `/api/activity` heartbeat on user interaction
3. Check server logs for session expiry warnings

---

## 📚 Additional Resources

- `SECURITY.md` — Comprehensive security documentation
- `HARDENING_SUMMARY.md` — Implementation details for all 5 hardening requirements
- `.env.example` — Configuration template with inline docs
- `test_vault.py` — Full test suite (pytest)
- `test_hardening.py` — Quick hardening verification

---

## ✅ Sign-Off

Before deploying to production, confirm:
- [ ] All tests pass (`run_tests.ps1`)
- [ ] Hardening tests pass (`test_hardening.py`)
- [ ] Environment variables set correctly
- [ ] HTTPS enabled via reverse proxy
- [ ] File permissions secured (vault.json = 600)
- [ ] Logs reviewed (no sensitive data)
- [ ] CORS allowlist contains only production domains
- [ ] Rate limiting active and tested
- [ ] Monitoring/alerting configured

**Deployed by:** _________________  
**Date:** _________________  
**Environment:** [ ] Development  [ ] Staging  [ ] Production
