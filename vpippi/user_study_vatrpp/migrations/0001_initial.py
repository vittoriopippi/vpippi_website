# Generated by Django 4.1.7 on 2024-09-15 18:38

from django.db import migrations, models
import django.db.models.deletion
import user_study_vatrpp.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Competitor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('winner', models.BooleanField(default=False)),
                ('available', models.BooleanField(default=True)),
                ('csv_file', models.FileField(blank=True, null=True, upload_to='user_study/csv_files/')),
            ],
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('accuracy', models.IntegerField(default=0)),
                ('visible', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('finished', models.BooleanField(default=False)),
                ('correct_control_answers', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='SampleImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('img', models.ImageField(max_length=1024, upload_to=user_study_vatrpp.models.content_file_name)),
                ('exclude_from_study', models.BooleanField(default=False)),
                ('iam_id', models.IntegerField()),
                ('competitor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_study_vatrpp.competitor')),
            ],
        ),
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_study_vatrpp.player')),
                ('winner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='winner', to='user_study_vatrpp.sampleimage')),
            ],
        ),
    ]
