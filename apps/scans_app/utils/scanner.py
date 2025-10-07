# apps/scans_app/utils/scanner.py
"""
Legit lightweight scanner:
- TCP connect scan of a small, safe port list
- Minimal banner grab
- HTTP HEAD/GET for basic metadata + headers
- TLS certificate info (days left, SANs, issuer)
- Optional CVE suggestions via providers (best-effort, informational)

All network activity is read-only & non-intrusive.
"""
from __future__ import annotations
import socket
import ssl
import re
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse

import requests

from .cve_providers import query_cves_for_product_version

# ---------- Config ----------
TCP_TIMEOUT = 2.0
HTTP_TIMEOUT = 5.0
MAX_WORKERS = 12
HTTP_HEADERS = {"User-Agent": "vulnscanner-lite/0.1 (+https://example.com)"}

TOP_PORTS_QUICK = [80, 443, 22, 21, 25, 3306, 445]
TOP_PORTS_FULL = [
    21,22,23,25,53,80,110,135,139,143,161,389,443,445,
    3389,5900,8080,8081,8443,3306,9200,27017
]

PORT_SERVICE = {
    21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "dns",
    80: "http", 110: "pop3", 135: "msrpc", 139: "netbios-ssn",
    143: "imap", 161: "snmp", 389: "ldap", 443: "https",
    445: "smb", 3389: "rdp", 5900: "vnc", 8080: "http-alt",
    8081: "http-alt", 8443: "https-alt", 3306: "mysql",
    9200: "elasticsearch", 27017: "mongodb"
}

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)

# Basic product/version heuristics
# Examples:
#   "Server: nginx/1.23.4"      -> ("nginx", "1.23.4")
#   "Apache/2.4.57 (Ubuntu)"    -> ("Apache", "2.4.57")
#   "OpenSSH_8.9p1 Ubuntu-3"    -> ("OpenSSH", "8.9p1")
#   "gunicorn/19.9.0"           -> ("gunicorn", "19.9.0")
PRODUCT_PATTERNS = [
    re.compile(r"(nginx)[/\- ](?P<ver>\d+(\.\d+){0,3})", re.I),
    re.compile(r"(apache)[/\- ](?P<ver>\d+(\.\d+){0,3})", re.I),
    re.compile(r"(httpd)[/\- ](?P<ver>\d+(\.\d+){0,3})", re.I),
    re.compile(r"(openssh)[_/ ](?P<ver>\d+[^\s/]*)", re.I),
    re.compile(r"(openssl)[/\- ](?P<ver>\d+(\.\d+){0,3}[a-z]?)", re.I),
    re.compile(r"(gunicorn)[/\- ](?P<ver>\d+(\.\d+){0,3})", re.I),
    re.compile(r"(mysql)[/\- ](?P<ver>\d+(\.\d+){0,3})", re.I),
    re.compile(r"(postgresql)[/\- ](?P<ver>\d+(\.\d+){0,3})", re.I),
]


def _normalize_target(target: str) -> Tuple[str, str]:
    t = target.strip()
    if t.startswith(("http://", "https://")):
        p = urlparse(t)
        host = p.netloc.split("/", 1)[0]
        scheme = p.scheme
        return host, f"{scheme}://{host}"
    return t, f"http://{t}"


def _tcp_connect(host: str, port: int, timeout: float = TCP_TIMEOUT) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def _banner_grab(host: str, port: int, timeout: float = TCP_TIMEOUT) -> Optional[str]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        try:
            s.sendall(b"\r\n")
        except Exception:
            pass
        data = b""
        try:
            data = s.recv(1024)
        except Exception:
            pass
        finally:
            s.close()
        if not data:
            return None
        return data.decode(errors="ignore").strip()
    except Exception:
        return None


def _http_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HTTP_HEADERS)
    return s


