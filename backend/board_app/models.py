"""
Board app models.

Board: a project/kanban board owned by a user.
BoardMember: membership of a user on a board (owner is not a member row).
"""

from django.conf import settings
from django.db import models

class Board(models.Model):
    """
    A board (project). Has one owner; members are in BoardMember.
    """

    title = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_boards",
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "board"
        verbose_name_plural = "boards"

    def __str__(self):
        return self.title

class BoardMember(models.Model):
    """
    Membership of a user on a board (read/write access).
    Owner is not stored here; use Board.owner.
    """

    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name="members",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="board_memberships",
    )

    class Meta:
        ordering = ["board", "user"]
        unique_together = [["board", "user"]]
        verbose_name = "board member"
        verbose_name_plural = "board members"

    def __str__(self):
        return f"{self.user_id} on {self.board_id}"
