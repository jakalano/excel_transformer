import os
import csv
import pandas as pd
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
# from .models import UploadedFile
from .forms import UploadFileForm, ParagraphErrorList

def detect_delimiter(file_path, num_lines=5):
    # detect the delimiter of a csv file
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        # read the first few lines of the file
        lines = [file.readline().strip() for _ in range(num_lines)]
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(''.join(lines)).delimiter
    return delimiter

def main_page(request):
    context = {
        'previous_page_url': None,  # to disable pagination
        'next_page_url': 'summary'
    }

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES, error_class=ParagraphErrorList)

        if form.is_valid():
            uploaded_file = form.save()  # Save the file and get an instance
            # Determine the file type based on extension
            file_path = uploaded_file.file.path
            file_extension = os.path.splitext(file_path)[1].lower()

            if file_extension == '.csv':
                delimiter = detect_delimiter(file_path)
                print(delimiter) # for debugging
                df_orig = pd.read_csv(file_path, delimiter=delimiter)
            elif file_extension in ['.xlsx', '.xls']:
                df_orig = pd.read_excel(file_path)
            # For example, print the first 5 rows
            print(df_orig.head())

            return redirect('summary')
        else:
            context['form'] = form  # Add the invalid form to the context so errors can be displayed
            return render(request, '1_index.html', context)

    form = UploadFileForm()
    context['form'] = form
    return render(request, '1_index.html', context)

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

# def failed(request):
#     context = {
#         'previous_page_url': 'main_page',  
#         'next_page_url': None 
#     }
#     template = loader.get_template('failed.html')
#     return HttpResponse(template.render(context, request)) 