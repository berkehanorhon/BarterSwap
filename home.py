from flask import Blueprint, render_template, session, redirect, url_for, request

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

@home_bp.route("/search", methods=['GET'])
def search():
    query = request.args.get('query')
    print(query)
    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM items WHERE title LIKE %s', ('%' + query + '%',))
    items = cursor.fetchall()
    conn.close()

    return render_template('home.html', items=items, search=query)