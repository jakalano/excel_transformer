# Generated by Django 4.2.5 on 2023-12-22 20:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_page', '0008_action_backup_data_path'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='undone',
            field=models.BooleanField(default=False),
        ),
    ]