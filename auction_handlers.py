from flask import Flask, render_template, request, redirect, url_for, Blueprint, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os.path
import RunFirstSettings
import uuid
import mimetypes
from PIL import Image
import barterswap
from datetime import datetime, timedelta

auction_handlers = Blueprint('auction_handlers', __name__, static_folder='static', template_folder='templates')


@auction_handlers.route('/start/<int:item_id>/<int:hours>', methods=['POST'])
def start_auction(item_id, hours):
    try:
        if 'user_id' not in session:
            flash("You need to sign in first", "error")
            return redirect(url_for('user_handlers.signin'))
        if hours > 720 or hours < 1:
            flash("Auction time can not be bigger than 1 month and can not be smaller than 1 hour!", "error")
            return redirect(url_for('item_handlers.get_item', item_id=item_id))

        user_id = session['user_id']
        conn = RunFirstSettings.create_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT 1 FROM items WHERE item_id = %s and user_id = %s', (item_id, user_id))
        is_user_owns_the_item = cursor.fetchone()
        if not is_user_owns_the_item:
            conn.close()
            flash("You do not have permission to do that operation!", "error")
            return redirect(url_for('item_handlers.get_item', item_id=item_id))
        cursor.execute(
            'SELECT is_active FROM auctions WHERE item_id = %s', (item_id,))
        does_item_have_an_auction = cursor.fetchone()
        if does_item_have_an_auction and does_item_have_an_auction[0]:
            conn.close()
            flash("Item already have an auction!", "error")
            return redirect(url_for('item_handlers.get_item', item_id=item_id))
        if does_item_have_an_auction and not does_item_have_an_auction[0]:
            cursor.execute('UPDATE auctions SET end_time = %s, is_active = %s WHERE item_id = %s',
                           (barterswap.set_end_time(hours), True, item_id))
        else:
            cursor.execute('INSERT INTO auctions (item_id ,end_time, is_active) VALUES (%s, %s, %s)',
                           (item_id, barterswap.set_end_time(hours), True))
        conn.commit()
        conn.close()
        return redirect(url_for('item_handlers.get_item', item_id=item_id))
    except Exception:
        flash("An error occured while starting the auction!", "error")
        conn.close()

    return redirect(url_for('home.home'))


@auction_handlers.route('/delete/<int:item_id>', methods=['GET'])  # TODO GET --> POST
def delete_auction(item_id):
    try:
        if 'user_id' not in session:
            flash("You need to sign in first", "error")
            return redirect(url_for('user_handlers.signin'))

        user_id = session['user_id']
        conn = RunFirstSettings.create_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT 1 FROM items WHERE item_id = %s and user_id = %s', (item_id, user_id))
        is_user_owns_the_item = cursor.fetchone()
        if not is_user_owns_the_item:
            conn.close()
            flash("You do not have permission to do that operation!", "error")
            return redirect(url_for('item_handlers.get_item', item_id=item_id))
        cursor.execute(
            'SELECT 1 FROM auctions WHERE item_id = %s', (item_id,))
        does_item_have_an_auction = cursor.fetchone()
        if not does_item_have_an_auction:
            conn.close()
            flash("Item does not have an auction!", "error")
            return redirect(url_for('item_handlers.get_item', item_id=item_id))
        cursor.execute('SELECT 1 FROM bids WHERE item_id = %s', (item_id,))
        if cursor.fetchone():
            conn.close()
            flash("You can not delete auction if there are bids on the item!", "error")
            return redirect(url_for('item_handlers.get_item', item_id=item_id))
        cursor.execute('DELETE FROM auctions WHERE item_id = %s', (item_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('item_handlers.get_item', item_id=item_id))
    except:
        flash("An error occured while deleting the auction!", "error")
        conn.close()

    return redirect(url_for('home.home'))
