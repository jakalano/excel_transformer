
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from .models import UploadedFile, Action, Template
from django.contrib.auth.models import User
import logging
from unittest.mock import patch
import json

class SummaryViewTest(TestCase):
    def setUp(self):
        # configures logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.client = Client()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.client.login(username='testuser', password='password')

        session = self.client.session
        session['file_path'] = 'media/_TEST_20231223233536/TEMP__TEST.csv'
        session['temp_file_path'] = 'media/_TEST_20231223233536/TEMP__TEST_EDITED.csv'
        session.save()

        self.logger.debug("setUp completed")

    @patch('main_page.views.load_dataframe_from_file')
    @patch('main_page.views.save_dataframe')
    @patch('main_page.views.UploadedFile.objects.get')
    @patch('main_page.models.Action.objects.create')
    def test_remove_empty_rows(self, mock_action_create, mock_get_uploaded_file, mock_save_df, mock_load_df):
        self.logger.info("Testing removal of empty rows")
        # creates a df with some empty rows
        df = pd.DataFrame({'A': [1, np.nan, 3], 'B': [4, np.nan, np.nan]})
        print("Original DataFrame before removing empty rows:", df)
        mock_load_df.return_value = df
        mock_get_uploaded_file.return_value = UploadedFile(file='media/_TEST_20231223233536/TEMP__TEST.csv')
        mock_save_df.side_effect = lambda df, path: path  # mocks saving and returns path

        url = reverse('summary')
        response = self.client.post(url, {
            'remove_empty_rows': 'Remove Empty Rows'
        })

        updated_df = mock_save_df.call_args[0][0]
        # checks that the empty row has been removed
        print("Updated DataFrame after removing empty rows:", updated_df)

        self.assertEqual(len(updated_df), 2)
        self.assertFalse(updated_df.isna().all(axis=1).any())
        self.assertEqual(response.status_code, 302)  # assuming redirect after operation
        self.logger.debug(f"Response status code: {response.status_code}")
        self.logger.debug(f"Updated DataFrame: {updated_df}")

    @patch('main_page.views.load_dataframe_from_file')
    @patch('main_page.views.save_dataframe')
    @patch('main_page.views.UploadedFile.objects.get')
    @patch('main_page.models.Action.objects.create')
    def test_remove_empty_columns(self, mock_action_create, mock_get_uploaded_file, mock_save_df, mock_load_df):
        # creates a df with some empty columns
        df = pd.DataFrame({'A': [1, 2, 3], 'B': [np.nan, np.nan, np.nan], 'C': [4, 5, 6]})
        print("Original DataFrame before removing empty columns:", df)
        mock_load_df.return_value = df
        mock_get_uploaded_file.return_value = UploadedFile(file='media/_TEST_20231223233536/TEMP__TEST.csv')
        mock_save_df.side_effect = lambda df, path: path  # mocks saving and returns path

        url = reverse('summary')
        response = self.client.post(url, {
            'remove_empty_cols': ['B']  # assuming 'B' is the name of the empty column
        })

        updated_df = mock_save_df.call_args[0][0]
        print("Updated DataFrame after removing empty columns:", updated_df)

        self.assertNotIn('B', updated_df.columns)  # checks that column 'B' has been removed
        self.assertEqual(response.status_code, 302)

    @patch('main_page.views.load_dataframe_from_file')
    @patch('main_page.views.save_dataframe')
    @patch('main_page.views.UploadedFile.objects.get')
    @patch('main_page.models.Action.objects.create')
    def test_delete_first_x_rows(self, mock_action_create, mock_get_uploaded_file, mock_save_df, mock_load_df):
        df = pd.DataFrame({'A': range(10), 'B': range(10, 20)})
        print("Original DataFrame before deleting first 3 rows:", df)
        mock_load_df.return_value = df
        mock_get_uploaded_file.return_value = UploadedFile(file='media/_TEST_20231223233536/TEMP__TEST.csv')
        mock_save_df.side_effect = lambda df, path: path  # mocks saving and returns path

        url = reverse('summary')
        response = self.client.post(url, {
            'num_rows_to_delete_start': '3'  # assuming we want to delete the first 3 rows
        })

        updated_df = mock_save_df.call_args[0][0]
        print("Updated DataFrame after deleting first 3 rows:", updated_df)
        self.assertEqual(len(updated_df), 7)  # checks that 3 rows have been removed
        self.assertEqual(response.status_code, 302)

    @patch('main_page.views.load_dataframe_from_file')
    @patch('main_page.views.save_dataframe')
    @patch('main_page.views.UploadedFile.objects.get')
    @patch('main_page.models.Action.objects.create')
    def test_delete_last_x_rows(self, mock_action_create, mock_get_uploaded_file, mock_save_df, mock_load_df):
        df = pd.DataFrame({'A': range(10), 'B': range(10, 20)})
        print("Original DataFrame before deleting last 2 rows:", df)
        mock_load_df.return_value = df
        mock_get_uploaded_file.return_value = UploadedFile(file='media/_TEST_20231223233536/TEMP__TEST.csv')
        mock_save_df.side_effect = lambda df, path: path  # mocks saving and returns path

        url = reverse('summary')
        response = self.client.post(url, {
            'num_rows_to_delete_end': '2'  # assuming we want to delete the last 2 rows
        })

        updated_df = mock_save_df.call_args[0][0]
        print("Updated DataFrame after deleting last 2 rows:", updated_df)
        self.assertEqual(len(updated_df), 8)  # checks that 2 rows have been removed
        self.assertEqual(response.status_code, 302)



class EditColumnsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        # creates a test user and losg in
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.client.login(username='testuser', password='password')

        session = self.client.session
        session['file_path'] = 'media/_TEST_20231223233536/TEMP__TEST.csv'
        session['temp_file_path'] = 'media/_TEST_20231223233536/TEMP__TEST_EDITED.csv'
        session.save()

    @patch('main_page.views.load_dataframe_from_file')
    @patch('main_page.views.save_dataframe')
    @patch('main_page.views.UploadedFile.objects.get')
    @patch('main_page.models.Action.objects.create')  # mocks the Action create method
    def test_add_column(self, mock_action_create, mock_get_uploaded_file, mock_save_df, mock_load_df):
        df = pd.DataFrame({'existing_column': [1, 2, 3]})
        print("Original DataFrame columns:", df.columns.tolist())
        mock_load_df.return_value = df
        mock_get_uploaded_file.return_value = UploadedFile(file='media/_TEST_20231223233536/TEMP__TEST.csv')

        # prevents the Action create method from attempting to save
        mock_action_create.return_value = MagicMock(spec=Action)

        url = reverse('edit_columns')
        response = self.client.post(url, {
            'action': 'add_column',
            'new_column_name': 'new_test_column'
        })

        updated_df = mock_save_df.call_args[0][0]
        print("Updated DataFrame columns after adding column:", updated_df.columns.tolist())

        self.assertIn('new_test_column', updated_df.columns)
        self.assertEqual(response.status_code, 302)
    @patch('main_page.views.load_dataframe_from_file')
    @patch('main_page.views.save_dataframe')
    @patch('main_page.views.UploadedFile.objects.get')
    @patch('main_page.models.Action.objects.create') 
    def test_delete_columns(self, mock_action_create, mock_get_uploaded_file, mock_save_df, mock_load_df):
        df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        print("Original DataFrame columns before deleting column:", df.columns.tolist())
        mock_load_df.return_value = df
        mock_get_uploaded_file.return_value = UploadedFile(file='media/_TEST_20231223233536/TEMP__TEST.csv')

        url = reverse('edit_columns')
        response = self.client.post(url, {
            'action': 'delete_columns',
            'columns_to_delete': ['A']
        })

        updated_df = mock_save_df.call_args[0][0]
        print("Updated DataFrame columns after deleting column:", updated_df.columns.tolist())

        self.assertNotIn('A', updated_df.columns)
        self.assertIn('B', updated_df.columns)
        self.assertEqual(response.status_code, 302)
    @patch('main_page.views.load_dataframe_from_file')
    @patch('main_page.views.save_dataframe')
    @patch('main_page.views.UploadedFile.objects.get')
    @patch('main_page.models.Action.objects.create') 
    def test_fill_column(self, mock_action_create, mock_get_uploaded_file, mock_save_df, mock_load_df):
        df = pd.DataFrame({'A': [None, 2, None]})
        print("Original DataFrame before filling column:", df)
        mock_load_df.return_value = df
        mock_get_uploaded_file.return_value = UploadedFile(file='media/_TEST_20231223233536/TEMP__TEST.csv')

        url = reverse('edit_columns')
        response = self.client.post(url, {
            'action': 'fill_column',
            'column_to_fill': 'A',
            'fill_value': '1',
            'fill_option': 'all'
        })

        updated_df = mock_save_df.call_args[0][0]
        print("Updated DataFrame after filling column:", updated_df)
        self.assertTrue((updated_df['A'] == '1').all())
        self.assertEqual(response.status_code, 302)
    @patch('main_page.views.load_dataframe_from_file')
    @patch('main_page.views.save_dataframe')
    @patch('main_page.views.UploadedFile.objects.get')
    @patch('main_page.models.Action.objects.create') 
    def test_split_column(self, mock_action_create, mock_get_uploaded_file, mock_save_df, mock_load_df):
        df = pd.DataFrame({'A': ['1-2', '3-4']})
        print("Original DataFrame columns before splitting column:", df.columns.tolist())
        mock_load_df.return_value = df
        mock_get_uploaded_file.return_value = UploadedFile(file='media/_TEST_20231223233536/TEMP__TEST.csv')

        url = reverse('edit_columns')
        response = self.client.post(url, {
            'action': 'split_column',
            'column_to_split': 'A',
            'split_value': '-',
            'delete_original': True
        })

        updated_df = mock_save_df.call_args[0][0]
        print("Updated DataFrame columns after splitting column:", updated_df.columns.tolist())
        self.assertIn('A_split_1', updated_df.columns)
        self.assertIn('A_split_2', updated_df.columns)
        self.assertNotIn('A', updated_df.columns)
        self.assertEqual(response.status_code, 302)
    @patch('main_page.views.load_dataframe_from_file')
    @patch('main_page.views.save_dataframe')
    @patch('main_page.views.UploadedFile.objects.get')
    @patch('main_page.models.Action.objects.create') 
    def test_merge_columns(self, mock_action_create, mock_get_uploaded_file, mock_save_df, mock_load_df):
        df = pd.DataFrame({'A': ['1', '3'], 'B': ['2', '4']})
        print("Original DataFrame before merging columns:", df)
        mock_load_df.return_value = df
        mock_get_uploaded_file.return_value = UploadedFile(file='media/_TEST_20231223233536/TEMP__TEST.csv')

        url = reverse('edit_columns')
        response = self.client.post(url, {
            'action': 'merge_columns',
            'columns_to_merge': ['A', 'B'],
            'merge_separator': '-',
            'new_merge_column_name': 'merged'
        })

        updated_df = mock_save_df.call_args[0][0]
        print("Updated DataFrame after merging columns:", updated_df)
        self.assertIn('merged', updated_df.columns)
        self.assertTrue((updated_df['merged'] == ['1-2', '3-4']).all())
        self.assertEqual(response.status_code, 302)
    @patch('main_page.views.load_dataframe_from_file')
    @patch('main_page.views.save_dataframe')
    @patch('main_page.views.UploadedFile.objects.get')
    @patch('main_page.models.Action.objects.create') 
    def test_rename_column(self, mock_action_create, mock_get_uploaded_file, mock_save_df, mock_load_df):
        df = pd.DataFrame({'old_name': [1, 2, 3]})
        print("Original DataFrame columns before renaming column:", df.columns.tolist())
        mock_load_df.return_value = df
        mock_get_uploaded_file.return_value = UploadedFile(file='media/_TEST_20231223233536/TEMP__TEST.csv')

        url = reverse('edit_columns')
        response = self.client.post(url, {
            'action': 'rename_column',
            'column_to_rename': 'old_name',
            'new_renamed_column_name': 'new_name'
        })

        updated_df = mock_save_df.call_args[0][0]
        print("Updated DataFrame columns after renaming column:", updated_df.columns.tolist())
        self.assertNotIn('old_name', updated_df.columns)
        self.assertIn('new_name', updated_df.columns)
        self.assertEqual(response.status_code, 302)

class EditDataViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.client.login(username='testuser', password='password')

        session = self.client.session
        session['file_path'] = 'media/_TEST_20231223233536/TEMP__TEST.csv'
        session['temp_file_path'] = 'media/_TEST_20231223233536/TEMP__TEST_EDITED.csv'
        session.save()


    @patch('main_page.views.load_dataframe_from_file')
    @patch('main_page.views.save_dataframe')
    @patch('main_page.views.UploadedFile.objects.get')
    @patch('main_page.models.Action.objects.create')
    def test_replace_symbol(self, mock_action_create, mock_get_uploaded_file, mock_save_df, mock_load_df):
        df = pd.DataFrame({'A': ['@text', '@text2', '@text3']})
        print("Original DataFrame before replacing symbol:", df)
        mock_load_df.return_value = df
        mock_get_uploaded_file.return_value = UploadedFile(file='media/_TEST_20231223233536/TEMP__TEST.csv')

        url = reverse('edit_data')
        response = self.client.post(url, {
            'action': 'replace_symbol',
            'columns_to_replace': ['A'],
            'old_symbol': '@',
            'new_symbol': '#',
            'case_sensitive': True
        })

        updated_df = mock_save_df.call_args[0][0]
        print("Updated DataFrame after replacing symbol:", updated_df)
        self.assertTrue((updated_df['A'] == ['#text', '#text2', '#text3']).all())
        self.assertEqual(response.status_code, 302)

    @patch('main_page.views.load_dataframe_from_file')
    @patch('main_page.views.save_dataframe')
    @patch('main_page.views.UploadedFile.objects.get')
    @patch('main_page.models.Action.objects.create')
    def test_delete_data(self, mock_action_create, mock_get_uploaded_file, mock_save_df, mock_load_df):
        # sets up df
        df = pd.DataFrame({'A': ['text1', 'text2', 'text3'], 'B': ['moretext1', 'moretext2', 'moretext3']})
        print("Original DataFrame before deleting data: ", df)
        mock_load_df.return_value = df
        mock_get_uploaded_file.return_value = UploadedFile(file='media/_TEST_20231223233536/TEMP__TEST.csv')

        # mocks Action.objects.create to return an Action with a valid id
        action_mock = MagicMock(spec=Action)
        action_mock.id = 123  # assigns a valid id
        mock_action_create.return_value = action_mock

        # prepares the POST request
        url = reverse('edit_data')
        response = self.client.post(url, {
            'action': 'delete_data',
            'columns_to_modify': ['A', 'B'],
            'delimiter': 'text',
            'delete_option': 'before',
            'include_delimiter': True
        })

        # Check df and response
        updated_df = mock_save_df.call_args[0][0]
        print("Updated DataFrame after deleting data:", updated_df)
        self.assertTrue((updated_df['A'] == ['1', '2', '3']).all())
        self.assertEqual(response.status_code, 302)

    @patch('main_page.views.load_dataframe_from_file')
    @patch('main_page.views.save_dataframe')
    @patch('main_page.views.UploadedFile.objects.get')
    @patch('main_page.models.Action.objects.create')
    def test_trim_and_replace_whitespaces(self, mock_action_create, mock_get_uploaded_file, mock_save_df, mock_load_df):
        df = pd.DataFrame({'A': ['  text  with   spaces', 'another   text  ']})
        print("Original DataFrame before trimming whitespaces: ", df)
        mock_load_df.return_value = df
        mock_get_uploaded_file.return_value = UploadedFile(file='media/_TEST_20231223233536/TEMP__TEST.csv')
        mock_save_df.side_effect = lambda df, path: path

        url = reverse('edit_data')
        response = self.client.post(url, {
            'action': 'trim_and_replace_whitespaces',
            'columns_to_trim': ['A']
        })

        updated_df = mock_save_df.call_args[0][0]
        print("Updated DataFrame after trimming whitespaces: ", updated_df)
        expected_output = ['text with spaces', 'another text']
        self.assertListEqual(updated_df['A'].tolist(), expected_output)
        self.assertEqual(response.status_code, 302)

    @patch('main_page.views.load_dataframe_from_file')
    @patch('main_page.views.save_dataframe')
    @patch('main_page.views.UploadedFile.objects.get')
    @patch('main_page.models.Action.objects.create')
    def test_change_case(self, mock_action_create, mock_get_uploaded_file, mock_save_df, mock_load_df):
        df = pd.DataFrame({'A': ['text', 'another text']})
        print("Original DataFrame before changing case: ", df)
        mock_load_df.return_value = df
        mock_get_uploaded_file.return_value = UploadedFile(file='media/_TEST_20231223233536/TEMP__TEST.csv')
        mock_save_df.side_effect = lambda df, path: path

        url = reverse('edit_data')
        response = self.client.post(url, {
            'action': 'change_case',
            'columns_to_change_case': ['A'],
            'case_type': 'upper'
        })

        updated_df = mock_save_df.call_args[0][0]
        print("Updated DataFrame after changing case: ", updated_df)
        expected_output = ['TEXT', 'ANOTHER TEXT']
        self.assertListEqual(updated_df['A'].tolist(), expected_output)
        self.assertEqual(response.status_code, 302)

    # @patch('main_page.views.load_dataframe_from_file')
    # @patch('main_page.views.save_dataframe')
    # @patch('main_page.views.UploadedFile.objects.get')
    # @patch('main_page.models.Action.objects.create')
    # def test_validate_data(self, mock_action_create, mock_get_uploaded_file, mock_save_df, mock_load_df):
    #     df = pd.DataFrame({'A': ['123', 'abc', '456']})
    #     print("Original DataFrame before validating data:", df)
    #     mock_load_df.return_value = df
    #     mock_get_uploaded_file.return_value = UploadedFile(file='media/_TEST_20231223233536/TEMP__TEST.csv')

    #     url = reverse('edit_data')
    #     response = self.client.post(url, {
    #         'action': 'validate_data',
    #         'columns_to_validate': ['A'],
    #         'validation_type': 'numbers',
    #         'regex_pattern': '',
    #         'ignore_whitespace': False
    #     })


    #     self.assertIn('error', response.context)

    # @patch('main_page.views.load_dataframe_from_file')
    # @patch('main_page.views.save_dataframe')
    # @patch('main_page.views.UploadedFile.objects.get')
    # @patch('main_page.models.Action.objects.create')
    # def test_check_duplicates(self, mock_action_create, mock_get_uploaded_file, mock_save_df, mock_load_df):
    #     df = pd.DataFrame({'A': [1, 1, 2], 'B': [3, 3, 4]})
    #     print("Original DataFrame before checking duplicates:", df)
    #     mock_load_df.return_value = df
    #     mock_get_uploaded_file.return_value = UploadedFile(file='media/_TEST_20231223233536/TEMP__TEST.csv')

    #     url = reverse('edit_data')
    #     response = self.client.post(url, {
    #         'action': 'check_duplicates',
    #         'columns_to_check_duplicates': ['A', 'B']
    #     })

    #     self.assertEqual(response.status_code, 302)
    #     self.assertIn('duplicates', response.context)
