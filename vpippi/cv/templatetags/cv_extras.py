import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def markdownify(content_md):
    """Render CVVariant.content_md (Markdown, with raw HTML passthrough for
    custom layouts) to HTML. Trusted content — only staff (admin or the
    assistant, gated behind confirm) can ever write it."""
    if not content_md:
        return ''
    return mark_safe(markdown.markdown(content_md, extensions=['extra']))
