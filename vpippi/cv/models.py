from django.db import models


class CVVariant(models.Model):
    """A named version of the CV, e.g. the main one served at '/' or a
    tailored one served at '/cv/<slug>/'.

    The entire visible page — name, contact links, section headings/colors,
    descriptions, publications, everything — lives in `content_md`: Markdown,
    with raw HTML allowed for custom layouts. Each variant is fully
    self-contained; nothing is shared between variants, so editing one can
    never affect another.
    """

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
    content_md = models.TextField(
        blank=True,
        help_text=(
            "The entire visible page: Markdown, with raw HTML allowed for custom layouts/styling. "
            "See cv/base.html for the CSS classes already available (section-title, cv-row, "
            "cv-left-col/cv-right-col, cv-entry-title/cv-entry-desc, tier color classes, highlight, ...)."
        ),
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
        super().save(*args, **kwargs)
