"""
Auth API URL routes.

Maps registration and login endpoints under /api/.
"""
from django.urls import path

from .views import LoginView, RegistrationView

app_name = "auth_api"

urlpatterns = [
    path("registration/", RegistrationView.as_view()),
    path("login/", LoginView.as_view()),
]
