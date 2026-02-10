"""
Board API Views.

GET /api/boards/: list. POST: create. PATCH: update. DELETE: delete (owner only).
"""

from django.db.models import Count, Q

from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from board_app.models import Board
from tasks_app.models import Task

from .permissions import IsBoardOwner
from .serializers import (
    BoardCreateSerializer,
    BoardDetailSerializer,
    BoardListSerializer,
    BoardUpdateSerializer,
    board_patch_response_data,
)

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
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAuthenticated(), IsBoardOwner()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Boards the user owns or is a member of, with annotated counts."""
        user = self.request.user
        base = Board.objects.filter(
            Q(owner=user) | Q(members__user=user)
        ).distinct()
        return _annotate_board_counts(base)

    def get_serializer_class(self):
        """Create/list/detail/update serializers by action."""
        if self.action == "create":
            return BoardCreateSerializer
        if self.action == "retrieve":
            return BoardDetailSerializer
        if self.action in ("partial_update", "update"):
            return BoardUpdateSerializer
        return BoardListSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        GET /api/boards/{id}/: board with members and tasks.

        404 if board not found, 403 if user is not owner or member.
        """
        board = self.get_object()
        serializer = BoardDetailSerializer(board)
        return Response(serializer.data, status=status.HTTP_200_OK)

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

    def partial_update(self, request, *args, **kwargs):
        """
        PATCH /api/boards/{id}/: update title and/or members.

        404 if board not found, 403 if not owner or member.
        Response: id, title, owner_data, members_data (200).
        """
        board = self.get_object()
        serializer = BoardUpdateSerializer(
            board, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            board_patch_response_data(board),
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        """
        DELETE /api/boards/{id}/: delete board (owner only).

        204 on success. 403 if not owner. 404 if board not found.
        Cascades: tasks and comments are removed.
        """
        board = self.get_object()
        board.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