def _http_basic_checks(session: requests.Session, base_url: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "status": None,
        "title": None,
        "server": None,
        "hsts": False,
        "csp": None,
        "robots": None,
        "cookie_flags": [],
        "redirect_chain": []
    }
    try:
        r = session.head(base_url, allow_redirects=True, timeout=HTTP_TIMEOUT, verify=True)
        out["status"] = r.status_code
        out["server"] = r.headers.get("Server")
        out["redirect_chain"] = [h.url for h in r.history] if r.history else []
        out["hsts"] = any(h.lower() == "strict-transport-security" for h in r.headers.keys())
        out["csp"] = r.headers.get("Content-Security-Policy")

        need_get = (out["status"] is None) or ("text/html" in (r.headers.get("Content-Type", "") or "").lower())
        if need_get:
            g = session.get(base_url, allow_redirects=True, timeout=HTTP_TIMEOUT, verify=True)
            out["status"] = g.status_code
            out["server"] = out["server"] or g.headers.get("Server")
            html = g.text or ""
            m = TITLE_RE.search(html)
            if m:
                out["title"] = re.sub(r"\s+", " ", m.group(1).strip())

            # robots.txt presence
            robots_url = base_url.rstrip("/") + "/robots.txt"
            try:
                rr = session.get(robots_url, timeout=HTTP_TIMEOUT, verify=True)
                out["robots"] = (rr.status_code == 200)
            except Exception:
                out["robots"] = None

            # Set-Cookie flags (crude)
            set_cookie_headers = g.headers.get("Set-Cookie", "")
            flags = []
            if "HttpOnly" in set_cookie_headers:
                flags.append("HttpOnly")
            if "Secure" in set_cookie_headers:
                flags.append("Secure")
            out["cookie_flags"] = flags

    except requests.RequestException:
        # try plain HTTP if HTTPS fails and scheme is https
        if base_url.startswith("https://"):
            try:
                http_url = "http://" + base_url.split("://", 1)[1]
                g = session.get(http_url, allow_redirects=True, timeout=HTTP_TIMEOUT, verify=False)
                out["status"] = g.status_code
                out["server"] = out["server"] or g.headers.get("Server")
                html = g.text or ""
                m = TITLE_RE.search(html)
                if m:
                    out["title"] = re.sub(r"\s+", " ", m.group(1).strip())
            except Exception:
                pass
    except Exception:
        pass

    return out


