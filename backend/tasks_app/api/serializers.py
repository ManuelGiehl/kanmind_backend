"""
Tasks API Serializers.

Explicit fields for task list/detail (checklist: no __all__).
"""

from django.db.models import Count

from rest_framework import serializers

from board_app.models import Board, BoardMember
from tasks_app.models import Comment, Task

STATUS_API_TO_MODEL = {
    "to-do": Task.Status.TO_DO,
    "in-progress": Task.Status.IN_PROGRESS,
    "review": Task.Status.REVIEW,
    "done": Task.Status.DONE,
}


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


class CommentListSerializer(serializers.Serializer):
    """Comment in list: id, created_at (ISO), author (full name), content."""

    id = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(
        read_only=True, format="%Y-%m-%dT%H:%M:%SZ"
    )
    author = serializers.SerializerMethodField()
    content = serializers.CharField(read_only=True, source="text")

    def get_author(self, obj):
        return _user_fullname(obj.user)


class CommentCreateSerializer(serializers.Serializer):
    """Create comment: content only; author from request.user."""

    content = serializers.CharField(allow_blank=False, trim_whitespace=True)

    def create(self, validated_data):
        """Create comment; task and user from context."""
        task = self.context["task"]
        user = self.context["user"]
        return Comment.objects.create(
            task=task,
            user=user,
            text=validated_data["content"],
        )


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


def _user_can_create_task_on_board(user, board):
    """True if user is board owner or a board member."""
    if board.owner_id == user.id:
        return True
    return BoardMember.objects.filter(board=board, user=user).exists()


def _user_is_board_member(user_id, board):
    """True if user is board owner or a board member."""
    if board.owner_id == user_id:
        return True
    return BoardMember.objects.filter(board=board, user_id=user_id).exists()


def _apply_task_update_fields(instance, validated_data):
    """Set instance fields from validated_data; map status API -> model."""
    if "title" in validated_data:
        instance.title = validated_data["title"]
    if "description" in validated_data:
        instance.description = validated_data["description"]
    if "status" in validated_data:
        instance.status = STATUS_API_TO_MODEL.get(
            validated_data["status"], validated_data["status"]
        )
    if "priority" in validated_data:
        instance.priority = validated_data["priority"]
    if "assignee_id" in validated_data:
        instance.assignee_id = validated_data["assignee_id"]
    if "reviewer_id" in validated_data:
        instance.reviewer_id = validated_data["reviewer_id"]
    if "due_date" in validated_data:
        instance.due_date = validated_data["due_date"]


class TaskCreateSerializer(serializers.Serializer):
    """
    Create task: board, title, description, status, priority,
    assignee_id, reviewer_id (optional), due_date (optional).
    """

    board = serializers.IntegerField(write_only=True)
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=list(STATUS_API_TO_MODEL.keys()))
    priority = serializers.ChoiceField(choices=[c[0] for c in Task.Priority.choices])
    assignee_id = serializers.IntegerField(required=False, allow_null=True)
    reviewer_id = serializers.IntegerField(required=False, allow_null=True)
    due_date = serializers.DateField(required=False, allow_null=True)

    def validate_board(self, value):
        """Use board from context (view already checked 404/403) or resolve."""
        if "board" in self.context:
            return self.context["board"]
        try:
            return Board.objects.get(pk=value)
        except Board.DoesNotExist:
            raise serializers.ValidationError("Board not found.")

    def validate(self, attrs):
        """Require assignee/reviewer to be board members if given."""
        board = attrs["board"]
        assignee_id = attrs.get("assignee_id")
        reviewer_id = attrs.get("reviewer_id")
        if assignee_id is not None and not _user_is_board_member(
            assignee_id, board
        ):
            raise serializers.ValidationError(
                {"assignee_id": "Assignee must be a member of the board."}
            )
        if reviewer_id is not None and not _user_is_board_member(
            reviewer_id, board
        ):
            raise serializers.ValidationError(
                {"reviewer_id": "Reviewer must be a member of the board."}
            )
        return attrs

    def create(self, validated_data):
        """Create task; status mapped from API to model values."""
        board = validated_data["board"]
        status_api = validated_data["status"]
        status_model = STATUS_API_TO_MODEL.get(
            status_api, validated_data["status"]
        )
        assignee_id = validated_data.get("assignee_id")
        reviewer_id = validated_data.get("reviewer_id")
        task = Task.objects.create(
            board=board,
            title=validated_data["title"],
            description=validated_data.get("description") or "",
            status=status_model,
            priority=validated_data["priority"],
            assignee_id=assignee_id,
            reviewer_id=reviewer_id,
            due_date=validated_data.get("due_date"),
        )
        return task


class TaskUpdateSerializer(serializers.Serializer):
    """
    Partial update: title, description, status, priority,
    assignee_id, reviewer_id, due_date. Board cannot be changed.
    """

    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(
        choices=list(STATUS_API_TO_MODEL.keys()), required=False
    )
    priority = serializers.ChoiceField(
        choices=[c[0] for c in Task.Priority.choices], required=False
    )
    assignee_id = serializers.IntegerField(required=False, allow_null=True)
    reviewer_id = serializers.IntegerField(required=False, allow_null=True)
    due_date = serializers.DateField(required=False, allow_null=True)

    def validate(self, attrs):
        """Require assignee/reviewer to be members of the task's board."""
        task = self.context["task"]
        board = task.board
        assignee_id = attrs.get("assignee_id")
        reviewer_id = attrs.get("reviewer_id")
        if assignee_id is not None and not _user_is_board_member(
            assignee_id, board
        ):
            raise serializers.ValidationError(
                {"assignee_id": "Assignee must be a member of the board."}
            )
        if reviewer_id is not None and not _user_is_board_member(
            reviewer_id, board
        ):
            raise serializers.ValidationError(
                {"reviewer_id": "Reviewer must be a member of the board."}
            )
        return attrs

    def update(self, instance, validated_data):
        """Apply partial update; map status from API to model values."""
        _apply_task_update_fields(instance, validated_data)
        instance.save()
        return instance
