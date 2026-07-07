import redis
import logging
import os
from urllib.parse import urlparse
from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client = None
_redis_checked = False


def get_redis() -> redis.Redis:
    global _redis_client, _redis_checked
    if _redis_checked and _redis_client is None:
        return None
    if _redis_client is None:
        try:
            redis_host = urlparse(settings.REDIS_URL).hostname
            if redis_host in {"redis", "db"} and not os.path.exists("/.dockerenv"):
                raise RuntimeError(
                    f"Redis host '{redis_host}' is a Docker service name and is not resolvable in local Windows runs"
                )
            _redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=0.5,
                socket_timeout=0.5,
                retry_on_timeout=False,
            )
            _redis_client.ping()
            _redis_checked = True
            logger.info("Redis connected.")
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}. OTP/rate limiting will use in-memory fallback.")
            _redis_client = None
            _redis_checked = True
    return _redis_client


class OTPStore:
    """
    Stores OTPs in Redis with TTL.
    Falls back to in-memory dict if Redis is unavailable.
    """
    _memory: dict = {}

    @staticmethod
    def key(email: str) -> str:
        return f"otp:{email.lower()}"

    @staticmethod
    def set(email: str, otp: str, ttl_seconds: int = 600):
        r = get_redis()
        key = OTPStore.key(email)
        if r:
            r.setex(key, ttl_seconds, otp)
        else:
            import time
            OTPStore._memory[key] = {"otp": otp, "expires": time.time() + ttl_seconds}

    @staticmethod
    def get(email: str) -> str | None:
        r = get_redis()
        key = OTPStore.key(email)
        if r:
            return r.get(key)
        else:
            import time
            entry = OTPStore._memory.get(key)
            if entry and entry["expires"] > time.time():
                return entry["otp"]
            return None

    @staticmethod
    def delete(email: str):
        r = get_redis()
        key = OTPStore.key(email)
        if r:
            r.delete(key)
        else:
            OTPStore._memory.pop(key, None)

    @staticmethod
    def increment_attempts(email: str) -> int:
        r = get_redis()
        attempt_key = f"otp_attempts:{email.lower()}"
        if r:
            count = r.incr(attempt_key)
            r.expire(attempt_key, 900)  # 15 min window
            return count
        return 0
