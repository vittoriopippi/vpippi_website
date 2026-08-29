from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from .models import JobApplication

STATUS_COLORS = {
    JobApplication.STATUS_APPLIED: '#4A4EA1',
    JobApplication.STATUS_INTERVIEWING: '#F79F20',
    JobApplication.STATUS_OFFER: '#0E9547',
    JobApplication.STATUS_REJECTED: '#adb5bd',
}


def _rows(applications):
    return [{'app': a, 'color': STATUS_COLORS.get(a.status, '#adb5bd')} for a in applications]


@staff_member_required
def board(request):
    all_applications = JobApplication.objects.order_by('-created_at')
    active = all_applications.exclude(status=JobApplication.STATUS_REJECTED)
    rejected = all_applications.filter(status=JobApplication.STATUS_REJECTED)
    context = {
        'applications': _rows(active),
        'rejected_applications': _rows(rejected),
        'total_count': all_applications.count(),
    }
    return render(request, 'jobs/board.html', context)
