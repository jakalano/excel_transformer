import os
import csv
import re
from datetime import datetime
import pandas as pd
from .models import Action, Template, UploadedFile

def detect_delimiter(file_path, num_lines=5):
    # detect the delimiter of a csv file
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        # read the first few lines of the file
        lines = [file.readline().strip() for _ in range(num_lines)]
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(''.join(lines)).delimiter
    return delimiter

def load_dataframe_from_file(file_path):
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == '.csv':
        delimiter = detect_delimiter(file_path)
        return pd.read_csv(file_path, delimiter=delimiter, encoding='utf8', dtype=str)
    elif file_extension in ['.xlsx', '.xls']:
        return pd.read_excel(file_path, engine='openpyxl')
    elif file_extension == '.json':
        return pd.read_json(file_path, dtype=str)
    elif file_extension == '.xml':
        return pd.read_xml(file_path, dtype=str)
    elif file_extension == '.tsv':
        return pd.read_csv(file_path, delimiter='\t', encoding='utf8', dtype=str)
    else:
        raise ValueError("Unsupported file type: {}".format(file_extension))

    
def save_dataframe(data, save_path, file_format=None):

    # check if data is a dictionary and extract DataFrame if necessary
    if isinstance(data, dict) and 'dataframe' in data:
        df = data['dataframe']
    elif isinstance(data, pd.DataFrame):
        df = data
    else:
        raise ValueError("Invalid data type for saving. Expected a DataFrame or a dictionary containing a DataFrame.")


    # get file format from save_path if not provided
    if file_format is None:
        _, file_format = os.path.splitext(save_path)
        file_format = file_format.lstrip('.')
    
    # ensure file has correct extension
    if not save_path.endswith(f'.{file_format}'):
        save_path = f'{save_path}.{file_format}'

    # ensure dir exists
    save_dir = os.path.dirname(save_path)
    os.makedirs(save_dir, exist_ok=True)

    # save the df in the specified format
    if file_format == 'csv':
        df.to_csv(save_path, index=False)
    elif file_format == 'xlsx':
        df.to_excel(save_path, index=False, engine='openpyxl')
    elif file_format == 'json':
        df.to_json(save_path, orient='records', force_ascii=False)
    elif file_format == 'xml':
        df = sanitize_column_names(df)
        df.to_xml(save_path, index=False, root_name='Root', row_name='Row')
    elif file_format == 'tsv':
        df.to_csv(save_path, index=False, sep='\t')
    else:
        raise ValueError(f"Unsupported file format: {file_format}")
    
    return save_path

def sanitize_column_names(df):
    """Sanitize column names to make them valid XML tag names."""
    def valid_xml_tag(col):
        # replace invalid characters with underscore
        # allow alphanumeric characters, including non-standard letters
        col = re.sub(r'[^\w]', '_', col, flags=re.UNICODE)
        # prefix with 'col_' if the column name starts with a digit
        if col[0].isdigit():
            col = 'col_' + col
        return col

    df.columns = [valid_xml_tag(col) for col in df.columns]
    return df

def dataframe_to_html(df, classes=None):

    df.columns = [col for col, dtype in zip(df.columns, df.dtypes)]

    # convert NaN values to an empty string and convert df to HTML
    return df.fillna('').to_html(classes=classes, escape=False)



def record_action(uploaded_file, action_type, parameters, user, session_id, df_backup=None):

    # check if the user is authenticated
    if user.is_authenticated:
        user_instance = user
    else:
        user_instance = None  

    # fetch the UploadedFile instance
    uploaded_file_instance = UploadedFile.objects.get(file=uploaded_file)


    action = Action.objects.create(
        uploaded_file=uploaded_file_instance,
        user=user_instance,
        action_type=action_type,
        parameters=parameters,
        session_id=session_id,
    )

    # if there's a backup df, store it
    if df_backup is not None:
        backup_path = f'backups/{action.id}_backup.csv'  # define a path for backup
        df_backup.to_csv(backup_path)
        action.backup_data_path = backup_path
        action.save()

    return action


def save_as_template(user, actions, template_name):

    template = Template.objects.create(name=template_name, user=user)
    template.actions.add(*actions)
    return template

