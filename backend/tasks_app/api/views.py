"""
Tasks API Views.

GET /api/tasks/assigned-to-me/: tasks where user is assignee or reviewer.
GET /api/tasks/reviewing/: tasks where user is reviewer.
POST /api/tasks/: create task (user must be board member).
PATCH /api/tasks/<id>/: update task (user must be board member).
DELETE /api/tasks/<id>/: delete task (creator or board owner only).
GET /api/tasks/<id>/comments/: list comments (board member only).
DELETE /api/tasks/<id>/comments/<comment_id>/: delete comment (creator only).
"""

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from board_app.models import Board
from tasks_app.models import Comment, Task

from .serializers import (
    CommentCreateSerializer,
    CommentListSerializer,
    TaskAssignedSerializer,
    TaskCreateSerializer,
    TaskUpdateSerializer,
    _user_can_create_task_on_board,
)


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


class TaskCreateView(APIView):
    """
    POST /api/tasks/.

    Create a task. User must be a member of the board. 201 created;
    400 invalid data; 401 unauthenticated; 403 not board member; 404 board not found.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create task; return 201 with full task or 400/403/404."""
        data = request.data
        board_id = data.get("board")
        context = {}
        if board_id is not None:
            board = get_object_or_404(Board, pk=board_id)
            if not _user_can_create_task_on_board(request.user, board):
                return Response(
                    {"detail": "You must be a member of the board to create a task."},
                    status=403,
                )
            context["board"] = board
        serializer = TaskCreateSerializer(data=data, context=context)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        task = serializer.save()
        task.creator = request.user
        task.save(update_fields=["creator"])
        qs = (
            Task.objects.filter(pk=task.pk)
            .select_related("assignee", "reviewer")
            .annotate(comments_count=Count("comments"))
        )
        payload = TaskAssignedSerializer(qs.first()).data
        return Response(payload, status=201)


def _user_can_delete_task(user, task):
    """True if user is task creator or board owner."""
    if task.board.owner_id == user.id:
        return True
    if task.creator_id is not None and task.creator_id == user.id:
        return True
    return False


class TaskUpdateView(APIView):
    """
    PATCH /api/tasks/<task_id>/: update (board member).
    DELETE /api/tasks/<task_id>/: delete (creator or board owner only).
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, task_id):
        """Partial update; return 200 with full task or 400/403/404."""
        task = get_object_or_404(Task, pk=task_id)
        if not _user_can_create_task_on_board(request.user, task.board):
            return Response(
                {"detail": "You must be a member of the board to update this task."},
                status=403,
            )
        serializer = TaskUpdateSerializer(
            task, data=request.data, partial=True, context={"task": task}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        serializer.save()
        qs = (
            Task.objects.filter(pk=task.pk)
            .select_related("assignee", "reviewer")
            .annotate(comments_count=Count("comments"))
        )
        payload = TaskAssignedSerializer(qs.first()).data
        return Response(payload, status=200)

    def delete(self, request, task_id):
        """Delete task; 204 no content, 403 not allowed, 404 not found."""
        task = get_object_or_404(Task, pk=task_id)
        if not _user_can_delete_task(request.user, task):
            return Response(
                {"detail": "Only the creator of the task or the board owner can delete it."},
                status=403,
            )
        task.delete()
        return Response(status=204)


def _get_task_and_check_board_member(request, task_id):
    """Return (task, None) or (None, error_response). 403 or 404."""
    task = get_object_or_404(Task, pk=task_id)
    if not _user_can_create_task_on_board(request.user, task.board):
        return None, Response(
            {"detail": "You must be a member of the board to access comments."},
            status=403,
        )
    return task, None


class TaskCommentsListView(APIView):
    """
    GET /api/tasks/<task_id>/comments/: list (board member).
    POST /api/tasks/<task_id>/comments/: create (board member); author from auth.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        """Return comments for task; 403 if not board member, 404 if no task."""
        task, err = _get_task_and_check_board_member(request, task_id)
        if err is not None:
            return err
        qs = task.comments.select_related("user").order_by("created_at")
        serializer = CommentListSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request, task_id):
        """Create comment; 201 with comment, 400/403/404 as per docs."""
        task, err = _get_task_and_check_board_member(request, task_id)
        if err is not None:
            return err
        serializer = CommentCreateSerializer(
            data=request.data,
            context={"task": task, "user": request.user},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        comment = serializer.save()
        payload = CommentListSerializer(comment).data
        return Response(payload, status=201)


class TaskCommentDetailView(APIView):
    """
    DELETE /api/tasks/<task_id>/comments/<comment_id>/.

    Delete a comment. Only the comment creator can delete. 204; 403/404 as per docs.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, task_id, comment_id):
        """Delete comment; 204 no content, 403 not creator, 404 task/comment not found."""
        get_object_or_404(Task, pk=task_id)
        comment = get_object_or_404(Comment, pk=comment_id, task_id=task_id)
        if comment.user_id != request.user.id:
            return Response(
                {"detail": "Only the creator of the comment can delete it."},
                status=403,
            )
        comment.delete()
        return Response(status=204)
