from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from .models import UploadedFile

def main_page(request):
    context = {
        'previous_page_url': None,  # to disable pagination
        'next_page_url': 'summary' 
    }
    template = loader.get_template('1_index.html')
    if request.method == 'POST':
        print("POST request received")  # Debugging print
        try:
            file = UploadedFile(file=request.FILES['file'])
            print("File received:", request.FILES['file'].name)  # Debugging print
            file.save()
            return redirect('summary')
        except Exception as e:
            print("Error uploading file:", str(e))  # Debugging print
    
    #return render(request, 'failed.html')
    return HttpResponse(template.render(context, request))

def summary(request):
    context = {

        'previous_page_url': 'main_page',
        'next_page_url': 'edit_data'   
    }
    template = loader.get_template('2_file_summary.html')
    return HttpResponse(template.render(context, request))

def edit_data(request):
    context = {
        'previous_page_url': 'summary',
        'next_page_url': 'edit_columns'    
    }
    template = loader.get_template('3_edit_data.html')
    return HttpResponse(template.render(context, request))

def edit_columns(request):
    context = {
        'previous_page_url': 'edit_data',
        'next_page_url': 'download'  
    }
    template = loader.get_template('4_edit_columns.html')
    return HttpResponse(template.render(context, request))

def download(request):
    context = {
        'previous_page_url': 'edit_columns',
        'next_page_url': None  # to disable pagination
    }
    template = loader.get_template('5_download.html')
    return HttpResponse(template.render(context, request))

#def upload(request):


def failed(request):
    context = {
        'previous_page_url': 'main_page',  
        'next_page_url': None 
    }
    template = loader.get_template('failed.html')
    return HttpResponse(template.render(context, request))