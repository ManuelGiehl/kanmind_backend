"""
Board API Serializers.

Explicit fields for list/detail (checklist: no __all__).
"""

from django.contrib.auth import get_user_model
from django.db.models import Count

from rest_framework import serializers

from board_app.models import Board, BoardMember
from tasks_app.models import Task

User = get_user_model()


def _user_fullname(user):
    """Return full name from first_name + last_name, fallback to username."""
    if not user:
        return None
    full = f"{user.first_name} {user.last_name}".strip()
    return full or user.username


class UserMiniSerializer(serializers.Serializer):
    """Minimal user for members, assignee, reviewer: id, email, fullname."""

    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    fullname = serializers.SerializerMethodField()

    def get_fullname(self, obj):
        return _user_fullname(obj)


STATUS_MODEL_TO_API = {
    Task.Status.TO_DO: "to-do",
    Task.Status.IN_PROGRESS: "in-progress",
    Task.Status.REVIEW: "review",
    Task.Status.DONE: "done",
}


class TaskDetailSerializer(serializers.Serializer):
    """
    Task in board detail: id, title, description, status, priority,
    assignee, reviewer, due_date, comments_count.
    Status in API format (to-do, in-progress) for frontend columns.
    """

    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True, allow_blank=True)
    status = serializers.SerializerMethodField()
    priority = serializers.CharField(read_only=True)

    def get_status(self, obj):
        """Return API status format (e.g. to-do, in-progress) for frontend."""
        return STATUS_MODEL_TO_API.get(obj.status, obj.status)
    assignee = UserMiniSerializer(read_only=True, allow_null=True)
    reviewer = UserMiniSerializer(read_only=True, allow_null=True)
    due_date = serializers.DateField(
        format="%Y-%m-%d", read_only=True, allow_null=True
    )
    comments_count = serializers.IntegerField(read_only=True, default=0)


class BoardCreateSerializer(serializers.Serializer):
    """
    POST /api/boards/: create board with title and member user IDs.

    Owner is set from request.user; members are added as BoardMember.
    """

    title = serializers.CharField(max_length=255)
    members = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
        required=False,
        default=list,
    )

    def validate_members(self, value):
        """Ensure all member IDs are existing user IDs."""
        if not value:
            return value
        existing = set(User.objects.filter(pk__in=value).values_list("pk", flat=True))
        missing = set(value) - existing
        if missing:
            raise serializers.ValidationError(
                "Invalid user IDs: " + ", ".join(str(pk) for pk in sorted(missing))
            )
        return value

    def create(self, validated_data):
        """Create board with owner from request; add members as BoardMember."""
        request = self.context["request"]
        board = Board.objects.create(
            title=validated_data["title"],
            owner=request.user,
        )
        for user_id in validated_data.get("members") or []:
            if user_id != board.owner_id:
                BoardMember.objects.get_or_create(
                    board=board,
                    user_id=user_id,
                )
        return board


class BoardDetailSerializer(serializers.Serializer):
    """
    GET /api/boards/{id}/: board with members and tasks.

    Fields: id, title, owner_id, members (list of user mini), tasks (list).
    """

    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    owner_id = serializers.IntegerField(read_only=True)
    members = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()

    def get_members(self, obj):
        """Board members as list of {id, email, fullname}."""
        users = [m.user for m in obj.members.select_related("user")]
        return UserMiniSerializer(users, many=True).data

    def get_tasks(self, obj):
        """Tasks with assignee, reviewer, comments_count."""
        qs = obj.tasks.select_related("assignee", "reviewer").annotate(
            comments_count=Count("comments"),
        )
        return TaskDetailSerializer(qs, many=True).data


class BoardUpdateSerializer(serializers.Serializer):
    """
    PATCH /api/boards/{id}/: update title and/or members.

    Members list replaces current members (unmentioned are removed).
    """

    title = serializers.CharField(max_length=255, required=False)
    members = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
        required=False,
    )

    def validate_members(self, value):
        """Ensure all member IDs are existing user IDs."""
        if value is None:
            return value
        existing = set(User.objects.filter(pk__in=value).values_list("pk", flat=True))
        missing = set(value) - existing
        if missing:
            raise serializers.ValidationError(
                "Invalid user IDs: " + ", ".join(str(pk) for pk in sorted(missing))
            )
        return value

    def update(self, instance, validated_data):
        """Update board title and set members to given list (skip owner)."""
        if "title" in validated_data:
            instance.title = validated_data["title"]
            instance.save(update_fields=["title"])
        if "members" in validated_data:
            _set_board_members(instance, validated_data["members"])
        return instance


def _set_board_members(board, user_ids):
    """Set board members to exactly user_ids; remove others, skip owner."""
    board.members.exclude(user_id__in=user_ids).delete()
    for uid in user_ids or []:
        if uid != board.owner_id:
            BoardMember.objects.get_or_create(board=board, user_id=uid)


def board_patch_response_data(board):
    """Build PATCH response: id, title, owner_data, members_data."""
    board.refresh_from_db()
    owner = board.owner
    # Query members directly so response reflects current DB after PATCH update
    member_users = [
        m.user
        for m in BoardMember.objects.filter(board=board).select_related("user")
    ]
    return {
        "id": board.id,
        "title": board.title,
        "owner_data": UserMiniSerializer(owner).data,
        "members_data": UserMiniSerializer(member_users, many=True).data,
    }


class BoardListSerializer(serializers.Serializer):
    """
    Board list item for GET /api/boards/.

    Fields: id, title, member_count, ticket_count, tasks_to_do_count,
    tasks_high_prio_count, owner_id.
    """

    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    ticket_count = serializers.IntegerField(read_only=True)
    tasks_to_do_count = serializers.IntegerField(read_only=True)
    tasks_high_prio_count = serializers.IntegerField(read_only=True)
    owner_id = serializers.IntegerField(read_only=True)
