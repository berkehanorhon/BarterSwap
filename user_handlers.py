from flask import Flask, render_template, request, jsonify, redirect, url_for, Blueprint, flash, session
import psycopg2
import yaml
from werkzeug.security import generate_password_hash, check_password_hash
import RunFirstSettings

user_handlers = Blueprint('user_handlers', __name__ , static_folder='static', template_folder='templates')

@user_handlers.route('/signin' , methods=['GET','POST'])
def signin():

    if 'user_id' in session:
        return redirect(url_for('home.home'))

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = RunFirstSettings.create_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            flash('Successfully logged in!', 'Login Success')
            session['user_id'] = user[0]
            return redirect(url_for('home.home'))
        else:
            flash('Invalid email or password', 'signin-error')
            return redirect(url_for('user_handlers.signin'))
    else:
        return render_template('signin.html')

@user_handlers.route('/signup' , methods=['GET','POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('home.home'))

    # add extra code here
    # check is username or mail used before
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

        flash("You have successfully registered", "signup success")
        return redirect(url_for("user_handlers.signin"))
    else:
        return render_template('signup.html')

@user_handlers.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home.home'))