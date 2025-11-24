"""
View controllers for VulnScan scanning application.

This module contains all API view classes that handle HTTP requests for
vulnerability scanning operations, including scan management, progress
tracking, result retrieval, and report generation.

Architecture:
- APIView-based classes with JWT authentication
- Comprehensive input validation and security checks
- Asynchronous task integration with Celery
- Multi-format report generation (PDF, HTML, JSON)
- User isolation for data security

Security Features:
- JWT authentication via HTTP-only cookies
- User-specific data access restrictions
- Input validation for scan targets
- Secure file download with proper content types
"""

#--
# apps/scans_app/views.py
from urllib.parse import urlparse
import ipaddress
from collections import Counter
from datetime import timedelta

from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
import django.db.models as djm
from weasyprint import HTML

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, authentication_classes

from .models import Scan, ScanResult, Vulnerability
from .serializers import (
    ScanCreateSerializer,
    ScanResultSerializer,
    VulnerabilitySerializer,
    ReportSerializer,
)
from apps.auth_app.authentication import CookieJWTAuthentication as JWTAuthentication
from .tasks import run_scan_task


class AuthenticatedView(APIView):
    """
    Base view class for all authenticated scanning endpoints.
    
    Provides consistent JWT authentication and permission checking
    across all scan-related views. Ensures users can only access
    their own scan data.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


def _is_valid_target(target: str) -> bool:
    """
    Validate scan target format.
    
    Supports multiple target formats:
    - CIDR notation (e.g., 192.168.1.0/24)
    - IP addresses (IPv4 and IPv6)
    - URLs with http/https schemes
    - Hostnames with domain notation
    
    Args:
        target (str): Target to validate
        
    Returns:
        bool: True if target format is valid
    """
    if not target or len(target) > 255:
        return False

    # CIDR (contains slash)
    try:
        if "/" in target:
            ipaddress.ip_network(target, strict=False)
            return True
    except ValueError:
        pass

    # IP address
    try:
        ipaddress.ip_address(target)
        return True
    except ValueError:
        pass

    # URL with scheme + host
    try:
        parsed = urlparse(target)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            return True
    except Exception:
        pass

    # Plain hostname (best-effort)
    if "." in target and " " not in target:
        return True

    return False


def _scan_summary_for_list(scan: Scan):
    """
    Generate summary data for scan list responses.
    
    Args:
        scan (Scan): Scan instance to summarize
        
    Returns:
        dict: Formatted scan summary for list views
    """
    base = {
        "scanId": f"s_{scan.id}",
        "target": scan.target,
        "mode": scan.mode,
        "status": scan.status,
        "createdAt": scan.created_at.isoformat(),
    }
    if scan.status == "completed" and hasattr(scan, "report") and scan.report:
        base["summary"] = {
            "critical": scan.report.critical,
            "high": scan.report.high,
            "medium": scan.report.medium,
            "low": scan.report.low,
            "info": scan.report.info,
        }
        base["duration"] = scan.report.duration
    elif scan.status == "running":
        base["progress"] = scan.progress
    return base


def _scan_detail_for_get(scan: Scan):
    """
    Generate detailed data for single scan responses.
    
    Args:
        scan (Scan): Scan instance to detail
        
    Returns:
        dict: Formatted scan details for single view
    """
    return {
        "scanId": f"s_{scan.id}",
        "target": scan.target,
        "mode": scan.mode,
        "status": scan.status,
        "progress": scan.progress,
        "startedAt": scan.started_at.isoformat() if scan.started_at else None,
        "estimatedTimeLeft": scan.estimated_time_left,
    }


class ScanListCreateView(AuthenticatedView):
    """
    Handle scan listing and creation.
    
    GET: Retrieve user's scan history with filtering and pagination
    POST: Create new scan session and enqueue background task
    """
    
    def post(self, request):
        """
        Create a new vulnerability scan.
        
        Validates target and mode, creates scan record, and starts
        background scanning task.
        """
        serializer = ScanCreateSerializer(data=request.data or {})
        if not serializer.is_valid():
            return Response({"error": {"code": 400, "message": serializer.errors}}, status=400)

        target = serializer.validated_data["target"]
        mode = serializer.validated_data["mode"]

        if mode not in ("quick", "full"):
            return Response({"error": {"code": 400, "message": "mode must be 'quick' or 'full'"}}, status=400)
        if not _is_valid_target(target):
            return Response({"error": {"code": 400, "message": "Invalid target URL/IP/CIDR"}}, status=400)

        scan = Scan.objects.create(
            user=request.user,
            target=target,
            mode=mode,
            status="queued",
            progress=0,
            created_at=timezone.now(),
        )

        # enqueue Celery task
        run_scan_task.delay(scan.id)

        return Response(
            {
                "scanId": f"s_{scan.id}",
                "target": scan.target,
                "mode": scan.mode,
                "status": "queued",
                "createdAt": scan.created_at.isoformat(),
            },
            status=201,
        )

    def get(self, request):
        """
        Retrieve user's scan history.
        
        Supports pagination and filtering by status and mode.
        """
        limit = int(request.query_params.get("limit", 10))
        offset = int(request.query_params.get("offset", 0))
        status_filter = request.query_params.get("status")
        mode_filter = request.query_params.get("mode")

        qs = Scan.objects.filter(user=request.user).order_by("-created_at")
        if status_filter in {"queued", "running", "completed", "failed", "canceled"}:
            qs = qs.filter(status=status_filter)
        if mode_filter in {"quick", "full"}:
            qs = qs.filter(mode=mode_filter)

        scans = qs[offset : offset + limit]
        return Response({"scans": [_scan_summary_for_list(s) for s in scans]}, status=200)


class ScanDetailView(AuthenticatedView):
    """
    Retrieve detailed information about a specific scan.
    
    Provides current status, progress, and timing information
    for ongoing or completed scans.
    """
    
    def get(self, request, scan_id: int):
        """
        Get scan details and progress information.
        """
        try:
            scan = Scan.objects.get(id=scan_id, user=request.user)
        except Scan.DoesNotExist:
            return Response({"error": {"code": 404, "message": "Scan not found"}}, status=404)
        return Response(_scan_detail_for_get(scan), status=200)


class ScanCancelView(AuthenticatedView):
    """
    Cancel an ongoing scan operation.
    
    Allows users to stop scans that are queued or running.
    Idempotent for already completed/failed/canceled scans.
    """
    
    def post(self, request, scan_id: int):
        """
        Cancel a scan if it's still running or queued.
        """
        try:
            scan = Scan.objects.get(id=scan_id, user=request.user)
        except Scan.DoesNotExist:
            return Response({"error": {"code": 404, "message": "Scan not found"}}, status=404)

        if scan.status in ("completed", "failed", "canceled"):
            # idempotent response
            return Response({"scanId": f"s_{scan.id}", "status": scan.status}, status=200)

        scan.status = "canceled"
        scan.estimated_time_left = None
        scan.save(update_fields=["status", "estimated_time_left"])
        return Response({"scanId": f"s_{scan.id}", "status": "canceled"}, status=200)


class ScanResultView(AuthenticatedView):
    """
    Retrieve detailed technical results from a completed scan.
    
    Provides access to raw scan data including open ports,
    service information, and TLS configuration details.
    """
    
    def get(self, request, scan_id: int):
        """
        Get detailed technical scan results.
        """
        scan = get_object_or_404(Scan, id=scan_id, user=request.user)
        if scan.status != "completed":
            return Response(
                {"detail": f"Scan is {scan.status}. Results available after completion."},
                status=status.HTTP_409_CONFLICT,
            )
        try:
            result = scan.result  # OneToOne
        except ScanResult.DoesNotExist:
            return Response({"detail": "Results not found."}, status=status.HTTP_404_NOT_FOUND)

        data = {
            "scanId": f"s_{scan.id}",
            "target": scan.target,
            "mode": scan.mode,
            "status": scan.status,
            "result": ScanResultSerializer(result).data,
        }
        return Response(data, status=status.HTTP_200_OK)


# Helper functions for report generation
def _dur_str(start, end):
    """
    Return a short human-readable duration (e.g. '1 min 22 sec').
    """
    try:
        if not start or not end:
            return "—"
        if isinstance(start, str):
            start = timezone.datetime.fromisoformat(start.replace("Z", "+00:00"))
        if isinstance(end, str):
            end = timezone.datetime.fromisoformat(end.replace("Z", "+00:00"))
        delta: timedelta = end - start
        secs = max(0, int(delta.total_seconds()))
        return f"{secs // 60} min {secs % 60} sec"
    except Exception:
        return "—"


def _sev_summary(vulns):
    """
    Aggregate counts by severity.
    """
    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for v in vulns:
        sev = (v.get("severity") or "info").lower()
        summary[sev] = summary.get(sev, 0) + 1
    summary["total"] = sum(summary.values())
    return summary


def _pct(n, total):
    """
    Calculate percentage safely.
    """
    try:
        return 0 if not total else round(n * 100 / total)
    except Exception:
        return 0


class ScanDownloadView(AuthenticatedView):
    """
    Handle scan report downloads in multiple formats.
    
    Supports PDF, HTML, and JSON output formats for scan reports.
    Generates professional reports with vulnerability details,
    severity summaries, and technical findings.
    """
    
    def get(self, request, scan_id: int, fmt: str | None = None):
        """
        Download scan report in requested format (PDF, HTML, JSON).
        """
        # Normalize requested format
        raw = fmt or request.GET.get("format") or request.GET.get("as") or "pdf"
        fmt = str(raw).strip().lower()

        # 1) Fetch scan & check ownership
        try:
            scan = Scan.objects.get(id=scan_id, user=request.user)
        except Scan.DoesNotExist:
            return JsonResponse({"detail": "Scan not found."}, status=404)

        if scan.status != "completed":
            return JsonResponse(
                {"detail": f"Scan is {scan.status}. Download available after completion."},
                status=409,
            )

        # 2) Pull related data (safe defaults)
        try:
            result: ScanResult = scan.result
        except ScanResult.DoesNotExist:
            result = None

        vulns_qs = (
            scan.vulnerabilities.all().order_by(
                djm.Case(
                    djm.When(severity="critical", then=djm.Value(0)),
                    djm.When(severity="high",    then=djm.Value(1)),
                    djm.When(severity="medium",  then=djm.Value(2)),
                    djm.When(severity="low",     then=djm.Value(3)),
                    djm.When(severity="info",    then=djm.Value(4)),
                    default=djm.Value(5),
                    output_field=djm.IntegerField(),
                ),
                "name",
            )
        )

        # 3) Build hosts structure compatible with template
        hosts: list[dict] = []
        if result:
            host_block = {
                "ip": scan.target,
                "reachable": bool(getattr(result, "open_ports", None)),
                "ports": getattr(result, "open_ports", []) or [],
                "http": getattr(result, "http_info", None),
                "tls": getattr(result, "tls_info", None),
                "vulnMatches": [],  # filled below
            }
            hosts.append(host_block)

        # 4) Convert Vulnerability queryset to list for both host-level and report table
        vulns: list[dict] = []
        for v in vulns_qs:
            vulns.append(
                {
                    "severity": (v.severity or "info"),
                    "name": v.name,
                    "host": scan.target,
                    "path": v.path or "",
                    "description": v.description or "",
                    "remediation": v.remediation or "",
                    "references": v.reference_links or [],
                }
            )
        if hosts:
            hosts[0]["vulnMatches"] = vulns

        # 5) Aggregates
        sev = _sev_summary(vulns)  # -> {critical,high,medium,low,info,total}
        duration = _dur_str(scan.started_at, scan.finished_at)

        open_ports_total = 0
        if result and isinstance(result.open_ports, (list, tuple)):
            open_ports_total = sum(
                1 for p in result.open_ports if (p or {}).get("state") == "open"
            )

        # widths for the severity bar in template
        total_for_bar = max(1, sev.get("total", 0))
        widths = {
            "critical": round(100 * sev.get("critical", 0) / total_for_bar, 2),
            "high":     round(100 * sev.get("high", 0) / total_for_bar, 2),
            "medium":   round(100 * sev.get("medium", 0) / total_for_bar, 2),
            "low":      round(100 * sev.get("low", 0) / total_for_bar, 2),
            "info":     round(100 * sev.get("info", 0) / total_for_bar, 2),
        }

        context = {
            "app_name": "VulnScanner",
            "logo_text": "VulnScanner",
            "generated_at": timezone.now(),
            "user_name": f"{getattr(request.user, 'first_name', 'User')} {getattr(request.user, 'last_name', '')}".strip(),
            "scan": {
                "target": scan.target,
                "type": scan.mode,
                "status": scan.status,
                "createdAt": scan.created_at.isoformat(),
                "finishedAt": scan.finished_at.isoformat() if scan.finished_at else "",
                "results": {"summary": {"hostsScanned": 1}, "hosts": hosts},
            },
            "hosts": hosts,
            "vulns": vulns,
            "sev": sev,
            "widths": widths,
            "duration": duration,
            "open_ports_total": open_ports_total,
        }

        # 6) Output formats
        if fmt == "json":
            return JsonResponse(context, status=200, safe=False)

        html = render_to_string("reports/scan_report.html", context)

        if fmt == "html":
            return HttpResponse(html)

        # default: PDF
        pdf = HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf()
        resp = HttpResponse(pdf, content_type="application/pdf")
        resp["Content-Disposition"] = f'attachment; filename="scan_report_{scan_id}.pdf"'
        return resp
    

@api_view(['GET'])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def most_common_vulns(request):
    """
    Retrieve statistics on most frequently found vulnerabilities.
    
    Analyzes user's scan history to identify common vulnerability patterns
    and provide insights for security prioritization.
    """
    user = request.user

    vulns = Vulnerability.objects.filter(scan__user=user)

    if not vulns.exists():
        return Response({"most_common": []}, status=200)

    vuln_names = [v.name for v in vulns]
    freq = Counter(vuln_names)

    result = [{"name": name, "count": count} for name, count in freq.most_common()]

    return Response({"most_common": result}, status=200)

#--
