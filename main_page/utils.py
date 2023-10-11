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
    df.columns = [f"{col}<br>({str(dtype)})" for col, dtype in zip(df.columns, df.dtypes)]
    
    # Convert NaN values to an empty string and convert DataFrame to HTML
    return df.fillna('').to_html(classes=classes, escape=False)

def remove_empty_rows(df):
    """Remove all rows from a DataFrame that contain only NaN values."""
    return df.dropna(how='all')
