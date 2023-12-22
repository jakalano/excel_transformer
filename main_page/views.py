import os
import pandas as pd
from datetime import datetime
from urllib.parse import urlparse
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import resolve
from django.template import loader
from django.conf import settings
from .utils import (
    load_dataframe_from_file, save_dataframe,
    dataframe_to_html, remove_empty_rows,record_action
)
from .forms import UploadFileForm, ParagraphErrorList
from .models import Action, UploadedFile
from django.contrib import messages
import re
import json


def main_page(request):
    context = {
        'previous_page_url': None,
        'next_page_url': 'summary',
        'active_page': 'home'
    }
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES, error_class=ParagraphErrorList)
        if form.is_valid():
            uploaded_file = form.save()  # saves the original file
            file_path = uploaded_file.file.path
            request.session['file_path'] = file_path
            df_orig = load_dataframe_from_file(file_path)
            
            # creates a modified copy
            file_dir, file_name = os.path.split(file_path)
            file_root, _ = os.path.splitext(file_name)
            temp_file_path = os.path.join(file_dir, f"TEMP_{file_root}.csv")
            
            save_dataframe(df_orig, temp_file_path, file_format='csv')
            df_orig = load_dataframe_from_file(temp_file_path)
            html_table = dataframe_to_html(df_orig,classes='table table-striped')
            request.session['html_table'] = html_table
            request.session['temp_file_path'] = temp_file_path
            print(temp_file_path)
            return redirect('summary')
            
        else:
            context['form'] = form  # adds the invalid form to the context so errors can be displayed
            return render(request, '1_index.html', context)

    form = UploadFileForm()
    context['form'] = form
    
    return render(request, '1_index.html', context)

def undo_last_action(request):
    print("Undo view accessed")
    print(f"Session Original File Path: {request.session.get('file_path')}")

    # loads the orig file
    original_file_path = request.session.get('file_path')
    if original_file_path is None:
        print("Original file path is None!")
        return JsonResponse({'status': 'error', 'error': 'Original file path not found'}, status=500)

        # Extract the relative path using MEDIA_ROOT
    relative_path = os.path.relpath(original_file_path, settings.MEDIA_ROOT).replace('\\', '/')

    try:
        current_file = UploadedFile.objects.get(file=relative_path)
    except UploadedFile.DoesNotExist:
        # Handle the case where the UploadedFile instance doesn't exist
        messages.error(request, "The file you're working on could not be found.")
        return redirect('main_page')  # Redirect to a safe page

    df = load_dataframe_from_file(original_file_path)

    # Get all actions for this session and current file, excluding the last one
    actions_count = Action.objects.filter(session_id=request.session.session_key, uploaded_file=current_file).count()
    if actions_count > 1:
        last_action = Action.objects.filter(session_id=request.session.session_key, uploaded_file=current_file).latest('timestamp')
        actions = Action.objects.filter(session_id=request.session.session_key, uploaded_file=current_file).exclude(id=last_action.id)

    else:
        actions = Action.objects.none()

    # applies all actions to the df
    for action in actions:
        df = apply_action(df, action.action_type, action.parameters)

    # saves the modified df back to the temporary file path
    temp_file_path = request.session.get('temp_file_path')
    save_dataframe(df, temp_file_path)

    # instead of redirecting returns a JsonResponse with the necessary data
    updated_table_html = dataframe_to_html(df)
    return JsonResponse({'status': 'success', 'updated_table': updated_table_html})

def apply_action(df, action_type, parameters):
    try:
        print(f"Applying {action_type} with {parameters}")

        if action_type == 'remove_empty_rows':
            return remove_empty_rows(df)
        
        elif action_type == 'remove_empty_cols':
            cols_to_delete = parameters.get('cols_to_delete')
            return df.drop(cols_to_delete, axis=1)
        
        elif action_type == 'delete_first_X_rows':
            num_rows_to_delete_start = int(parameters.get('num_rows_to_delete_start', 0))
            return df.iloc[num_rows_to_delete_start:]
        
        elif action_type == 'replace_header':
            df.columns = df.iloc[0]
            return df.iloc[1:]
        
        elif action_type == 'delete_last_X_rows':
            num_rows_to_delete_end = int(parameters.get('num_rows_to_delete_end', 0))
            return df.iloc[:-num_rows_to_delete_end] if num_rows_to_delete_end else df
        
        else:
            print(f"Unknown action type: {action_type}")
            return df
    
    except Exception as e:
        print(f"Error applying action {action_type} with parameters {parameters}: {str(e)}")
        return df

