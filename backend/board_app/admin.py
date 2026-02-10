"""
Board app admin.
"""

from django.contrib import admin
from .models import Board, BoardMember

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "owner")
    list_filter = ("owner",)

@admin.register(BoardMember)
class BoardMemberAdmin(admin.ModelAdmin):
    list_display = ("id", "board", "user")
    list_filter = ("board",)
