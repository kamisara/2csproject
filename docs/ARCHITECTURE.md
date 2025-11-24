# VulnScan Architecture Documentation

## System Overview
VulnScan is a full-stack web application for educational vulnerability scanning, built with a modern microservices-inspired architecture using Django REST Framework and React.

## 🏗️ High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React         │    │   Django REST    │    │   PostgreSQL    │
│   Frontend      │◄──►│   API Backend    │◄──►│   Database      │
│   (Vite)        │    │   (DRF)          │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         │              ┌────────┴────────┐              │
         │              │                 │              │
         │              ▼                 ▼              │
         │       ┌─────────────┐   ┌─────────────┐       │
         └──────►│   Redis     │   │   Celery    │       │
                 │   Broker    │   │   Workers   │       │
                 └─────────────┘   └─────────────┘       │
                                │                        │
                                ▼                        ▼
                        ┌─────────────────┐    ┌─────────────────┐
                        │   External      │    │   File Storage  │
                        │   APIs (NVD)    │    │   (Media)       │
                        └─────────────────┘    └─────────────────┘
```

## 📱 Frontend Architecture

### Technology Stack
- **Framework**: React 19 with Hooks
- **Build Tool**: Vite for fast development
- **Styling**: Tailwind CSS for responsive design
- **Routing**: React Router DOM for SPA navigation
- **State Management**: React Context + useState/useReducer
- **HTTP Client**: Axios for API communication
- **Charts**: Recharts for data visualization
- **Icons**: React Icons library

### Component Structure
```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── common/         # Button, Input, Modal, Loader
│   │   ├── layout/         # Header, Sidebar, Footer, Navigation
│   │   ├── auth/           # LoginForm, RegisterForm
│   │   ├── scanning/       # ScanForm, ProgressBar, Results
│   │   └── dashboard/      # StatsCards, VulnerabilityChart
│   ├── pages/              # Route components
│   │   ├── Auth/           # Login, Register pages
│   │   ├── Dashboard/      # Main dashboard with overview
│   │   ├── Scanning/       # Scan creation and monitoring
│   │   ├── History/        # Scan history and reports
│   │   └── Profile/        # User profile management
│   ├── services/           # API service layer
│   │   ├── auth.js         # Authentication API calls
│   │   ├── scans.js        # Scan management API calls
│   │   ├── reports.js      # Report generation API calls
│   │   └── api.js          # Axios configuration and interceptors
│   ├── contexts/           # React Context providers
│   │   ├── AuthContext.js  # Authentication state management
│   │   └── ScanContext.js  # Global scan state management
│   ├── hooks/              # Custom React hooks
│   │   ├── useAuth.js      # Authentication logic
│   │   ├── useScans.js     # Scan management logic
│   │   └── useApi.js       # API call abstractions
│   ├── utils/              # Helper functions and utilities
│   │   ├── validators.js   # Form validation functions
│   │   ├── constants.js    # Application constants
│   │   ├── formatters.js   # Data formatting functions
│   │   └── helpers.js      # General utility functions
│   └── styles/             # Global styles and Tailwind config
│       ├── index.css       # Global CSS
│       └── tailwind.css    # Tailwind imports
```

### Key Frontend Components

#### Authentication Flow
```javascript
// AuthContext provides global authentication state
const AuthContext = createContext();

// Usage in components
const { user, login, logout, isLoading } = useAuth();