def summary(request):
    temp_file_path = request.session.get('temp_file_path')
    file_path = request.session.get('file_path')
    df_v1 = load_dataframe_from_file(temp_file_path)
    print(file_path)
        # Extract the relative path using MEDIA_ROOT
    relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT).replace('\\', '/')
    print(relative_path)

    try:
        uploaded_file_instance = UploadedFile.objects.get(file=relative_path)
    except UploadedFile.DoesNotExist:
        # Handle the case where the UploadedFile instance doesn't exist
        messages.error(request, "The file you're working on could not be found.")
        return redirect('main_page')  # Redirect to a safe page
    # identifies emty columns
    empty_cols = df_v1.columns[df_v1.isna().all()].tolist()

    if request.method == 'POST':
        # deletes all empty rows
        if 'remove_empty_rows' in request.POST:
            initial_row_count = df_v1.shape[0]
            df_v1 = remove_empty_rows(df_v1)
            final_row_count = df_v1.shape[0]
            rows_removed = initial_row_count - final_row_count

            messages.success(request, f'{rows_removed} empty rows removed.')

            record_action(
                uploaded_file=uploaded_file_instance,        
                action_type='remove_empty_rows',
                parameters={},
                user=request.user,
                session_id=request.session.session_key,
                )
           
        # deletes selected columns
        if 'remove_empty_cols' in request.POST:
            initial_col_count = df_v1.shape[1]
            cols_to_delete = request.POST.getlist('remove_empty_cols')
            df_v1 = df_v1.drop(columns=cols_to_delete)
            final_col_count = df_v1.shape[1]
            cols_removed = initial_col_count - final_col_count

            messages.success(request, f'{cols_removed} empty columns removed.')
            record_action(        
                    uploaded_file=uploaded_file_instance,
                    action_type='remove_empty_cols',
                    parameters={'cols_to_delete': cols_to_delete},
                    user=request.user,
                    session_id=request.session.session_key,
                    )

        num_rows_to_delete_start = request.POST.get('num_rows_to_delete_start')
        replace_header = 'replace_header' in request.POST
        num_rows_to_delete_end = request.POST.get('num_rows_to_delete_end')

        # check if num_rows_to_delete_start is not None and convert to int, else default to 0
        num_rows_to_delete_start = int(num_rows_to_delete_start) if num_rows_to_delete_start else 0
        

        # deletes the first X rows
        if num_rows_to_delete_start > 0:
            df_v1 = df_v1.iloc[num_rows_to_delete_start:]
            messages.success(request, f'First {num_rows_to_delete_start} deleted successfully.')
            record_action(        
                    uploaded_file=uploaded_file_instance,
                    action_type='delete_first_X_rows',
                    parameters={'num_rows_to_delete_start': num_rows_to_delete_start},
                    user=request.user,
                    session_id=request.session.session_key,
                    )
        
        # if replace_header is True, set the df columns to the first row's values
        if replace_header:
            df_v1.columns = df_v1.iloc[0]
            df_v1 = df_v1.iloc[1:]
            record_action(        
                    uploaded_file=uploaded_file_instance,
                    action_type='replace_header',
                    parameters={},
                    user=request.user,
                    session_id=request.session.session_key,
                    )

        # checks if num_rows_to_delete_end is not None and convert to int, else default to 0
        num_rows_to_delete_end = int(num_rows_to_delete_end) if num_rows_to_delete_end else 0
        
        # deletes the last X rows
        if num_rows_to_delete_end > 0:
            df_v1 = df_v1.iloc[:-num_rows_to_delete_end]
            messages.success(request, f'Last {num_rows_to_delete_end} deleted successfully.')
            record_action(        
                    uploaded_file=uploaded_file_instance,
                    action_type='delete_last_X_rows',
                    parameters={'num_rows_to_delete_end': num_rows_to_delete_end},
                    user=request.user,
                    session_id=request.session.session_key,
                    )
        
        temp_file_path = save_dataframe(df_v1, temp_file_path)
        # updates the session with the new file path
        request.session['temp_file_path'] = temp_file_path
        # redirects to avoid resubmit on refresh
        return redirect('summary')

    context = {
        'num_rows': df_v1.shape[0],
        'num_cols': df_v1.shape[1],
        'col_names': df_v1.columns.tolist(),
        'num_empty_rows': df_v1[df_v1.isna().all(axis=1)].shape[0],
        'num_empty_cols': df_v1.columns[df_v1.isna().all(axis=0)].size,
        'empty_cols': empty_cols,
        'table': dataframe_to_html(df_v1, classes='table table-striped'),
        'original_file_name': os.path.basename(file_path),
        'previous_page_url': 'main_page',
        'active_page': 'summary',
        'next_page_url': 'edit_columns',
    }
    
    return render(request, '2_file_summary.html', context)

