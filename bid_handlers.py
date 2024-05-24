from flask import Blueprint, flash, redirect, url_for, request, session
import RunFirstSettings
import barterswap

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
        SELECT bids.*, users.username 
        FROM bids 
        INNER JOIN users ON bids.user_id = users.user_id 
        WHERE bids.item_id = %s 
        ORDER BY bids.bid_amount DESC 
        LIMIT 3
    ''', (item_id,))

    bids = cursor.fetchall()
    last_bid = bids[0]
    cursor.execute('UPDATE virtualcurrency SET balance = balance - %s WHERE user_id = %s', (last_bid[2], last_bid[1]))

    if len(bids) > 1:
        before_bid = bids[1]
        cursor.execute('UPDATE virtualcurrency SET balance = balance + %s WHERE user_id = %s',
                       (before_bid[2], before_bid[1]))

    conn.commit()
    conn.close()

    return redirect(url_for('item_handlers.get_item', item_id=item_id))
