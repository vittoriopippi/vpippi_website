from django.shortcuts import render
from .models import Paper

def index(request):
    papers = Paper.objects.select_related('conference').prefetch_related('authors', 'tags').order_by('-publication_date')
    return render(request, 'main/index.html', {'papers': papers})