def edit_columns(request):
    temp_file_path = request.session.get('temp_file_path')
    file_path = request.session.get('file_path')
    # Extract the relative path using MEDIA_ROOT
    relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT).replace('\\', '/')

    try:
        uploaded_file_instance = UploadedFile.objects.get(file=relative_path)
    except UploadedFile.DoesNotExist:
        # Handle the case where the UploadedFile instance doesn't exist
        messages.error(request, "The file you're working on could not be found.")
        return redirect('main_page')  # Redirect to a safe page
    df_v2 = load_dataframe_from_file(temp_file_path)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_column':
            new_column_name = request.POST.get('new_column_name')
            print(f"New column name: {new_column_name}")  
            if new_column_name:
                df_v2[new_column_name] = None
            messages.success(request, f'Column "{new_column_name}" added successfully.')
            record_action(
                uploaded_file=uploaded_file_instance,        
                action_type='add_column',
                parameters={'new_column_name': new_column_name},
                user=request.user,
                session_id=request.session.session_key,
            )



            # handles deleting selected columns
        elif action == 'delete_columns':
            columns_to_delete = request.POST.getlist('columns_to_delete')
            df_v2.drop(columns=columns_to_delete, inplace=True)
            messages.success(request, f'{len(columns_to_delete)} columns deleted successfully.')
            record_action(
                uploaded_file=uploaded_file_instance,        
                action_type='delete_columns',
                parameters={'columns_to_delete': columns_to_delete},
                user=request.user,
                session_id=request.session.session_key,
            )


        elif action == 'fill_column':
            column_to_fill = request.POST.get('column_to_fill')
            fill_value = request.POST.get('fill_value')
            fill_option = request.POST.get('fill_option')

            if column_to_fill and fill_value is not None:
                if fill_option == 'all':
                    df_v2[column_to_fill] = fill_value
                elif fill_option == 'empty':
                    df_v2[column_to_fill].fillna(fill_value, inplace=True)
            messages.success(request, f'Column "{column_to_fill}" filled successfully with "{fill_value}".')

            record_action(
                uploaded_file=uploaded_file_instance,        
                action_type='fill_column',
                parameters={
                    'column_to_fill': column_to_fill,
                    'fill_value': fill_value,
                    'fill_option': fill_option
                },
                user=request.user,
                session_id=request.session.session_key,
            )


        elif action == 'split_column':
            column_to_split = request.POST.get('column_to_split')
            split_value = request.POST.get('split_value')
            delete_original = 'delete_original' in request.POST

            if column_to_split in df_v2.columns and split_value:
                # performs the split operation
                split_data = df_v2[column_to_split].str.split(split_value, expand=True)
                for i, new_column in enumerate(split_data.columns):
                    new_column_name = f"{column_to_split}_split_{i+1}"
                    df_v2[new_column_name] = split_data[new_column]

                # if user opted to delete the original column, drop it
                if delete_original:
                    df_v2.drop(columns=[column_to_split], inplace=True)
            messages.success(request, f'Column "{column_to_split}" split successfully.')
            record_action(
                uploaded_file=uploaded_file_instance,        
                action_type='split_column',
                parameters={
                    'column_to_split': column_to_split,
                    'split_value': split_value,
                    'delete_original': delete_original
                },
                user=request.user,
                session_id=request.session.session_key,
            )


        elif action == 'merge_columns':
            columns_to_merge = request.POST.getlist('columns_to_merge')
            merge_separator = request.POST.get('merge_separator', '')
            new_column_name = request.POST.get('new_merge_column_name')

            if not new_column_name:
                new_column_name = 'merged_column'

            if columns_to_merge:
                # performs the merge operation
                df_v2[new_column_name] = df_v2[columns_to_merge].astype(str).apply(merge_separator.join, axis=1)
            messages.success(request, f'Columns merged into "{new_column_name}" successfully.')
            record_action(
                uploaded_file=uploaded_file_instance,        
                action_type='merge_columns',
                parameters={
                    'columns_to_merge': columns_to_merge,
                    'merge_separator': merge_separator,
                    'new_column_name': new_column_name
                },
                user=request.user,
                session_id=request.session.session_key,
            )


        elif action == 'rename_column':
            column_to_rename = request.POST.get('column_to_rename')
            new_column_name = request.POST.get('new_renamed_column_name')

            if column_to_rename in df_v2.columns and new_column_name:
                df_v2.rename(columns={column_to_rename: new_column_name}, inplace=True)
                save_dataframe(df_v2, temp_file_path)
            messages.success(request, f'Column "{column_to_rename}" renamed to "{new_column_name}" successfully.')
            record_action(
                uploaded_file=uploaded_file_instance,        
                action_type='rename_column',
                parameters={
                    'column_to_rename': column_to_rename,
                    'new_column_name': new_column_name
                },
                user=request.user,
                session_id=request.session.session_key,
            )

            
        save_dataframe(df_v2, temp_file_path)
        return redirect('edit_columns')

    context = {
        'previous_page_url': 'summary',
        'active_page': 'edit_columns',
        'next_page_url': 'edit_data',
        'table': dataframe_to_html(df_v2, classes='table table-striped'),
        'original_file_name': os.path.basename(file_path),
        'df_v2': df_v2,  # passes the df to the template context
    }
    return render(request, '3_edit_columns.html', context)

