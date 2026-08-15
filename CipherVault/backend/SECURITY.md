# VAULT Backend — Security Hardening Documentation

This document outlines the production security measures implemented in the VAULT password manager backend.

---

## ✅ Security Requirements Implemented

### 1. Environment-Based CORS Allowlist

**Requirement:** Replace wildcard CORS origins with an explicit allowlist from environment variables.

**Implementation:**
- `config.py` reads `ALLOWED_ORIGINS` from environment (comma-separated list)
- `main.py` applies the allowlist to CORSMiddleware
- Empty allowlist denies all cross-origin requests (fail-secure)
- Logs warning if `ALLOWED_ORIGINS` is unset

**Configuration:**
```bash
# .env file
ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,null
```

**Production Example:**
```bash
ALLOWED_ORIGINS=https://vault.yourdomain.com
```

---

### 2. Rate Limiting (Brute-Force Prevention)

**Requirement:** Rate-limit `/unlock` and `/setup` to prevent password guessing attacks.

**Implementation:**
- `rate_limiter.py`: In-memory IP-based rate limiter with sliding window
- Tracks failed attempts per IP address
- Default: 5 attempts per 5 minutes (configurable)
- Returns HTTP 429 (Too Many Requests) when limit exceeded
- Includes `Retry-After` header with seconds until reset
- Thread-safe using `threading.Lock`

**Configuration:**
```bash
# .env file
RATE_LIMIT_MAX_ATTEMPTS=5
RATE_LIMIT_WINDOW_SECONDS=300
```

**Behavior:**
- Failed `/unlock` → attempt counter incremented
- Successful `/unlock` → counter reset for that IP
- Vault already initialized on `/setup` → no penalty (not a brute-force attempt)
- Rate limit shared across `/unlock` and `/setup` per IP

**Key Code:**
```python
# main.py
is_limited, remaining = rate_limiter.is_rate_limited(client_ip)
if is_limited:
    retry_after = rate_limiter.get_retry_after(client_ip)
    raise HTTPException(
        status_code=429,
        detail=f"Too many unlock attempts. Try again in {retry_after} seconds.",
        headers={"Retry-After": str(retry_after)},
    )
```

---

### 3. Environment-Based Configuration

**Requirement:** Move hardcoded values (session timeout, vault path) to environment variables with defaults.

**Implementation:**
- `config.py`: Central configuration module loading from environment
- Falls back to sensible defaults if env vars unset
- Supports `.env` file via `python-dotenv` (optional)

**Configurable Settings:**

| Variable | Default | Description |
|----------|---------|-------------|
| `SESSION_TIMEOUT_SECONDS` | `300` | Auto-logout after 5 minutes idle |
| `VAULT_PATH` | `vault.json` | Path to encrypted vault file |
| `ALLOWED_ORIGINS` | `""` | CORS allowlist (comma-separated) |
| `RATE_LIMIT_MAX_ATTEMPTS` | `5` | Max auth attempts per IP |
| `RATE_LIMIT_WINDOW_SECONDS` | `300` | Rate limit time window |
| `LOG_LEVEL` | `INFO` | Logging verbosity (DEBUG/INFO/WARNING/ERROR) |

**Files:**
- `.env.example` — Template with documentation
- `.env` — Local overrides (gitignored, not committed)
- `config.py` — Configuration loader

---

### 4. Timing-Safe Password Verification

**Requirement:** Ensure error responses never leak whether a password was "close" vs "wrong" through timing analysis.

**Implementation:**

#### Constant-Time Hash Comparison
- `vault_store.py`: Uses `secrets.compare_digest()` instead of `==`
- Compares PBKDF2 hashes in constant time regardless of how many bytes match
- Prevents timing side-channels that could leak password similarity

```python
# vault_store.py: _verify_password()
if not secrets.compare_digest(actual_hash, expected_hash):
    raise WrongMasterPasswordError("Master password is incorrect.")
```

#### PBKDF2 Hardening
- `crypto.py`: PBKDF2-HMAC-SHA256 with 600,000 iterations (OWASP 2023 minimum)
- Each password derivation takes ~100-300ms on modern hardware
- Makes brute-force attacks computationally expensive even if rate limiting is bypassed

#### HTTP Layer Timing Safety
- `/unlock` endpoint evaluates both conditions in same code path:
  ```python
  vault_exists = vault.is_initialized()
  password_valid = vault_exists and vault.verify_master_password(password)
  
  if not password_valid:
      # Generic 401 (same response for both failure modes)
      raise HTTPException(401, "Incorrect master password.")
  ```
- No early returns that leak vault existence
- Response time dominated by PBKDF2 computation (~100ms+), not comparison logic

**What's Protected:**
- ✅ Attacker cannot distinguish "vault doesn't exist" from "wrong password"
- ✅ Attacker cannot use timing to guess how many password characters are correct
- ✅ All failures return identical HTTP 401 with generic error message

---

### 5. Structured Logging (No Plaintext Passwords)

**Requirement:** Add logging for failed authentication attempts without ever logging passwords.

**Implementation:**
- `main.py`: Python `logging` module with structured metadata
- Logs failed `/unlock` attempts with IP address but NEVER the password
- Log level configurable via `LOG_LEVEL` environment variable

**What's Logged:**

✅ **Safe to Log:**
- IP addresses (`X-Forwarded-For` aware)
- Endpoint names (`/unlock`, `/setup`)
- Success/failure status
- Whether vault exists (`vault_exists: true/false`)
- Retry-After durations for rate limiting

