import math

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask import Blueprint
from werkzeug.security import check_password_hash

import RunFirstSettings

admin_handlers = Blueprint('admin_handlers', __name__, static_folder='static', template_folder='templates')

@admin_handlers.route('/home')
def home():
    return render_template('admin/adminhome.html')

ITEMS_PER_PAGE = 10

@admin_handlers.route("/view_users/", defaults={'page': 1}, methods=['GET'])
@admin_handlers.route("/view_users/<int:page>", methods=['GET'])
def view_users(page):
    search_query = request.args.get('search', '')
    per_page = 10  # Change this as per your requirement
    offset = (page - 1) * per_page

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM users WHERE username LIKE %s', ('%' + search_query + '%',))
    total_items = cursor.fetchone()[0]
    total_pages = math.ceil(total_items / per_page)

    if page <= 0 or page > total_pages:
        return render_template('404.html')

    cursor.execute('SELECT * FROM users WHERE username LIKE %s ORDER BY user_id LIMIT %s OFFSET %s', ('%' + search_query + '%', per_page, offset))
    users = cursor.fetchall()

    conn.close()

    return render_template('admin/view_users.html', users=users, search=search_query, total_pages=total_pages+1, current_page=page)

@admin_handlers.route('/view_items')
def view_items():
    # Get all items from the database
    # ...

    # Render a template with the items
    return render_template('view_items.html', items=items)

@admin_handlers.route('/view_transactions')
def view_transactions():
    # Get all transactions from the database
    # ...

    # Render a template with the transactions
    return render_template('view_transactions.html', transactions=transactions)

@admin_handlers.route('/view_withdraw_requests')
def view_withdraw_requests():
    # Get all withdraw requests from the database
    # ...

    # Render a template with the withdraw requests
    return render_template('view_withdraw_requests.html', withdraw_requests=withdraw_requests)