def edit_data(request):

    temp_file_path = request.session.get('temp_file_path')
    file_path = request.session.get('file_path')
    # Extract the relative path using MEDIA_ROOT
    relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT).replace('\\', '/')

    try:
        uploaded_file_instance = UploadedFile.objects.get(file=relative_path)
    except UploadedFile.DoesNotExist:
        # Handle the case where the UploadedFile instance doesn't exist
        messages.error(request, "The file you're working on could not be found.")
        return redirect('main_page')  # Redirect to a safe page
    df_v3 = load_dataframe_from_file(temp_file_path)
    if request.method == 'POST':
        print("POST request received")  # this should always print when a form is submitted
        action = request.POST.get('action')
        print(f"Action received: {action}")  # prints the action value


        if action == 'delete_data':
            columns_to_modify = request.POST.getlist('columns_to_modify')
            delimiter = request.POST.get('delimiter')
            delete_option = request.POST.get('delete_option')
            include_delimiter = 'include_delimiter' in request.POST
            apply_to_all = '__all__' in columns_to_modify

            if apply_to_all:
                columns_to_modify = df_v3.columns.tolist()  # lists all columns if '--ALL COLUMNS--' is selected

            for column in columns_to_modify:
                if column in df_v3.columns:
                    # converts entire column to strings, replacing NaN with empty strings
                    column_series = df_v3[column].fillna('').astype(str)
                    try:
                        # print(f"Before operation: {column_series.head()}")
                        if include_delimiter:
                            # if the user wants to delete the delimiter along with the data
                            if delete_option == 'before':
                                df_v3[column] = column_series.apply(lambda x: x.split(delimiter)[-1] if delimiter in x else x)
                            elif delete_option == 'after':
                                df_v3[column] = column_series.apply(lambda x: x.split(delimiter)[0] if delimiter in x else x)
                        else:
                            # if the user wants to keep the delimiter
                            if delete_option == 'before':
                                df_v3[column] = column_series.apply(lambda x: x.split(delimiter, 1)[-1] if delimiter in x else x)
                            elif delete_option == 'after':
                                # appends the delimiter after the operation if it's not to be deleted
                                df_v3[column] = column_series.apply(lambda x: delimiter + x.split(delimiter, 1)[-1] if delimiter in x else x)
                                # print(f"After operation: {df_v3[column].head()}")
                    except Exception as e:
                        print(f"Error processing column {column}: {e}")
            messages.success(request, f'Data deleted successfully based on your criteria.')
            record_action(
                uploaded_file=uploaded_file_instance,        
                action_type='delete_data',
                parameters={
                    'columns_to_modify': columns_to_modify,
                    'delimiter': delimiter,
                    'delete_option': delete_option
                },
                user=request.user,
                session_id=request.session.session_key,
            )



        elif action == 'replace_symbol':
            columns_to_replace = request.POST.getlist('columns_to_replace')
            old_symbol = request.POST.get('old_symbol')
            new_symbol = request.POST.get('new_symbol')
            # defaults to False if the checkbox is not checked
            case_sensitive = 'case_sensitive' in request.POST
            apply_to_all = '__all__' in columns_to_replace

            if apply_to_all:
                columns_to_replace = df_v3.columns.tolist()  # lists all columns if '--ALL COLUMNS--' is selected


            for column in columns_to_replace:
                if column in df_v3.columns:
                    try:
                        #print(f"Before operation: {df_v3[column].head()}")
                        if case_sensitive:
                            # case sensitive replacement
                            df_v3[column] = df_v3[column].str.replace(old_symbol, new_symbol, regex=True)
                        else:
                            # case insensitive replacement
                            df_v3[column] = df_v3[column].str.replace(old_symbol, new_symbol, case=False, regex=True)
                        #print(f"After operation: {df_v3[column].head()}")
                    except Exception as e:
                        print(f"Error processing column {column}: {e}")
            messages.success(request, f'Symbols replaced successfully.')
            record_action(
                uploaded_file=uploaded_file_instance,        
                action_type='replace_symbol',
                parameters={
                    'columns_to_replace': columns_to_replace if not apply_to_all else 'All Columns',
                    'old_symbol': old_symbol,
                    'new_symbol': new_symbol,
                    'case_sensitive': case_sensitive
                },
                user=request.user,
                session_id=request.session.session_key,
            )

            

        elif action == 'validate_data':
            columns_to_validate = request.POST.getlist('columns_to_validate')
            validation_type = request.POST.get('validation_type')
            regex_pattern = request.POST.get('regex_pattern')
            ignore_whitespace = 'ignore_whitespace' in request.POST
            apply_to_all = '__all__' in columns_to_validate

            if apply_to_all:
                columns_to_validate = df_v3.columns.tolist()

            invalid_rows = {}

            for column in columns_to_validate:
                if column in df_v3.columns:
                    column_series = df_v3[column].fillna('').astype(str)
                    invalid_rows[column] = []

                    for index, value in column_series.items():
                        if ignore_whitespace:
                            value = value.replace(' ', '')

                        if validation_type == 'letters' and not value.isalpha():
                            invalid_rows[column].append(index)
                        elif validation_type == 'numbers' and not value.isdigit():
                            invalid_rows[column].append(index)
                        elif validation_type == 'no_specials' and not value.isalnum():
                            invalid_rows[column].append(index)
                        elif validation_type == 'regex' and not re.match(regex_pattern, value):
                            invalid_rows[column].append(index)

            # TODO process and display invalid rows in the table
            print(f"Invalid rows: {invalid_rows}")

        elif action == 'check_duplicates':
            columns_to_check = request.POST.getlist('columns_to_check_duplicates')
            if columns_to_check:
                if '__all__' in columns_to_check:
                    columns_to_check = df_v3.columns.tolist()

                duplicates = df_v3[df_v3.duplicated(subset=columns_to_check, keep=False)]
                duplicates.sort_values(by=columns_to_check, inplace=True)

                # converts df to JSON
                duplicates_json = duplicates.to_json(orient='records')

                # sets the JSON data in the session
                request.session['duplicates_json'] = duplicates_json
            print(f"Found {len(duplicates)} duplicates")
            # TODO implement filter for all duplicate values in the table        

        save_dataframe(df_v3, temp_file_path)
        return redirect('edit_data')
    
    context = {
        # 'num_empty_rows': df[df.isna().all(axis=1)].shape[0],
        # 'num_empty_cols': df.columns[df.isna().all(axis=0)].size,
        'previous_page_url': 'edit_columns',
        'active_page': 'edit_data',
        'next_page_url': 'download',
        'table': dataframe_to_html(df_v3, classes='table table-striped'),
        'original_file_name': os.path.basename(file_path),
        'df_v3': df_v3,  # Pass the df to the template context
        'duplicates_json': request.session.get('duplicates_json', '[]'),  # pass the duplicates as JSON
        #'showing_duplicates': 'duplicates_json' in request.session and bool(request.session['duplicates_json'])
    }
    
    return render(request, '4_edit_data.html', context)




def download(request):
    temp_file_path = request.session.get('temp_file_path', 'data')  # default to 'data'
    file_path = request.session.get('file_path', 'data')
    context = {
        'original_file_name': os.path.basename(file_path),
        'previous_page_url': 'edit_columns',
        'active_page': 'download',
        'next_page_url': None  # to disable pagination
    }
    file_format = request.GET.get('format')
    print(f"File format: {file_format}")

    ############# for filtering from db session activities for template creation
    ############# actions_for_session = Action.objects.filter(session_id=some_session_key)

    
    if file_format:
        
        original_file_name = os.path.basename(file_path)
        original_file_dir = os.path.dirname(file_path)  # get the directory of the original file
        
        print(f"Original file name: {original_file_name}")
        df = load_dataframe_from_file(temp_file_path)
        print(df.head())
        file_name_no_ext, _ = os.path.splitext(original_file_name)

        # generate the new filename
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
                # handle unexpected format
                return HttpResponse("Unexpected format", status=400)
                
        response['Content-Disposition'] = f'attachment; filename="{new_file_name}.{file_format}"'
        return response
    else:
        # if no format is specified, render the HTML page
        return render(request, '5_download.html', context)




 