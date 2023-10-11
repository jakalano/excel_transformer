import os
import json
from datetime import datetime
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

def validate_file_extension(value):
    valid_content_type = ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'text/csv', 'application/vnd.ms-excel']
    if not value.file.content_type in valid_content_type:
        raise ValidationError('Unsupported file type. Please upload a .csv, .xls or .xlsx file.')

def get_upload_path(instance, filename):
    # Get the file extension
    _, ext = os.path.splitext(filename)
    # Create a folder name based on the current datetime and the filename (without extension)
    folder_name = f"{filename.rsplit('.', 1)[0]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return os.path.join(folder_name, f"{filename}")

class UploadedFile(models.Model):
    file = models.FileField(upload_to=get_upload_path, validators=[validate_file_extension])
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

class Action(models.Model):
    ACTION_CHOICES = [
        ('delete_row', 'Delete Row'),
        # Add other actions as needed
    ]
    action_type = models.CharField(choices=ACTION_CHOICES, max_length=50)
    parameters = models.JSONField()  # Store parameters as JSON
    timestamp = models.DateTimeField(auto_now_add=True)  # Automatically set when record is created
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)  # Link action to user
    session_id = models.CharField(max_length=256, null=True)  # Store session ID
    
class Template(models.Model):
    actions = models.ManyToManyField(Action)
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link template to user