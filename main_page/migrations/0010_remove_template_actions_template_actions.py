# Generated by Django 4.2.5 on 2023-12-22 20:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_page', '0009_action_undone'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='template',
            name='actions',
        ),
        migrations.AddField(
            model_name='template',
            name='actions',
            field=models.JSONField(default=1),
            preserve_default=False,
        ),
    ]