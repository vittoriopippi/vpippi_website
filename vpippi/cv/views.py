import hashlib
import logging

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils.html import escape

from .latex import LatexError, latex_to_pdf
from .models import CVVariant

logger = logging.getLogger(__name__)

PDF_CACHE_DIR = settings.MEDIA_ROOT / 'cv_pdf_cache'


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


def _serve_pdf(request, variant):
    if variant.source_type != 'latex':
        raise Http404("This CV has no LaTeX source to compile a PDF from.")

    PDF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    content_hash = hashlib.sha256(variant.source_content.encode('utf-8')).hexdigest()[:16]
    cache_path = PDF_CACHE_DIR / f'{variant.slug}-{content_hash}.pdf'

    if not cache_path.exists():
        try:
            pdf_bytes = latex_to_pdf(variant.source_content)
        except LatexError as e:
            logger.exception("Failed to compile PDF for CV variant %r", variant.slug)
            if request.user.is_staff:
                return HttpResponse(f'<pre>{escape(str(e))}</pre>', status=503)
            return HttpResponse("Sorry, PDF generation is temporarily unavailable for this CV.", status=503)
        cache_path.write_bytes(pdf_bytes)

    return FileResponse(
        open(cache_path, 'rb'),
        as_attachment=True,
        filename=f'{variant.slug or "cv"}.pdf',
        content_type='application/pdf',
    )


def default_cv_pdf(request):
    variant = CVVariant.objects.filter(is_default=True, is_published=True).first()
    if variant is None:
        raise Http404("No default CV has been configured yet.")
    return _serve_pdf(request, variant)


def variant_cv_pdf(request, slug):
    variant = CVVariant.objects.filter(slug=slug, is_published=True).first()
    if variant is None:
        raise Http404("No such CV.")
    return _serve_pdf(request, variant)
