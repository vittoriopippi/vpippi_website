from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from .models import JobApplication

STATUS_COLORS = {
    JobApplication.STATUS_APPLIED: '#4A4EA1',
    JobApplication.STATUS_INTERVIEWING: '#F79F20',
    JobApplication.STATUS_OFFER: '#0E9547',
    JobApplication.STATUS_REJECTED: '#adb5bd',
}


@staff_member_required
def board(request):
    applications = [
        {'app': a, 'color': STATUS_COLORS.get(a.status, '#adb5bd')}
        for a in JobApplication.objects.all()
    ]
    return render(request, 'jobs/board.html', {'applications': applications})
