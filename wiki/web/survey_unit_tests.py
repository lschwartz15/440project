import unittest
import sys
import os
import json
from flask import url_for

# Adjust the path to include the directory where Riki.py is located
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Riki import create_app

class SurveyRouteTestCase(unittest.TestCase):
    def setUp(self):
        # Create a test instance of the Flask application
        self.app = create_app(os.path.join(os.path.dirname(__file__), 'path_to_test_config')).test_client()
        self.app.testing = True

    def test_get_survey_route(self):
        response = self.app.get('/survey')
        self.assertEqual(response.status_code, 200)

    def test_post_survey_valid_data(self):
        survey_data = {
            'nm': 'Test User',
            'rating': '5',
            'bugsEncountered': 'yes',
            'suggestions': 'More features!'
        }
        response = self.app.post('/survey', data=survey_data)
        self.assertEqual(response.status_code, 302)  # Assuming it redirects

    def test_post_survey_invalid_data(self):
        survey_data = {
            'nm': '',  # Missing name
            'rating': '5'
        }
        response = self.app.post('/survey', data=survey_data)
        self.assertIn(response.status_code, [400, 302])  # Depending on how you handle invalid data

    def test_survey_confirmation_route(self):
        response = self.app.get('/survey_confirmation')
        self.assertEqual(response.status_code, 200)

    def test_survey_data_saving(self):
        survey_data = {
            'nm': 'Test User',
            'rating': '4',
            'bugsEncountered': 'no',
            'suggestions': 'Great job!'
        }
        self.app.post('/survey', data=survey_data)

        # Assuming your JSON file path is correct
        directory = os.path.join(os.path.dirname(__file__), 'path_to_json_file')
        file_path = os.path.join(directory, 'survey_results.json')

        with open(file_path, 'r') as file:
            data = json.load(file)
            self.assertTrue(any(item['name'] == 'Test User' for item in data))

if __name__ == '__main__':
    unittest.main()
