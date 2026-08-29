from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CVVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(help_text="URL path segment, e.g. 'apple' for /cv/apple/. Ignored for the default CV.", unique=True)),
                ('label', models.CharField(help_text="Internal name shown in the admin only, e.g. 'Apple recruiter'.", max_length=100)),
                ('page_title', models.CharField(blank=True, help_text="Browser tab title. Falls back to the label above if left blank.", max_length=200)),
                ('content_md', models.TextField(blank=True, help_text="The entire visible page: Markdown, with raw HTML allowed for custom layouts/styling. See cv/base.html for the CSS classes already available (section-title, cv-row, cv-left-col/cv-right-col, cv-entry-title/cv-entry-desc, tier color classes, highlight, ...).")),
                ('is_default', models.BooleanField(default=False, help_text='Serve this CV at the site root (vpippi.com). Only one variant can be default.')),
                ('is_published', models.BooleanField(default=True)),
                ('is_locked', models.BooleanField(default=False, help_text='Freezes this CV against changes from the assistant chatbot. The bot can lock a CV but cannot unlock one — only uncheck this here in the admin.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['label'],
            },
        ),
    ]
