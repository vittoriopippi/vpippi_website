from django.shortcuts import render, redirect
from .models import Paper

def index(request):
    # if the user is not logged in or not staff, redirect:
    if not request.user.is_staff:
        return redirect('https://scholar.google.com/citations?user=OHmt2vUAAAAJ')

    # otherwise load and render the index as before
    papers = (
        Paper.objects
        .select_related('conference')
        .prefetch_related('authors', 'tags')
        .order_by('-publication_date')
    )
    return render(request, 'main/index.html', {'papers': papers})
