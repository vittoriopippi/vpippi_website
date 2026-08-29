"""Gemini agent loop: turns a user chat message into a reply. Read tools run
inline. Write tools run immediately too — except delete_cv_variant, which
stages a PendingAction and waits for an explicit Confirm click in the UI (see
REQUIRES_CONFIRMATION below).

Verified against the installed google-genai==2.20.0 source directly
(Content.role is 'user'/'model' only — not 'tool'; FunctionDeclaration takes
plain JSON Schema via `parameters_json_schema`; GenerateContentResponse
exposes `.function_calls` and `.text`).
"""
from django.conf import settings
from google import genai
from google.genai import types

from . import executor
from .models import ChatMessage, PendingAction
from .tools import FUNCTION_DECLARATIONS, READ_HANDLERS, WRITE_VALIDATORS

MAX_TOOL_ITERATIONS = 25

# Only these tools stage a PendingAction and wait for an explicit Confirm click in the
# chat UI. Every other write executes immediately once the model calls it.
REQUIRES_CONFIRMATION = {'delete_cv_variant', 'delete_job_application'}

SYSTEM_INSTRUCTION = """You help maintain Vittorio Pippi's CV and job application tracker, published as a \
Django site with multiple CV "variants" (one per URL: the default variant is served at the site root, \
others at /cv/<slug>/) and a job board at /jobs/ listing tracked job applications.

Each CV variant is exactly ONE self-contained document: `content_md`. There is nothing else — no separate \
tables for work experience, education, publications, or contact links. content_md holds the entire visible \
page: the person's name, contact links, technical summary, work experience, education, training, \
publications, section headings, colors — everything. It's rendered as Markdown (headings, bold, links, \
lists all work normally), but raw HTML blocks are also passed through untouched, so you can drop in custom \
`<div>`/`<span>` markup wherever plain Markdown isn't expressive enough. Because each variant is one \
independent document, editing one CV can never leak into or affect another — that's the whole point of \
this design, so always work within a single variant's content_md rather than trying to share text between \
variants (use create_cv_variant_from to start a new one from an existing one's content instead).

Available CSS classes (all defined in cv/base.html, wrap the page in a `<div class="cv-container">` — \
which the template already provides, don't add another one) if you want the original polished look for a \
dated, two-column entry (work experience / education / training / publication):
```
<div class="row g-0 cv-row work-high">
  <div class="col-md-3 cv-left-col">Mar 2026 - Aug 2026</div>
  <div class="col-md-9 cv-right-col">
    <div class="cv-entry-title">Research Scientist</div>
    <div class="cv-entry-desc">Design HTG models<br>Docling Team at IBM, Zurich</div>
  </div>
</div>
```
- Row wrapper classes: `work-*` (green), `edu-*` (orange), `train-*` (blue), `pub-*` (purple) — each with a \
`-high`/`-mid`/`-low` tier suffix controlling color intensity (`pub-*` only has `-high`/`-low`). Use these \
consistently as `cv-row <section>-<tier>` on the outer div.
- `<span class="highlight">text</span>` for a soft-background emphasis (e.g. the CV owner's own name in a \
publication's author list).
- `<span class="oral-label" style="color:#C29BC8;font-size:.75rem;font-weight:600;">Oral</span>` for a \
publication's "Oral" badge.
- A publication venue with a footnote uses a tooltip: `<span data-bs-toggle="tooltip" data-bs-placement="top" \
title="explanation">CVPR 2025*</span>`.
- Plain Markdown (`# Name`, `## Section Heading`, paragraphs, bullet lists, links) also renders with \
reasonable default styling — use it for anything that doesn't need the fancier two-column layout. You don't \
have to use the structured markup for every section; mix and match freely.

Rules:
- Before creating or editing a CV, call list_cv_variants / get_cv_variant to see what already exists — \
never guess ids or duplicate an existing variant.
- To make small, precise changes to an existing CV, prefer edit_cv_content over write_cv_content: it does a \
find-and-replace against the CURRENT content_md, so first call get_cv_variant to get the exact current text, \
then pass a short, unique snippet as old_text (enough surrounding context to be unambiguous — it must match \
exactly once). Use write_cv_content instead only for first-time authoring or a genuine full rewrite.
- create_cv_variant, create_cv_variant_from, write_cv_content, edit_cv_content, update_cv_variant, and \
lock_cv_variant all apply IMMEDIATELY when you call them — there is no confirmation step, so tell the user \
what you did in the past tense (created/updated/wrote/edited/locked), not what you're about to do.
- delete_cv_variant is the one exception: it only STAGES the deletion — the user must click Confirm on it \
in the chat UI before anything is actually deleted. After calling it, tell the user it's awaiting their \
confirmation, not that it's already deleted.
- A CV variant can be locked (is_locked). Once locked, nothing about it can be changed through you — every \
write tool will refuse with an error if it targets a locked variant. You CAN lock a variant (lock_cv_variant) \
when the user says a CV is final/frozen/done, but there is no unlock tool: only the site owner can unlock \
one, from the Django admin. If a tool call fails because something is locked, tell the user that plainly and \
point them to the admin — don't retry the same edit.
- Keep replies short and concrete.
- When a request needs several independent tool calls (e.g. building out multiple sections of a new CV), \
issue them together in the same turn rather than one call, one reply, one call — you're allowed to call \
multiple tools at once. You have a limited number of tool-call rounds per message, so batching matters for \
bulk operations.

Job application tracker (list_job_applications, get_job_application, create_job_application, \
update_job_application, delete_job_application):
- The user will typically paste a job posting, an email, or a short note ("applied to X at Y today", \
"got an interview with Z", "rejected by W") — turn that into the right tool call rather than asking for a \
rigid form. If the status isn't mentioned, default to 'Applied'; if the location isn't mentioned, default \
to 'Zurich'; if the applied date isn't mentioned, leave it unset (don't guess a date).
- Before updating or deleting, call list_job_applications (optionally filtered by status) to find the \
right id by matching company/title — never guess an id.
- create_job_application and update_job_application apply IMMEDIATELY when you call them — describe what \
you did in the past tense, not what you're about to do.
- delete_job_application is the one exception: it only STAGES the deletion — the user must click Confirm \
in the chat UI before anything is actually deleted. After calling it, tell the user it's awaiting their \
confirmation, not that it's already deleted.
"""


