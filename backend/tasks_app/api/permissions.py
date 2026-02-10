"""
Tasks API Permissions.

Helpers and permission classes for task/comment endpoints.
"""
from rest_framework import permissions

from board_app.models import BoardMember
from tasks_app.models import Comment, Task

def user_can_create_task_on_board(user, board):
    """True if user is board owner or a board member."""
    if board.owner_id == user.id:
        return True
    return BoardMember.objects.filter(board=board, user=user).exists()

def user_is_board_member(user_id, board):
    """True if user is board owner or a board member."""
    if board.owner_id == user_id:
        return True
    return BoardMember.objects.filter(board=board, user_id=user_id).exists()

def user_can_delete_task(user, task):
    """True if user is task creator or board owner."""
    if task.board.owner_id == user.id:
        return True
    if task.creator_id is not None and task.creator_id == user.id:
        return True
    return False

def user_can_delete_comment(user, comment):
    """True if user is the comment creator."""
    return comment.user_id == user.id

class IsBoardMemberForTask(permissions.BasePermission):
    """
    Object-level: allow if user is member or owner of the task's board.
    Use for task PATCH (update).
    """

    def has_object_permission(self, request, view, obj):
        return user_can_create_task_on_board(request.user, obj.board)

class IsTaskCreatorOrBoardOwner(permissions.BasePermission):
    """
    Object-level: allow if user is task creator or board owner.
    Use for task DELETE.
    """

    def has_object_permission(self, request, view, obj):
        return user_can_delete_task(request.user, obj)

class IsBoardMemberForTaskUpdate(permissions.BasePermission):
    """
    Request-level: allow if user is member or owner of the task's board.
    Reads task_id from view.kwargs. Use for task PATCH.
    """

    def has_permission(self, request, view):
        task_id = view.kwargs.get("task_id")
        if not task_id:
            return False
        task = Task.objects.filter(pk=task_id).first()
        if not task:
            return False
        return user_can_create_task_on_board(request.user, task.board)

class IsTaskCreatorOrBoardOwnerForDelete(permissions.BasePermission):
    """
    Request-level: allow if user is task creator or board owner.
    Reads task_id from view.kwargs. Use for task DELETE.
    """

    def has_permission(self, request, view):
        task_id = view.kwargs.get("task_id")
        if not task_id:
            return False
        task = Task.objects.filter(pk=task_id).first()
        if not task:
            return False
        return user_can_delete_task(request.user, task)

class IsBoardMemberForTaskComments(permissions.BasePermission):
    """
    Request-level: allow if user is member or owner of the task's board.
    Reads task_id from view.kwargs. Use for GET/POST comments.
    """

    def has_permission(self, request, view):
        task_id = view.kwargs.get("task_id")
        if not task_id:
            return False
        task = Task.objects.filter(pk=task_id).first()
        if not task:
            return False
        return user_can_create_task_on_board(request.user, task.board)

class IsCommentCreator(permissions.BasePermission):
    """
    Request-level: allow if user is the comment creator.
    Reads task_id, comment_id from view.kwargs. Use for DELETE comment.
    """

    def has_permission(self, request, view):
        task_id = view.kwargs.get("task_id")
        comment_id = view.kwargs.get("comment_id")
        if not task_id or not comment_id:
            return False
        comment = Comment.objects.filter(
            pk=comment_id, task_id=task_id
        ).first()
        if not comment:
            return False
        return user_can_delete_comment(request.user, comment)
