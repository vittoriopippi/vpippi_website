"""Tools for CVVariant — the whole CV is one self-contained document
(source_content), either raw HTML or a full LaTeX document depending on
source_type. Each write operation is split into a `validate_*` function
(called immediately when the model invokes the tool — checks input and
returns a human-readable summary plus normalized arguments, but touches no
data) and an `apply_*` function (called only once the user confirms —
performs the actual write).
"""
from cv.models import CVVariant


def _get_variant(slug):
    try:
        return CVVariant.objects.get(slug=slug)
    except CVVariant.DoesNotExist:
        raise ValueError(f"No CVVariant with slug {slug!r}. Call list_cv_variants to see what exists.")


def _check_unlocked(variant):
    if variant.is_locked:
        raise ValueError(
            f"Refusing: '{variant.label}' ({variant.slug}) is locked. Locked CVs can only be "
            "changed from the Django admin, not by the assistant."
        )


def _check_default_swap_unlocked():
    current_default = CVVariant.objects.filter(is_default=True).first()
    if current_default and current_default.is_locked:
        raise ValueError(
            f"Cannot change the default CV: '{current_default.label}' is currently the default "
            "and is locked. Unlock it from the admin first."
        )


# --- read tools -----------------------------------------------------------

def list_cv_variants():
    return [
        {
            'slug': v.slug,
            'label': v.label,
            'page_title': v.page_title,
            'source_type': v.source_type,
            'is_default': v.is_default,
            'is_published': v.is_published,
            'is_locked': v.is_locked,
            'content_length': len(v.source_content),
        }
        for v in CVVariant.objects.all()
    ]


def get_cv_variant(slug):
    v = _get_variant(slug)
    return {
        'slug': v.slug,
        'label': v.label,
        'page_title': v.page_title,
        'source_type': v.source_type,
        'is_default': v.is_default,
        'is_published': v.is_published,
        'is_locked': v.is_locked,
        'source_content': v.source_content,
    }


# --- write tools ------------------------------------------------------------

def validate_create_cv_variant(slug, label, page_title='', source_type='html', is_default=False):
    if CVVariant.objects.filter(slug=slug).exists():
        raise ValueError(f"A CVVariant with slug {slug!r} already exists. Use update_cv_variant or write_cv_content instead.")
    if source_type not in ('html', 'latex'):
        raise ValueError(f"source_type must be 'html' or 'latex', got {source_type!r}.")
    if is_default:
        _check_default_swap_unlocked()
    args = dict(slug=slug, label=label, page_title=page_title, source_type=source_type, is_default=bool(is_default))
    text = f"Create a new, empty {source_type.upper()} CV variant '{label}' (slug: {slug})"
    if is_default:
        text += ' and make it the default CV served at the site root'
    return text, args


def apply_create_cv_variant(slug, label, page_title, source_type, is_default):
    v = CVVariant.objects.create(
        slug=slug, label=label, page_title=page_title, source_type=source_type,
        is_default=is_default, source_content='',
    )
    return f"Created empty CVVariant '{v.label}' (slug: {v.slug})."


def validate_create_cv_variant_from(new_slug, new_label, source_slug=None, page_title='', is_default=False):
    if CVVariant.objects.filter(slug=new_slug).exists():
        raise ValueError(f"A CVVariant with slug {new_slug!r} already exists. Use update_cv_variant or write_cv_content instead.")
    if source_slug:
        source = _get_variant(source_slug)
    else:
        source = CVVariant.objects.filter(is_default=True).first()
        if source is None:
            raise ValueError("No default CV exists to clone from. Pass source_slug explicitly.")
    if is_default:
        _check_default_swap_unlocked()
    args = dict(new_slug=new_slug, new_label=new_label, source_slug=source.slug, page_title=page_title, is_default=bool(is_default))
    text = f"Create CV variant '{new_label}' (slug: {new_slug}) as a full copy of '{source.label}' ({source.slug})"
    if is_default:
        text += ' and make it the default CV served at the site root'
    return text, args


def apply_create_cv_variant_from(new_slug, new_label, source_slug, page_title, is_default):
    source = CVVariant.objects.get(slug=source_slug)
    v = CVVariant.objects.create(
        slug=new_slug, label=new_label, page_title=page_title, is_default=is_default,
        source_type=source.source_type, source_content=source.source_content,
    )
    return f"Created CVVariant '{v.label}' (slug: {v.slug}) as a copy of '{source.label}'."


