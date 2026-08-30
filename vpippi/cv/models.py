from django.db import models

from .latex import LatexError, latex_to_html


class CVVariant(models.Model):
    """A named version of the CV, e.g. the main one served at '/' or a
    tailored one served at '/cv/<slug>/'.

    The entire visible page — name, contact links, section headings/colors,
    descriptions, publications, everything — lives in `source_content`,
    either as raw HTML (shown as-is) or as a full standalone LaTeX document
    (compiled to HTML for the web view, and to a real PDF on demand). Each
    variant is fully self-contained; nothing is shared between variants, so
    editing one can never affect another.
    """

    SOURCE_TYPE_CHOICES = [
        ('html', 'HTML'),
        ('latex', 'LaTeX'),
    ]

    slug = models.SlugField(
        unique=True,
        help_text="URL path segment, e.g. 'apple' for /cv/apple/. Ignored for the default CV.",
    )
    label = models.CharField(
        max_length=100,
        help_text="Internal name shown in the admin only, e.g. 'Apple recruiter'.",
    )
    page_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Browser tab title. Falls back to the label above if left blank.",
    )
    source_type = models.CharField(
        max_length=10,
        choices=SOURCE_TYPE_CHOICES,
        default='html',
        help_text="'HTML' is shown as-is. 'LaTeX' is a full standalone document, compiled to HTML for the web view and to a real PDF on demand.",
    )
    source_content = models.TextField(
        blank=True,
        help_text=(
            "The entire CV source. For HTML: raw HTML shown as-is (see cv/base.html for the CSS "
            "classes already available — section-title, cv-row, cv-left-col/cv-right-col, "
            "cv-entry-title/cv-entry-desc, tier color classes, highlight, ...). "
            "For LaTeX: a full standalone .tex document."
        ),
    )
    rendered_html = models.TextField(
        blank=True,
        editable=False,
        help_text="Cached HTML for the web view. Mirrors source_content for HTML sources; compiled from LaTeX via pandoc otherwise.",
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Serve this CV at the site root (vpippi.com). Only one variant can be default.",
    )
    is_published = models.BooleanField(default=True)
    is_locked = models.BooleanField(
        default=False,
        help_text=(
            "Freezes this CV against changes from the assistant chatbot. "
            "The bot can lock a CV but cannot unlock one — only uncheck this here in the admin."
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['label']

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        if self.is_default:
            CVVariant.objects.exclude(pk=self.pk).update(is_default=False)
        if self.source_type == 'latex':
            try:
                self.rendered_html = latex_to_html(self.source_content)
            except LatexError as e:
                self.rendered_html = f'<pre class="cv-latex-error">LaTeX conversion failed:\n{e}</pre>'
        else:
            self.rendered_html = self.source_content
        super().save(*args, **kwargs)
