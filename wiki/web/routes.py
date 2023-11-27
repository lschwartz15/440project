"""
    Routes
    ~~~~~~
"""
from flask import Blueprint, jsonify
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
    form = SignUpForm()  # Correct the form class name to SignupForm
    if form.validate_on_submit():
        user_name = form.name.data
        return redirect(url_for('wiki.mfa', name=user_name))
    page_data = {'title': 'Sign Up Page'}  # Replace with your actual page data
    return render_template('signup.html', form=form, page=page_data)

@bp.route('/mfa/', methods=['GET', 'POST'])
def mfa():
    page = {'title': 'MFA Page'}
    user_name = request.args.get('name')
    issuer_name = "SethSuttonApp"
    # Random generate of the secret key
    key = pyotp.random_base32()
    # Temporary One Time Password
    totp = pyotp.TOTP(key)
    uri = totp.provisioning_uri(name=user_name, issuer_name=issuer_name)
    print(uri)

    # directory = os.path.join(os.path.dirname(__file__), 'wiki/web/static/qr-code-imgs')
    # if not os.path.exists(directory):
    #     os.makedirs(directory)

    # Generate a random number for the QR code image filename
    random_number = random.randint(1, 100)
    qrcode_path = f'440project/wiki/web/static/qr-code-imgs/totp_qr_code{random_number}.png'
    print(f"Generated QR Code Path: {qrcode_path}")
    # Create and save the QR code image
    qrcode.make(uri).save(qrcode_path)
    # Store the generated key in the session for later use in the /login route
    session['random_key'] = key

    return render_template('mfa.html',page=page, qrcode_path=qrcode_path)

@bp.route('/user/login/', methods=['GET', 'POST'])
def user_login():
    form = LoginForm()
    if form.validate_on_submit():
        user = current_users.get_user(form.name.data)
        login_user(user)
        user.set('authenticated', True)
        flash('Login successful.', 'success')
        return redirect(request.args.get("next") or url_for('wiki.index'))
    return render_template('login.html', form=form)


@bp.route('/static/qr-code-imgs/<filename>')
def serve_qr_code(filename):
    return send_from_directory('static/qr-code-imgs', filename)

@bp.route('/user/logout/')
@login_required
def user_logout():
    current_user.set('authenticated', False)
    logout_user()
    flash('Logout successful.', 'success')
    return redirect(url_for('wiki.index'))


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


# SURVEY RESULTS
import json
import os

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

        # Get the directory of the current file (routes.py)
        directory = os.path.dirname(os.path.realpath(__file__))

        # File path for the JSON file
        file_path = os.path.join(directory, 'survey_results.json')

        # Initialize data as an empty list
        data = []

        # Read existing data, if file exists and is not empty
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

        # Redirect to a route to display the result or a thank you page
        return redirect(url_for('wiki.surveyP2', name=name, rating=rating, bugsEncountered=bugsEncountered, suggestions=suggestions))
    else:
        # Render a template if GET request
        return render_template("home.html")



@bp.route("/surveyP2")
def surveyP2():
    name = request.args.get('name')
    rating = request.args.get('rating')
    bugsEncountered = request.args.get('bugsEncountered')
    suggestions = request.args.get('suggestions')

    return f"<h1>Survey Results</h1><p>Name: {name}</p><p>Rating: {rating}</p><p>Bugs Encountered: {bugsEncountered}</p><p>Suggestions: {suggestions}</p>"






"""
    Error Handlers
    ~~~~~~~~~~~~~~
"""


@bp.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

