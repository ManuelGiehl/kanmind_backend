"""
Tasks API URL routes.

Maps task endpoints under /api/tasks/ (resource-oriented).
"""
from django.urls import path

from .views import (
    AssignedToMeView,
    ReviewingView,
    TaskCreateView,
    TaskUpdateView,
)

app_name = "tasks_api"

urlpatterns = [
    path("assigned-to-me/", AssignedToMeView.as_view()),
    path("reviewing/", ReviewingView.as_view()),
    path("<int:task_id>/", TaskUpdateView.as_view()),
    path("", TaskCreateView.as_view()),
]
