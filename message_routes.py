from flask import Blueprint, render_template, session, redirect, url_for, request
import psycopg2
from datetime import datetime
import RunFirstSettings

message_routes = Blueprint('message_routes', __name__, static_folder='static', template_folder='templates')

@message_routes.route('/<username>', methods=['GET', 'POST'])
def get_user_messages(username):

    if username == session['username']:
        return redirect(url_for('home.home'))

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM Users WHERE username = %s', (username,))
    result = cursor.fetchone()
    if result is None:
        return redirect(url_for('home.home'))
    user_id = result[0]

    if request.method == 'POST':
        message = request.form.get('message')
        cursor.execute('INSERT INTO Messages (sender_id, receiver_id, message_text) VALUES (%s, %s, %s)', (session['user_id'], user_id, message))
        conn.commit()

    cursor.execute('SELECT * FROM Messages WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)', (session['user_id'], user_id, user_id, session['user_id']))
    messages = cursor.fetchall()
    print(messages)
    conn.close()
    return render_template('message.html', messages=messages , username=username)