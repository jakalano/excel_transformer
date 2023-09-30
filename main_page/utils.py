import os
import csv
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
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == '.csv':
        delimiter = detect_delimiter(file_path)
        print(delimiter)  # for debugging
        return pd.read_csv(file_path, delimiter=delimiter)
    
    elif file_extension in ['.xlsx', '.xls']:
        return pd.read_excel(file_path)
    
    else:
        raise ValueError("Unsupported file type: {}".format(file_extension))