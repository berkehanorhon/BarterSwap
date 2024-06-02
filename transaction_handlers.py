from flask import Blueprint, flash, redirect, url_for, request, session, render_template
import RunFirstSettings
import barterswap
import math
import psycopg2
import time

transaction_handlers = Blueprint('transaction_handlers', __name__, static_folder='static', template_folder='templates')


@transaction_handlers.route("/mytransactions", defaults={'page': 1})
@transaction_handlers.route("/mytransactions/<int:page>")
def mytransactions(page):
    if 'user_id' not in session:
        flash("You need to sign in first", "error")
        return redirect(url_for('user_handlers.signin'))

    per_page = 10  # Change this as per your requirement
    offset = (page - 1) * per_page

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT items.title,items.description,items.current_price,transactions.transaction_date,transactions.transaction_status,transactions.item_id FROM items JOIN transactions ON items.item_id = transactions.item_id WHERE transactions.buyer_id = %s ORDER BY transactions.transaction_date DESC LIMIT %s OFFSET %s', (session['user_id'],per_page,offset))
    items = cursor.fetchall()
    total_items = len(items)
    total_pages = math.ceil(total_items / per_page)
    conn.close()

    return render_template('mytransactions.html', items=items, total_pages=total_pages + 1, current_page=page)

@transaction_handlers.route("/mytransactions/search", defaults={'page': 1}, methods=['GET'])
@transaction_handlers.route("/mytransactions/<int:page>", methods=['GET'])
def search(page, per_page=10):
    if 'user_id' not in session:
        flash("You need to sign in first", "error")
        return redirect(url_for('transaction_handlers.mytransactions'))

    offset = (page - 1) * per_page

    query = request.args.get('query')
    if query == "":
        return redirect(url_for('bid_handlers.mybids'))

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT items.title,items.description,items.current_price,transactions.transaction_date,transactions.transaction_status,transactions.item_id FROM items JOIN transactions ON items.item_id = transactions.item_id WHERE transactions.buyer_id = %s and title ILIKE %s ORDER BY transactions.transaction_date DESC LIMIT %s OFFSET %s", (session["user_id"], '%' + query + '%', per_page, offset))

    items = cursor.fetchall()
    total_items = len(items)
    total_pages = math.ceil(total_items / per_page)
    conn.close()

    return render_template('mytransactions.html', items=items, search=query, total_pages=total_pages+1, current_page=page)

@transaction_handlers.route("/approve/<int:item_id>/<int:buyer_id>", methods=['GET'])
def approve(item_id, buyer_id):
    if 'user_id' not in session:
        flash("You need to sign in first", "error")
    if buyer_id != session['user_id']:
        flash("You do not have permission to do that operation!", "error")

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('BEGIN')
        cursor.execute('SELECT 1 FROM transactions WHERE item_id = %s and buyer_id = %s and transaction_status = 1 FOR UPDATE', (item_id, buyer_id))
        transaction = cursor.fetchone()
        if not transaction:
            raise Exception("Transaction not found!")
        cursor.execute('UPDATE transactions SET transaction_status = 2 WHERE item_id = %s and buyer_id = %s and transaction_status = 1', (item_id, buyer_id))
        cursor.execute('SELECT current_price, user_id FROM items WHERE item_id = %s FOR UPDATE', (item_id,))
        current_price, seller_id = cursor.fetchone()
        cursor.execute('SELECT 1 FROM virtualcurrency WHERE user_id = %s FOR UPDATE', (seller_id,))
        cursor.execute('UPDATE virtualcurrency SET balance = balance + %s WHERE user_id = %s', (current_price, seller_id))
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        flash("An error occurred while approving the transaction!", "error")
        return redirect(url_for('transaction_handlers.mytransactions'))
    conn.close()
    flash("Transaction approved successfully!", "success")
    return redirect(url_for('transaction_handlers.mytransactions'))

@transaction_handlers.route("/evaluate/<int:item_id>/<int:buyer_id>/<int:point>", methods=['GET'])
def evaluate(item_id, buyer_id, point):
    if 'user_id' not in session:
        flash("You need to sign in first", "error")
    if buyer_id != session['user_id']:
        flash("You do not have permission to do that operation!", "error")

    if point not in [0, 1]:
        flash("Invalid evaluation point!", "error")
        return redirect(url_for('transaction_handlers.mytransactions'))
    point = 2 if point == 1 else -1
    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()
    cursor.execute('BEGIN')
    cursor.execute('SELECT * FROM transactions WHERE item_id = %s and buyer_id = %s and transaction_status = 2 FOR UPDATE', (item_id, buyer_id))
    transaction = cursor.fetchone()
    if not transaction:
        conn.rollback()
        conn.close()
        flash("An error occurred while evaluating the transaction!", "error")
        return redirect(url_for('transaction_handlers.mytransactions'))
    cursor.execute('SELECT user_id FROM items WHERE item_id = %s FOR UPDATE', (item_id,))
    seller_id = cursor.fetchone()[0]
    cursor.execute('UPDATE users SET reputation = reputation + %s WHERE user_id = %s', (point, seller_id))
    cursor.execute('UPDATE transactions SET transaction_status = 3 WHERE item_id = %s and buyer_id = %s and transaction_status = 2', (item_id, buyer_id))
    conn.commit()
    conn.close()
    flash("Transaction evaluated successfully!", "success")
    return redirect(url_for('transaction_handlers.mytransactions'))