def get_actions_for_session(session_key, uploaded_file, exclude_last_action=False):
    print(f"Retrieving actions for session: {session_key}, uploaded file: {uploaded_file}")

    # filter out actions that are already undone
    actions = Action.objects.filter(session_id=session_key, uploaded_file=uploaded_file, undone=False)
    print(f"Initial actions found: {actions}")

    if exclude_last_action and actions.exists():
        # get the last action that has not been undone
        last_action = actions.latest('timestamp')
        print(f"Excluding last action: {last_action}")
        actions = actions.exclude(id=last_action.id)
    else:
        print("Not excluding last action.")

    print(f"Final actions returned: {actions}")
    return actions



def action_to_dict(action):

    return {
        'action_type': action.action_type,
        'parameters': action.parameters,
        'timestamp': action.timestamp.isoformat(),  # convert datetime to string
    }

################## summary view actions ###################


def handle_remove_empty_rows(df):
    try:
        initial_row_count = df.shape[0]
        df = df.dropna(how='all')
        final_row_count = df.shape[0]
        rows_removed = initial_row_count - final_row_count
        return {'dataframe': df, 'rows_removed': rows_removed}
    except Exception as e:
        raise ValueError(f"Error while removing empty rows: {e}")

def handle_remove_empty_cols(df, cols_to_delete):
    try:
        initial_col_count = df.shape[1]
        df = df.drop(columns=cols_to_delete)
        final_col_count = df.shape[1]
        cols_removed = initial_col_count - final_col_count
        return {'dataframe': df, 'cols_removed': cols_removed}
    except Exception as e:
        raise ValueError(f"Error while removing empty columns: {e}")

def handle_delete_first_x_rows(df, num_rows_to_delete_start):
    try:
        initial_row_count = df.shape[0]
        df = df.iloc[num_rows_to_delete_start:]
        final_row_count = df.shape[0]
        rows_deleted = initial_row_count - final_row_count
        return {'dataframe': df, 'rows_deleted': rows_deleted}
    except Exception as e:
        raise ValueError(f"Error while deleting the first {num_rows_to_delete_start} rows: {e}")

def handle_delete_last_x_rows(df, num_rows_to_delete_end):
    try:
        initial_row_count = df.shape[0]
        if num_rows_to_delete_end > 0:
            df = df.iloc[:-num_rows_to_delete_end]
        final_row_count = df.shape[0]
        rows_deleted = initial_row_count - final_row_count
        return {'dataframe': df, 'rows_deleted': rows_deleted}
    except Exception as e:
        raise ValueError(f"Error while deleting the last {num_rows_to_delete_end} rows: {e}")


def handle_replace_header_with_first_row(df):
    try:
        df.columns = df.iloc[0]
        return df.iloc[1:]
    except Exception as e:
        raise ValueError("Error while replacing header with the first row: {e}")


################## edit_columns view actions ###################

def add_column(df, new_column_name):
    df[new_column_name] = None
    return df

def delete_columns(df, columns_to_delete):
    df.drop(columns=columns_to_delete, inplace=True)
    return df

def fill_column(df, column_to_fill, fill_value, fill_option):
    if fill_option == 'all':
        df[column_to_fill] = fill_value
    elif fill_option == 'empty':
        df[column_to_fill].fillna(fill_value, inplace=True)
    return df

def split_column(df, column_to_split, split_value, delete_original, ignore_repeated):
    temp_column = column_to_split + "_temp"

    if ignore_repeated:
        # use a temp column to handle repeated split values
        df[temp_column] = df[column_to_split].str.replace(f'{split_value}+', split_value, regex=True)
    else:
        df[temp_column] = df[column_to_split]

    split_data = df[temp_column].str.split(split_value, expand=True)
    for i, new_column in enumerate(split_data.columns):
        new_column_name = f"{column_to_split}_split_{i+1}"
        df[new_column_name] = split_data[new_column]

    # clean up: remove the temp column and optionally the original column
    df.drop(columns=[temp_column], inplace=True)
    if delete_original:
        df.drop(columns=[column_to_split], inplace=True)

    return df

