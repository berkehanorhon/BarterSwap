from flask import Blueprint, flash, redirect, url_for, request, session, render_template
import RunFirstSettings
import barterswap
import math
bid_handlers = Blueprint('bid_handlers', __name__, static_folder='static', template_folder='templates')


@bid_handlers.route('/<int:item_id>/bid', methods=['POST'])
def add_bid(item_id):
    if 'user_id' not in session:
        flash("You need to sign in first", "error")
        return redirect(url_for('user_handlers.signin'))

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()
    now = barterswap.get_current_time()
    cursor.execute('SELECT 1 FROM auctions WHERE item_id = %s and end_time > %s AND is_active = True', (item_id, now))
    has_an_auction = cursor.fetchone()
    if not has_an_auction:
        flash("The auction has not started yet!", "error")
        return redirect(url_for('item_handlers.get_item', item_id=item_id))

    cursor.execute('SELECT current_price,user_id FROM items WHERE item_id = %s', (item_id,))

    item = cursor.fetchone()
    owner_id = item[1]
    current_price = item[0]

    if (owner_id == session['user_id']):
        flash("You can't bid on your own item", "error")
        return redirect(url_for('item_handlers.get_item', item_id=item_id))

    cursor.execute('SELECT balance FROM virtualcurrency WHERE user_id = %s', (session['user_id'],))
    balance = cursor.fetchone()[0]

    bid_amount = request.form['bid_amount']
    if (float(balance) < float(current_price)) or (float(balance) < float(bid_amount)):
        flash("You don't have enough balance", "error")
        return redirect(url_for('item_handlers.get_item', item_id=item_id))

    print(bid_amount)
    # Check if the bid is higher than the current price
    cursor.execute('SELECT current_price FROM items WHERE item_id = %s', (item_id,))
    current_price = cursor.fetchone()[0]
    if float(bid_amount) <= current_price:
        flash("Your bid must be higher than the current price", "error")
        return redirect(url_for('item_handlers.get_item', item_id=item_id))

    # Insert the new bid
    cursor.execute('INSERT INTO bids (user_id, item_id, bid_amount) VALUES (%s, %s, %s)',
                   (session['user_id'], item_id, bid_amount))

    # Update the current price of the item
    cursor.execute('UPDATE items SET current_price = %s WHERE item_id = %s',
                   (bid_amount, item_id))

    cursor.execute('''
        SELECT bids.user_id, bids.bid_amount, users.username 
        FROM bids 
        INNER JOIN users ON bids.user_id = users.user_id 
        WHERE bids.item_id = %s 
        ORDER BY bids.bid_amount DESC 
        LIMIT 3
    ''', (item_id,))

    bids = cursor.fetchall()
    last_bid = bids[0]

    cursor.execute('UPDATE virtualcurrency SET balance = balance - %s WHERE user_id = %s', (last_bid[1], last_bid[0]))

    if len(bids) > 1:
        before_bid = bids[1]
        cursor.execute('UPDATE virtualcurrency SET balance = balance + %s WHERE user_id = %s',
                       (before_bid[1], before_bid[0]))

    conn.commit()
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

    cursor.execute('SELECT items.*, bids.* FROM items JOIN bids ON items.item_id = bids.item_id WHERE bids.user_id = %s ORDER BY bids.bid_date DESC', (session['user_id'], ))
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
        return redirect(url_for('bid_handlers.myitems'))

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT items.*, bids.* FROM items JOIN bids ON items.item_id = bids.item_id WHERE bids.user_id = %s and title ILIKE %s ORDER BY bids.bid_date DESC LIMIT %s OFFSET %s", (session["user_id"], '%' + query + '%', per_page, offset))

    items = cursor.fetchall()
    total_items = len(items)
    total_pages = math.ceil(total_items / per_page)
    conn.close()

    return render_template('mybids.html', items=items, search=query, total_pages=total_pages+1, current_page=page)