// Protected route wrapper
<Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>}
```

#### Real-time Scan Monitoring
```javascript
// Custom hook for real-time progress updates
const useScanProgress = (scanId) => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('queued');
  
  useEffect(() => {
    const interval = setInterval(async () => {
      const data = await fetchScanProgress(scanId);
      setProgress(data.progress);
      setStatus(data.status);
    }, 2000);
    
    return () => clearInterval(interval);
  }, [scanId]);
  
  return { progress, status };
};
```

## 🖥️ Backend Architecture

### Technology Stack
- **Framework**: Django 5.2 + Django REST Framework 3.16
- **Database**: PostgreSQL with JSONB support
- **Task Queue**: Celery 5.4 + Redis 5.0
- **Authentication**: JWT with HTTP-only cookies
- **Containerization**: Docker + Docker Compose
- **PDF Generation**: WeasyPrint
- **File Handling**: Django FileField with Pillow

### Application Structure
```
backend/
├── vulnscanner/              # Project configuration
│   ├── settings.py           # Django settings and configuration
│   ├── urls.py               # Root URL configuration
│   ├── wsgi.py               # WSGI application entry point
│   ├── celery.py             # Celery configuration
│   └── middleware/           # Custom middleware classes
│       ├── jwt_middleware.py # JWT authentication middleware
│       └── cors_middleware.py# CORS handling middleware
├── apps/
│   ├── auth_app/             # User authentication & profiles
│   │   ├── models.py         # User, Profile models
│   │   ├── views.py          # Auth API views
│   │   ├── serializers.py    # User serializers
│   │   ├── urls.py           # Auth endpoint routes
│   │   └── utils.py          # Auth utilities
│   ├── scans_app/            # Vulnerability scanning core
│   │   ├── models.py         # Scan, Vulnerability models
│   │   ├── views.py          # Scan API views
│   │   ├── serializers.py    # Scan data serializers
│   │   ├── urls.py           # Scan endpoint routes
│   │   ├── scanners/         # Scanning engines
│   │   │   ├── port_scanner.py       # TCP port scanning
│   │   │   ├── service_detector.py   # HTTP service detection
│   │   │   └── vulnerability_scanner.py # CVE detection
│   │   ├── tasks.py          # Celery tasks for async scanning
│   │   └── utils.py          # Scanning utilities
│   └── core/                 # Shared utilities and base classes
│       ├── models.py         # Base models with common fields
│       ├── utils.py          # Common utility functions
│       └── exceptions.py     # Custom exceptions
├── media/                    # User uploads and generated files
│   ├── avatars/              # User profile pictures
│   └── reports/              # Generated scan reports
└── static/                   # Static files (CSS, JS, images)
```

### Database Schema

#### User Models
```python
class User(AbstractUser):
    user_id = models.CharField(max_length=20, unique=True, default=generate_user_id)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### Scan Models
```python
class Scan(models.Model):
    SCAN_STATUS = [
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
    ]
    
    SCAN_MODES = [
        ('quick', 'Quick Scan'),
        ('full', 'Full Scan'),
    ]
    
    scan_id = models.CharField(max_length=20, unique=True, default=generate_scan_id)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    target = models.CharField(max_length=255)
    mode = models.CharField(max_length=10, choices=SCAN_MODES)
    status = models.CharField(max_length=10, choices=SCAN_STATUS, default='queued')
    progress = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
class Vulnerability(models.Model):
    SEVERITY_LEVELS = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
        ('info', 'Information'),
    ]
    
    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name='vulnerabilities')
    vulnerability_id = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    description = models.TextField()
    impact = models.TextField()
    remediation = models.TextField()
    references = models.JSONField(default=list)  # List of URLs
    cvss_score = models.FloatField(null=True, blank=True)
    detected_at = models.DateTimeField(auto_now_add=True)
```

### API Layer Architecture

#### RESTful Endpoint Design
```python
# Example API view structure
class ScanViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ScanSerializer
    
    def get_queryset(self):
        return Scan.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        scan = self.get_object()
        scan.status = 'canceled'
        scan.save()
        return Response({'status': 'canceled'})
```

#### Serializer Structure
```python
class ScanSerializer(serializers.ModelSerializer):
    vulnerabilities = VulnerabilitySerializer(many=True, read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = Scan
        fields = ['scan_id', 'target', 'mode', 'status', 'progress', 
                 'created_at', 'started_at', 'completed_at', 'vulnerabilities', 'duration']
    
    def get_duration(self, obj):
        if obj.started_at and obj.completed_at:
            return obj.completed_at - obj.started_at
        return None
```

## 🔧 Core Components

### Authentication System
```python
# JWT Authentication Middleware
class JWTAuthenticationMiddleware:
    """
    Custom JWT middleware that:
    - Extracts JWT from HTTP-only cookies
    - Validates token and sets user on request
    - Handles token refresh automatically
    - Provides seamless stateless authentication
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        token = request.COOKIES.get('auth_token')
        if token:
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user = User.objects.get(id=payload['user_id'])
                request.user = user
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
                # Token is invalid or user doesn't exist
                pass
        
        response = self.get_response(request)
        return response
```

