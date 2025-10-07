# apps/scans_app/utils/cve_providers.py
"""
Lightweight CVE provider wrappers with caching.
- OSV (preferred for OSS) — no API key required.
- NVD (optional) — needs API key if you enable it.
- CIRCL (community) — no key; rate limits apply.

All lookups are best-effort and safe-failing (return []).
"""
from __future__ import annotations
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

from .cache import get_json, set_json, cache_key

# ---- Config / toggles ----
ENABLE_OSV = True
ENABLE_NVD = bool(os.getenv("NVD_API_KEY"))  # only if you set an API key
ENABLE_CIRCL = True

CACHE_TTL_SECONDS = int(os.getenv("CVE_CACHE_TTL", "86400"))  # 24h default
HTTP_TIMEOUT = float(os.getenv("CVE_HTTP_TIMEOUT", "6.0"))

NVD_API_KEY = os.getenv("NVD_API_KEY")
OSV_URL = "https://api.osv.dev/v1/query"
NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
CIRCL_URL_TMPL = "https://cve.circl.lu/api/search/{vendor}/{product}"

UA = {"User-Agent": "vulnscanner-cve/0.1 (+https://example.com)"}


def _cached(key: str, ttl: int, fetch_fn):
    hit = get_json(key)
    if hit is not None:
        return hit
    data = fetch_fn()
    if data is not None:
        set_json(key, data, ttl=ttl)
    return data


# ---------------- OSV ----------------

def osv_lookup(product: str, version: Optional[str] = None) -> List[str]:
    """
    Query OSV by ecosystem-less package (best effort).
    If version provided, filter tighter. Returns list of CVE IDs (strings).
    """
    if not ENABLE_OSV:
        return []

    p = (product or "").strip()
    if not p:
        return []

    key = cache_key("cve", "osv", p, version or "")
    def _fetch():
        try:
            payload = {"query": p}
            if version:
                payload["version"] = version
            r = requests.post(OSV_URL, json=payload, headers=UA, timeout=HTTP_TIMEOUT)
            if r.status_code != 200:
                return []
            data = r.json() or {}
            cves: List[str] = []
            for v in data.get("vulns", []):
                ids = [a.get("id") for a in v.get("aliases", []) if isinstance(a, dict) and a.get("id")]
                # OSV also has v.get("id") itself which may be a GHSA; include CVE if present elsewhere
                # Normalize to CVE-*
                for aid in ids:
                    if isinstance(aid, str) and aid.startswith("CVE-"):
                        cves.append(aid)
                # Fallback: if no alias is CVE, but 'id' is CVE-like (rare)
                vid = v.get("id")
                if isinstance(vid, str) and vid.startswith("CVE-"):
                    cves.append(vid)
            return sorted(list(set(cves)))
        except Exception:
            return []
    return _cached(key, CACHE_TTL_SECONDS, _fetch) or []


# ---------------- NVD ----------------

def nvd_lookup(product: str, version: Optional[str] = None) -> List[str]:
    """
    Query NVD by keyword (product + version). Requires API key to be enabled.
    Returns list of CVE IDs.
    """
    if not ENABLE_NVD or not NVD_API_KEY:
        return []

    q = f"{product} {version}".strip() if version else product.strip()
    if not q:
        return []

    key = cache_key("cve", "nvd", q)
    def _fetch():
        try:
            params = {"keywordSearch": q, "resultsPerPage": 50}
            headers = {"apiKey": NVD_API_KEY, **UA}
            r = requests.get(NVD_URL, params=params, headers=headers, timeout=HTTP_TIMEOUT)
            if r.status_code != 200:
                return []
            data = r.json() or {}
            cves: List[str] = []
            for item in data.get("vulnerabilities", []):
                cve = item.get("cve", {}).get("id")
                if isinstance(cve, str):
                    cves.append(cve)
            return sorted(list(set(cves)))
        except Exception:
            return []
    return _cached(key, CACHE_TTL_SECONDS, _fetch) or []


# ---------------- CIRCL ----------------

def circl_lookup(vendor: str, product: str) -> List[str]:
    """
    CIRCL requires vendor+product; we try vendor from product heuristics (e.g., 'apache', 'nginx').
    Returns list of CVE IDs.
    """
    if not ENABLE_CIRCL:
        return []

    v = (vendor or "").strip().lower()
    p = (product or "").strip().lower()
    if not v or not p:
        return []

    key = cache_key("cve", "circl", v, p)
    def _fetch():
        try:
            url = CIRCL_URL_TMPL.format(vendor=v, product=p)
            r = requests.get(url, headers=UA, timeout=HTTP_TIMEOUT)
            if r.status_code != 200:
                return []
            data = r.json() or []
            cves = [row.get("id") for row in data if isinstance(row, dict) and isinstance(row.get("id"), str)]
            # Normalize to CVE-*
            cves = [c for c in cves if c.startswith("CVE-")]
            return sorted(list(set(cves)))
        except Exception:
            return []
    return _cached(key, CACHE_TTL_SECONDS, _fetch) or []


# ------------- Orchestrator -------------

def query_cves_for_product_version(product: str, version: Optional[str]) -> List[str]:
    """
    Call providers in order, merge, de-dup.
    """
    product = (product or "").strip()
    version = (version or None) or None
    if not product:
        return []

    out: List[str] = []
    # OSV first (good for OSS)
    out.extend(osv_lookup(product, version))
    # NVD (if enabled)
    out.extend(nvd_lookup(product, version))
    # CIRCL with vendor heuristic
    vendor = _guess_vendor(product)
    if vendor:
        out.extend(circl_lookup(vendor, product))

    # De-dup and sort
    out = sorted(set(out))
    return out


_VENDOR_MAP = {
    "nginx": "nginx",
    "apache": "apache",
    "httpd": "apache",
    "openssl": "openssl",
    "openssh": "openssh",
    "mysql": "oracle",
    "postgresql": "postgresql",
    "gunicorn": "gunicorn",
}


def _guess_vendor(product: str) -> Optional[str]:
    p = (product or "").strip().lower()
    for k, v in _VENDOR_MAP.items():
        if k in p:
            return v
    return None
