import os
import pandas as pd
from datetime import datetime
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.template import loader
# from .models import UploadedFile
from .utils import (
    load_dataframe_from_file, save_dataframe,
    dataframe_to_html, remove_empty_rows
)
from .forms import UploadFileForm, ParagraphErrorList




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
            df_orig = load_dataframe_from_file(file_path)
            # save table and add to session
            html_table = dataframe_to_html(df_orig,classes='table table-striped')
            request.session['html_table'] = html_table
            request.session['file_path'] = file_path
            print(file_path)
            return redirect('summary')
            
        else:
            context['form'] = form  # Add the invalid form to the context so errors can be displayed
            return render(request, '1_index.html', context)

    form = UploadFileForm()
    context['form'] = form
    
    return render(request, '1_index.html', context)

def summary(request):
    file_path = request.session.get('file_path')
    df_v1 = load_dataframe_from_file(file_path)
    # Identify empty columns
    empty_cols = df_v1.columns[df_v1.isna().all()].tolist()

    if request.method == 'POST':
        if 'remove_empty_rows' in request.POST:
            print("Removing empty rows")
            df_v1 = remove_empty_rows(df_v1)
            print(f"DataFrame shape after drop rows: {df_v1.shape}")
            save_dataframe(df_v1, file_path)
        
        # Get selected columns to delete from POST data
        cols_to_delete = request.POST.getlist('remove_empty_cols')
        # Delete selected columns
        df_v1 = df_v1.drop(columns=cols_to_delete)
        save_dataframe(df_v1, file_path)
        # Redirect to avoid resubmit on refresh
        return redirect('summary')

    context = {
        'num_rows': df_v1.shape[0],
        'num_cols': df_v1.shape[1],
        'col_names': df_v1.columns.tolist(),
        'num_empty_rows': df_v1[df_v1.isna().all(axis=1)].shape[0],
        'num_empty_cols': df_v1.columns[df_v1.isna().all(axis=0)].size,
        'empty_cols': empty_cols,
        'previous_page_url': 'main_page',
        'next_page_url': 'edit_data',
    }
    
    return render(request, '2_file_summary.html', context)

def edit_data(request):
    file_path = request.session.get('file_path')
    df = load_dataframe_from_file(file_path)
    
    context = {
        'num_empty_rows': df[df.isna().all(axis=1)].shape[0],
        'num_empty_cols': df.columns[df.isna().all(axis=0)].size,
        'previous_page_url': 'summary',
        'next_page_url': 'edit_columns',
        'table': dataframe_to_html(df, classes='table table-striped'),
    }
    
    return render(request, '3_edit_data.html', context)


def edit_columns(request):
    context = {
        'previous_page_url': 'edit_data',
        'next_page_url': 'download'  
    }
    return render(request, '4_edit_columns.html', context)

def download(request):
    context = {
        'previous_page_url': 'edit_columns',
        'next_page_url': None  # to disable pagination
    }

    file_format = request.GET.get('format')
    print(f"File format: {file_format}")
    
    if file_format:
        file_path = request.session.get('file_path', 'data')  # default to 'data'
        original_file_name = os.path.basename(file_path)
        original_file_dir = os.path.dirname(file_path)  # get the directory of the original file
        
        print(f"Original file name: {original_file_name}")
        df = load_dataframe_from_file(file_path)
        print(df.head())
        file_name_no_ext, _ = os.path.splitext(original_file_name)

        # Generate the new filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        new_file_name = f"{file_name_no_ext}_EDITED_{timestamp}"
        print(f"New file name: {new_file_name}")
        save_path = os.path.join(original_file_dir, f"{new_file_name}.{file_format}")  # save in the original file's directory
        save_dataframe(df, save_path, file_format)

        with open(save_path, 'rb') as f:
            if file_format == 'csv':
                response = HttpResponse(f, content_type='text/csv')
            elif file_format == 'xlsx':
                response = HttpResponse(f, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            elif file_format == 'json':
                response = HttpResponse(f, content_type='application/json')
            elif file_format == 'xml':
                response = HttpResponse(f, content_type='application/xml')
        
            else:
                # Handle unexpected format
                return HttpResponse("Unexpected format", status=400)
                
        response['Content-Disposition'] = f'attachment; filename="{new_file_name}.{file_format}"'
        return response
    else:
        # If no format is specified, render the HTML page
        return render(request, '5_download.html', context)




 