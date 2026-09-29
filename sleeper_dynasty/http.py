"""Tiny HTTP + disk-cache helper. Stdlib only, no external deps required."""
import json
import os
import time
import urllib.request
import urllib.error

CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "sleeper-dynasty")
USER_AGENT = "sleeper-dynasty-cli/1.0"


def _cache_path(key: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    safe = key.replace("/", "_").replace(":", "_").replace("?", "_").replace("&", "_")
    return os.path.join(CACHE_DIR, safe + ".json")


def get_json(url: str, cache_key: str | None = None, ttl_seconds: int = 0):
    """GET a URL as JSON, optionally cached on disk for ttl_seconds."""
    if cache_key and ttl_seconds > 0:
        path = _cache_path(cache_key)
        if os.path.exists(path) and time.time() - os.path.getmtime(path) < ttl_seconds:
            with open(path, "r") as f:
                return json.load(f)

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} fetching {url}: {e.reason}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to fetch {url}: {e.reason}") from e

    if cache_key and ttl_seconds > 0:
        path = _cache_path(cache_key)
        with open(path, "w") as f:
            json.dump(data, f)
    return data
