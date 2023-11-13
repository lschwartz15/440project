from flask import Flask, render_template, flash, request, jsonify

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for message flashing

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/exit', methods=['POST'])
def exit():
    flash('You are exiting')
    return jsonify(success=True)  # Respond to the AJAX request

if __name__ == "__main__":
    app.run(debug=True)
