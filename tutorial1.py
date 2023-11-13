from flask import Flask, redirect, url_for, render_template
app = Flask(__name__)

#define pages
@app.route('/<name>')
def home(name):
    return render_template("index.html", content=["tim", "joe", "bill"], r=2)


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