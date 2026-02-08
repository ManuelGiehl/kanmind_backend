"""
Board API Views.

GET /api/boards/: list boards the user owns or is member of (with counts).
"""

from django.db.models import Count, Q

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from board_app.models import Board
from tasks_app.models import Task

from .serializers import BoardListSerializer


def _annotate_board_counts(queryset):
    """Add member_count, ticket_count, tasks_to_do_count, tasks_high_prio_count."""
    return queryset.annotate(
        member_count=Count("members", distinct=True),
        ticket_count=Count("tasks", distinct=True),
        tasks_to_do_count=Count(
            "tasks",
            filter=Q(tasks__status=Task.Status.TO_DO),
            distinct=True,
        ),
        tasks_high_prio_count=Count(
            "tasks",
            filter=Q(tasks__priority=Task.Priority.HIGH),
            distinct=True,
        ),
    )


class BoardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/boards/: list boards for the authenticated user.

    Only boards where user is owner or member. Returns id, title,
    member_count, ticket_count, tasks_to_do_count, tasks_high_prio_count,
    owner_id. 401 if not logged in.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = BoardListSerializer

    def get_queryset(self):
        """Boards the user owns or is a member of, with annotated counts."""
        user = self.request.user
        base = Board.objects.filter(
            Q(owner=user) | Q(members__user=user)
        ).distinct()
        return _annotate_board_counts(base)
