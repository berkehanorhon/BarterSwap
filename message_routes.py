from flask import Blueprint, render_template, session, redirect, url_for, request, flash
import psycopg2
from datetime import datetime
import RunFirstSettings

message_routes = Blueprint('message_routes', __name__, static_folder='static', template_folder='templates')

@message_routes.route('/<username>', methods=['GET', 'POST'])
def get_user_messages(username):

    if username == session['username']:
        flash("You cannot talk with yourself.", "error")
        return redirect(url_for('home.home'))

    if 'user_id' not in session:
        flash("You need to sign in first", "error")
        return redirect(url_for('user_handlers.signin'))

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

@message_routes.route('/', methods=['GET'])
def get_users_last_messages():
    if 'user_id' not in session:
        flash("You need to sign in first", "error")
        return redirect(url_for('user_handlers.signin'))

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()

    cursor.execute('''WITH latest_messages AS (
                        SELECT
                            GREATEST(sender_id, receiver_id) AS user1,
                            LEAST(sender_id, receiver_id) AS user2,
                            MAX(message_id) AS max_message_id
                        FROM
                            messages
                        GROUP BY
                            GREATEST(sender_id, receiver_id),
                            LEAST(sender_id, receiver_id)
                    )
                    SELECT
                        m.message_id,
                        m.sender_id,
                        sender.username AS sender_username,
                        m.receiver_id,
                        receiver.username AS receiver_username,
                        m.message_text,
                        m.send_time
                    FROM
                        messages m
                    JOIN
                        latest_messages lm ON m.message_id = lm.max_message_id
                    JOIN
                        users sender ON m.sender_id = sender.user_id
                    JOIN
                        users receiver ON m.receiver_id = receiver.user_id
                    WHERE
                        %s IN (m.sender_id, m.receiver_id);''', (session['user_id'],))
    print(session['user_id'])
    messages = cursor.fetchall()
    print(messages)
    conn.close()
    return render_template('messagebox.html', messages=messages)
