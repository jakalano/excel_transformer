# Generated by Django 4.2.5 on 2023-12-22 18:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_page', '0007_action_uploaded_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='backup_data_path',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
    ]
