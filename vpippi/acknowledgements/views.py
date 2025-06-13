from django.shortcuts import render, get_object_or_404
from django.views import View
from .models import Acknowledgement, LinkAcknowledgement, FakeAcknowledgement
import re
from random import choice

class AcknowledgementView(View):
    def get(self, request):
        return render(request, 'acknowledgements/index.html')

    def post(self, request):
        name_surname = request.POST.get('name_surname')
        if name_surname is None:
            return render(request, 'acknowledgements/index.html')

        name_surname = name_surname.lower()
        name_surname = re.sub('[^a-z ]', '', name_surname)

        try:
            acknowledgement = Acknowledgement.objects.get(name_surname=name_surname)
            name = acknowledgement.name
            text = acknowledgement.text
        except Acknowledgement.DoesNotExist:
            try:
                link_acknowledgement = LinkAcknowledgement.objects.get(alt=name_surname)
                name = link_acknowledgement.ack.name
                text = link_acknowledgement.ack.text
            except LinkAcknowledgement.DoesNotExist:
                fake_acknowledgement = choice(FakeAcknowledgement.objects.all())
                name = name_surname.title()
                text = fake_acknowledgement.text.replace('<name>', name)

        return render(request, 'acknowledgements/acknowledgement.html', {'name': name, 'text': text})
