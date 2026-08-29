from cv.models import CVVariant
from django.db import transaction
from django.utils import timezone
from jobs.models import JobApplication

from .models import PendingAction
from .tools import WRITE_APPLIERS


def _affected_label(tool_name, arguments):
    """Best-effort label of the CVVariant/JobApplication a write tool touches,
    resolved BEFORE the write is applied so it still works for the delete tools."""
    if tool_name == 'create_cv_variant':
        return arguments.get('label')
    if tool_name == 'create_cv_variant_from':
        return arguments.get('new_label')
    if tool_name == 'update_cv_variant':
        new_label = (arguments.get('changes') or {}).get('label')
        if new_label:
            return new_label
    if tool_name == 'create_job_application':
        return f"{arguments.get('title')} @ {arguments.get('company')}"
    if tool_name in ('update_job_application', 'delete_job_application'):
        app = JobApplication.objects.filter(pk=arguments.get('id')).first()
        return f"{app.title} @ {app.company}" if app else None
    slug = arguments.get('slug')
    if not slug:
        return None
    variant = CVVariant.objects.filter(slug=slug).first()
    return variant.label if variant else None


def _note_touched_variant(session, label):
    """Keep the session's title as a deduplicated, ordered list of every
    CVVariant label it has created/updated/deleted, so the sidebar shows
    what a conversation was about instead of a generic 'Session N'."""
    if not label:
        return
    names = [n.strip() for n in session.title.split('/')] if session.title else []
    if label in names:
        return
    names.append(label)
    session.title = '/'.join(names)
    session.save(update_fields=['title'])


def confirm(pending_action: PendingAction):
    """Apply a pending action's frozen arguments. Returns (success, message).
    On failure the action is left 'pending' (not silently marked confirmed)
    so the user can retry or cancel."""
    if pending_action.status != PendingAction.STATUS_PENDING:
        return False, f"This action is already {pending_action.status}."

    applier = WRITE_APPLIERS.get(pending_action.tool_name)
    if applier is None:
        return False, f"Unknown tool '{pending_action.tool_name}'."

    label = _affected_label(pending_action.tool_name, pending_action.arguments)

    try:
        with transaction.atomic():
            message = applier(**pending_action.arguments)
    except Exception as exc:
        pending_action.result = f"Failed to apply: {exc}"
        pending_action.save(update_fields=['result'])
        return False, pending_action.result

    pending_action.status = PendingAction.STATUS_CONFIRMED
    pending_action.resolved_at = timezone.now()
    pending_action.result = message
    pending_action.save(update_fields=['status', 'resolved_at', 'result'])
    _note_touched_variant(pending_action.session, label)
    return True, message


def cancel(pending_action: PendingAction):
    if pending_action.status != PendingAction.STATUS_PENDING:
        return False, f"This action is already {pending_action.status}."
    pending_action.status = PendingAction.STATUS_CANCELLED
    pending_action.resolved_at = timezone.now()
    pending_action.result = 'Cancelled by user.'
    pending_action.save(update_fields=['status', 'resolved_at', 'result'])
    return True, pending_action.result
