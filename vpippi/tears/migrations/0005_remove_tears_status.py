# Generated by Django 4.2.9 on 2024-01-13 16:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tears', '0004_alter_user_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tears',
            name='status',
        ),
    ]
