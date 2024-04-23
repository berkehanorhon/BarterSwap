from flask import Flask, render_template,request,jsonify,redirect,url_for
from user import user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.register_blueprint(user,url_prefix='/user')

@app.route('/')
def home():
    return render_template('base.html')


if __name__ == '__main__':
    app.run()
