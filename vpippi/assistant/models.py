from django.db import models


class ChatSession(models.Model):
    title = models.CharField(max_length=200, blank=True)
    model = models.CharField(max_length=100, blank=True, help_text='Gemini model for this conversation. Blank falls back to GEMINI_MODEL.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title or f'Session {self.pk}'


class ChatMessage(models.Model):
    ROLE_USER = 'user'
    ROLE_MODEL = 'model'
    ROLE_CHOICES = [(ROLE_USER, 'User'), (ROLE_MODEL, 'Model')]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    parts = models.JSONField(
        help_text='List of Gemini SDK Content.parts dicts: {"text": ...} / {"function_call": {...}} / {"function_response": {...}}.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']

    def __str__(self):
        return f'{self.role} #{self.pk} (session {self.session_id})'


class PendingAction(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='pending_actions')
    tool_name = models.CharField(max_length=100)
    arguments = models.JSONField(help_text='Normalized arguments, frozen at proposal time and replayed verbatim on confirm.')
    summary = models.TextField(help_text='Human-readable description shown in the chat UI and used as the audit trail.')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    result = models.TextField(blank=True, help_text='What actually happened when applied, or the error if it failed.')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.tool_name} ({self.status})'
