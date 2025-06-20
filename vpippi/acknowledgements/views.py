from datetime import datetime

from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views import View

from .models import Acknowledgement, LinkAcknowledgement, FakeAcknowledgement

import re
from random import choice


class AcknowledgementView(View):
    # helper to check the countdown condition
    def _should_countdown(self, request):
        # make the cutoff timezone-aware in the current TZ
        cutoff = timezone.make_aware(
            datetime(2025, 6, 20, 18, 15),
            timezone.get_current_timezone()
        )
        return (not request.user.is_staff) and (timezone.now() < cutoff)

    def dispatch(self, request, *args, **kwargs):
        # if we’re before the cutoff and the user isn’t staff, show the countdown
        if self._should_countdown(request):
            return render(request, 'acknowledgements/countdown.html')
        # otherwise proceed to get/post as normal
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, 'acknowledgements/index.html')

    def post(self, request):
        name_surname = request.POST.get('name_surname')
        if not name_surname:
            return render(request, 'acknowledgements/index.html')

        # normalize input
        cleaned = re.sub('[^a-z ]', '',
                         name_surname.lower())

        try:
            ack = Acknowledgement.objects.get(
                name_surname=cleaned
            )
            name, text = ack.name, ack.text

        except Acknowledgement.DoesNotExist:
            return render(request, 'acknowledgements/no_acknowledgement.html', {'name_surname': name_surname})

        return render(request, 'acknowledgements/acknowledgement.html', {
            'name': name,
            'text': text
        })
