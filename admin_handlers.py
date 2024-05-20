from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask import Blueprint
from werkzeug.security import check_password_hash

import RunFirstSettings

admin_handlers = Blueprint('admin_handlers', __name__, static_folder='static', template_folder='templates')

@admin_handlers.route('/home')
def home():
    return render_template('admin/adminhome.html')

@admin_handlers.route('/view_users')
def view_users():
    # Get all users from the database
    # ...

    # Render a template with the users
    return render_template('view_users.html', users=users)

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