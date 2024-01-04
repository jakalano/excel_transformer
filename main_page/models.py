import os
import json
from datetime import datetime
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

def validate_file_extension(value):
    valid_extensions = ['.csv', '.xls', '.xlsx', '.json', '.xml', '.tsv']
    ext = os.path.splitext(value.name)[1]
    if ext.lower() not in valid_extensions:
        raise ValidationError('Unsupported file type. Please upload a .csv, .xls, .xlsx, .json, .xml, or .tsv file.')

def get_upload_path(instance, filename):
    # gets the file extension
    _, ext = os.path.splitext(filename)
    # creates a folder name based on the current datetime and the filename (without extension)
    folder_name = f"{filename.rsplit('.', 1)[0]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return os.path.join(folder_name, f"{filename}")

class UploadedFile(models.Model):
    file = models.FileField(upload_to=get_upload_path, validators=[validate_file_extension], max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return self.file.name

class Action(models.Model):
    ACTION_CHOICES = [
        ('remove_empty_rows', 'Remove Empty Rows'),
        ('remove_empty_cols', 'Remove Empty Columns'),
        ('delete_first_X_rows', 'Delete First X Rows'),
        ('replace_header', 'Replace Header'),
        ('delete_last_X_rows', 'Delete Last X Rows'),
        ('add_column', 'Add Column'),
        ('delete_columns', 'Delete Columns'),
        ('fill_column', 'Fill Column'),
        ('split_column', 'Split Column'),
        ('merge_columns', 'Merge Columns'),
        ('rename_column', 'Rename Column'),
        ('delete_data', 'Delete Data'),
        ('replace_symbol', 'Replace Symbol'),
        ('change_case', 'Change Case'),
        ('trim_and_replace_whitespaces', 'Trim and Replace Multiple Whitespaces'),

    ]
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE)
    action_type = models.CharField(choices=ACTION_CHOICES, max_length=50)
    parameters = models.JSONField()  # stores parameters as JSON
    timestamp = models.DateTimeField(auto_now_add=True)  # automatically set when record is created
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)  # links action to user
    session_id = models.CharField(max_length=256, null=True)  # stores session ID
    backup_data_path = models.CharField(max_length=1024, null=True, blank=True)
    undone = models.BooleanField(default=False)  # tracks if an action is undone

    def __str__(self):
        return f"{self.action_type} - {self.timestamp}"
    
class Template(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # links template to user
    original_headers = models.JSONField(default=list)  # stores original file's headers
    actions = models.JSONField()  # stores list of actions

    def __str__(self):
        return self.name