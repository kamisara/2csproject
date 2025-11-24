"""
URL configuration for VulnScan scanning application.

This module defines all API endpoints for vulnerability scanning operations,
including scan management, progress tracking, result retrieval, and reporting.
The URLs follow RESTful conventions for scan resource operations.

Base Path: /api/scans/ (when included from main urls.py)

Endpoint Groups:
- Scan Management: List, create, detail, and cancellation
- Results & Reporting: Technical results, vulnerability reports, downloads
- Analytics: Common vulnerability statistics

Security Note:
- All endpoints require JWT authentication via HTTP-only cookies
- User isolation ensures users can only access their own scans
- Input validation prevents malicious scan targets
"""

from django.urls import path
from .views import ScanListCreateView, ScanDetailView, ScanCancelView, ScanResultView, ScanReportView, ScanDownloadView, most_common_vulns

# Scanning application URL patterns
urlpatterns = [
    # =========================================================================
    # SCAN MANAGEMENT ENDPOINTS
    # =========================================================================
    
    # Scan list and creation - GET for user's scan history, POST to start new scan
    path("scans/", ScanListCreateView.as_view(), name="scan-list-create"),
    
    # Scan details and progress - GET for scan status, progress, and basic information
    path("scans/<int:scan_id>/", ScanDetailView.as_view(), name="scan-detail"),
    
    # Scan cancellation - POST to cancel an ongoing scan operation
    path("scans/<int:scan_id>/cancel/", ScanCancelView.as_view(), name="scan-cancel"),
    
    # =========================================================================
    # RESULTS & REPORTING ENDPOINTS
    # =========================================================================
    
    # Technical results - GET for detailed scan findings and raw data
    path("scans/<int:scan_id>/result/", ScanResultView.as_view(), name="scan-result"),
    
    # Vulnerability report - GET for formatted vulnerability information
    path("scans/<int:scan_id>/report/", ScanReportView.as_view(), name="scan-report"),
    
    # Report download - GET for downloadable reports in various formats
    path("scans/<int:scan_id>/download/", ScanDownloadView.as_view(), name="scan-download"),
    
    # =========================================================================
    # ANALYTICS ENDPOINTS
    # =========================================================================
    
    # Common vulnerabilities - GET for statistics on most frequent vulnerability types
    path("most-common-vuln/", most_common_vulns, name="most-common-vuln"),
]


"""
Complete API Endpoint Reference:

Scan Management Routes:
GET    /api/scans/                    - List user's scans (with filtering)
POST   /api/scans/                    - Create new scan session
GET    /api/scans/{scan_id}/          - Get scan details and progress
POST   /api/scans/{scan_id}/cancel/   - Cancel ongoing scan

Results & Reporting Routes:
GET    /api/scans/{scan_id}/result/   - Get detailed technical results
GET    /api/scans/{scan_id}/report/   - Get vulnerability report
GET    /api/scans/{scan_id}/download/ - Download report (PDF, JSON, CSV)

Analytics Routes:
GET    /api/most-common-vuln/         - Get most common vulnerability statistics

Request/Response Examples:

Scan Creation:
  POST /api/scans/
  Body: {"target": "example.com", "mode": "quick"}
  Response: 201 Created with scan metadata

Scan Progress:
  GET /api/scans/123/
  Response: 200 OK with status, progress, and timing information

Scan Results:
  GET /api/scans/123/result/
  Response: 200 OK with open ports, services, and vulnerability data

Authentication Requirements:
- All endpoints require valid JWT authentication
- Users can only access their own scan data
- Administrative endpoints may require staff privileges

Error Handling:
- 400: Invalid scan target or parameters
- 401: Missing or invalid authentication
- 403: Attempt to access another user's scan
- 404: Scan not found
- 409: Scan already in progress for target

URL Parameter Notes:
- scan_id: Integer primary key of Scan model
- Supports standard Django URL pattern matching
- Parameter validation occurs in view classes

Testing Strategy:
- Test full scan lifecycle: create → monitor → results → report
- Verify user isolation between different accounts
- Test error conditions for invalid scan targets
- Validate report generation and download functionality
"""
