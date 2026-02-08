"""
Board API URL routes.

Maps board endpoints under /api/boards/ (resource-oriented).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import BoardViewSet

app_name = "board_api"

router = DefaultRouter()
router.register(r"", BoardViewSet, basename="board")
urlpatterns = [path("", include(router.urls))]
