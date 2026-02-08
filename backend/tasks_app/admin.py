"""
Tasks app admin.
"""

from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "board", "status", "priority")
    list_filter = ("board", "status", "priority")
