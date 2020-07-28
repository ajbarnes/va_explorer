# Generated by Django 3.0.8 on 2020-07-28 16:37

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('verbal_autopsy', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CauseCodingIssue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('severity', models.CharField(choices=[('error', 'error'), ('warning', 'warning')], max_length=7)),
                ('algorithm', models.TextField()),
                ('settings', django.contrib.postgres.fields.jsonb.JSONField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('verbalautopsy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coding_issues', to='verbal_autopsy.VerbalAutopsy')),
            ],
        ),
    ]