def _tls_cert_info(host: str, port: int = 443, timeout: float = TCP_TIMEOUT) -> Optional[Dict[str, Any]]:
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(socket.AF_INET), server_hostname=host) as s:
            s.settimeout(timeout)
            s.connect((host, port))
            cert = s.getpeercert()

        def _parse_dt(x: Optional[str]) -> Optional[datetime]:
            if not x:
                return None
            try:
                return datetime.strptime(x, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
            except Exception:
                return None

        not_before = _parse_dt(cert.get("notBefore"))
        not_after = _parse_dt(cert.get("notAfter"))
        now = datetime.now(timezone.utc)

        days_left = None
        valid = None
        if not_after:
            days_left = (not_after - now).days
            valid = (days_left is not None) and (days_left > 0)

        sans = [v for (_t, v) in cert.get("subjectAltName", ())]
        issuer = cert.get("issuer")
        subject = cert.get("subject")

        return {
            "issuer": issuer,
            "subject": subject,
            "sans": sans,
            "valid_from": cert.get("notBefore"),
            "valid_to": cert.get("notAfter"),
            "days_left": days_left,
            "valid": valid,
        }
    except Exception:
        return None


def _extract_product_version(text: Optional[str]) -> Optional[Tuple[str, Optional[str]]]:
    """
    Try several patterns to find (product, version) in banners / server headers.
    """
    if not text:
        return None
    t = text.strip()
    for pat in PRODUCT_PATTERNS:
        m = pat.search(t)
        if m:
            prod = m.group(1)
            ver = m.group("ver")
            return (prod, ver)
    # Fallback: product without version
    tokens = re.split(r"[ /()_;\-]", t)
    for tok in tokens:
        if tok and tok.isalpha() and len(tok) > 2:
            return (tok, None)
    return None


def _scan_port_worker(host: str, port: int) -> Dict[str, Any]:
    state = "open" if _tcp_connect(host, port) else "closed"
    banner = _banner_grab(host, port) if state == "open" else None
    return {
        "port": port,
        "service": PORT_SERVICE.get(port, "unknown"),
        "state": state,
        "banner": banner
    }


# ---------- Public API (used by tasks.py) ----------

def run_scan(scan_id: int, target: str, mode: str) -> Dict[str, Any]:
    """
    Return dict consumed by tasks.py:
      - open_ports: [ {port, service, state, banner} ]
      - http_info:  {status, title, server, hsts, csp, robots, cookie_flags, redirect_chain}
      - tls_info:   {issuer, subject, sans, valid_from, valid_to, days_left, valid}
      - vulnerabilities: [ {severity, name, path, description, impact, remediation, reference_links} ]
    """
    host, base_url = _normalize_target(target)
    ports = TOP_PORTS_QUICK if mode == "quick" else TOP_PORTS_FULL

    # 1) Port scan
    open_ports: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, max(1, len(ports)))) as pool:
        futures = {pool.submit(_scan_port_worker, host, p): p for p in ports}
        for fut in as_completed(futures):
            open_ports.append(fut.result())

    # 2) HTTP checks
    http_info: Dict[str, Any] = {}
    try:
        has_http = any(p["port"] == 80 and p["state"] == "open" for p in open_ports)
        has_https = any(p["port"] == 443 and p["state"] == "open" for p in open_ports)
        if has_https:
            base = base_url if base_url.startswith("https://") else "https://" + host
        elif has_http:
            base = base_url if base_url.startswith("http://") else "http://" + host
        else:
            base = None

        if base:
            with _http_session() as sess:
                http_info = _http_basic_checks(sess, base)
    except Exception:
        http_info = {}

    # 3) TLS cert info
    tls_info = _tls_cert_info(host, 443) if any(p["port"] == 443 and p["state"] == "open" for p in open_ports) else {}

    # 4) CVE suggestions (best-effort)
    # Collect product/version candidates from banners & server header
    candidates: List[Tuple[str, Optional[str]]] = []

    # From port banners
    for p in open_ports:
        if p.get("banner"):
            pv = _extract_product_version(p["banner"])
            if pv:
                candidates.append(pv)

    # From HTTP server header
    if http_info.get("server"):
        pv = _extract_product_version(http_info["server"])
        if pv:
            candidates.append(pv)

    # Deduplicate (product,version)
    seen = set()
    unique_candidates: List[Tuple[str, Optional[str]]] = []
    for prod, ver in candidates:
        k = (prod.lower(), (ver or "").lower())
        if k not in seen:
            seen.add(k)
            unique_candidates.append((prod, ver))

    # Query providers and build informational findings (only in full mode)
    vulnerabilities: List[Dict[str, Any]] = []
    if mode == "full":
        for prod, ver in unique_candidates:
            try:
                cves = query_cves_for_product_version(prod, ver)
            except Exception:
                cves = []
            for cve in cves:
                vulnerabilities.append({
                    "severity": "low",  # policy: CVE hint = low until confirmed/version precise
                    "name": f"Possible exposure: {cve}",
                    "path": "/",
                    "description": (
                        f"Service fingerprint suggests {prod}"
                        + (f" {ver}" if ver else "")
                        + f" may be affected by {cve}. Manual verification required."
                    ),
                    "impact": "May indicate outdated or vulnerable software version.",
                    "remediation": "Verify software version; if affected, update to a patched release.",
                    "reference_links": [f"https://cve.mitre.org/cgi-bin/cvename.cgi?name={cve}"],
                })

    return {
        "open_ports": open_ports,
        "http_info": http_info,
        "tls_info": tls_info or {},
        "vulnerabilities": vulnerabilities,
    }
