# Generated by Django 4.2.9 on 2024-01-14 11:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0002_alter_map_height_alter_map_width'),
    ]

    operations = [
        migrations.RenameField(
            model_name='door',
            old_name='dst_orentation',
            new_name='dst_orientation',
        ),
        migrations.RenameField(
            model_name='map',
            old_name='origin_orentation',
            new_name='origin_orientation',
        ),
    ]
