from flask import Blueprint, render_template, session, redirect, url_for, request
import psycopg2
from datetime import datetime
import RunFirstSettings
import barterswapdb

message_routes = Blueprint('message_routes', __name__, static_folder='static', template_folder='templates')


@message_routes.route('/<username>', methods=['GET', 'POST'])
def get_user_messages(username):
    if username == session['username']:
        return redirect(url_for('home.home'))

    result = barterswapdb.get_user_id_by_username(username)
    if result is None:
        return redirect(url_for('home.home'))
    user_id = result[0]

    if request.method == 'POST':
        message = request.form.get('message')
        barterswapdb.insert_message(session['user_id'], user_id, message)

    messages = barterswapdb.select_messages(user_id, session['user_id'])

    return render_template('message.html', messages=messages, username=username)
