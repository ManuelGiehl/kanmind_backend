"""
Core URL configuration.

Central routing: admin and API app URLs are included here.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("auth_app.api.urls")),
    path("api/boards/", include("board_app.api.urls")),
    path("api/tasks/", include("tasks_app.api.urls")),
]
