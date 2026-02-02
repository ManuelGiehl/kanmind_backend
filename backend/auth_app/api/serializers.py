"""
Auth API Serializers.

Serializers for registration and login requests/responses.
"""

from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

User = get_user_model()


class RegistrationSerializer(serializers.Serializer):
    """
    Serializer for POST /api/registration/.

    Creates a new user. Fields: fullname, email, password, repeated_password.
    """

    fullname = serializers.CharField(max_length=150, write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(
        max_length=128, write_only=True, style={"input_type": "password"}
    )
    repeated_password = serializers.CharField(
        max_length=128, write_only=True, style={"input_type": "password"}
    )

    def validate_email(self, value):
        """Ensure email is not already registered."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "Ein Benutzer mit dieser E-Mail existiert bereits."
            )
        return value

    def validate(self, attrs):
        """Ensure password and repeated_password match."""
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError(
                {"repeated_password": "Die Passwörter stimmen nicht überein."}
            )
        return attrs

    def create(self, validated_data):
        """Create user with email as username; split fullname into first/last."""
        fullname = validated_data["fullname"].strip()
        parts = fullname.split(maxsplit=1)
        first_name = parts[0] if parts else ""
        last_name = parts[1] if len(parts) > 1 else ""

        return User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=first_name,
            last_name=last_name,
        )


class LoginSerializer(serializers.Serializer):
    """
    Serializer for POST /api/login/.

    Authenticates by email and password. Fields: email, password.
    Puts authenticated user in validated_data["user"].
    """

    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(
        max_length=128, write_only=True, style={"input_type": "password"}
    )

    def validate(self, attrs):
        """Authenticate user; attach user to attrs or raise ValidationError."""
        request = self.context.get("request")
        user = authenticate(
            request,
            username=attrs["email"],
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError(
                "Ungültige E-Mail oder Passwort."
            )
        attrs["user"] = user
        return attrs
