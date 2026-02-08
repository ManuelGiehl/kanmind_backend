"""
Auth API Views.

Endpoints for registration, login (token-based), and email check.
"""

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegistrationSerializer

User = get_user_model()


class RegistrationView(APIView):
    """
    POST /api/registration/.

    Creates a new user. No auth required.
    Returns token, fullname, email, user_id (201).
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Validate input, create user and token, return auth payload."""
        serializer = RegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        fullname = _build_fullname(user)

        return Response(
            {
                "token": token.key,
                "fullname": fullname,
                "email": user.email,
                "user_id": user.pk,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    POST /api/login/.

    Authenticates user and returns token and user info. No auth required.
    Returns token, fullname, email, user_id (200).
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Validate credentials, return token and user payload or 400."""
        serializer = LoginSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        fullname = _build_fullname(user)

        return Response(
            {
                "token": token.key,
                "fullname": fullname,
                "email": user.email,
                "user_id": user.pk,
            },
            status=status.HTTP_200_OK,
        )


def _build_fullname(user):
    """Return user full name from first_name + last_name, fallback to username."""
    full = f"{user.first_name} {user.last_name}".strip()
    return full or user.username


class EmailCheckView(APIView):
    """
    GET /api/email-check/?email=...

    Checks if the email is already registered. Requires auth.
    Returns user id, email, fullname (200) or 404 if not found.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return user by email or 400/404."""
        email = request.query_params.get("email", "").strip()
        if not email:
            return Response(
                {"detail": "Email address missing or invalid format."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            validate_email(email)
        except ValidationError:
            return Response(
                {"detail": "Email address missing or invalid format."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return Response(
                {"detail": "Email not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {
                "id": user.pk,
                "email": user.email,
                "fullname": _build_fullname(user),
            },
            status=status.HTTP_200_OK,
        )
