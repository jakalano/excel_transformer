import os
from datetime import datetime
from django.db import models
from django.core.exceptions import ValidationError

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

