"""Token-protected JSON API over the assistant's tools, so a trusted client (Claude Code
on the owner's PC, see tools/site_api.py) can run exactly the same operations as the chat
assistant against the live site. It goes through dispatch.run_tool, so validation, the
lock rules and the stage-then-confirm step for deletes are identical.

Auth: `Authorization: Bearer <ASSISTANT_API_TOKEN>`. If the token isn't configured, or is
wrong, every endpoint answers 404 so the API's existence isn't advertised.
"""
import hmac
import json

from django.conf import settings
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from . import executor
from .dispatch import REQUIRES_CONFIRMATION, run_tool
from .models import PendingAction
from .tools import FUNCTION_DECLARATIONS

MIN_TOKEN_LENGTH = 32


def token_required(view):
    @csrf_exempt
    def wrapper(request, *args, **kwargs):
        expected = settings.ASSISTANT_API_TOKEN
        header = request.META.get('HTTP_AUTHORIZATION', '')
        scheme, _, supplied = header.partition(' ')
        if (
            len(expected) < MIN_TOKEN_LENGTH
            or scheme.lower() != 'bearer'
            or not hmac.compare_digest(supplied.encode(), expected.encode())
        ):
            raise Http404
        return view(request, *args, **kwargs)
    wrapper.__name__ = view.__name__
    return wrapper


def _pending_json(pa):
    return {'id': pa.id, 'tool_name': pa.tool_name, 'summary': pa.summary, 'arguments': pa.arguments}


@token_required
@require_GET
def list_tools(request):
    return JsonResponse({
        'tools': [
            {**d, 'requires_confirmation': d['name'] in REQUIRES_CONFIRMATION}
            for d in FUNCTION_DECLARATIONS
        ],
    })


@token_required
@require_POST
def call_tool(request, name):
    try:
        args = json.loads(request.body or b'{}')
    except ValueError:
        return JsonResponse({'error': 'Request body must be a JSON object.'}, status=400)
    if not isinstance(args, dict):
        return JsonResponse({'error': 'Request body must be a JSON object of tool arguments.'}, status=400)

    result = run_tool(None, name, args, [])
    return JsonResponse(result, status=400 if 'error' in result else 200)


@token_required
@require_GET
def list_pending(request):
    pending = PendingAction.objects.filter(status=PendingAction.STATUS_PENDING)
    return JsonResponse({'pending_actions': [_pending_json(pa) for pa in pending]})


@token_required
@require_POST
def confirm_action(request, pk):
    pending = get_object_or_404(PendingAction, pk=pk)
    success, message = executor.confirm(pending)
    return JsonResponse({'success': success, 'message': message, 'status': pending.status}, status=200 if success else 400)


@token_required
@require_POST
def cancel_action(request, pk):
    pending = get_object_or_404(PendingAction, pk=pk)
    success, message = executor.cancel(pending)
    return JsonResponse({'success': success, 'message': message, 'status': pending.status}, status=200 if success else 400)
