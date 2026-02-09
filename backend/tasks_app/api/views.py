"""
Tasks API Views.

GET /api/tasks/assigned-to-me/: tasks where user is assignee or reviewer.
GET /api/tasks/reviewing/: tasks where user is reviewer.
"""

from django.db.models import Count, Q

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tasks_app.models import Task

from .serializers import TaskAssignedSerializer


def _assigned_to_user_queryset(user):
    """Tasks where user is assignee or reviewer, with comments_count."""
    return (
        Task.objects.filter(Q(assignee=user) | Q(reviewer=user))
        .select_related("assignee", "reviewer")
        .annotate(comments_count=Count("comments"))
        .order_by("-id")
    )


def _reviewing_queryset(user):
    """Tasks where user is reviewer, with comments_count."""
    return (
        Task.objects.filter(reviewer=user)
        .select_related("assignee", "reviewer")
        .annotate(comments_count=Count("comments"))
        .order_by("-id")
    )


class AssignedToMeView(APIView):
    """
    GET /api/tasks/assigned-to-me/.

    Returns tasks assigned to the authenticated user as assignee or reviewer.
    Requires auth. 200 with list of tasks (id, board, title, description,
    status, priority, assignee, reviewer, due_date, comments_count).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return list of tasks for current user as assignee or reviewer."""
        qs = _assigned_to_user_queryset(request.user)
        serializer = TaskAssignedSerializer(qs, many=True)
        return Response(serializer.data)


class ReviewingView(APIView):
    """
    GET /api/tasks/reviewing/.

    Returns tasks where the authenticated user is the reviewer.
    Requires auth. 200 with list of tasks; 401 if not logged in.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return list of tasks for current user as reviewer."""
        qs = _reviewing_queryset(request.user)
        serializer = TaskAssignedSerializer(qs, many=True)
        return Response(serializer.data)
