# Generated by Django 4.1.7 on 2024-09-15 18:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_study_vatrpp', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='competitor',
            name='csv_file',
        ),
        migrations.AddField(
            model_name='competitor',
            name='reference',
            field=models.BooleanField(default=False),
        ),
    ]
