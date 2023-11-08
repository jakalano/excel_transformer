# excel-failu-parveidotajs
```
create venv in project root folder
pip install -r requirements.txt

excel\Scripts\Activate

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
- rework undo for the system to take snapshots every five actions that the redo -1 will be applied to? would increase performance for large files or long lists of actions. or create snapshots for every view?
- fix undo
- add action recording for every action
- wrap each action in a collapsible wrapper to declutter the views?
- implement better data manipulation for column merge in cases of all values NaN or some values NaN
- disappearing pop-up after each action about how many values were changed


# error log fixed
- remove empty NaN rows
- remove empty NaN columns
- move the save dataframe function from views to utils
- fix how numbers are displayed