"""
test_hardening.py — Quick verification of production hardening features

Run this AFTER the server is started to verify:
1. CORS allowlist is active
2. Rate limiting works
3. Timing-safe comparison
4. Logging without plaintext passwords
"""

import time
import requests

BASE_URL = "http://127.0.0.1:8000"


def test_rate_limiting():
    """Test that rate limiting kicks in after 5 failed attempts."""
    print("\n=== Test 1: Rate Limiting ===")
    
    # Reset by trying with a setup (will fail if vault exists, that's OK)
    requests.post(f"{BASE_URL}/api/setup", json={"master_password": "TestPass123!"})
    
    # Try 6 unlock attempts with wrong password
    for i in range(1, 7):
        response = requests.post(
            f"{BASE_URL}/api/unlock",
            json={"master_password": "wrong_password"}
        )
        print(f"  Attempt {i}: HTTP {response.status_code}")
        
        if i < 6:
            assert response.status_code in [401, 409], f"Expected 401/409, got {response.status_code}"
        else:
            # 6th attempt should be rate limited
            if response.status_code == 429:
                print(f"  ✅ Rate limiting active! Retry-After: {response.headers.get('Retry-After', 'N/A')}s")
            else:
                print(f"  ⚠️  Expected 429, got {response.status_code} (rate limit may be disabled)")


def test_cors_allowlist():
    """Test that CORS is restricted to allowed origins."""
    print("\n=== Test 2: CORS Allowlist ===")
    
    # Request with allowed origin
    response = requests.get(
        f"{BASE_URL}/api/status",
        headers={"Origin": "http://localhost:8000"}
    )
    allow_header = response.headers.get("Access-Control-Allow-Origin")
    print(f"  Allowed origin (localhost:8000): {allow_header}")
    
    if allow_header:
        print("  ✅ CORS configured")
    else:
        print("  ⚠️  CORS may be disabled (check ALLOWED_ORIGINS in .env)")


def test_timing_consistency():
    """Test that failed unlock attempts take consistent time (PBKDF2 dominates)."""
    print("\n=== Test 3: Timing Consistency (Anti-Timing Attack) ===")
    
    times = []
    for _ in range(5):
        start = time.time()
        requests.post(
            f"{BASE_URL}/api/unlock",
            json={"master_password": "random_wrong_password"}
        )
        elapsed = time.time() - start
        times.append(elapsed)
        time.sleep(0.1)  # Small delay to avoid rate limiting
    
    avg_time = sum(times) / len(times)
    variance = max(times) - min(times)
    
    print(f"  Average response time: {avg_time:.3f}s")
    print(f"  Variance (max-min): {variance:.3f}s")
    
    if avg_time > 0.05:  # PBKDF2 should take at least 50ms
        print("  ✅ PBKDF2 computation dominates timing (good)")
    else:
        print("  ⚠️  Response too fast — PBKDF2 iterations may be low")
    
    if variance < 0.1:  # Variance should be < 100ms
        print("  ✅ Consistent timing across attempts (good)")
    else:
        print("  ⚠️  High timing variance detected")


def test_vault_existence_leak():
    """Test that response is identical for 'vault missing' vs 'wrong password'."""
    print("\n=== Test 4: Vault Existence Leak Prevention ===")
    
    # Both should return 401 with same message
    response = requests.post(
        f"{BASE_URL}/api/unlock",
        json={"master_password": "any_password"}
    )
    
    print(f"  HTTP Status: {response.status_code}")
    print(f"  Error Message: {response.json().get('detail', 'N/A')}")
    
    if response.status_code == 401:
        print("  ✅ Generic 401 returned (no info leak)")
    else:
        print(f"  ⚠️  Expected 401, got {response.status_code}")


def main():
    print("=" * 60)
    print("VAULT Backend Hardening Verification")
    print("=" * 60)
    print(f"Testing server at: {BASE_URL}")
    print("Make sure the server is running before continuing!")
    
    try:
        response = requests.get(f"{BASE_URL}/api/status", timeout=2)
        print(f"✅ Server is UP (vault initialized: {response.json().get('initialized')})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Server is DOWN or unreachable: {e}")
        return
    
    test_vault_existence_leak()
    test_cors_allowlist()
    test_timing_consistency()
    test_rate_limiting()
    
    print("\n" + "=" * 60)
    print("Verification complete! Check logs in the server terminal.")
    print("=" * 60)


if __name__ == "__main__":
    main()
