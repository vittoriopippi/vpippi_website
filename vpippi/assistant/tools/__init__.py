"""Registry of tools exposed to Gemini: JSON-schema declarations plus the
three dispatch tables the agent loop and the confirm-time executor use.

READ_HANDLERS    -- run immediately, return JSON straight back to the model.
WRITE_VALIDATORS -- run immediately when the model calls a mutating tool;
                    validate input and stage a PendingAction. Never touch data.
WRITE_APPLIERS   -- run only when the user confirms a PendingAction.
"""
from . import cv_content as cvc


def _prop(type_, description, enum=None):
    schema = {'type': type_, 'description': description}
    if enum is not None:
        schema['enum'] = enum
    return schema


def _obj(properties, required):
    return {'type': 'object', 'properties': properties, 'required': required}


FUNCTION_DECLARATIONS = [
    # --- read tools ---------------------------------------------------
    {
        'name': 'list_cv_variants',
        'description': 'List every CV variant (slug, label, page_title, whether it is the default/site-root CV, published/locked state, and content length). Does not include the full content.',
        'parameters': _obj({}, []),
    },
    {
        'name': 'get_cv_variant',
        'description': 'Get one CV variant in full, including its entire content_md. Call this before edit_cv_content — you need the exact current text to match against.',
        'parameters': _obj({'slug': _prop('string', 'The CVVariant slug.')}, ['slug']),
    },
    # --- write tools ------------------------------------------------------
    {
        'name': 'create_cv_variant',
        'description': 'Create a new, empty CV variant, served at /cv/<slug>/ (or at the site root if is_default is true). Its content_md starts blank — use write_cv_content afterwards to author it.',
        'parameters': _obj({
            'slug': _prop('string', "URL slug, e.g. 'apple' for /cv/apple/."),
            'label': _prop('string', 'Internal name shown in the admin.'),
            'page_title': _prop('string', 'Browser tab title. Falls back to label if omitted.'),
            'is_default': _prop('boolean', 'Make this the CV served at the site root. Unsets any previous default.'),
        }, ['slug', 'label']),
    },
    {
        'name': 'create_cv_variant_from',
        'description': "Create a new CV variant as a full copy of another one's content — the standard way to start a tailored CV without cross-contaminating the original. If source_slug is omitted, clones the current default CV.",
        'parameters': _obj({
            'new_slug': _prop('string', "URL slug for the new variant, e.g. 'apple'."),
            'new_label': _prop('string', 'Internal name shown in the admin for the new variant.'),
            'source_slug': _prop('string', 'Slug of the CV to copy content from. Omit to copy the current default CV.'),
            'page_title': _prop('string', 'Browser tab title for the new variant. Falls back to new_label if omitted.'),
            'is_default': _prop('boolean', 'Make the new variant the site-root CV. Unsets any previous default.'),
        }, ['new_slug', 'new_label']),
    },
    {
        'name': 'write_cv_content',
        'description': 'Overwrite the ENTIRE content_md of a CV variant. Use for first-time authoring or large rewrites. For a small, precise change to an existing document prefer edit_cv_content instead.',
        'parameters': _obj({
            'slug': _prop('string', 'The CVVariant slug to write.'),
            'content_md': _prop('string', 'The full new page content: Markdown, with raw HTML allowed for custom layouts.'),
        }, ['slug', 'content_md']),
    },
    {
        'name': 'edit_cv_content',
        'description': 'Replace one exact, unique occurrence of old_text with new_text inside a CV variant\'s content_md — a targeted find-and-replace, cheaper and safer than resending the whole document. old_text must match the CURRENT content_md exactly (call get_cv_variant first) and must occur exactly once; include enough surrounding context to make it unique.',
        'parameters': _obj({
            'slug': _prop('string', 'The CVVariant slug to edit.'),
            'old_text': _prop('string', 'Exact substring to find in the current content_md (must be unique).'),
            'new_text': _prop('string', 'Text to replace it with.'),
        }, ['slug', 'old_text', 'new_text']),
    },
    {
        'name': 'update_cv_variant',
        'description': 'Update metadata fields of an existing CV variant (slug, label, page_title, is_default, is_published) — not its content. Omit fields you are not changing. Refused if the variant is locked.',
        'parameters': _obj({
            'slug': _prop('string', 'The CVVariant slug to update.'),
            'new_slug': _prop('string', 'New slug, if renaming.'),
            'label': _prop('string', 'New internal label.'),
            'page_title': _prop('string', 'New browser tab title.'),
            'is_default': _prop('boolean', 'Make/unmake this the site-root CV.'),
            'is_published': _prop('boolean', 'Whether this CV is reachable at its URL.'),
        }, ['slug']),
    },
    {
        'name': 'delete_cv_variant',
        'description': (
            'Delete a CV variant and its content entirely. Unlike every other write tool, this one does '
            'NOT apply immediately — it stages the deletion and the user must click Confirm in the chat UI. '
            'Refused if it is currently the default (site-root) CV, or if it is locked.'
        ),
        'parameters': _obj({'slug': _prop('string', 'The CVVariant slug to delete.')}, ['slug']),
    },
    {
        'name': 'lock_cv_variant',
        'description': (
            'Lock a CV variant so nothing about it can be changed by this assistant anymore. This is '
            'one-way from here: there is no unlock tool — only the site owner can unlock it, from the '
            'Django admin. Use this when the user says a CV is final/frozen/done and should not be '
            'touched further.'
        ),
        'parameters': _obj({'slug': _prop('string', 'The CVVariant slug to lock.')}, ['slug']),
    },
]

READ_HANDLERS = {
    'list_cv_variants': cvc.list_cv_variants,
    'get_cv_variant': cvc.get_cv_variant,
}

WRITE_VALIDATORS = {
    'create_cv_variant': cvc.validate_create_cv_variant,
    'create_cv_variant_from': cvc.validate_create_cv_variant_from,
    'write_cv_content': cvc.validate_write_cv_content,
    'edit_cv_content': cvc.validate_edit_cv_content,
    'update_cv_variant': cvc.validate_update_cv_variant,
    'delete_cv_variant': cvc.validate_delete_cv_variant,
    'lock_cv_variant': cvc.validate_lock_cv_variant,
}

WRITE_APPLIERS = {
    'create_cv_variant': cvc.apply_create_cv_variant,
    'create_cv_variant_from': cvc.apply_create_cv_variant_from,
    'write_cv_content': cvc.apply_write_cv_content,
    'edit_cv_content': cvc.apply_edit_cv_content,
    'update_cv_variant': cvc.apply_update_cv_variant,
    'delete_cv_variant': cvc.apply_delete_cv_variant,
    'lock_cv_variant': cvc.apply_lock_cv_variant,
}

assert set(WRITE_VALIDATORS) == set(WRITE_APPLIERS)
assert set(READ_HANDLERS) | set(WRITE_VALIDATORS) == {d['name'] for d in FUNCTION_DECLARATIONS}
