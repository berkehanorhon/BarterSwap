from flask import Flask, render_template, request, jsonify, redirect, url_for, Blueprint, flash, session
import psycopg2
import yaml
from werkzeug.security import generate_password_hash, check_password_hash
import RunFirstSettings
import re
import barterswap
import mimetypes
import os.path
from PIL import Image
from werkzeug.utils import secure_filename
import uuid

user_handlers = Blueprint('user_handlers', __name__, static_folder='static', template_folder='templates')


@user_handlers.app_context_processor
def inject_user_balance():
    if 'user_id' in session:
        conn = RunFirstSettings.create_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM virtualcurrency WHERE user_id = %s', (session['user_id'],))
        balance = cursor.fetchone()[0]
        conn.close()
        return dict(user_balance=balance)
    return dict(user_balance=0)


@user_handlers.route('/signin', methods=['GET', 'POST'])
def signin():
    if 'user_id' in session:
        return redirect(url_for('home.home'))

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = RunFirstSettings.create_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT user_id, username, password, is_admin FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()

        cursor.execute('SELECT * FROM virtualcurrency WHERE user_id = %s', (user[0],))
        virtualcurrency = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user[2], password):
            is_admin = user[3]
            if is_admin:
                flash('Hoş geldin sahip!', 'Admin Login')
            else:
                flash('Successfully logged in!', 'Login Success')
            session['user_id'] = user[0]
            session['username'] = user[1]
            if not is_admin:
                print(1)
                session['is_admin'] = False
                session['balance'] = virtualcurrency[1]
                return redirect(url_for('home.home'))
            else:
                print(2)
                session['is_admin'] = True
                return redirect(url_for('admin_handlers.home'))
        else:
            flash('Invalid email or password', 'signin-error')
            return redirect(url_for('user_handlers.signin'))
    else:
        return render_template('signin.html')


@user_handlers.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('home.home'))

    if request.method == 'POST':
        data = request.form
        username = data['username']
        mail = data['mail']
        password = data['password']

        # Check username format
        if not re.match('^[a-zA-Z0-9]+$', username) or not (3 <= len(username) <= 20):
            flash("Invalid username format", "signup error")
            return render_template('signup.html')

        # Check email format
        if not re.match('^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', mail):
            flash("Invalid email format", "signup error")
            return render_template('signup.html')

        # Check password format
        if not re.search('[A-Z]', password) or not re.search('\d', password) or len(password) < 8:
            flash("Invalid password format", "signup error")
            return render_template('signup.html')

        hashed_password = generate_password_hash(password)
        conn = RunFirstSettings.create_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s OR email = %s', (username, mail))
        if cursor.fetchone() is not None:
            flash("Username or email is already used", "signup error")
            return render_template('signup.html')

        try:
            # Start transaction
            cursor.execute('BEGIN')
            cursor.execute('INSERT INTO users (username, password,email) VALUES (%s, %s,%s)',
                           (username, hashed_password, mail))
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            user = cursor.fetchone()
            cursor.execute('INSERT INTO virtualcurrency (user_id, balance) VALUES (%s, %s)', (user[0], 1000))

            # Commit transaction
            conn.commit()
        except Exception as e:
            # Rollback transaction in case of error
            conn.rollback()
            flash(str(e), "signup error")
            return render_template('signup.html')
        finally:
            conn.close()
        flash("You have successfully registered", "signup success")
        return redirect(url_for("user_handlers.signin"))
    else:
        return render_template('signup.html')


@user_handlers.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home.home'))


@user_handlers.route('/profile')
def profile():
    if 'user_id' not in session:
        flash("You need to sign in first", "error")
        return redirect(url_for('user_handlers.signin'))
    username = session['username']
    return redirect(url_for('user_handlers.user_profile', username=username))


@user_handlers.route('/profile/<username>')
def user_profile(username):
    if 'user_id' not in session:
        flash("You need to sign in first", "error")
        return redirect(url_for('user_handlers.signin'))
    if not re.match('^[a-zA-Z0-9_]*$', username):
        return render_template('404.html')
    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
    user = cursor.fetchone()
    if not user:
        return render_template('404.html')
    cursor.execute('SELECT * FROM items WHERE user_id = %s', (user[0],))
    items = cursor.fetchall()
    conn.close()

    return render_template('profile.html', user=user, items=items)


@user_handlers.route('/profile/<username>/edit', methods=['GET', 'POST'])
def user_profile_edit(username):
    if 'user_id' not in session:
        flash("You need to sign in first", "error")
        return redirect(url_for('user_handlers.signin'))
    if username != session['username']:
        return render_template('404.html')
    if request.method == 'POST':
        print(request.form)
        new_username = request.form['username']
        email = request.form['email']
        conn = RunFirstSettings.create_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.execute('SELECT 1 FROM users WHERE username = %s', (new_username,))
        new_user_exists = cursor.fetchone()
        if not user or (new_user_exists and new_username != username):
            return render_template('404.html')
        # print('is_new_image' in request.form and request.form['is_new_image'] == 'on')
        if 'is_new_image' in request.form and request.form['is_new_image'] == 'on':
            try:  # TODO bu try except silinecek
                random_filename = barterswap.upload_and_give_name('static/avatars', request.files['image'],
                                                                  barterswap.ALLOWED_ADDITEM_IMAGE_TYPES)
                cursor.execute(
                    'UPDATE users SET username = %s, email = %s, avatar_url = %s WHERE username = %s',
                    (new_username, email, random_filename, username))
                conn.commit()
            except Exception as e:
                print(e, 54321)
        else:
            cursor.execute(
                'UPDATE users SET username = %s, email = %s WHERE username = %s',
                (new_username, email, username))
            conn.commit()
        conn.close()
        session['username'] = new_username
        flash("Profile updated!", "profile update")
        return redirect(url_for('user_handlers.user_profile', username=new_username))

    elif request.method == 'GET':
        if not re.match('^[a-zA-Z0-9_]*$', username):
            return render_template('404.html')
        conn = RunFirstSettings.create_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        if not user:
            return render_template('404.html')
        conn.close()

        return render_template('editprofile.html', user=user, max_content_length=barterswap.max_content_length,
                               ALLOWED_IMAGE_TYPES=barterswap.ALLOWED_ADDITEM_IMAGE_TYPES, username=username)
