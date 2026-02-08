"""
Board API Views.

GET /api/boards/: list boards. POST /api/boards/: create board with members.
"""

from django.db.models import Count, Q

from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from board_app.models import Board
from tasks_app.models import Task

from .serializers import BoardCreateSerializer, BoardListSerializer


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


class BoardViewSet(viewsets.ModelViewSet):
    """
    GET /api/boards/: list boards for the authenticated user.
    POST /api/boards/: create board (owner=request.user, optional members).
    """

    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        """Boards the user owns or is a member of, with annotated counts."""
        user = self.request.user
        base = Board.objects.filter(
            Q(owner=user) | Q(members__user=user)
        ).distinct()
        return _annotate_board_counts(base)

    def get_serializer_class(self):
        """Use create serializer for create, list serializer for list/retrieve."""
        if self.action == "create":
            return BoardCreateSerializer
        return BoardListSerializer

    def create(self, request, *args, **kwargs):
        """Create board and return 201 with same shape as list item."""
        serializer = BoardCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        board = serializer.save()
        annotated = _annotate_board_counts(Board.objects.filter(pk=board.pk)).first()
        out = BoardListSerializer(annotated).data
        return Response(out, status=status.HTTP_201_CREATED)
