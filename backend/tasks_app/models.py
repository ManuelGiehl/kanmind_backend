"""
Tasks app models.

Task: a task/ticket on a board. Comment: for comments_count on tasks.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class Task(models.Model):
    """
    A task on a board (title, description, status, priority, assignee, reviewer).
    """

    class Status(models.TextChoices):
        TO_DO = "to_do", "To Do"
        IN_PROGRESS = "in_progress", "In Progress"
        REVIEW = "review", "Review"
        DONE = "done", "Done"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
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
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewing_tasks",
    )
    due_date = models.DateField(null=True, blank=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tasks",
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "task"
        verbose_name_plural = "tasks"

    def __str__(self):
        return self.title


class Comment(models.Model):
    """Comment on a task; used for comments_count."""

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_comments",
    )
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "comment"
        verbose_name_plural = "comments"

    def __str__(self):
        return f"Comment on task {self.task_id}"
