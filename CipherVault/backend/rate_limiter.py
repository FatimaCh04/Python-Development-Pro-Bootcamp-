"""
rate_limiter.py — In-memory rate limiting for brute-force prevention.

Tracks failed authentication attempts per IP address with a sliding window.
When an IP exceeds MAX_ATTEMPTS within WINDOW_SECONDS, further attempts
are rejected with HTTP 429 (Too Many Requests).

Thread-safe: uses threading.Lock for concurrent request safety.
"""

import time
import threading
from typing import Dict, Tuple
from collections import deque

import config


class RateLimiter:
    """
    IP-based rate limiter with sliding window.
    
    Tracks timestamps of failed attempts per IP. When an IP makes more than
    MAX_ATTEMPTS requests within WINDOW_SECONDS, it's temporarily blocked.
    """

    def __init__(
        self,
        max_attempts: int = None,
        window_seconds: int = None,
    ) -> None:
        if max_attempts is None:
            max_attempts = config.RATE_LIMIT_MAX_ATTEMPTS
        if window_seconds is None:
            window_seconds = config.RATE_LIMIT_WINDOW_SECONDS

        self._max_attempts = max_attempts
        self._window = window_seconds
        
        # Map: IP address → deque of attempt timestamps
        self._attempts: Dict[str, deque] = {}
        self._lock = threading.Lock()

    def _purge_old_attempts(self, ip: str) -> None:
        """Remove attempts older than the sliding window (called inside lock)."""
        if ip not in self._attempts:
            return
        
        now = time.monotonic()
        cutoff = now - self._window
        
        # Remove timestamps older than cutoff
        while self._attempts[ip] and self._attempts[ip][0] < cutoff:
            self._attempts[ip].popleft()
        
        # Clean up empty deques
        if not self._attempts[ip]:
            del self._attempts[ip]

    def is_rate_limited(self, ip: str) -> Tuple[bool, int]:
        """
        Check if an IP is currently rate-limited.
        
        Returns:
            (is_limited, remaining_attempts): 
            - is_limited: True if IP has exceeded the rate limit
            - remaining_attempts: Number of attempts left (0 if limited)
        """
        with self._lock:
            self._purge_old_attempts(ip)
            
            if ip not in self._attempts:
                return False, self._max_attempts
            
            current_count = len(self._attempts[ip])
            
            if current_count >= self._max_attempts:
                return True, 0
            
            return False, self._max_attempts - current_count

    def record_attempt(self, ip: str) -> None:
        """
        Record a failed authentication attempt for an IP.
        
        Call this AFTER a failed /unlock or /setup attempt.
        """
        with self._lock:
            self._purge_old_attempts(ip)
            
            if ip not in self._attempts:
                self._attempts[ip] = deque()
            
            self._attempts[ip].append(time.monotonic())

    def reset(self, ip: str) -> None:
        """
        Clear rate limit state for an IP (e.g., after successful auth).
        
        Call this AFTER a successful /unlock or /setup.
        """
        with self._lock:
            self._attempts.pop(ip, None)

    def get_retry_after(self, ip: str) -> int:
        """
        Get the number of seconds until the rate limit resets for an IP.
        
        Returns:
            Seconds until oldest attempt expires (0 if not rate limited).
        """
        with self._lock:
            if ip not in self._attempts or not self._attempts[ip]:
                return 0
            
            oldest = self._attempts[ip][0]
            now = time.monotonic()
            retry_after = int(self._window - (now - oldest))
            
            return max(0, retry_after)


# ---------------------------------------------------------------------------
# Module-level singleton — imported by main.py
# ---------------------------------------------------------------------------
rate_limiter = RateLimiter()
