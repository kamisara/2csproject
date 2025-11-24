"""
Serializers for VulnScan scanning application.

This module defines all serializers used for vulnerability scanning operations,
data transformation, and API response formatting. Serializers handle the
conversion between Django model instances and JSON representations suitable
for frontend consumption.

Architecture:
- ModelSerializers for direct model field mapping
- Nested serializers for related object inclusion
- Read-only fields for computed properties and relationships
- Field selection for optimized API responses

Key Features:
- Nested relationships for comprehensive scan data
- Field optimization for different use cases
- Read-only fields for calculated properties
- Support for PostgreSQL JSONB and ArrayField types
"""

from rest_framework import serializers
from .models import Scan, ScanResult, Vulnerability, Report


class ScanResultSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed scan technical results.
    
    Handles the serialization of raw scan data stored in JSONB fields,
    including open port information, HTTP service details, TLS configuration,
    and raw scanning tool output.
    
    Fields:
    - open_ports: JSON array of discovered open ports with service details
    - http_info: JSON object with HTTP service information and headers
    - tls_info: JSON object with TLS/SSL certificate details
    - raw_output: JSON object with complete raw scanning tool output
    - created_at: Timestamp when results were first created
    - updated_at: Timestamp when results were last updated
    """
    
    class Meta:
        model = ScanResult
        fields = ["open_ports", "http_info", "tls_info", "raw_output", "created_at", "updated_at"]


class VulnerabilitySerializer(serializers.ModelSerializer):
    """
    Serializer for individual vulnerability findings.
    
    Provides detailed information about security vulnerabilities discovered
    during scans, including severity classification, impact assessment,
    remediation guidance, and reference materials.
    
    Fields:
    - id: Unique vulnerability identifier
    - severity: Criticality level (info, low, medium, high, critical)
    - name: Vulnerability title or CVE identifier
    - path: Affected endpoint or component
    - description: Technical explanation of the issue
    - impact: Potential consequences if exploited
    - remediation: Recommended fix or mitigation steps
    - reference_links: Array of reference URLs for additional information
    - status: Current state in vulnerability management workflow
    - evidence: Technical evidence or proof of the vulnerability
    - created_at: Timestamp when vulnerability was recorded
    """
    
    class Meta:
        model = Vulnerability
        fields = ["id", "severity", "name", "path", "description", "impact", "remediation", 
                 "reference_links", "status", "evidence", "created_at"]


class ReportSerializer(serializers.ModelSerializer):
    """
    Serializer for scan report summaries.
    
    Handles aggregated scan results suitable for reporting and dashboards,
    including vulnerability statistics, duration information, and download links.
    
    Fields:
    - total: Total number of vulnerabilities found
    - critical: Number of critical severity vulnerabilities
    - high: Number of high severity vulnerabilities
    - medium: Number of medium severity vulnerabilities
    - low: Number of low severity vulnerabilities
    - info: Number of informational findings
    - duration: Total scan duration in human-readable format
    - vulnerabilities: Array of vulnerability IDs included in the report
    - download_link: URL or path to downloadable report file
    - generated_at: Timestamp when report was generated
    """
    
    class Meta:
        model = Report
        fields = ["total", "critical", "high", "medium", "low", "info", "duration", 
                 "vulnerabilities", "download_link", "generated_at"]


class ScanSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for scan sessions with nested relationships.
    
    Provides complete scan information including basic scan metadata,
    technical results, discovered vulnerabilities, and generated reports
    in a single API response.
    
    Nested Relationships:
    - result: Detailed technical findings (one-to-one)
    - vulnerabilities: List of discovered security issues (one-to-many)
    - report: Aggregated results summary (one-to-one)
    
    Fields:
    - Basic scan metadata: id, target, mode, status, progress, timestamps
    - Nested objects: result, vulnerabilities, report
    - Progress tracking: progress, estimated_time_left
    - Timing information: created_at, started_at, finished_at
    """
    
    # Nested serializers for related objects
    result = ScanResultSerializer(read_only=True)
    vulnerabilities = VulnerabilitySerializer(many=True, read_only=True)
    report = ReportSerializer(read_only=True)

    class Meta:
        model = Scan
        fields = [
            "id", "target", "mode", "status", "progress", "created_at",
            "started_at", "finished_at", "estimated_time_left",
            "result", "vulnerabilities", "report",
        ]


class ScanCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new scan sessions.
    
    Handles scan initiation with minimal required input fields.
    Used specifically for scan creation endpoints where only target
    and scan mode are required from the user.
    
    Fields:
    - target: Hostname, IP address, or URL to scan (required)
    - mode: Scan intensity level - quick or full (required)
    
    Validation:
    - Target must be a valid hostname, IP, or URL
    - Mode must be either 'quick' or 'full'
    - User authentication is handled at view level
    """
    
    class Meta:
        model = Scan
        fields = ["target", "mode"]


"""
Serialization Patterns:

1. ModelSerializer Usage:
   - Automatic field mapping from model definitions
   - Built-in validation based on model field constraints
   - Support for model methods and properties

2. Nested Serializers:
   - ScanResultSerializer: One-to-one relationship with Scan
   - VulnerabilitySerializer: One-to-many relationship with Scan  
   - ReportSerializer: One-to-one relationship with Scan

3. Field Optimization:
   - ScanCreateSerializer: Minimal fields for creation
   - ScanSerializer: Comprehensive fields for detail views
   - Separate serializers for different API contexts

Performance Considerations:
- Nested serializers can cause N+1 query problems
- Consider using select_related and prefetch_related in views
- Use specific serializers for different API endpoints
- Limit nested depth for large result sets

API Response Examples:

Scan Creation:
  POST /api/scans/
  Body: {"target": "example.com", "mode": "quick"}
  Response: ScanSerializer with initial scan data

Scan Detail:
  GET /api/scans/1/
  Response: ScanSerializer with nested results, vulnerabilities, and report

Security Considerations:
- Input validation occurs at both serializer and model levels
- User authentication enforced at view level
- Field-level permissions can be implemented if needed
- Sensitive data filtering in different serializer contexts
"""
        
