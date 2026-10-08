"""Runs one assistant tool call against the database. Shared by the Gemini agent
loop (gemini.py) and the token-protected HTTP API (api.py), so both go through the
exact same validation, confirmation rules and lock checks."""
from . import executor
from .models import PendingAction
from .tools import READ_HANDLERS, WRITE_VALIDATORS

# Only these tools stage a PendingAction and wait for an explicit confirmation. Every
# other write executes immediately once it is called.
REQUIRES_CONFIRMATION = {'delete_cv_variant', 'delete_job_application'}


def run_tool(session, name, args, new_pending_actions):
    """Execute tool `name` with `args`. Returns {'output': ...} or {'error': ...}.
    `session` may be None (HTTP API calls aren't part of a chat). Staged actions
    that still need confirming are appended to `new_pending_actions`."""
    args = args or {}

    if name in READ_HANDLERS:
        try:
            return {'output': READ_HANDLERS[name](**args)}
        except Exception as exc:
            return {'error': str(exc)}

    if name in WRITE_VALIDATORS:
        try:
            summary, normalized_args = WRITE_VALIDATORS[name](**args)
        except Exception as exc:
            return {'error': str(exc)}

        pending = PendingAction.objects.create(
            session=session, tool_name=name, arguments=normalized_args, summary=summary,
        )

        if name in REQUIRES_CONFIRMATION:
            new_pending_actions.append(pending)
            return {'output': {'status': 'pending_confirmation', 'action_id': pending.id, 'summary': summary}}

        # Everything else applies immediately — no confirm click needed.
        success, message = executor.confirm(pending)
        if not success:
            return {'error': message}
        return {'output': {'status': 'applied', 'summary': summary, 'result': message}}

    return {'error': f"Unknown tool '{name}'."}
