from flask import Flask, render_template, request, jsonify, redirect, url_for, Blueprint
import psycopg2
import yaml
from werkzeug.security import generate_password_hash
import RunFirstSettings

user = Blueprint('user', __name__ , static_folder='static', template_folder='templates')

@user.route('/signin' , methods=['GET','POST'])
def signin():
    if request.method == 'POST':

        return redirect(url_for("home"))
    else:

        return render_template('signin.html')

@user.route('/signup')
def signup():
    if request.method == 'POST':

        return redirect(url_for("home"))
    else:
        return render_template('signup.html')