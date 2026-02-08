"""
Tasks app models.

Task: a task/ticket on a board (status, priority for list counts).
"""

from django.conf import settings
from django.db import models


class Task(models.Model):
    """
    A task on a board. Used for ticket_count and status/priority counts.
    """

    class Status(models.TextChoices):
        TO_DO = "to_do", "To Do"
        IN_PROGRESS = "in_progress", "In Progress"
        DONE = "done", "Done"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    title = models.CharField(max_length=255)
    board = models.ForeignKey(
        "board_app.Board",
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TO_DO,
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "task"
        verbose_name_plural = "tasks"

    def __str__(self):
        return self.title
