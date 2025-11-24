```python
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
- Authentication: register, login, logout
- Profile Management: profile, profile/name, profile/photo  
- Security Operations: profile/change-password, profile/delete-account

API Versioning:
Currently using unversioned endpoints. For production applications,
consider adding versioning (e.g., /api/v1/auth/register) for backward compatibility.
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
    
    path("register", 
         RegisterView.as_view(), 
         name="register",
         help_text="Create new user account with email and password"),
    
    path("login",    
         LoginView.as_view(),    
         name="login",
         help_text="Authenticate user and set JWT cookie"),
    
    path("logout",   
         LogoutView.as_view(),   
         name="logout",
         help_text="Invalidate JWT token and clear authentication cookie"),
    
    path("profile",  
         ProfileView.as_view(),  
         name="profile",
         help_text="Get current user profile information"),
    
    # =========================================================================
    # SECURITY ENDPOINTS
    # =========================================================================
    
    path("profile/change-password", 
         ChangePasswordView.as_view(), 
         name="profile-change-password",
         help_text="Change user password with current password verification"),
    
    path("profile/delete-account",  
         DeleteAccountView.as_view(),  
         name="profile-delete-account",
         help_text="Permanently delete user account with safety confirmations"),
    
    # =========================================================================
    # PROFILE MANAGEMENT ENDPOINTS
    # =========================================================================
    
    path("profile/photo", 
         ProfilePhotoView.as_view(), 
         name="profile-photo",
         help_text="Upload or update user profile picture"),
    
    path("profile/name",  
         ProfileNameView.as_view(),  
         name="profile-name",
         help_text="Update user's first and last names"),
]

"""
Complete API Endpoint Reference:

Authentication Routes:
POST   /api/auth/register                 - User registration
POST   /api/auth/login                    - User authentication  
POST   /api/auth/logout                   - User logout
GET    /api/auth/profile                  - Get user profile

Security Routes:
POST   /api/auth/profile/change-password  - Change account password
POST   /api/auth/profile/delete-account   - Delete user account

Profile Management Routes:
POST   /api/auth/profile/photo            - Upload profile photo
POST   /api/auth/profile/name             - Update profile names

Request/Response Examples:

Registration:
  POST /api/auth/register
  Body: {"firstName": "John", "lastName": "Doe", "email": "john@example.com", "password": "Secure123!"}
  Response: 201 Created with user data

Login:
  POST /api/auth/login  
  Body: {"email": "john@example.com", "password": "Secure123!"}
  Response: 200 OK with user data + Set-Cookie: auth_token

Profile:
  GET /api/auth/profile
  Response: 200 OK with {"userId": "u_1", "email": "john@example.com", ...}

Authentication Requirements:
- Register, Login: Public endpoints (no authentication required)
- All other endpoints: Require valid JWT token in cookie

Error Handling:
- 400 Bad Request: Invalid input data
- 401 Unauthorized: Missing or invalid authentication
- 403 Forbidden: Valid token but insufficient permissions  
- 404 Not Found: Resource not found
- 409 Conflict: Email already registered

Rate Limiting Considerations:
- Register: 5 attempts per hour per IP
- Login: 10 attempts per hour per IP  
- Password changes: 5 attempts per hour per user
- Consider implementing django-ratelimit for production

Future Enhancements:
- Password reset endpoints (/api/auth/password-reset)
- Email verification endpoints (/api/auth/verify-email)
- Two-factor authentication endpoints
- Session management endpoints
- OAuth2 integration endpoints

Testing URLs:
- Use Django test client or tools like Postman
- Test authentication flow: register → login → protected endpoint → logout
- Verify error responses for invalid inputs
- Test file upload for profile photos
"""
```
