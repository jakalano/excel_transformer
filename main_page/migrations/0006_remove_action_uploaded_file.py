# Generated by Django 4.2.5 on 2023-11-07 14:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main_page', '0005_action_uploaded_file'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='action',
            name='uploaded_file',
        ),
    ]
