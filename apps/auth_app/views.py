from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import authenticate
from .serializers import RegisterSerializer, LoginSerializer, ProfileSerializer
from .jwt_utils import create_jwt_for_user
from .authentication import CookieJWTAuthentication
from django.conf import settings
from django.utils import timezone

# Cookie settings: change Secure=True when deploying with HTTPS
AUTH_COOKIE_NAME = "auth_token"
AUTH_COOKIE_AGE = 7 * 24 * 60 * 60  # seconds (7 days)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # optional: auto-login — create token and set cookie
            token = create_jwt_for_user(user)
            response_data = {
                "user": {
                    "userId": f"u_{user.id}",
                    "email": user.email,
                    "firstName": user.first_name,
                    "lastName": user.last_name,
                    "createdAt": user.date_joined.isoformat() if hasattr(user, "date_joined") else timezone.now().isoformat()
                }
            }
            response = Response(response_data, status=status.HTTP_201_CREATED)
            response.set_cookie(
                AUTH_COOKIE_NAME,
                token,
                httponly=True,
                samesite="Strict",
                secure=False,  # set to True in production (HTTPS)
                max_age=AUTH_COOKIE_AGE,
                path="/",
            )
            return response
        else:
            # If email already exists, serializer will raise message -> map to 409
            if "email" in serializer.errors and any("already registered" in str(m) for m in serializer.errors["email"]):
                return Response({"error": {"code": 409, "message": "Email already registered"}}, status=409)
            return Response({"error": {"code": 400, "message": serializer.errors}}, status=400)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        # authenticate by username (we used email as username)
        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response({"error": {"code": 401, "message": "Invalid email or password"}}, status=401)

        token = create_jwt_for_user(user)
        response_data = {
            "user": {
                "userId": f"u_{user.id}",
                "email": user.email,
                "firstName": user.first_name,
                "lastName": user.last_name
            }
        }
        response = Response(response_data, status=200)
        response.set_cookie(
            AUTH_COOKIE_NAME,
            token,
            httponly=True,
            samesite="Strict",
            secure=False,  # set to True in prod
            max_age=AUTH_COOKIE_AGE,
            path="/",
        )
        return response


class LogoutView(APIView):
    """
    POST /logout -> clears auth cookie
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(AUTH_COOKIE_NAME, path="/")
        return response


class ProfileView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = ProfileSerializer(user)
        return Response({"user": serializer.data}, status=200)