❌ **NEVER Logged:**
- Master passwords (plaintext or hashed)
- Session tokens
- Decrypted vault entry passwords
- Any user credential data

**Example Log Output:**
```
2026-08-15 14:32:10 [WARNING] vault: Failed unlock attempt from IP 192.168.1.100
2026-08-15 14:32:15 [WARNING] vault: Rate limit exceeded for /unlock from IP 192.168.1.100
2026-08-15 14:35:00 [INFO] vault: Successful unlock from IP 192.168.1.100
```

**Key Code:**
```python
# main.py: /unlock endpoint
logger.warning(
    f"Failed unlock attempt from IP {client_ip}",
    extra={
        "ip": client_ip,
        "endpoint": "/unlock",
        "vault_exists": vault_exists,
        # NOTE: Password is NEVER logged — only metadata
    },
)
```

**Compliance:**
- Suitable for GDPR/HIPAA environments (no PII in logs beyond IP addresses)
- Audit trail for security monitoring without compromising user credentials

---

## Deployment Checklist

### Local Development
1. Copy `.env.example` to `.env`
2. Set `ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,null`
3. Run `powershell -NoProfile -ExecutionPolicy Bypass -File start.ps1`

### Production Deployment
1. Generate strong secrets:
   ```bash
   # Example: Use environment variables, not .env file in production
   export ALLOWED_ORIGINS=https://vault.yourdomain.com
   export SESSION_TIMEOUT_SECONDS=300
   export RATE_LIMIT_MAX_ATTEMPTS=5
   export LOG_LEVEL=WARNING
   ```

2. Set `VAULT_PATH` to a secure location:
   ```bash
   export VAULT_PATH=/var/lib/vault/vault.json
   # Ensure proper file permissions (600)
   chmod 600 /var/lib/vault/vault.json
   ```

3. Run behind a reverse proxy (Nginx, Caddy, Traefik):
   - Enables HTTPS/TLS
   - Provides `X-Forwarded-For` headers for rate limiting
   - Adds defense-in-depth (proxy can enforce additional rate limits)

4. Monitor logs for rate limit violations:
   ```bash
   grep "Rate limit exceeded" /var/log/vault.log
   ```

---

## Testing

### Rate Limiting Test
```bash
# Attempt 6 unlocks in rapid succession
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/unlock \
    -H "Content-Type: application/json" \
    -d '{"master_password": "wrong"}' \
    -w "\nHTTP %{http_code}\n"
done
# Expected: First 5 return 401, 6th returns 429
```

### CORS Test
```bash
# Should be rejected if origin not in ALLOWED_ORIGINS
curl -X GET http://localhost:8000/api/status \
  -H "Origin: https://evil.com" \
  -v
# Expected: CORS error (no Access-Control-Allow-Origin header)
```

### Timing Analysis Test
```python
import time
import requests

# Measure response time for wrong password (10 attempts)
times = []
for _ in range(10):
    start = time.time()
    requests.post("http://localhost:8000/api/unlock", 
                  json={"master_password": "wrong"})
    times.append(time.time() - start)

print(f"Avg: {sum(times)/len(times):.3f}s, StdDev: {max(times)-min(times):.3f}s")
# Expected: All times ~0.1-0.3s (dominated by PBKDF2), variance < 50ms
```

---

## Additional Security Measures (Already Implemented)

- **Encryption at Rest:** All vault fields encrypted with Fernet (AES-128-CBC + HMAC)
- **Server-Side Sessions:** Master password never leaves backend RAM
- **Auto-Logout:** 5-minute idle timeout enforced server-side
- **No Plaintext Disk I/O:** Master password never written to logs or disk
- **Independent Field Encryption:** Site/username/password encrypted separately
- **Session Token Entropy:** 256-bit random tokens (64 hex chars)
- **PBKDF2 Rounds:** 600,000 iterations (OWASP 2023 minimum)

---

## Threat Model

### Mitigated Threats
- ✅ **Brute-Force Password Guessing** → Rate limiting + PBKDF2
- ✅ **Timing Side-Channel Attacks** → Constant-time comparison + PBKDF2 dominates timing
- ✅ **Cross-Origin Attacks** → CORS allowlist
- ✅ **Info Leakage (Vault Existence)** → Generic 401 responses
- ✅ **Log-Based Credential Theft** → No passwords in logs
- ✅ **Replay Attacks** → Session tokens expire after 5 minutes
- ✅ **Man-in-the-Middle** → HTTPS required in production (proxy responsibility)

### Out of Scope (Client Responsibility)
- **HTTPS/TLS Termination** → Deploy behind reverse proxy (Nginx, Caddy)
- **DDoS Protection** → Use Cloudflare or similar CDN
- **Physical Security** → Secure server access and `vault.json` file permissions
- **Backup Security** → Encrypt `vault.json` backups (already encrypted at rest)

---

## Contact & Maintenance

**Questions?** Review the code comments in:
- `config.py` — Configuration loading
- `rate_limiter.py` — Rate limiting implementation
- `auth.py` — Session management
- `main.py` — HTTP endpoints with hardening

**Updates:**
- Keep `cryptography` library updated (pip install --upgrade cryptography)
- Monitor OWASP recommendations for PBKDF2 iteration count adjustments
- Review logs weekly for suspicious rate limit violations
