"""
Board API Serializers.

Explicit fields for list/detail (checklist: no __all__).
"""

from rest_framework import serializers


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
