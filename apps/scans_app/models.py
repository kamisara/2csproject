"""
Database models for VulnScan scanning application.

This module defines the core data structures for vulnerability scanning operations,
including scan sessions, results, vulnerabilities, reports, and user notes.
The models leverage PostgreSQL-specific features like JSONB and ArrayField
for flexible data storage while maintaining relational integrity.

Architecture:
- Scan: Master record for scanning sessions with status tracking
- ScanResult: Detailed technical findings from scans (JSONB for flexibility)
- Vulnerability: Individual security issues with severity classification
- Report: Aggregated scan results for presentation and export
- Note: User annotations on vulnerabilities for collaboration

PostgreSQL Features Used:
- JSONB: For schemaless storage of scan results and technical data
- ArrayField: For storing lists of references and vulnerability IDs
- Foreign Keys: For maintaining relational integrity with CASCADE operations
- DateTimeField: For audit trails and temporal analysis
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import ArrayField


class Scan(models.Model):
    """
    Master model for vulnerability scanning sessions.
    
    Tracks the lifecycle of a scan from creation through completion,
    including progress monitoring, timing information, and user association.
    Each scan progresses through states: queued → running → completed/failed/canceled.
    """
    
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
    ]
    MODE_CHOICES = [('quick', 'Quick'), ('full', 'Full')]

    # User relationship - each scan belongs to one user
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # auth_user FK
    
    # Scan target - hostname, IP address, or URL to be scanned
    target = models.CharField(max_length=255)
    
    # Scan intensity level - quick for fast scans, full for comprehensive
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    
    # Current state in scan lifecycle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    
    # Completion percentage with validation (0-100%)
    progress = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Timestamps for tracking scan lifecycle
    created_at = models.DateTimeField(auto_now_add=True)   # DEFAULT NOW()
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    # Human-readable time estimate for ongoing scans
    estimated_time_left = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        """Human-readable string representation for admin interface."""
        return f"[{self.id}] {self.target} ({self.mode}) - {self.status}"

    class Meta:
        """Metadata options for Scan model."""
        verbose_name = "Vulnerability Scan"
        verbose_name_plural = "Vulnerability Scans"
        ordering = ['-created_at']  # Most recent scans first


class ScanResult(models.Model):
    """
    Detailed technical results from a vulnerability scan.
    
    Stores raw and processed scan data using PostgreSQL JSONB fields
    for flexibility in storing varying types of scan results without
    requiring schema changes for new scan types or tools.
    """
    
    # One-to-one relationship with Scan - each scan has one result set
    scan = models.OneToOneField(Scan, on_delete=models.CASCADE, related_name="result")
    
    # JSONB field for open port information with service details
    open_ports = models.JSONField(default=list)   # [{"port":80,"service":"http","banner":"nginx"}, ...]
    
    # JSONB field for HTTP service information and headers
    http_info = models.JSONField(default=dict)    # {"status":200,"title":"Home","server":"Apache"}
    
    # JSONB field for TLS/SSL certificate and configuration details
    tls_info = models.JSONField(default=dict)     # {"issuer":"Let's Encrypt","valid":true,...}
    
    # JSONB field for complete raw output from scanning tools
    raw_output = models.JSONField(default=dict)   # optional raw results / debug
    
    # Timestamps for tracking when results were created and updated
    created_at = models.DateTimeField(auto_now_add=True)  # DEFAULT NOW()
    updated_at = models.DateTimeField(auto_now=True)      # trigger equivalent

    def __str__(self):
        """Human-readable string representation."""
        return f"Results for Scan #{self.scan_id}"


class Vulnerability(models.Model):
    """
    Individual security vulnerability findings from scans.
    
    Represents specific security issues discovered during scanning,
    with detailed information about severity, impact, and remediation.
    Supports user collaboration through notes and status tracking.
    """
    
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('new', 'New'),
        ('acknowledged', 'Acknowledged'),
        ('fixed', 'Fixed'),
    ]

    # Many-to-one relationship with Scan - vulnerabilities belong to a scan
    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name="vulnerabilities")
    
    # Criticality level of the vulnerability for prioritization
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    
    # Vulnerability name or CVE identifier
    name = models.CharField(max_length=255)
    
    # Affected endpoint, URL, or component path
    path = models.CharField(max_length=255, null=True, blank=True)
    
    # Technical description of the vulnerability
    description = models.TextField(null=True, blank=True)
    
    # Potential consequences if exploited
    impact = models.TextField(null=True, blank=True)
    
    # Recommended fix or mitigation steps
    remediation = models.TextField(null=True, blank=True)
    
    # Array of reference URLs for additional information
    # TEXT[] in SQL → ArrayField(CharField)
    reference_links = ArrayField(
        base_field=models.CharField(max_length=1024),
        default=list,
        blank=True,
    )
    
    # Current status in vulnerability management workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    
    # Technical evidence or proof of the vulnerability
    evidence = models.TextField(null=True, blank=True)
    
    # Timestamp when vulnerability was recorded
    created_at = models.DateTimeField(auto_now_add=True)  # DEFAULT NOW()

    def __str__(self):
        """Human-readable string representation."""
        return f"{self.name} ({self.severity}) - Scan #{self.scan_id}"

    class Meta:
        """Metadata options for Vulnerability model."""
        verbose_name = "Vulnerability"
        verbose_name_plural = "Vulnerabilities"
        ordering = ['-severity', 'name']  # Sort by severity then name


class Report(models.Model):
    """
    Aggregated scan results for presentation and export.
    
    Provides summarized information about a scan session suitable for
    reports, dashboards, and external sharing. Includes statistics
    and references to specific vulnerabilities.
    """
    
    # One-to-one relationship with Scan - each scan has one report
    scan = models.OneToOneField(Scan, on_delete=models.CASCADE, related_name="report")
    
    # Vulnerability count statistics
    total = models.IntegerField(default=0)
    critical = models.IntegerField(default=0)
    high = models.IntegerField(default=0)
    medium = models.IntegerField(default=0)
    low = models.IntegerField(default=0)
    info = models.IntegerField(default=0)
    
    # Total scan duration in human-readable format
    duration = models.CharField(max_length=50, null=True, blank=True)
    
    # Array of vulnerability IDs included in this report
    # INT[] in SQL → ArrayField(IntegerField)
    vulnerabilities = ArrayField(
        base_field=models.IntegerField(),
        default=list,
        blank=True,
    )
    
    # URL or path to downloadable report file (PDF, etc.)
    download_link = models.CharField(max_length=255, null=True, blank=True)
    
    # Timestamp when report was generated
    generated_at = models.DateTimeField(auto_now_add=True)  # DEFAULT NOW()

    def __str__(self):
        """Human-readable string representation."""
        return f"Report for Scan #{self.scan_id}"

    class Meta:
        """Metadata options for Report model."""
        verbose_name = "Scan Report"
        verbose_name_plural = "Scan Reports"
        ordering = ['-generated_at']


class Note(models.Model):
    """
    User annotations and comments on vulnerability findings.
    
    Enables collaboration and knowledge sharing by allowing users
    to add context, observations, and follow-up information to
    specific vulnerabilities.
    """
    
    # Many-to-one relationship with Vulnerability
    vuln = models.ForeignKey(Vulnerability, on_delete=models.CASCADE, related_name="notes")
    
    # Many-to-one relationship with User - notes are created by users
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Text content of the note or comment
    content = models.TextField()
    
    # Timestamp when note was created
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Human-readable string representation."""
        return f"Note by {self.user} on Vuln #{self.vuln_id}"

    class Meta:
        """Metadata options for Note model."""
        verbose_name = "Vulnerability Note"
        verbose_name_plural = "Vulnerability Notes"
        ordering = ['-created_at']  # Most recent notes first


"""
Database Schema Relationships:

Scan (1) ───── (1) ScanResult
   │
   │ (1)
   │
   ▼
Vulnerability (1) ───── (N) Note
   │
   │ (N)
   │  
   ▼
Report (includes vulnerability IDs)

Key Design Decisions:
1. JSONB fields in ScanResult allow flexible storage of varying scan data
2. ArrayField for reference_links enables efficient storage of URL lists
3. Separate Report model aggregates data for presentation layer
4. Note model supports collaborative vulnerability management
5. All models include created_at for audit trail

Performance Considerations:
- Foreign key indexes are automatically created by Django
- JSONB fields support efficient querying of nested data
- ArrayField provides better performance than many-to-many for simple lists
- DateTime fields with timezone support for accurate timestamping

Migration Safety:
- No changes to existing field definitions
- Only comments and documentation added
- All existing data relationships preserved
- No database schema modifications required
"""
