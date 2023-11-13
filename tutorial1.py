from flask import Flask, redirect, url_for
app = Flask(__name__)

#define pages
@app.route('/')
def home():
    return "Hello! This is the main page"

#passing in different info
@app.route('/<name>')
def user(name):
    return f"hello {name}"

#redirecting
@app.route('/admin')
def admin():
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run()