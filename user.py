from flask import Flask, render_template, request, jsonify, redirect, url_for, Blueprint, flash
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

@user.route('/signup' , methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        username = data['username']
        mail = data['mail']
        password = data['password']
        hashed_password = generate_password_hash(password)
        conn = RunFirstSettings.create_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password,email) VALUES (%s, %s,%s)', (username, hashed_password, mail))
        conn.commit()
        conn.close()

        flash("You have successfully registered", "signup-success")
        return redirect(url_for("user.signin"))
    else:
        print(1123123)
        return render_template('signup.html')