def _tool_declarations():
    return [
        types.Tool(function_declarations=[
            types.FunctionDeclaration(
                name=d['name'],
                description=d['description'],
                parameters_json_schema=d['parameters'],
            )
            for d in FUNCTION_DECLARATIONS
        ])
    ]


def _load_history(session):
    history = []
    for msg in session.messages.all():
        history.append(types.Content(role=msg.role, parts=[types.Part(**p) for p in msg.parts]))
    return history


def _persist(session, content):
    ChatMessage.objects.create(
        session=session,
        role=content.role or ChatMessage.ROLE_USER,
        parts=[p.model_dump(exclude_none=True, mode='json') for p in (content.parts or [])],
    )


def _pending_notes(session):
    """Short system note about actions confirmed/cancelled since the model last spoke,
    so the model stays aware without us fabricating an extra function-call/response pair."""
    resolved = session.pending_actions.exclude(status=PendingAction.STATUS_PENDING).order_by('resolved_at')
    last_model_msg = session.messages.filter(role=ChatMessage.ROLE_MODEL).order_by('-created_at').first()
    cutoff = last_model_msg.created_at if last_model_msg else None
    if cutoff:
        resolved = resolved.filter(resolved_at__gte=cutoff)
    notes = [f"(System: action #{a.id} [{a.tool_name}] was {a.status} — {a.result})" for a in resolved]
    return '\n'.join(notes)


def run_turn(session, user_text):
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    model_name = session.model or settings.GEMINI_MODEL
    history = _load_history(session)

    note = _pending_notes(session)
    full_text = f"{note}\n\n{user_text}" if note else user_text
    user_content = types.Content(role='user', parts=[types.Part.from_text(text=full_text)])
    history.append(user_content)
    _persist(session, user_content)

    config = types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION, tools=_tool_declarations())
    new_pending_actions = []

    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.models.generate_content(model=model_name, contents=history, config=config)
        if not response.candidates or not response.candidates[0].content:
            feedback = getattr(response, 'prompt_feedback', None)
            return {'reply': f"Gemini returned no response (possibly blocked: {feedback}).", 'pending_actions': new_pending_actions}
        model_content = response.candidates[0].content
        history.append(model_content)
        _persist(session, model_content)

        calls = response.function_calls
        if not calls:
            return {'reply': response.text or '', 'pending_actions': new_pending_actions}

        response_parts = []
        for call in calls:
            result = _dispatch(session, call, new_pending_actions)
            response_parts.append(types.Part.from_function_response(name=call.name, response=result))

        function_response_content = types.Content(role='user', parts=response_parts)
        history.append(function_response_content)
        _persist(session, function_response_content)

    return {
        'reply': (
            f"I hit the limit of {MAX_TOOL_ITERATIONS} tool-call rounds for a single message without "
            "finishing. Check the actions staged below, confirm what looks right, then just say "
            "'continue' and I'll pick up where I left off."
        ),
        'pending_actions': new_pending_actions,
    }


def _dispatch(session, call, new_pending_actions):
    name = call.name
    args = call.args or {}

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
