# Generated by Django 4.2.9 on 2025-01-25 16:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_study_emuru', '0002_remove_sampleimage_unique_competitor_iamid_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sampleimage',
            name='dataset',
            field=models.CharField(max_length=256, null=True),
        ),
    ]
