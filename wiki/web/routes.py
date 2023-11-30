"""
    Routes
    ~~~~~~
"""
from flask import Blueprint, jsonify, make_response
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import session
from flask import send_from_directory
from flask_login import current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user
from wtforms.validators import ValidationError


from wiki.core import Processor
from wiki.web.forms import SignUpForm
from wiki.web.forms import EditorForm
from wiki.web.forms import LoginForm
from wiki.web.forms import SearchForm
from wiki.web.forms import URLForm
from wiki.web import current_wiki
from wiki.web import current_users
from wiki.web.user import protect
import os
import json

import pyotp
import qrcode
import os
import random


bp = Blueprint('wiki', __name__)


@bp.route('/')
@protect
def home():
    page = current_wiki.get('home')
    if page:
        return display('home')
    return render_template('home.html')


@bp.route('/index/')
@protect
def index():
    pages = current_wiki.index()
    return render_template('index.html', pages=pages)


@bp.route('/<path:url>/')
@protect
def display(url):
    page = current_wiki.get_or_404(url)
    return render_template('page.html', page=page)


@bp.route('/create/', methods=['GET', 'POST'])
@protect
def create():
    form = URLForm()
    if form.validate_on_submit():
        return redirect(url_for(
            'wiki.edit', url=form.clean_url(form.url.data)))
    return render_template('create.html', form=form)


@bp.route('/edit/<path:url>/', methods=['GET', 'POST'])
@protect
def edit(url):
    page = current_wiki.get(url)
    form = EditorForm(obj=page)
    if form.validate_on_submit():
        if not page:
            page = current_wiki.get_bare(url)
        form.populate_obj(page)
        page.save()
        flash('"%s" was saved.' % page.title, 'success')
        return redirect(url_for('wiki.display', url=url))
    return render_template('editor.html', form=form, page=page)


@bp.route('/preview/', methods=['POST'])
@protect
def preview():
    data = {}
    processor = Processor(request.form['body'])
    data['html'], data['body'], data['meta'] = processor.process()
    return data['html']


@bp.route('/move/<path:url>/', methods=['GET', 'POST'])
@protect
def move(url):
    page = current_wiki.get_or_404(url)
    form = URLForm(obj=page)
    if form.validate_on_submit():
        newurl = form.url.data
        current_wiki.move(url, newurl)
        return redirect(url_for('wiki.display', url=newurl))
    return render_template('move.html', form=form, page=page)


@bp.route('/delete/<path:url>/')
@protect
def delete(url):
    page = current_wiki.get_or_404(url)
    current_wiki.delete(url)
    flash('Page "%s" was deleted.' % page.title, 'success')
    return redirect(url_for('wiki.home'))


@bp.route('/tags/')
@protect
def tags():
    tags = current_wiki.get_tags()
    return render_template('tags.html', tags=tags)


@bp.route('/tag/<string:name>/')
@protect
def tag(name):
    tagged = current_wiki.index_by_tag(name)
    return render_template('tag.html', pages=tagged, tag=name)


@bp.route('/search/', methods=['GET', 'POST'])
@protect
def search():
    form = SearchForm()
    if form.validate_on_submit():
        results = current_wiki.search(form.term.data, form.ignore_case.data)
        return render_template('search.html', form=form,
                               results=results, search=form.term.data)
    return render_template('search.html', form=form, search=None)


@bp.route('/signup/', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        try:
            form.save_user_to_json()
            flash('Signup successful!', 'success')
            return redirect(url_for('wiki.mfa', name=form.name.data))
        except ValidationError as e:
            flash(str(e), 'danger')

    page_data = {'title': 'Sign Up Page'}
    return render_template('signup.html', form=form, page=page_data)



@bp.route('/mfa', methods=['GET'])
def mfa():
    page = {'title': 'MFA Page'}
    user_name = request.args.get('name')
    issuer_name = "Riki"

    # Random generate of the secret key
    key = pyotp.random_base32()

    # Temporary One Time Password
    totp = pyotp.TOTP(key)
    uri = totp.provisioning_uri(name=user_name, issuer_name=issuer_name)

    # Generate the users for the QR code image filename with the user name
    qrcode_filename = f"{user_name}_totp_qr_code.png"

    # Specify the folder where your QR code images are stored
    qrcode_folder = os.path.join(os.path.abspath("wiki/web/static/QRimages"))

    # Construct the full path to the QR code image
    qrcode_path = os.path.join(qrcode_folder, qrcode_filename)

    # Create and save the QR code image
    qrcode.make(uri).save(qrcode_path)

    # Store the generated key in the session for later use in the /login route
    session['random_key'] = key

    return render_template('mfa.html', page=page, qrcode_path=qrcode_path, qrcode_filename=qrcode_filename)


@bp.route('/QRimages/<filename>')
def path_static(filename):
    return send_from_directory(os.path.abspath("wiki/web/static/QRimages"), filename)


@bp.route('/user/login/', methods=['GET', 'POST'])
def user_login():
    form = LoginForm()

    if request.method == 'POST' and form.validate_on_submit():
        username = form.name.data
        user_input_code = form.totp.data

        user = current_users.get_user(username)

        # Check TOTP
        user_secret_key = session.get('random_key')
        if not user_secret_key:
            flash("You need to set up a new MFA. Please re-scan the QR Code")  # Error message routes you back to MFA
            return render_template('mfa.html', form=form)

        totp = pyotp.TOTP(user_secret_key)
        is_valid = totp.verify(user_input_code)

        if is_valid:
            login_user(user)
            user.set('authenticated', True)
            flash('Login successful.', 'success')
            flash('To Logout please click on "Logout"')
            return redirect(request.args.get("next") or url_for('wiki.index'))
        else:
            flash("Invalid TOTP code. Please try again.")  # Error message

    return render_template('login.html', form=form)


@bp.route('/user/logout/')
@login_required
def user_logout():
    current_user.set('authenticated', False)
    logout_user()
    flash('Logout successful.', 'success')
    return redirect(url_for('wiki.home'))


@bp.route('/user/')
def user_index():
    pass


@bp.route('/user/create/')
def user_create():
    pass


@bp.route('/user/<int:user_id>/')
def user_admin(user_id):
    pass


@bp.route('/user/delete/<int:user_id>/')
def user_delete(user_id):
    pass


# SURVEY ROUTES
@bp.route("/survey", methods=["POST", "GET"])
def survey():
    if request.method == "POST":
        # Extract form data
        name = request.form.get("nm")
        rating = request.form.get("rating")
        bugsEncountered = request.form.get("bugsEncountered")
        suggestions = request.form.get("suggestions")

        # Create a dictionary of the form data
        survey_data = {
            "name": name,
            "rating": rating,
            "bugsEncountered": bugsEncountered,
            "suggestions": suggestions
        }

        confirmation_html = "<div>Thank you for submitting the survey!</div>"

        directory = os.path.dirname(os.path.realpath(__file__))

        file_path = os.path.join(directory, 'survey_results.json')

        data = []

        if os.path.isfile(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, 'r') as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    # If JSON is invalid, initialize data as an empty list
                    data = []

        # Append new survey data
        data.append(survey_data)

        # Write the updated data back to the file
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

        return redirect(url_for('wiki.survey_confirmation'))
    else:
        # Render a template if GET request
        return render_template("home.html")


@bp.route("/survey_confirmation")
def survey_confirmation():
    return render_template("survey_confirmation.html")



"""
    Error Handlers
    ~~~~~~~~~~~~~~
"""


@bp.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

