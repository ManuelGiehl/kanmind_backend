"""
Board API Permissions.

Custom permission classes for board endpoints.
"""
from rest_framework import permissions


def user_can_access_board(user, board):
    """True if user is owner or member of the board."""
    if board.owner_id == user.pk:
        return True
    return board.members.filter(user=user).exists()


def user_is_board_owner(user, board):
    """True if user is the owner of the board."""
    return board.owner_id == user.pk


class IsBoardOwner(permissions.BasePermission):
    """
    Object-level: allow only the board owner.
    Use for destroy (delete board).
    """

    def has_object_permission(self, request, view, obj):
        return user_is_board_owner(request.user, obj)