def validate_write_cv_content(slug, source_content):
    v = _get_variant(slug)
    _check_unlocked(v)
    if not source_content.strip():
        raise ValueError(
            "source_content is empty. If you really mean to blank out this CV, confirm that explicitly "
            "with the user first before calling this — an empty page is almost certainly a mistake."
        )
    args = dict(slug=slug, source_content=source_content)
    text = f"Overwrite the full {v.source_type.upper()} source of '{v.label}' ({slug}) with {len(source_content)} characters"
    return text, args


def apply_write_cv_content(slug, source_content):
    v = _get_variant(slug)
    v.source_content = source_content
    v.save(update_fields=['source_content', 'rendered_html'])
    return f"Updated content for '{v.label}' ({v.slug})."


def validate_edit_cv_content(slug, old_text, new_text):
    v = _get_variant(slug)
    _check_unlocked(v)
    count = v.source_content.count(old_text)
    if count == 0:
        raise ValueError(
            "old_text was not found verbatim in the current source_content. Call get_cv_variant to see the "
            "exact current content and copy the text precisely (including exact whitespace/markup)."
        )
    if count > 1:
        raise ValueError(
            f"old_text appears {count} times in source_content — it must match exactly once. Include more "
            "surrounding context to make it unique, or use write_cv_content to replace the whole document."
        )
    args = dict(slug=slug, old_text=old_text, new_text=new_text)
    text = f"Edit '{v.label}' ({slug}): replace one occurrence of {len(old_text)} chars with {len(new_text)} chars"
    return text, args


def apply_edit_cv_content(slug, old_text, new_text):
    v = _get_variant(slug)
    v.source_content = v.source_content.replace(old_text, new_text, 1)
    v.save(update_fields=['source_content', 'rendered_html'])
    return f"Edited content for '{v.label}' ({v.slug})."


def validate_update_cv_variant(slug, new_slug=None, label=None, page_title=None, is_default=None, is_published=None):
    v = _get_variant(slug)
    _check_unlocked(v)
    if is_default:
        _check_default_swap_unlocked()
    changes = {}
    if new_slug is not None and new_slug != v.slug:
        if CVVariant.objects.filter(slug=new_slug).exclude(pk=v.pk).exists():
            raise ValueError(f"Another CVVariant already uses slug {new_slug!r}.")
        changes['slug'] = new_slug
    if label is not None:
        changes['label'] = label
    if page_title is not None:
        changes['page_title'] = page_title
    if is_default is not None:
        changes['is_default'] = bool(is_default)
    if is_published is not None:
        changes['is_published'] = bool(is_published)
    if not changes:
        raise ValueError('No fields to update were provided.')
    args = dict(slug=slug, changes=changes)
    text = f"Update CV variant '{v.label}' (slug: {slug}): " + ', '.join(f'{k}={val!r}' for k, val in changes.items())
    return text, args


def apply_update_cv_variant(slug, changes):
    v = _get_variant(slug)
    for field, value in changes.items():
        setattr(v, field, value)
    v.save()
    return f"Updated CVVariant (slug now: {v.slug})."


def validate_delete_cv_variant(slug):
    v = _get_variant(slug)
    if v.is_default:
        raise ValueError(f"Refusing to delete CVVariant {slug!r}: it is the default CV served at the site root. Make another variant the default first.")
    _check_unlocked(v)
    args = dict(slug=slug)
    text = f"Delete CV variant '{v.label}' (slug: {slug}) and its content entirely"
    return text, args


def apply_delete_cv_variant(slug):
    v = _get_variant(slug)
    label = v.label
    v.delete()
    return f"Deleted CVVariant '{label}'."


def validate_lock_cv_variant(slug):
    v = _get_variant(slug)
    if v.is_locked:
        raise ValueError(f"CVVariant {slug!r} is already locked.")
    args = dict(slug=slug)
    text = (
        f"Lock CV variant '{v.label}' (slug: {slug}): once locked, the assistant will refuse "
        "to change anything about it — only the admin can unlock it."
    )
    return text, args


def apply_lock_cv_variant(slug):
    v = _get_variant(slug)
    v.is_locked = True
    v.save(update_fields=['is_locked'])
    return f"Locked CVVariant '{v.label}'. Only the admin can unlock it now."
