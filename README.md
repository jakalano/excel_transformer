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
- implement better data manipulation for column merge in cases of all values NaN or some values NaN. currently merging | *empty* | *empty* | a | results in nan/nan/a
- disappearing pop-up after each action about how many values were changed
- fix split_column on repeating symbols (e.g., "aaaaa" split with value aa creates three new columns: *empty* | *empty* | a )
- merge_columns no longer renames the column with the user-given custom name, defaults to merged_column
- add "delete original columns" option to merge_columns
- add "trim spaces" function
- implement visual feedback to validate_data and check_duplicates



# error log fixed
- remove empty NaN rows
- remove empty NaN columns
- move the save dataframe function from views to utils
- fix how numbers are displayed
- add_column is now broken, doesn't do anything
- split input submissions to separate forms
- include a display cutoff point in the case of extremely long column names