# excel-failu-parveidotajs
```
create venv
pip install -r requirements.txt

excel\Scripts\Activate.ps1

py manage.py runserver

python manage.py makemigrations
python manage.py migrate


pip freeze > requirements.txt
```

# error log to fix
- fix csv ingestion issues with different delimiters
- fix excel ingestion encoding issue
- figure out how files should be stored for fastest processing
- add back xml format?
- add odt, tsv formats for both read and save?
- append column headers with text


# error log fixed
- remove empty NaN rows
- remove empty NaN columns
- move the save dataframe function from views to utils
- fix how numbers are displayed