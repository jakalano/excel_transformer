from django import forms
from .models import UploadedFile, Action, Template
from django.forms.utils import ErrorList

class UploadFileForm(forms.ModelForm):
    class Meta:
        model = UploadedFile
        fields = ['file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={'accept': '.csv,.xls,.xlsx,.json,.xml,.tsv'})
        }

class ParagraphErrorList(ErrorList):
    def __str__(self):
        return self.as_paragraphs()

    def as_paragraphs(self):
        if not self:
            return ''
        return '<p class="alert alert-danger">%s</p>' % '</p><p class="alert alert-danger">'.join([str(e) for e in self])
    
class ActionForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = ['action_type', 'parameters']

class TemplateForm(forms.ModelForm):
    class Meta:
        model = Template
        fields = ['name', 'actions']