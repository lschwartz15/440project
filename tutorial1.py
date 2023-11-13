from flask import Flask, redirect, url_for, render_template
app = Flask(__name__)

#define pages
@app.route('/<name>')
def home(name):
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)