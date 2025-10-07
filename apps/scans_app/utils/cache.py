# apps/scans_app/utils/cache.py
import os, json, time
from typing import Any, Optional

try:
    import redis  # optional; we already depend on it for Celery
except Exception:  # pragma: no cover
    redis = None

_redis_client = None
_memory_store: dict[str, tuple[str, Optional[float]]] = {}  # key -> (json_str, expires_at_ts)


def _pick_redis_url() -> Optional[str]:
    """
    Prefer REDIS_URL. If not set, try Celery's result backend, then broker.
    Return None if nothing suitable.
    """
    url = (
        os.getenv("REDIS_URL")
        or os.getenv("CELERY_RESULT_BACKEND")
        or os.getenv("CELERY_BROKER_URL")
    )
    if url and url.startswith("redis://"):
        return url
    return None


def get_client():
    """
    Create a singleton Redis client when possible; otherwise return None
    to indicate using the in-memory fallback.
    """
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    url = _pick_redis_url()
    if redis and url:
        _redis_client = redis.Redis.from_url(url, decode_responses=True)
    else:
        _redis_client = None
    return _redis_client


# ---------- Primitive string API ----------

def get(key: str) -> Optional[str]:
    r = get_client()
    if r:
        try:
            return r.get(key)
        except Exception:
            # fall through to memory on transient Redis errors
            pass

    # in-memory fallback with TTL
    item = _memory_store.get(key)
    if not item:
        return None
    value, expires_at = item
    if expires_at and expires_at < time.time():
        _memory_store.pop(key, None)
        return None
    return value


def set(key: str, value: str, ttl: int = 3600) -> None:
    r = get_client()
    if r:
        try:
            r.setex(key, ttl, value)
            return
        except Exception:
            # fall back to memory
            pass
    expires_at = (time.time() + ttl) if ttl else None
    _memory_store[key] = (value, expires_at)


# ---------- JSON convenience wrappers ----------

def get_json(key: str) -> Optional[Any]:
    raw = get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def set_json(key: str, value: Any, ttl: int = 3600) -> None:
    try:
        raw = json.dumps(value)
    except Exception:
        raw = str(value)
    set(key, raw, ttl=ttl)


# Optional: tiny helper to build namespaced keys
def cache_key(*parts: str) -> str:
    safe = ":".join((p or "").replace(" ", "_").lower() for p in parts if p)
    return f"vulnscanner:{safe}"
