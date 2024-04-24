from flask import Blueprint, render_template, session, redirect, url_for

import RunFirstSettings

home_bp = Blueprint('home', __name__, static_folder='static', template_folder='templates')

@home_bp.route("/")
def home():

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM items')
    items = cursor.fetchall()
    conn.close()

    return render_template('home.html', items=items)