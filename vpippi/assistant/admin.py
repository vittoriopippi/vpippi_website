from django.contrib import admin

from .models import ChatSession, ChatMessage, PendingAction


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('role', 'parts', 'created_at')
    can_delete = False


class PendingActionInline(admin.TabularInline):
    model = PendingAction
    extra = 0
    readonly_fields = ('tool_name', 'summary', 'status', 'created_at', 'resolved_at', 'result')
    can_delete = False


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'created_at', 'updated_at')
    inlines = [ChatMessageInline, PendingActionInline]


@admin.register(PendingAction)
class PendingActionAdmin(admin.ModelAdmin):
    list_display = ('tool_name', 'status', 'session', 'created_at', 'resolved_at')
    list_filter = ('status', 'tool_name')
    readonly_fields = ('session', 'tool_name', 'arguments', 'summary', 'created_at')
    search_fields = ('tool_name', 'summary')
