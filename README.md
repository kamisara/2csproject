# VulnScan - Educational Vulnerability Scanner

## 🛡️ Project Overview
VulnScan is a comprehensive educational web application designed for learning vulnerability scanning and security assessment techniques. It provides a beginner-friendly platform for conducting basic security analysis and understanding cybersecurity concepts.

## 🎯 Features
- **Port Scanning**: TCP port scanning with configurable parameters
- **Vulnerability Detection**: CVE integration with NVD database
- **User Authentication**: Secure JWT-based authentication system
- **Real-time Monitoring**: Live scan progress tracking
- **Report Generation**: Multi-format reports (PDF, HTML, JSON)
- **Responsive Design**: Mobile-friendly interface

## 🏗️ Architecture
- **Frontend**: React 19 + Vite + Tailwind CSS
- **Backend**: Django REST Framework + PostgreSQL
- **Task Queue**: Celery + Redis for background processing
- **Containerization**: Docker + Docker Compose
- **Authentication**: JWT with HTTP-only cookies

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for development)
- Python 3.12+ (for development)

### Using Docker (Recommended)
# Clone the repository
git clone https://github.com/your-username/vulnscan.git
cd vulnscan

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000

###Manual Development Setup

##Backend Setup
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
python manage.py migrate

# Start development server
python manage.py runserver

##Frontend Setup
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev


🔧 API Documentation
The backend provides a RESTful API with the following main endpoints:

Authentication: /api/auth/

User Management: /api/users/

Scan Management: /api/scans/

Report Generation: /api/reports/

For detailed API documentation, see API_DOCUMENTATION.md

🐳 Docker Services
web: Django backend application

frontend: React development server

redis: Message broker for Celery

worker: Celery worker for background tasks

db: PostgreSQL database

👥 Development Team
Sara Madaoui - Team Lead & Backend Development

Roufaida Madoui - Scanning Engine & Integration

Asma Belkerrouche - Report Generation & Backend API

Mouna Bouchenafa - Frontend Authentication & UI

Aya Teyar - Frontend Pages & User Interface

📚 Academic Context
This project was developed as part of the 2nd Year Computer Science program at the Higher School of Computer Science and Digital Technologies (ESTIN) under the supervision of Pr. Sebaa and M. Brahmi.

🔒 Security Note
This tool is designed for educational purposes only. Use only on systems you own or have explicit permission to test. The developers are not responsible for any misuse of this software.

📄 License
This project is developed for educational purposes as part of academic coursework.

🤝 Contributing
For development guidelines and contribution instructions, please refer to CONTRIBUTING.md


# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
