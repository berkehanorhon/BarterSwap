from flask import Blueprint, flash, redirect, url_for, request, session, render_template
import RunFirstSettings
import barterswap
import math
import psycopg2
import time

bid_handlers = Blueprint('bid_handlers', __name__, static_folder='static', template_folder='templates')


@bid_handlers.route('/<int:item_id>/bid', methods=['POST'])
def add_bid(item_id):
    if 'user_id' not in session:
        flash("You need to sign in first", "error")
        return redirect(url_for('user_handlers.signin'))

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()
    now = barterswap.get_current_time()
    user_id = session['user_id']
    bid_amount = float(request.form['bid_amount'])

    cursor.execute('SELECT user_id FROM items WHERE item_id = %s', (item_id,))
    if str(cursor.fetchone()[0]) == str(user_id):
        flash("You can not bid on your own item!", "error")
        return redirect(url_for('item_handlers.get_item', item_id=item_id))

    cursor.execute('SELECT end_time FROM auctions WHERE item_id = %s AND end_time > %s AND is_active = True',
                   (item_id, now))
    has_an_auction = cursor.fetchone()
    if not has_an_auction:
        flash("The auction has not started yet or has ended!", "error")
        return redirect(url_for('item_handlers.get_item', item_id=item_id))

    cursor.execute('SELECT current_price FROM items WHERE item_id = %s', (item_id,))
    current_price = float(cursor.fetchone()[0])
    if (current_price + 1.0) > bid_amount:
        flash("Your bid must be higher than the current price by at least 1.0", "error")
        return redirect(url_for('item_handlers.get_item', item_id=item_id))

    cursor.execute('SELECT user_id FROM bids WHERE item_id = %s ORDER BY bid_amount DESC LIMIT 1', (item_id,))
    last_bidder_id = cursor.fetchone()

    if last_bidder_id and last_bidder_id[0] == user_id:
        flash("Highest bid is already yours!", "error")
        return redirect(url_for('item_handlers.get_item', item_id=item_id))

    time_diff = (has_an_auction[0] - now).total_seconds() * 1000
    timeout = 4000 if time_diff < 5000 else (int(time_diff) if time_diff < 10000 else 10000)
    start_time = time.time()
    try:
        cursor.execute('BEGIN')
        cursor.execute('SET LOCAL statement_timeout = %s', (timeout,))

        # Call function
        cursor.execute('SELECT add_bid_function(%s, %s, %s, %s)', (item_id, bid_amount, user_id, now))
        if (time.time() - start_time) > (timeout / 1000):
            raise psycopg2.Error('Timeout Error!')
        conn.commit()
    except psycopg2.Error as e:
        conn.rollback()
        if e.pgcode == 'P0001':
            flash(f"New bids on the item!")
        else:
            flash(f"An error occurred: {e}", "error")
            print(e)
    except Exception:
        conn.rollback()
        flash("An error occurred!", "error")
    finally:
        conn.close()

    return redirect(url_for('item_handlers.get_item', item_id=item_id))


@bid_handlers.route("/mybids", defaults={'page': 1})
@bid_handlers.route("/mybids/<int:page>")
def mybids(page):
    if 'user_id' not in session:
        flash("You need to sign in first", "error")
        return redirect(url_for('user_handlers.signin'))

    per_page = 10  # Change this as per your requirement
    offset = (page - 1) * per_page

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT items.title,items.description,items.current_price,bids.bid_amount,bids.bid_date,items.item_id FROM items JOIN bids ON items.item_id = bids.item_id WHERE bids.user_id = %s ORDER BY bids.bid_date DESC LIMIT %s OFFSET %s', (session['user_id'],per_page,offset))
    items = cursor.fetchall()
    total_items = len(items)
    total_pages = math.ceil(total_items / per_page)
    conn.close()

    return render_template('mybids.html', items=items, total_pages=total_pages + 1, current_page=page)

@bid_handlers.route("/mybids/search", defaults={'page': 1}, methods=['GET'])
@bid_handlers.route("/mybids/<int:page>", methods=['GET'])
def search(page, per_page=10):
    if 'user_id' not in session:
        flash("You need to sign in first", "error")
        return redirect(url_for('user_handlers.signin'))

    offset = (page - 1) * per_page

    query = request.args.get('query')
    if query == "":
        return redirect(url_for('bid_handlers.mybids'))

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT items.*, bids.* FROM items JOIN bids ON items.item_id = bids.item_id WHERE bids.user_id = %s and title ILIKE %s ORDER BY bids.bid_date DESC LIMIT %s OFFSET %s", (session["user_id"], '%' + query + '%', per_page, offset))

    items = cursor.fetchall()
    total_items = len(items)
    total_pages = math.ceil(total_items / per_page)
    conn.close()

    return render_template('mybids.html', items=items, search=query, total_pages=total_pages+1, current_page=page)
