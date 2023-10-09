import os
import csv
import re
from datetime import datetime
import pandas as pd

def detect_delimiter(file_path, num_lines=5):
    # detect the delimiter of a csv file
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        # read the first few lines of the file
        lines = [file.readline().strip() for _ in range(num_lines)]
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(''.join(lines)).delimiter
    return delimiter

def load_dataframe_from_file(original_file_path, view_name):
    """
    Load the latest version of a DataFrame from the directory where the original file is stored.

    :param original_file_path: Path to the original file
    :param view_name: Name of the view or stage
    :return: The loaded DataFrame
    """
    dir_name, original_file_name = os.path.split(original_file_path)
    original_name, original_ext = os.path.splitext(original_file_name)

    # Create a pattern that matches versioned files for the current view
    pattern = re.compile(re.escape(view_name + '_' + original_name) + r'_v(\d+)' + re.escape('.csv'))

    # Find all versioned files in the directory
    versioned_files = [f for f in os.listdir(dir_name) if pattern.match(f)]

    # If there are versioned files, use the most recent one. Otherwise, use the original file.
    if versioned_files:
        latest_file = max(versioned_files, key=lambda f: int(pattern.search(f).group(1)))
        file_to_load = os.path.join(dir_name, latest_file)
    else:
        file_to_load = original_file_path
    
    # Determine the file type and load the data accordingly
    file_extension = original_ext

    if file_extension == '.csv':
        delimiter = detect_delimiter(file_to_load)
        return pd.read_csv(file_to_load, delimiter=delimiter, encoding='utf8', dtype=str)
    
    elif file_extension in ['.xlsx', '.xls']:
        return pd.read_excel(file_to_load)
    
    else:
        raise ValueError("Unsupported file type: {}".format(file_extension))
    
def save_dataframe(df, original_file_path, view_name, file_format=None, overwrite=False):
    dir_name, original_file_name = os.path.split(original_file_path)
    original_name, original_ext = os.path.splitext(original_file_name)
    
    pattern = re.compile(re.escape(view_name + '_' + original_name) + r'_v(\d+)' + re.escape('.csv'))
    versioned_files = [f for f in os.listdir(dir_name) if pattern.match(f)]

    if versioned_files and overwrite:
        # Overwrite the latest version
        new_file_name = max(versioned_files, key=lambda f: int(pattern.search(f).group(1)))
    else:
        # Find the latest version number
        if versioned_files:
            latest_file = max(versioned_files, key=lambda f: int(pattern.search(f).group(1)))
            latest_version = int(pattern.search(latest_file).group(1))
        else:
            latest_version = 0  # No versioned file found, start with version 1

        # Create a new version
        new_file_name = f"{view_name}_{original_name}_v{latest_version + 1}.csv"
    
    save_path = os.path.join(dir_name, new_file_name)
    if file_format is None:
        _, file_ext = os.path.splitext(new_file_name)
        file_format = file_ext.lstrip('.')
    
    if file_format == 'csv':
        df.to_csv(save_path, index=False)
    elif file_format == 'xlsx':
        df.to_excel(save_path, index=False, engine='openpyxl')
    elif file_format == 'json':
        df.to_json(save_path, index=False, force_ascii=False)
    elif file_format == 'xml':
        df.to_xml(save_path, index=False)
    else:
        raise ValueError(f"Unsupported file format: {file_format}")

    return save_path


def dataframe_to_html(df, classes=None):
    """Convert a DataFrame to an HTML table."""
    df.columns = [f"{col}<br>({str(dtype)})" for col, dtype in zip(df.columns, df.dtypes)]
    
    # Convert NaN values to an empty string and convert DataFrame to HTML
    return df.fillna('').to_html(classes=classes, escape=False)

def remove_empty_rows(df):
    """Remove all rows from a DataFrame that contain only NaN values."""
    return df.dropna(how='all')