def merge_columns(df, columns_to_merge, merge_separator, new_column_name, delete_original):
    if not new_column_name:
        # use a counter to create a unique name
        existing_columns = [col for col in df.columns if col.startswith('merged_column_')]
        new_column_index = len(existing_columns) + 1
        new_column_name = f'merged_column_{new_column_index}'
    df[new_column_name] = df.apply(
        lambda row: merge_separator.join(
            [str(row[col]) for col in columns_to_merge if pd.notna(row[col])]
        ),
        axis=1
    )
    if delete_original:
        df.drop(columns=columns_to_merge, inplace=True)
    return {'dataframe': df, 'new_column_name': new_column_name}

def rename_column(df, column_to_rename, new_column_name):
    df.rename(columns={column_to_rename: new_column_name}, inplace=True)
    return df

################## edit_data view actions ###################

def delete_data(df, columns_to_modify, delimiter, delete_option, include_delimiter, case_sensitive=False):
    for column in columns_to_modify:
        if column in df.columns:
            column_series = df[column].fillna('').astype(str)
            try:
                if case_sensitive:
                    # case sensitive: use the provided delimiter as is
                    pattern = re.escape(delimiter)
                else:
                    # case insensitive: use re.IGNORECASE flag
                    pattern = '(?i)' + re.escape(delimiter)

                if include_delimiter:
                    if delete_option == 'before':
                        # deletes everything before the delimiter, including the delimiter itself
                        df[column] = column_series.apply(lambda x: ''.join(re.split(pattern, x)[1:]) if re.search(pattern, x) else x)
                    elif delete_option == 'after':
                        # deletes everything after the delimiter and the delimiter itself
                        df[column] = column_series.apply(lambda x: re.split(pattern, x, 1)[0] if re.search(pattern, x) else x)
                else:
                    if delete_option == 'before':
                        # deletes everything before the delimiter but leaves the delimiter alone
                        df[column] = column_series.apply(lambda x: delimiter + ''.join(re.split(pattern, x)[1:]) if re.search(pattern, x) else x)

                    elif delete_option == 'after':
                        # deletes everything after the delimiter but leaves the delimiter alone
                        df[column] = column_series.apply(lambda x: re.split(pattern, x, 1)[0] + delimiter if re.search(pattern, x) else x)


            except Exception as e:
                raise ValueError(f"Error processing column {column}: {e}")
    return df



def replace_symbol(df, columns_to_replace, old_symbol, new_symbol, case_sensitive):
    for column in columns_to_replace:
        if column in df.columns:
            try:
                #print(f"Before operation: {df_v3[column].head()}")
                if case_sensitive:
                    # case sensitive replacement
                    df[column] = df[column].str.replace(old_symbol, new_symbol, regex=True)
                else:
                    # case insensitive replacement
                    df[column] = df[column].str.replace(old_symbol, new_symbol, case=False, regex=True)
                #print(f"After operation: {df_v3[column].head()}")
            except Exception as e:
                print(f"Error processing column {column}: {e}")
    return df

def trim_and_replace_multiple_whitespaces(df, columns_to_modify=None, replace_all=False):
    # if replace_all is True, set columns_to_modify to all columns.
    if replace_all:
        columns_to_modify = df.columns.tolist()
    elif not columns_to_modify:
        # if columns_to_modify is None or empty, modify all columns
        columns_to_modify = df.columns.tolist()
    
    for column in columns_to_modify:
        if column in df.columns:
            try:
            # uses regex to replace multiple spaces with a single space and strip leading/trailing spaces.
                df[column] = df[column].astype(str).apply(lambda x: re.sub(r'\s+', ' ', x).strip())
            except Exception as e:
                print(f"Error processing column {column}: {e}")
    return df

def change_case(df, columns, case_type):
    for column in columns:
        if column in df.columns:
            if case_type == 'upper':
                df[column] = df[column].str.upper()
            elif case_type == 'lower':
                df[column] = df[column].str.lower()
            elif case_type == 'title':
                df[column] = df[column].str.title()
            elif case_type == 'sentence':
                df[column] = df[column].apply(lambda x: x.capitalize() if isinstance(x, str) else x)
    return df
