# Generated by Django 4.2.9 on 2024-01-14 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0004_player'),
    ]

    operations = [
        migrations.AddField(
            model_name='map',
            name='walls_array',
            field=models.TextField(blank=True, null=True),
        ),
    ]
