from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.shortcuts import reverse
from .models import Template, UploadedFile
from django.core.files.uploadedfile import SimpleUploadedFile
from .views import summary
import shutil
import tempfile
import os
import pandas as pd

class AccessibilityTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')


        # Path to the actual file you want to use for testing
        actual_file_path = os.path.join('media', '_TEST_20231223224412', '_TEST.xlsx')

        # Create an UploadedFile instance with the actual file
        UploadedFile.objects.create(file=actual_file_path)

        # Set up the session data expected by the views
        session = self.client.session
        session['file_path'] = actual_file_path
        session['temp_file_path'] = actual_file_path
        session.save()


    def test_pages_accessibility(self):
        url_names = [
            'main_page',
            'summary',
            'edit_data',
            'edit_columns',
            'undo_last_action',
            'save_template',
            'apply_template',
            'download',
            # 'login' and 'logout' are Django's built-in views
        ]

        for name in url_names:
            url = reverse(name)
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 200, f"Page at {url} is not accessible")

    def tearDown(self):
        # Clean up
        self.user.delete()
 
class SummaryViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')

        # Original file path
        original_file_path = 'media/_TEST_20231223233536/TEMP__TEST.csv'

        # Create a temporary file for testing
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        self.temp_file_path = temp_file.name
        temp_file.close()

        # Copy contents of the original file to the temporary file
        shutil.copyfile(original_file_path, self.temp_file_path)

        # Use the temporary file for testing
        with open(self.temp_file_path, 'rb') as file:
            self.uploaded_file = SimpleUploadedFile(
                name='test_file.csv',
                content=file.read(),
                content_type='text/csv'
            )

    def test_summary_view(self):
        # Simulate file upload
        response = self.client.post(reverse('main_page'), {'file': self.uploaded_file})
        self.assertEqual(response.status_code, 302)  # Assuming redirect after upload

        # Test removing empty rows
        response = self.client.post(reverse('summary'), {'remove_empty_rows': []})
        self.assertEqual(response.status_code, 302)  # Assuming redirect after action

        # Test removing empty columns
        response = self.client.post(reverse('summary'), {'remove_empty_cols': []})
        self.assertEqual(response.status_code, 302)

        # Test deleting first X rows
        response = self.client.post(reverse('summary'), {'num_rows_to_delete_start': '2'})
        self.assertEqual(response.status_code, 302)

        # Test replacing header
        # response = self.client.post(reverse('summary'), {'replace_header': 'true'})
        # self.assertEqual(response.status_code, 302)

        # Test deleting last X rows
        response = self.client.post(reverse('summary'), {'num_rows_to_delete_end': '2'})
        self.assertEqual(response.status_code, 302)

    def tearDown(self):
        # Clean up
        os.remove(self.temp_file_path)
        self.user.delete()
        

class EditColumnsViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')

        # Original file path
        self.file_path = 'media/_TEST_20231223233536/TEMP__TEST.csv'  # Update with actual path

        # Create a temporary file for testing
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        self.temp_file_path = temp_file.name
        temp_file.close()

        # Copy contents of the original file to the temporary file
        shutil.copyfile(self.file_path, self.temp_file_path)
        # Use the temporary file for testing
        with open(self.temp_file_path, 'rb') as file:
            self.uploaded_file = SimpleUploadedFile(
                name='test_file2.csv',
                content=file.read(),
                content_type='text/csv'
            )
        # Set up the session data expected by the views
        session = self.client.session
        session['file_path'] = self.file_path
        session['temp_file_path'] = self.temp_file_path
        session.save()

    def test_add_column(self):
        response = self.client.post(reverse('edit_columns'), {
            'action': 'add_column',
            'new_column_name': 'test_column'
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        # Read the modified file and check if the column was added
        df = pd.read_csv(self.temp_file_path)
        self.assertIn('test_column', df.columns)

    def test_delete_columns(self):
        # Assuming 'column_to_delete' exists in the test file
        response = self.client.post(reverse('edit_columns'), {
            'action': 'delete_columns',
            'columns_to_delete': ['Unnamed: 1']
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        df = pd.read_csv(self.temp_file_path)
        self.assertNotIn('Unnamed: 1', df.columns)

    def test_fill_column(self):
        # Assuming 'column_to_fill' exists in the test file
        response = self.client.post(reverse('edit_columns'), {
            'action': 'fill_column',
            'column_to_fill': 'Unnamed: 2',
            'fill_value': 'test_fill',
            'fill_option': 'all'  # or 'empty'
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        df = pd.read_csv(self.temp_file_path)
        self.assertTrue((df['Unnamed: 2'] == 'test_fill').all())

    def test_split_column(self):
        # Assuming 'column_to_split' exists in the test file
        response = self.client.post(reverse('edit_columns'), {
            'action': 'split_column',
            'column_to_split': 'Unnamed: 3',
            'split_value': '.'  # Split based on a delimiter
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        df = pd.read_csv(self.temp_file_path)
        self.assertIn('Unnamed: 3_split_1', df.columns)

    def test_merge_columns(self):
        # Assuming 'column1' and 'column2' exist in the test file
        response = self.client.post(reverse('edit_columns'), {
            'action': 'merge_columns',
            'columns_to_merge': ['Unnamed: 4', 'Unnamed: 5'],
            'merge_separator': '+',
            'new_column_name': 'merged_column'
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        df = pd.read_csv(self.temp_file_path)
        self.assertIn('merged_column', df.columns)

    def test_rename_column(self):
        # Assuming 'old_column_name' exists in the test file
        response = self.client.post(reverse('edit_columns'), {
            'action': 'rename_column',
            'column_to_rename': 'Unnamed: 6',
            'new_renamed_column_name': 'new_column_name'
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        df = pd.read_csv(self.temp_file_path)
        self.assertIn('new_column_name', df.columns)
        self.assertNotIn('Unnamed: 6', df.columns)


    def tearDown(self):
        self.user.delete()
        os.remove(self.temp_file_path)  # Remove the temporary file