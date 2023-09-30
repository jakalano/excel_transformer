from django.db import models
from django.core.exceptions import ValidationError

def validate_file_extension(value):
    valid_content_type = ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'text/csv', 'application/vnd.ms-excel']
    if not value.file.content_type in valid_content_type:
        raise ValidationError('Unsupported file type. Please upload a .csv, .xls or .xlsx file.')


class UploadedFile(models.Model):
    file = models.FileField(upload_to='upload/', validators=[validate_file_extension])
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name
