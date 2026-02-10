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

from .permissions import (
    IsBoardMemberForTaskComments,
    IsCommentCreator,
    IsBoardMemberForTaskUpdate,
    IsTaskCreatorOrBoardOwnerForDelete,
    user_can_create_task_on_board,
)
from .serializers import (
    CommentCreateSerializer,
    CommentListSerializer,
    TaskAssignedSerializer,
    TaskCreateSerializer,
    TaskUpdateSerializer,
)

def _task_response_payload(task):
    """Return serialized task with comments_count for API response."""
    qs = (
        Task.objects.filter(pk=task.pk)
        .select_related("assignee", "reviewer")
        .annotate(comments_count=Count("comments"))
    )
    return TaskAssignedSerializer(qs.first()).data

def _task_create_context(request, board_id):
    """Return context dict with board or 403/404 Response. Board may be None."""
    if board_id is None:
        return {}
    board = get_object_or_404(Board, pk=board_id)
    if not user_can_create_task_on_board(request.user, board):
        return Response(
            {"detail": "You must be a member of the board to create a task."},
            status=403,
        )
    return {"board": board}

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
        context = _task_create_context(request, data.get("board"))
        if isinstance(context, Response):
            return context
        serializer = TaskCreateSerializer(data=data, context=context)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        task = serializer.save()
        task.creator = request.user
        task.save(update_fields=["creator"])
        return Response(_task_response_payload(task), status=201)

class TaskUpdateView(APIView):
    """
    PATCH /api/tasks/<task_id>/: update (board member).
    DELETE /api/tasks/<task_id>/: delete (creator or board owner only).
    """

    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "PATCH":
            return [IsAuthenticated(), IsBoardMemberForTaskUpdate()]
        if self.request.method == "DELETE":
            return [IsAuthenticated(), IsTaskCreatorOrBoardOwnerForDelete()]
        return [IsAuthenticated()]

    def patch(self, request, task_id):
        """Partial update; return 200 with full task or 400/403/404."""
        task = get_object_or_404(Task, pk=task_id)
        serializer = TaskUpdateSerializer(
            task, data=request.data, partial=True, context={"task": task}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        serializer.save()
        return Response(_task_response_payload(task), status=200)

    def delete(self, request, task_id):
        """Delete task; 204 no content, 403 not allowed, 404 not found."""
        task = get_object_or_404(Task, pk=task_id)
        task.delete()
        return Response(status=204)

class TaskCommentsListView(APIView):
    """
    GET /api/tasks/<task_id>/comments/: list (board member).
    POST /api/tasks/<task_id>/comments/: create (board member); author from auth.
    """

    permission_classes = [IsAuthenticated, IsBoardMemberForTaskComments]

    def get(self, request, task_id):
        """Return comments for task; 403 if not board member, 404 if no task."""
        task = get_object_or_404(Task, pk=task_id)
        qs = task.comments.select_related("user").order_by("created_at")
        serializer = CommentListSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request, task_id):
        """Create comment; 201 with comment, 400/403/404 as per docs."""
        task = get_object_or_404(Task, pk=task_id)
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

    permission_classes = [IsAuthenticated, IsCommentCreator]

    def delete(self, request, task_id, comment_id):
        """Delete comment; 204 no content, 403 not creator, 404 task/comment not found."""
        get_object_or_404(Task, pk=task_id)
        comment = get_object_or_404(Comment, pk=comment_id, task_id=task_id)
        comment.delete()
        return Response(status=204)
