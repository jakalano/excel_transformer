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
    """
    Load the latest version of a DataFrame from the directory where the original file is stored.

    :param original_file_path: Path to the original file
    :param view_name: Name of the view or stage
    :return: The loaded DataFrame
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    

    if file_extension == '.csv':
        delimiter = detect_delimiter(file_path)
        return pd.read_csv(file_path, delimiter=delimiter, encoding='utf8', dtype=str)
    
    elif file_extension in ['.xlsx', '.xls']:
        return pd.read_excel(file_path, engine='openpyxl')
    
    else:
        raise ValueError("Unsupported file type: {}".format(file_extension))
    
def save_dataframe(df, save_path, file_format=None):
    """
    Save a DataFrame to a file, optionally in a user-specified format.
    :param df: DataFrame to save
    :param save_path: Path to save the file
    :param file_format: Format to save the file in (optional, if None, infer from save_path)
    """
    # Infer file format from save_path if not provided
    if file_format is None:
        _, file_format = os.path.splitext(save_path)
        file_format = file_format.lstrip('.')
    
    # Ensure file has correct extension
    if not save_path.endswith(f'.{file_format}'):
        save_path = f'{save_path}.{file_format}'

    # Ensure directory exists
    save_dir = os.path.dirname(save_path)
    os.makedirs(save_dir, exist_ok=True)

    # Save the DataFrame in the specified format
    if file_format == 'csv':
        df.to_csv(save_path, index=False)
    elif file_format == 'xlsx':
        df.to_excel(save_path, index=False, engine='openpyxl')
    elif file_format == 'json':
        df.to_json(save_path, force_ascii=False)
    elif file_format == 'xml':
        df.to_xml(save_path, index=False)
    else:
        raise ValueError(f"Unsupported file format: {file_format}")
    
    return save_path

def dataframe_to_html(df, classes=None):
    """Convert a DataFrame to an HTML table."""
    df.columns = [col for col, dtype in zip(df.columns, df.dtypes)]
    
    # Convert NaN values to an empty string and convert DataFrame to HTML
    return df.fillna('').to_html(classes=classes, escape=False)



def record_action(uploaded_file, action_type, parameters, user, session_id, df_backup=None):
    """
    Record an action performed by a user, including a backup of the DataFrame if provided.
    """
    # Check if the user is authenticated
    if user.is_authenticated:
        user_instance = user
    else:
        user_instance = None  

    # Fetch the UploadedFile instance
    uploaded_file_instance = UploadedFile.objects.get(file=uploaded_file)


    action = Action.objects.create(
        uploaded_file=uploaded_file_instance,
        user=user_instance,
        action_type=action_type,
        parameters=parameters,
        session_id=session_id,
    )

    # If there's a backup DataFrame, store it
    if df_backup is not None:
        backup_path = f'backups/{action.id}_backup.csv'  # Define a path for backup
        df_backup.to_csv(backup_path)
        action.backup_data_path = backup_path  # Assuming Action model has a field for this
        action.save()

    return action


def save_as_template(user, actions, template_name):
    """
    Save actions as a template.
    """
    template = Template.objects.create(name=template_name, user=user)
    template.actions.add(*actions)
    return template

def get_actions_for_session(session_key, uploaded_file, exclude_last_action=False):
    """
    Retrieves actions for a given session and uploaded file.
    Optionally excludes the last action.
    """
    actions = Action.objects.filter(session_id=session_key, uploaded_file=uploaded_file)
    if exclude_last_action and actions.exists():
        last_action = actions.latest('timestamp')
        actions = actions.exclude(id=last_action.id)
    return actions

def action_to_dict(action):
    """
    Converts an Action model instance into a dictionary.

    Args:
        action (Action): The Action model instance.

    Returns:
        dict: A dictionary representation of the Action.
    """
    return {
        'action_type': action.action_type,
        'parameters': action.parameters,
        'timestamp': action.timestamp.isoformat(),  # Convert datetime to string
    }

################## summary view actions ###################

def remove_empty_rows(df):
    """Remove all rows from a DataFrame that contain only NaN values."""
    return df.dropna(how='all')

def handle_remove_empty_rows(df):
    initial_row_count = df.shape[0]
    df = df.dropna(how='all')
    final_row_count = df.shape[0]
    rows_removed = initial_row_count - final_row_count
    return df, rows_removed

def handle_remove_empty_cols(df, cols_to_delete):
    initial_col_count = df.shape[1]
    df = df.drop(columns=cols_to_delete)
    final_col_count = df.shape[1]
    cols_removed = initial_col_count - final_col_count
    return df, cols_removed

def handle_delete_first_x_rows(df, num_rows_to_delete_start):
    if num_rows_to_delete_start > 0:
        return df.iloc[num_rows_to_delete_start:]
    return df

def handle_delete_last_x_rows(df, num_rows_to_delete_end):
    if num_rows_to_delete_end > 0:
        return df.iloc[:-num_rows_to_delete_end]
    return df

def handle_replace_header_with_first_row(df):
    df.columns = df.iloc[0]
    return df.iloc[1:]


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

def split_column(df, column_to_split, split_value, delete_original):
    split_data = df[column_to_split].str.split(split_value, expand=True)
    for i, new_column in enumerate(split_data.columns):
        new_column_name = f"{column_to_split}_split_{i+1}"
        df[new_column_name] = split_data[new_column]
    if delete_original:
        df.drop(columns=[column_to_split], inplace=True)
    return df

def merge_columns(df, columns_to_merge, merge_separator, new_column_name):
    if not new_column_name:
        # Use a counter to create a unique name
        existing_columns = [col for col in df.columns if col.startswith('merged_column_')]
        new_column_index = len(existing_columns) + 1
        new_column_name = f'merged_column_{new_column_index}'
    df[new_column_name] = df.apply(
        lambda row: merge_separator.join(
            [str(row[col]) for col in columns_to_merge if pd.notna(row[col])]
        ),
        axis=1
    )
    return df

def rename_column(df, column_to_rename, new_column_name):
    df.rename(columns={column_to_rename: new_column_name}, inplace=True)
    return df

################## edit_data view actions ###################