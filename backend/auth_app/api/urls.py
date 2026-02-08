"""
Auth API URL routes.

Maps registration, login, and email-check endpoints under /api/.
"""
from django.urls import path

from .views import EmailCheckView, LoginView, RegistrationView

app_name = "auth_api"

urlpatterns = [
    path("registration/", RegistrationView.as_view()),
    path("login/", LoginView.as_view()),
    path("email-check/", EmailCheckView.as_view()),
]
