from django.contrib.auth.models import User
from rest_framework import serializers
from django.utils import timezone


class RegisterSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source="first_name")
    lastName = serializers.CharField(source="last_name")
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("firstName", "lastName", "email", "password")

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value

    def create(self, validated_data):
        first = validated_data.get("first_name", "")
        last = validated_data.get("last_name", "")
        email = validated_data.get("email")
        password = validated_data.get("password")
        # Use email as username to avoid having to change AUTH_USER_MODEL
        user = User.objects.create_user(username=email, email=email, password=password,
                                        first_name=first, last_name=last)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ProfileSerializer(serializers.ModelSerializer):
    userId = serializers.SerializerMethodField()
    firstName = serializers.CharField(source="first_name")
    lastName = serializers.CharField(source="last_name")
    createdAt = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("userId", "email", "firstName", "lastName", "createdAt")

    def get_userId(self, obj):
        return f"u_{obj.id}"

    def get_createdAt(self, obj):
        # User model does not have created_at by default; fallback to last_login or now
        # If you add a creation timestamp in a custom model, read that instead.
        return (obj.date_joined.isoformat() if hasattr(obj, "date_joined") else timezone.now().isoformat())
