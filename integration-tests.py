import os
import unittest
import json
from Riki import create_app
from unittest.mock import patch

class TestSignUpIntegration(unittest.TestCase):

    def setUp(self):
        self.directory = os.getcwd()
        self.app = create_app(self.directory)
        self.testing_app = create_app(self.directory, testing=True)
        self.client = self.app.test_client()

    @patch('440project.wiki.web.routes.open', create=True)
    def test_signup_successful(self, mock_open):
        mock_open.return_value.read.return_value = '{}'

        response = self.client.post('/signup/', data={
            'name': 'testuser',
            'password': 'testpassword',
            'recaptcha': 'test_recaptcha_response'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Signup successful!', response.data)

        users_data = json.loads(mock_open.return_value.read.return_value)
        self.assertIn('testuser', users_data)

    @patch('440project.wiki.web.routes.open', create=True)
    def test_signup_username_taken(self, mock_open):
        mock_open.return_value.read.return_value = '{"testuser": {"active": true, "authentication_method": "cleartext", "password": "12345678", "authenticated": true, "roles": []}}'

        response = self.client.post('/signup/', data={
            'name': 'testuser',
            'password': 'testpassword',
            'recaptcha': 'test_recaptcha_response'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'This username is already taken.', response.data)

        users_data = json.loads(mock_open.return_value.read.return_value)
        self.assertIn('testuser', users_data)

if __name__ == '__main__':
    unittest.main()