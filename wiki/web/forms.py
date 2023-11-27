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
    password = PasswordField('', [InputRequired(),Length(min=8)])
    totp = StringField('', [InputRequired()])
    def validate_name(form, field):
        user = current_users.get_user(field.data)
        if not user:
            raise ValidationError('This username does not exist.')

    def validate_password(form, field):
        user = current_users.get_user(form.name.data)
        if not user:
            return
        if not user.check_password(field.data):
            raise ValidationError('Username and password do not match.')

    # def validate_totp(form, field):
    #     user = current_users.get_user(form.name.data)
    #     if not user:
    #         return
    #     if not user.check_totp(field.data):
    #         raise ValidationError('Username and 6 digit code does not match.')
class SignUpForm(FlaskForm):
    name = StringField('', [InputRequired()])
    password = PasswordField('', [InputRequired()])
    recaptcha = RecaptchaField()
    submit = SubmitField('Sign Up')

    def validate_username(self, field):
        user = current_users.get_user(field.data)
        if user:
            raise ValidationError('This username is already taken. Please choose a different one.')


