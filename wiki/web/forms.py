"""
    Forms
    ~~~~~
"""
from flask_wtf import FlaskForm

from wtforms import BooleanField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms import PasswordField
from wtforms import SubmitField
from wtforms.validators import InputRequired
from wtforms.validators import ValidationError
from wtforms.validators import Length
from flask_wtf.recaptcha import RecaptchaField
from wiki.core import clean_url
from wiki.web import current_wiki
from wiki.web import current_users

import json
import os

class URLForm(FlaskForm):
    url = StringField('', [InputRequired()])

    def validate_url(form, field):
        if current_wiki.exists(field.data):
            raise ValidationError('The URL "%s" exists already.' % field.data)

    def clean_url(self, url):
        return clean_url(url)


class SearchForm(FlaskForm):
    term = StringField('', [InputRequired()])
    ignore_case = BooleanField(
        description='Ignore Case',
        # FIXME: default is not correctly populated
        default=True)


class EditorForm(FlaskForm):
    title = StringField('', [InputRequired()])
    body = TextAreaField('', [InputRequired()])
    tags = StringField('')


class LoginForm(FlaskForm):
    name = StringField('', [InputRequired(), Length(max=255)])
    password = PasswordField('', [InputRequired(), Length(min=8)])
    totp = StringField('', [InputRequired(), Length(max=6, min=6)])

    def validate_name(self, field):
        user = current_users.get_user(field.data)
        print(f"Username: {field.data}, User: {user}")
        if not user:
            raise ValidationError('Invalid Username, try again. Click "Sign Up" if you are a new user')

    def validate_password(self, field):
        user = current_users.get_user(self.name.data)
        if not user:
            return
        if not user.check_password(field.data):
            raise ValidationError('Invalid Password, try again.')


class SignUpForm(FlaskForm):
    name = StringField('Username', validators=[InputRequired(), Length(max=255)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8)])
    recaptcha = RecaptchaField()
    submit = SubmitField('Sign Up')

    def validate_name(self, field):
        # Checks if the username is already taken
        user = current_users.get_user(field.data)
        if user:
            raise ValidationError('This username is already taken. Please choose a different one.')

    def save_user_to_json(self):
        #New users login
        username = self.name.data
        password = self.password.data

        # Load existing user data for checking if the user was preivously made
        current_file_path = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))
        file_path = os.path.join(project_root, 'user', 'users.json')

        with open(file_path, 'r') as file:
            users_data = json.load(file)

        # Checks if the username exist
        if username in users_data:
            raise ValidationError('This username is already taken. Please choose a different one.')

        # Adds new user
        users_data[username] = {
            "active": True,
            "authentication_method": "cleartext",
            "password": password,
            "authenticated": True,
            "roles": []
        }

        # Save the updated user data
        current_file_path = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))
        file_path = os.path.join(project_root, 'user', 'users.json')
        with open(file_path, 'w') as file:
            json.dump(users_data, file, indent=2)

        print("Signup successful.")