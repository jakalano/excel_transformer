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
- remove empty NaN rows
- move the save dataframe function from views to utils