### Scanning Engine Architecture
```python
class ScanningEngine:
    """
    Core vulnerability scanning functionality with modular design:
    - Port scanning via non-blocking socket connections
    - HTTP service detection and banner grabbing
    - CVE vulnerability matching via NVD API integration
    - Asynchronous task processing with progress tracking
    - Configurable timeouts and error handling
    """
    
    def __init__(self, target, mode='quick'):
        self.target = target
        self.mode = mode
        self.results = []
        self.progress = 0
        
    async def run_scan(self):
        """Execute complete vulnerability scan"""
        try:
            # Phase 1: Port scanning
            await self.scan_ports()
            self.update_progress(25)
            
            # Phase 2: Service detection
            await self.detect_services()
            self.update_progress(50)
            
            # Phase 3: Vulnerability assessment
            await self.assess_vulnerabilities()
            self.update_progress(75)
            
            # Phase 4: Report generation
            await self.generate_findings()
            self.update_progress(100)
            
        except ScanException as e:
            logger.error(f"Scan failed: {e}")
            raise
    
    async def scan_ports(self):
        """Perform TCP port scanning with configurable parameters"""
        open_ports = []
        ports_to_scan = self.get_ports_for_mode()
        
        for port in ports_to_scan:
            if await self.is_port_open(port):
                open_ports.append(port)
        
        self.results['open_ports'] = open_ports
    
    async def detect_services(self):
        """Detect services running on open ports"""
        for port in self.results['open_ports']:
            service_info = await self.identify_service(port)
            self.results['services'].append(service_info)
    
    async def assess_vulnerabilities(self):
        """Check for known vulnerabilities in detected services"""
        for service in self.results['services']:
            vulnerabilities = await self.check_cve_database(service)
            self.results['vulnerabilities'].extend(vulnerabilities)
```

### Celery Task Management
```python
# tasks.py
@app.task(bind=True, queue='scans')
def run_scan_task(self, scan_id):
    """
    Celery task for asynchronous vulnerability scanning
    - Updates progress in real-time
    - Handles task cancellation
    - Manages resource limits
    - Provides detailed error reporting
    """
    scan = Scan.objects.get(scan_id=scan_id)
    
    try:
        scanner = ScanningEngine(target=scan.target, mode=scan.mode)
        
        # Update progress callback
        def progress_callback(progress):
            scan.progress = progress
            scan.save()
            self.update_state(state='PROGRESS', meta={'progress': progress})
        
        scanner.on_progress = progress_callback
        results = scanner.run_scan()
        
        # Save results to database
        save_scan_results(scan, results)
        scan.status = 'completed'
        scan.progress = 100
        scan.save()
        
        return {'status': 'completed', 'results': results}
        
    except Exception as e:
        scan.status = 'failed'
        scan.save()
        logger.error(f"Scan task failed: {e}")
        raise self.retry(exc=e, countdown=60)
```

### Report Generation System
```python
class ReportGenerator:
    """
    Multi-format report generation system:
    - PDF reports with professional styling using WeasyPrint
    - JSON export for data processing
    - CSV export for spreadsheet analysis
    - HTML reports for web viewing
    - Caching system for performance optimization
    """
    
    def generate_pdf_report(self, scan):
        """Generate professional PDF vulnerability report"""
        template = get_template('reports/pdf_template.html')
        context = {
            'scan': scan,
            'vulnerabilities': scan.vulnerabilities.all(),
            'generated_at': timezone.now()
        }
        html_content = template.render(context)
        
        # Generate PDF with WeasyPrint
        pdf_file = HTML(string=html_content).write_pdf()
        return pdf_file
    
    def generate_json_report(self, scan):
        """Generate structured JSON report for API consumption"""
        return {
            'scan_id': scan.scan_id,
            'target': scan.target,
            'summary': self.generate_summary(scan),
            'vulnerabilities': list(scan.vulnerabilities.values()),
            'metadata': {
                'generated_at': timezone.now().isoformat(),
                'report_version': '1.0'
            }
        }
```

## 🗄️ Database Design

### Data Models Relationships
```
User (1) ───── (1) Profile
   │
   │ (1)
   │
   ▼
Scan (1) ───── (N) Vulnerability
```

### Key Database Optimizations

#### Indexes for Performance
```sql
-- User and authentication indexes
CREATE INDEX CONCURRENTLY idx_user_email ON auth_app_user(email);
CREATE INDEX CONCURRENTLY idx_user_created ON auth_app_user(created_at);

-- Scan performance indexes
CREATE INDEX CONCURRENTLY idx_scan_user ON scans_app_scan(user_id);
CREATE INDEX CONCURRENTLY idx_scan_status ON scans_app_scan(status);
CREATE INDEX CONCURRENTLY idx_scan_created ON scans_app_scan(created_at);
CREATE INDEX CONCURRENTLY idx_scan_target ON scans_app_scan(target);

-- Vulnerability query optimization
CREATE INDEX CONCURRENTLY idx_vuln_scan ON scans_app_vulnerability(scan_id);
CREATE INDEX CONCURRENTLY idx_vuln_severity ON scans_app_vulnerability(severity);
CREATE INDEX CONCURRENTLY idx_vuln_detected ON scans_app_vulnerability(detected_at);
```

