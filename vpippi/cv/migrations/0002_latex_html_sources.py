import markdown
from django.db import migrations, models


def bake_markdown_to_html(apps, schema_editor):
    """Existing CVVariant rows hold Markdown+raw-HTML in content_md, rendered
    at request time via python-markdown. That rendering step is retired —
    run it once here so every existing CV keeps looking exactly the same as
    a plain 'html' source_type."""
    CVVariant = apps.get_model('cv', 'CVVariant')
    for variant in CVVariant.objects.all():
        variant.source_type = 'html'
        variant.source_content = markdown.markdown(variant.content_md, extensions=['extra'])
        variant.rendered_html = variant.source_content
        variant.save(update_fields=['source_type', 'source_content', 'rendered_html'])


def unbake(apps, schema_editor):
    CVVariant = apps.get_model('cv', 'CVVariant')
    for variant in CVVariant.objects.all():
        variant.content_md = variant.source_content
        variant.save(update_fields=['content_md'])


class Migration(migrations.Migration):

    dependencies = [
        ('cv', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cvvariant',
            name='source_type',
            field=models.CharField(choices=[('html', 'HTML'), ('latex', 'LaTeX')], default='html', help_text="'HTML' is shown as-is. 'LaTeX' is a full standalone document, compiled to HTML for the web view and to a real PDF on demand.", max_length=10),
        ),
        migrations.AddField(
            model_name='cvvariant',
            name='source_content',
            field=models.TextField(blank=True, help_text='The entire CV source. For HTML: raw HTML shown as-is (see cv/base.html for the CSS classes already available — section-title, cv-row, cv-left-col/cv-right-col, cv-entry-title/cv-entry-desc, tier color classes, highlight, ...). For LaTeX: a full standalone .tex document.'),
        ),
        migrations.AddField(
            model_name='cvvariant',
            name='rendered_html',
            field=models.TextField(blank=True, editable=False, help_text='Cached HTML for the web view. Mirrors source_content for HTML sources; compiled from LaTeX via pandoc otherwise.'),
        ),
        migrations.RunPython(bake_markdown_to_html, unbake),
        migrations.RemoveField(
            model_name='cvvariant',
            name='content_md',
        ),
    ]
