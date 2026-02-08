"""
Tasks API Serializers.

Explicit fields for task list/detail (checklist: no __all__).
"""

from django.db.models import Count

from rest_framework import serializers

from tasks_app.models import Task


def _user_fullname(user):
    """Return full name from first_name + last_name, fallback to username."""
    if not user:
        return None
    full = f"{user.first_name} {user.last_name}".strip()
    return full or user.username


class UserMiniSerializer(serializers.Serializer):
    """Minimal user for assignee/reviewer: id, email, fullname."""

    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    fullname = serializers.SerializerMethodField()

    def get_fullname(self, obj):
        return _user_fullname(obj)


class TaskAssignedSerializer(serializers.Serializer):
    """
    Task in assigned-to-me list: id, board, title, description, status,
    priority, assignee, reviewer, due_date, comments_count.
    """

    id = serializers.IntegerField(read_only=True)
    board = serializers.IntegerField(read_only=True, source="board_id")
    title = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True, allow_blank=True)
    status = serializers.CharField(read_only=True)
    priority = serializers.CharField(read_only=True)
    assignee = UserMiniSerializer(read_only=True, allow_null=True)
    reviewer = UserMiniSerializer(read_only=True, allow_null=True)
    due_date = serializers.DateField(
        format="%Y-%m-%d", read_only=True, allow_null=True
    )
    comments_count = serializers.IntegerField(read_only=True, default=0)
