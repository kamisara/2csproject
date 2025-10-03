from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.contrib.auth.models import User
from .jwt_utils import decode_jwt

class CookieJWTAuthentication(BaseAuthentication):
    """
    Authenticate using a JWT stored in the 'auth_token' cookie.
    """

    def authenticate(self, request):
        token = request.COOKIES.get("auth_token")
        if not token:
            return None  # no credentials provided

        try:
            payload = decode_jwt(token)
        except Exception as e:
            raise exceptions.AuthenticationFailed("Invalid or expired token")

        user_id = payload.get("user_id")
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found")

        return (user, token)
