import os
import pandas as pd
from datetime import datetime
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.template import loader
# from .models import UploadedFile
from .utils import load_dataframe_from_file, save_dataframe_to_file
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
            html_table = df_orig.to_html(classes='table table-striped')
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
    df_orig = load_dataframe_from_file(file_path)
    
    if request.method == 'POST' and 'remove_empty_rows' in request.POST:
        df_orig.dropna(how='all', inplace=True)
        save_dataframe_to_file(df_orig, file_path)
        return redirect('edit_data')

    num_rows = df_orig.shape[0]
    num_cols = df_orig.shape[1]
    col_names = df_orig.columns.tolist()
    num_empty_rows = df_orig[df_orig.isna().all(axis=1)].shape[0]
    
    context = {
        'num_rows': num_rows,
        'num_cols': num_cols,
        'col_names': col_names,
        'num_empty_rows': num_empty_rows,
        'previous_page_url': 'main_page',
        'next_page_url': 'edit_data',
    }
    
    return render(request, '2_file_summary.html', context)

def edit_data(request):
    num_empty_rows = request.session.get('num_empty_rows', 0)
    context = {
        'num_empty_rows': num_empty_rows,
        'previous_page_url': 'summary',
        'next_page_url': 'edit_columns',
        
    }
    context['table'] = request.session.get('html_table', '')
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
    # If a format is specified, handle file download
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

        if file_format == 'csv':
            df.to_csv(save_path, index=False)
            with open(save_path, 'rb') as f:
                response = HttpResponse(f, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{new_file_name}.csv"'
        elif file_format == 'xlsx':
            df.to_excel(save_path, index=False, engine='openpyxl')
            with open(save_path, 'rb') as f:
                response = HttpResponse(f, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{new_file_name}.xlsx"'
                

        elif file_format == 'json':
            df.to_json(save_path, index=False)
            with open(save_path, 'rb') as f:
                response = HttpResponse(f, content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="{new_file_name}.json"'
            
        elif file_format == 'xml':
            df.to_xml(save_path, index=False)
            with open(save_path, 'rb') as f:
                response = HttpResponse(f, content_type='application/xml')
            response['Content-Disposition'] = f'attachment; filename="{new_file_name}.xml"'
            
        else:
            # Handle unexpected format
            return HttpResponse("Unexpected format", status=400)

        return response
    else:
        # If no format is specified, render the HTML page
        return render(request, '5_download.html', context)



@csrf_exempt
def delete_empty_rows(request):
    file_path = request.session.get('file_path')
    df = load_dataframe_from_file(file_path)
    df_cleaned1 = df.dropna(how='all')
    # Save the cleaned dataframe back
    save_dataframe_to_file(df_cleaned1, file_path)
    return JsonResponse({'status': 'success'})


#def upload(request):

# def failed(request):
#     context = {
#         'previous_page_url': 'main_page',  
#         'next_page_url': None 
#     }
#     template = loader.get_template('failed.html')
#     return HttpResponse(template.render(context, request)) 