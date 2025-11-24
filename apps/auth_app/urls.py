"""
URL configuration for VulnScan authentication application.

This module defines all API endpoints for user authentication, profile management,
and account operations. The URLs are designed to follow RESTful conventions
while providing clear, descriptive endpoint names for frontend consumption.

Base Path: /api/auth/

Security Note:
- All endpoints except register and login require authentication
- JWT tokens are handled via HTTP-only cookies for enhanced security
- Password-related endpoints include additional security validations

Endpoint Groups:
- Authentication: register, login, logout, profile
- Security Operations: change-password, delete-account  
- Profile Management: name updates, photo uploads
"""

from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView, ProfileView,
    ChangePasswordView, DeleteAccountView,
    ProfilePhotoView, ProfileNameView
)

# Authentication application URL patterns
urlpatterns = [
    # =========================================================================
    # AUTHENTICATION ENDPOINTS
    # =========================================================================
    
    # User registration - creates new account and returns JWT token
    path("register", RegisterView.as_view(), name="register"),
    
    # User authentication - validates credentials and sets JWT cookie
    path("login", LoginView.as_view(), name="login"),
    
    # Session termination - clears authentication cookie
    path("logout", LogoutView.as_view(), name="logout"),
    
    # Profile retrieval - gets current user's profile information
    path("profile", ProfileView.as_view(), name="profile"),
    
    # =========================================================================
    # SECURITY ENDPOINTS
    # =========================================================================
    
    # Password change - requires current password verification
    path("profile/change-password", ChangePasswordView.as_view(), name="profile-change-password"),
    
    # Account deletion - requires multiple safety confirmations
    path("profile/delete-account", DeleteAccountView.as_view(), name="profile-delete-account"),
    
    # =========================================================================
    # PROFILE MANAGEMENT ENDPOINTS
    # =========================================================================
    
    # Avatar upload - handles profile picture upload and processing
    path("profile/photo", ProfilePhotoView.as_view(), name="profile-photo"),
    
    # Name updates - supports both snake_case and camelCase field names
    path("profile/name", ProfileNameView.as_view(), name="profile-name"),
]


"""
Complete API Endpoint Reference:

Authentication Routes (Public):
POST /api/auth/register     - User registration with automatic login
POST /api/auth/login        - User authentication with JWT cookie
POST /api/auth/logout       - Session termination
GET  /api/auth/profile      - Current user profile (requires authentication)

Security Routes (Authenticated):
POST /api/auth/profile/change-password  - Password change with verification
POST /api/auth/profile/delete-account   - Account deletion with confirmations

Profile Management Routes (Authenticated):
POST /api/auth/profile/photo  - Profile picture upload (multipart/form-data)
POST /api/auth/profile/name   - Update first and last names

Request/Response Examples:

Registration:
  POST /api/auth/register
  Body: {"firstName": "John", "lastName": "Doe", "email": "john@example.com", "password": "Secure123!"}
  Response: 201 Created with user data + auth_token cookie

Login:
  POST /api/auth/login  
  Body: {"email": "john@example.com", "password": "Secure123!"}
  Response: 200 OK with user data + auth_token cookie

Authentication Requirements:
- Public endpoints: register, login (no authentication required)
- Protected endpoints: All others require valid JWT token in cookie

Error Handling:
- 400: Bad request (validation errors)
- 401: Unauthorized (missing/invalid authentication)
- 403: Forbidden (valid token but insufficient permissions)
- 404: Not found
- 409: Conflict (email already registered)

Testing Strategy:
- Test full authentication flow: register → login → protected endpoint → logout
- Verify error responses for invalid inputs
- Test file upload functionality for profile photos
- Validate security endpoints with proper confirmations
"""
