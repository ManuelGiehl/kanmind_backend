"""
Board API Serializers.

Explicit fields for list/detail (checklist: no __all__).
"""

from django.contrib.auth import get_user_model

from rest_framework import serializers

from board_app.models import Board, BoardMember

User = get_user_model()


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
                "Ungültige Benutzer-IDs: " + ", ".join(str(pk) for pk in sorted(missing))
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
