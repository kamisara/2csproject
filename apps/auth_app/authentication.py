```python
"""
JWT Authentication middleware for VulnScan API.

This module provides custom JWT authentication using HTTP-only cookies
for enhanced security compared to traditional header-based token approaches.

Key Features:
- Extracts JWT tokens from 'auth_token' HTTP-only cookies
- Validates token signature and expiration
- Retrieves user from database based on token payload
- Provides seamless integration with Django REST Framework
- Enhances security by preventing XSS token theft

Security Benefits:
- HTTP-only cookies prevent JavaScript access (XSS protection)
- Automatic token inclusion in same-origin requests
- Secure flag ensures HTTPS-only transmission in production
- SameSite=Strict prevents CSRF attacks

Dependencies:
- Requires JWT utility functions from apps.auth_app.jwt_utils
- Integrates with Django's User model for authentication
"""

from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.contrib.auth.models import User
from apps.auth_app.jwt_utils import decode_jwt


class CookieJWTAuthentication(BaseAuthentication):
    """
    Custom JWT authentication class that uses HTTP-only cookies for token storage.
    
    This authentication method provides enhanced security by storing JWT tokens
    in HTTP-only cookies, making them inaccessible to client-side JavaScript
    and protecting against XSS attacks while maintaining stateless authentication.
    
    Authentication Flow:
    1. Extract JWT token from 'auth_token' cookie
    2. Decode and validate token using JWT utility functions
    3. Retrieve user from database based on user_id in token payload
    4. Return authenticated user or raise appropriate exception
    
    Usage:
    - Add to DEFAULT_AUTHENTICATION_CLASSES in settings.py
    - Requires 'auth_token' cookie to be set after login
    - Automatically handles token validation on each request
    """

    def authenticate(self, request):
        """
        Authenticate the request using JWT token from HTTP-only cookie.
        
        Args:
            request: HTTP request object containing cookies
            
        Returns:
            tuple: (user, token) if authentication successful
            None: if no credentials provided (allowing other auth methods)
            
        Raises:
            AuthenticationFailed: If token is invalid, expired, or user not found
            PermissionDenied: If user account is inactive or banned
            
        Example:
            >>> authentication = CookieJWTAuthentication()
            >>> user, token = authentication.authenticate(request)
        """
        # Extract JWT token from 'auth_token' cookie
        token = request.COOKIES.get("auth_token")
        
        # Return None if no token provided (allow other auth methods to try)
        if not token:
            return None

        try:
            # Decode and validate JWT token
            # This verifies signature and checks expiration
            payload = decode_jwt(token)
        except Exception as e:
            # Token is invalid, expired, or tampered with
            raise exceptions.AuthenticationFailed("Invalid or expired authentication token")

        # Extract user_id from token payload
        user_id = payload.get("user_id")
        if not user_id:
            raise exceptions.AuthenticationFailed("Invalid token payload: missing user_id")

        try:
            # Retrieve user from database using ID from token
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            # User was deleted or doesn't exist anymore
            raise exceptions.AuthenticationFailed("User account not found")

        # Optional: Check if user is active
        if not user.is_active:
            raise exceptions.AuthenticationFailed("User account is deactivated")

        # Return authenticated user and token
        # The token can be used for additional validation if needed
        return (user, token)

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response.
        
        This method is required by DRF BaseAuthentication class and
        provides the authentication scheme for the challenge.
        
        Args:
            request: HTTP request object
            
        Returns:
            str: Authentication scheme identifier
        """
        return 'Cookie realm="api"'

"""
Integration Notes:

1. Settings Configuration:
   Add to REST_FRAMEWORK settings in settings.py:
   
   REST_FRAMEWORK = {
       'DEFAULT_AUTHENTICATION_CLASSES': [
           'apps.auth_app.authentication.CookieJWTAuthentication',
       ],
   }

2. Cookie Requirements:
   - Name: 'auth_token'
   - Flags: HttpOnly, Secure, SameSite=Strict
   - Set via response.set_cookie() after successful login

3. Security Considerations:
   - Tokens have expiration (typically 24 hours)
   - Automatic token refresh can be implemented
   - Logout clears the cookie on client and server
   - Regular token rotation is recommended

4. Error Handling:
   - 401 Unauthorized: Invalid/missing token
   - 403 Forbidden: Valid token but insufficient permissions
   - 400 Bad Request: Malformed token (rare)

Example Token Payload:
{
    "user_id": 123,
    "email": "user@example.com",
    "exp": 1698765432,
    "iat": 1698679032
}

Alternative Approaches Considered:
- Header-based tokens (less secure, vulnerable to XSS)
- Session-based authentication (stateful, requires server storage)
- OAuth2/OpenID Connect (more complex, for enterprise use)
"""
```  
