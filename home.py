import math

from flask import Blueprint, render_template, session, redirect, url_for, request

import RunFirstSettings

home_bp = Blueprint('home', __name__, static_folder='static', template_folder='templates')

@home_bp.route("/", defaults={'page': 1})
@home_bp.route("/<int:page>")
def home(page):
    if 'is_admin' in session and session['is_admin']:
        return redirect(url_for('admin_handlers.home'))

    per_page = 10  # Change this as per your requirement
    offset = (page - 1) * per_page

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM items')
    total_items = cursor.fetchone()[0]
    total_pages = math.ceil(total_items / per_page)

    if page <= 0 or page > total_pages:
        return render_template('404.html')

    cursor.execute('SELECT * FROM items ORDER BY item_id LIMIT %s OFFSET %s', (per_page, offset))
    items = cursor.fetchall()
    conn.close()

    return render_template('home.html', items=items, total_pages=total_pages+1, current_page=page)

@home_bp.route("/search", defaults={'page': 1}, methods=['GET'])
@home_bp.route("/search/<int:page>", methods=['GET'])
def search(page, per_page=10):
    offset = (page - 1) * per_page

    query = request.args.get('query')

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE title ILIKE %s ORDER BY item_id LIMIT %s OFFSET %s", ('%' + query + '%', per_page, offset))

    items = cursor.fetchall()
    total_items = len(items)
    total_pages = math.ceil(total_items / per_page)
    conn.close()

    return render_template('home.html', items=items, search=query, total_pages=total_pages+1, current_page=page)
