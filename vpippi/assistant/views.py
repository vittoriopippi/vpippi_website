import json

import markdown
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST

from . import executor, gemini
from .models import ChatMessage, ChatSession, PendingAction


def _display_text(message):
    texts = [p.get('text') for p in message.parts if p.get('text')]
    return '\n'.join(t for t in texts if t) or None


def _render_reply(text):
    """Render a model reply's Markdown to HTML. Trusted content — only staff
    can reach this chat, and the text comes from our own Gemini call."""
    if not text:
        return ''
    return mark_safe(markdown.markdown(text, extensions=['extra']))


@staff_member_required
def chat_view(request):
    session_id = request.GET.get('session')
    if session_id:
        session = get_object_or_404(ChatSession, pk=session_id)
    else:
        session = ChatSession.objects.first()
        if session is None:
            session = ChatSession.objects.create()

    display_messages = []
    for m in session.messages.all():
        text = _display_text(m)
        if not text:
            continue
        html = _render_reply(text) if m.role == ChatMessage.ROLE_MODEL else None
        display_messages.append({'role': m.role, 'text': text, 'html': html})
    context = {
        'session': session,
        'sessions': ChatSession.objects.all()[:20],
        'chat_messages': display_messages,
        'pending_actions': session.pending_actions.filter(status=PendingAction.STATUS_PENDING),
        'available_models': settings.GEMINI_AVAILABLE_MODELS,
        'current_model': session.model or settings.GEMINI_MODEL,
    }
    return render(request, 'assistant/chat.html', context)


@staff_member_required
@require_POST
def new_session(request):
    model = request.POST.get('model') or ''
    if model not in settings.GEMINI_AVAILABLE_MODELS:
        model = ''
    session = ChatSession.objects.create(model=model)
    return redirect(f'/assistant/?session={session.pk}')


@staff_member_required
@require_POST
def set_model(request, pk):
    session = get_object_or_404(ChatSession, pk=pk)
    data = json.loads(request.body)
    model = data.get('model') or ''
    if model not in settings.GEMINI_AVAILABLE_MODELS:
        return JsonResponse({'error': f"Unknown model '{model}'."}, status=400)
    session.model = model
    session.save(update_fields=['model'])
    return JsonResponse({'model': session.model})


@staff_member_required
@require_POST
def send_message(request):
    data = json.loads(request.body)
    session = get_object_or_404(ChatSession, pk=data['session_id'])
    message = (data.get('message') or '').strip()
    if not message:
        return JsonResponse({'error': 'Empty message.'}, status=400)

    result = gemini.run_turn(session, message)
    session.save()  # bump updated_at

    return JsonResponse({
        'reply': result['reply'],
        'reply_html': _render_reply(result['reply']),
        'pending_actions': [
            {'id': pa.id, 'tool_name': pa.tool_name, 'summary': pa.summary}
            for pa in result['pending_actions']
        ],
    })


@staff_member_required
@require_POST
def confirm_action(request, pk):
    pending = get_object_or_404(PendingAction, pk=pk)
    success, message = executor.confirm(pending)
    return JsonResponse({'success': success, 'message': message, 'status': pending.status})


@staff_member_required
@require_POST
def cancel_action(request, pk):
    pending = get_object_or_404(PendingAction, pk=pk)
    success, message = executor.cancel(pending)
    return JsonResponse({'success': success, 'message': message, 'status': pending.status})