#### JSONB Fields for Flexible Data
```python
# Using PostgreSQL JSONB for dynamic vulnerability data
class Vulnerability(models.Model):
    # ... other fields ...
    technical_details = models.JSONField(default=dict)  # Raw scan data
    custom_fields = models.JSONField(default=dict)      # User-added data
    references = models.JSONField(default=list)         # URL references
```

## 🔄 Data Flow

### Scan Execution Pipeline
1. **User Initiation**: Frontend sends scan request to `/api/scans/`
2. **Task Creation**: Backend creates Scan record and queues Celery task
3. **Async Processing**: Celery worker executes scanning logic
4. **Progress Updates**: Real-time progress updates via task state
5. **Result Storage**: Vulnerabilities stored in database with JSONB fields
6. **Frontend Polling**: Frontend polls for progress and final results
7. **Report Generation**: On-demand report generation in multiple formats

### Authentication Flow
1. **Login/Register**: User credentials validated, JWT token generated
2. **Cookie Setting**: Token stored in HTTP-only, Secure cookie
3. **Request Authentication**: Middleware validates token on each request
4. **Automatic Refresh**: Token refresh handled transparently
5. **Logout**: Cookie cleared on server and client

## 🚀 Deployment Architecture

### Development Environment
```
Development Stack:
├── Django Development Server (port 8000)
├── React Vite Dev Server (port 5173)
├── PostgreSQL Database (port 5432)
├── Redis Server (port 6379)
└── Celery Worker Processes
```

### Production Environment
```
Production Stack:
├── Nginx (Reverse Proxy + SSL Termination)
├── Gunicorn (WSGI Application Server)
├── PostgreSQL with Connection Pooling
├── Redis with Persistence
├── Celery Workers with Autoscaling
├── Docker Containerization
└── Cloud Storage for Media Files
```

### Docker Architecture
```yaml
# docker-compose.yml
services:
  web:
    build: ./backend
    ports: ["8000:8000"]
    depends_on:
      - db
      - redis
  
  frontend:
    build: ./frontend
    ports: ["5173:5173"]
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: vulnscan
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
  
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
  
  worker:
    build: ./backend
    command: celery -A vulnscanner worker --loglevel=info -Q scans
    depends_on:
      - db
      - redis
```

## 📈 Scalability Considerations

### Horizontal Scaling Strategies
- **Stateless API Design**: No server-side sessions, enables multiple backend instances
- **Database Connection Pooling**: PgBouncer for PostgreSQL connection management
- **Redis Cluster**: For distributed session and cache storage
- **Load Balancer**: Nginx or cloud load balancer for traffic distribution
- **CDN Integration**: For static assets and media files

### Performance Optimizations
- **Database Query Optimization**: Selective field loading, prefetching related objects
- **Caching Strategy**: Redis caching for frequent queries and report generation
- **Background Processing**: Celery for all resource-intensive operations
- **Asset Optimization**: Frontend code splitting and lazy loading
- **Database Indexing**: Comprehensive indexing strategy for query performance

### Monitoring and Observability
- **Application Metrics**: Response times, error rates, throughput
- **Database Performance**: Query performance, connection pool usage
- **Celery Monitoring**: Task queue lengths, worker performance
- **Infrastructure Metrics**: CPU, memory, disk I/O, network usage
- **Business Metrics**: User activity, scan volumes, vulnerability trends

## 🔮 Future Architecture Enhancements

### Planned Technical Improvements
- [ ] **Real-time WebSocket** integration for live progress updates
- [ ] **Microservices Split** for scanning engine and user management
- [ ] **Advanced Caching** with Redis Cluster for distributed caching
- [ ] **API Gateway** for request routing and rate limiting
- [ ] **Message Queue** upgrade to RabbitMQ for complex workflows

### Feature Roadmap
- [ ] **Plugin System** for extensible scanning capabilities
- [ ] **Team Collaboration** features with role-based access
- [ ] **Advanced Reporting** with custom templates and branding
- [ ] **API Rate Limiting** with tiered access levels
- [ ] **Mobile Application** with React Native

This architecture provides a solid foundation for the VulnScan educational vulnerability scanner while maintaining flexibility for future enhancements and scalability requirements.
