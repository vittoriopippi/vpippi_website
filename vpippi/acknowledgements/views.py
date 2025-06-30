from datetime import datetime
import re
from random import choice  # still unused, but left if you later re‑enable fake acks

from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views import View

from .models import Acknowledgement, LinkAcknowledgement


class AcknowledgementView(View):
    """Handles the acknowledgement search → password → reveal flow."""

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    def _should_countdown(self, request):
        """Return *True* when the countdown page should be shown."""
        cutoff = timezone.make_aware(
            datetime(2025, 6, 30, 18, 15), timezone.get_current_timezone()
        )
        return (not request.user.is_staff) and (timezone.now() < cutoff)

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------
    def dispatch(self, request, *args, **kwargs):
        # Show countdown until the Go‑Live time, unless the user is staff.
        return super().dispatch(request, *args, **kwargs)

    # ------------------------------------------------------------------
    # HTTP methods
    # ------------------------------------------------------------------
    def get(self, request):
        """Render the landing/search page."""
        return render(request, "acknowledgements/index.html")

    def post(self, request):
        """Either:

        1. Handle the *search* form (name_surname submitted).
        2. Handle the *password* form (ack_id + password submitted).
        """

        # --------------------------------------------------------------
        # Branch 1: password check
        # --------------------------------------------------------------
        if "password" in request.POST:
            ack_id = request.POST.get("ack_id")
            password = request.POST.get("password", "")
            ack = get_object_or_404(Acknowledgement, pk=ack_id)

            if password.lower() == ack.password.lower():
                # Success! Show the full acknowledgement.
                return render(
                    request,
                    "acknowledgements/acknowledgement.html",
                    {
                        "name_surname": ack.name,  # title‑case via property
                        "html": ack.html,
                    },
                )

            # Wrong password → redisplay form with error message.
            return render(
                request,
                "acknowledgements/acknowledgement_password.html",
                {
                    "name_surname": ack.name,
                    "question": ack.question,
                    "ack_id": ack.id,
                    "error": "Incorrect password. Please try again.",
                },
            )

        # --------------------------------------------------------------
        # Branch 2: initial surname lookup
        # --------------------------------------------------------------
        name_surname = request.POST.get("name_surname", "").strip()
        if not name_surname:
            return render(request, "acknowledgements/index.html")

        # Normalise: only alphabet + space, lowercase (to match stored key).
        cleaned = re.sub("[^a-z ]", "", name_surname.lower())

        try:
            ack = Acknowledgement.objects.get(name_surname=cleaned)
        except Acknowledgement.DoesNotExist:
            try:
                ack = LinkAcknowledgement.objects.get(alt=cleaned).ack
            except LinkAcknowledgement.DoesNotExist:
                return render(
                    request,
                    "acknowledgements/no_acknowledgement.html",
                    {"name_surname": name_surname},
                )

        if ack.password == "" or ack.password == "none" or ack.password is None:
            # No password set → show the full acknowledgement.
            return render(
                request,
                "acknowledgements/acknowledgement.html",
                {
                    "name_surname": ack.name,  # title‑case via property
                    "html": ack.html,
                },
            )

        # Found –> ask for password.
        return render(
            request,
            "acknowledgements/acknowledgement_password.html",
            {
                "name_surname": ack.name,
                "question": ack.question,
                "ack_id": ack.id,
            },
        )
