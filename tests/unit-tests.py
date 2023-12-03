import unittest
from flask import Flask
from flask import session
from wiki.web.forms import LoginForm, SignUpForm
from wiki.web.routes import mfa, user_login, signup, bp
from flask_wtf.csrf import generate_csrf
import os
import pyotp
import qrcode
import json
import time
from Riki import create_app
from wiki.core import PageVersionManager


class LoginTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.testing = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def test_missing_name(self):
        print("Running Test for missing username")
        form = LoginForm(password='valid_password', totp='123456')
        validation_result = form.validate()
        self.assertFalse(validation_result, 'Expected validation to fail for missing name')
        if not validation_result:
            print('Validation failed for missing username. This is expected.')

    def test_missing_password(self):
        print("\nRunning Test for missing password")
        form = LoginForm(name='valid_user', totp='123456')
        validation_result = form.validate()
        self.assertFalse(validation_result, 'Expected validation to fail for missing password')
        if not validation_result:
            print('Validation failed for missing password. This is expected.')

    def test_missing_totp(self):
        print("\nRunning Test for missing totp")
        form = LoginForm(name='valid_user', password='valid_password')
        validation_result = form.validate()
        self.assertFalse(validation_result, 'Expected validation to fail for missing totp')
        if not validation_result:
            print('Validation failed for missing totp. This is expected.')


class MFATest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.register_blueprint(bp)
        self.client = self.app.test_client()

    def test_generate_totp_and_qrcode(self):
        print("\nRunning Test for totp and qrcode")
        with self.app.test_request_context('/wiki/web/routes/mfa?name=test_user'):
            user_name = 'test_user'
            user_key = pyotp.random_base32()
            totp = pyotp.TOTP(user_key)
            uri = totp.provisioning_uri(name=user_name, issuer_name="Riki")
            self.assertIn(user_name, uri)
            qrcode_folder = os.path.join(os.path.abspath("wiki/web/static/QRimages"))
            qrcode_filename = f"{user_name}_totp_qr_code.png"
            qrcode_path = os.path.join(qrcode_folder, qrcode_filename)
            self.assertTrue(os.path.isfile(qrcode_path))
            print("path to qr code image: ", qrcode_path)


class SignUpFormTest(unittest.TestCase):
    def setUp(self):
        # Just in Case
        pass

    def test_recaptcha_field_checked_marked(self):
        print("\nRunning Test for checked reCAPTCHA")
        form = SignUpForm(meta={'csrf': False})
        form.name.data = 'test_user'
        form.password.data = 'test_password'
        form.recaptcha.data = 'test_recaptcha_response'
        self.assertTrue(form.recaptcha.data, "reCAPTCHA field should be checked")
        print("Is reCAPTCHA checked?", form.recaptcha.data)

    def test_recaptcha_field_not_checked_marked(self):
        print("\nRunning Test for unchecked reCAPTCHA")
        form = SignUpForm(meta={'csrf': False})
        form.name.data = 'test_user'
        form.password.data = 'test_password'
        self.assertFalse(form.recaptcha.data, "reCAPTCHA field should not be checked")
        print("Is reCAPTCHA checked?", form.recaptcha.data)


# SURVEY UNIT TESTS
class SurveyRouteTestCase(unittest.TestCase):
    def setUp(self):
        directory = os.path.dirname(os.path.abspath(__file__))
        self.app = create_app(directory).test_client()
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
        self.assertEqual(response.status_code, 302)

    def test_post_survey_invalid_data(self):
        survey_data = {
            'nm': '',  # Missing name
            'rating': '5'
        }
        response = self.app.post('/survey', data=survey_data)
        self.assertIn(response.status_code, [400, 302])

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

        directory = os.path.join(os.path.dirname(__file__), 'wiki/web/')
        file_path = os.path.join(directory, 'survey_results.json')

        with open(file_path, 'r') as file:
            data = json.load(file)
            self.assertTrue(any(item['name'] == 'Test User' for item in data))


