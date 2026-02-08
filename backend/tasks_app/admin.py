"""
Tasks app admin.
"""

from django.contrib import admin
from .models import Comment, Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "id", "title", "board", "status", "priority",
        "assignee", "reviewer", "due_date",
    )
    list_filter = ("board", "status", "priority")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "task", "user")
    list_filter = ("task",)
