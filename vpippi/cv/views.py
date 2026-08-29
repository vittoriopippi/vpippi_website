from django.http import Http404
from django.shortcuts import redirect, render

from .models import CVVariant


def _render_variant(request, variant):
    return render(request, 'cv/detail.html', {'variant': variant})


def default_cv(request):
    variant = CVVariant.objects.filter(is_default=True, is_published=True).first()
    if variant is None:
        raise Http404("No default CV has been configured yet.")
    return _render_variant(request, variant)


def cv_variant(request, slug):
    variant = CVVariant.objects.filter(slug=slug, is_published=True).first()
    if variant is None:
        return redirect('cv:default')
    return _render_variant(request, variant)