class TestPageVersionManager(unittest.TestCase):
	def setUp(self):
		self.app = create_app(os.getcwd())
		self.client = self.app.test_client()
		self.app.testing = True
		self.app.config['WTF_CSRF_ENABLED'] = False
		self.user = 'TEST'
		self.url = 'TESTPAGE'
		self.pvm = PageVersionManager(self.url, self.user)
		self.client.post('/user/login', data={'name': self.user, 'password': 'TEST'}, follow_redirects=True)

	def tearDown(self):
		self.client.get('/delete/' + self.url, follow_redirects=True)

	def get_page_data(self):
		with open(self.pvm.page_path, 'r', encoding='utf-8') as f:
			content = f.read().splitlines()
			title = content[0][7:]
			tags = content[1][6:]
			body = content[3]
			return title, tags, body

	def test_create_page(self):
		title = 'TEST_TITLE'
		tags = 'TEST'
		body = 'TEST_BODY'
		response = self.client.post('/edit/' + self.url,
									data={'title': title, 'body': body, 'tags': tags},
									follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertTrue(os.path.exists(self.pvm.page_path))
		self.assertTrue(os.path.exists(self.pvm.dir_path))
		self.assertTrue(os.path.exists(self.pvm.edits_path))
		self.assertTrue(os.path.exists(self.pvm.dir_path + '/' + self.pvm.get_timestamp().replace(':', ' ') + '.md'))
		edits = self.pvm.get_edits()
		self.assertEqual(len(edits), 1)
		page_title, page_tags, page_body = self.get_page_data()
		self.assertEqual(page_title, title)
		self.assertEqual(page_tags, tags)
		self.assertEqual(page_body, body)

	def test_update_page(self):
		title = 'TEST_TITLE'
		tags = 'TEST'
		body = 'TEST_BODY'
		title2 = 'TEST_TITLE2'
		tags2 = 'TEST2'
		body2 = 'TEST_BODY2'
		self.client.post('/edit/' + self.url,
									data={'title': title, 'body': body, 'tags': tags},
									follow_redirects=True)
		self.client.post('/user/login', data={'name': 'eric_jackman', 'password': 'pass'}, follow_redirects=True)
		time.sleep(1)
		response = self.client.post('/edit/' + self.url,
									data={'title': title2, 'body': body2, 'tags': tags2},
									follow_redirects=True)
		self.assertTrue(os.path.exists(self.pvm.dir_path + '/' + self.pvm.get_timestamp().replace(':', ' ') + '.md'))
		self.assertEqual(response.status_code, 200)
		edits = self.pvm.get_edits()
		self.assertEqual(len(edits), 2)
		page_title, page_tags, page_body = self.get_page_data()
		self.assertEqual(page_title, title2)
		self.assertEqual(page_tags, tags2)
		self.assertEqual(page_body, body2)

	def test_restore_page(self):
		title = 'TEST_TITLE'
		tags = 'TEST'
		body = 'TEST_BODY'
		title2 = 'TEST_TITLE2'
		tags2 = 'TEST2'
		body2 = 'TEST_BODY2'
		self.client.post('/edit/' + self.url,
									data={'title': title, 'body': body, 'tags': tags},
									follow_redirects=True)
		self.client.post('/user/login', data={'name': 'eric_jackman', 'password': 'pass'}, follow_redirects=True)
		time.sleep(1)
		response = self.client.post('/edit/' + self.url,
									data={'title': title2, 'body': body2, 'tags': tags2},
									follow_redirects=True)
		page_title, page_tags, page_body = self.get_page_data()
		self.assertEqual(page_title, title2)
		self.assertEqual(page_tags, tags2)
		self.assertEqual(page_body, body2)
		self.client.get('/edit/' + self.url + '/0', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		page_title, page_tags, page_body = self.get_page_data()
		self.assertEqual(page_title, title)
		self.assertEqual(page_tags, tags)
		self.assertEqual(page_body, body)

	def test_delete_page(self):
		title = 'TEST_TITLE'
		tags = 'TEST'
		body = 'TEST_BODY'
		self.client.post('/edit/' + self.url,
									data={'title': title, 'body': body, 'tags': tags},
									follow_redirects=True)
		response = self.client.get('/delete/' + self.url, follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertTrue(not os.path.exists(self.pvm.page_path))
		self.assertTrue(not os.path.exists(self.pvm.edits_path))
		self.assertTrue(not os.path.exists(self.pvm.dir_path))


if __name__ == '__main__':
    unittest.main()
