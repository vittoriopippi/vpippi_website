# Generated by Django 4.1.7 on 2024-09-17 21:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_study_vatrpp', '0003_skipped_sampleimage_unique_competitor_iamid_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sampleimage',
            name='exclude_from_study',
        ),
        migrations.AddField(
            model_name='sampleimage',
            name='available',
            field=models.BooleanField(default=True),
        ),
    ]
