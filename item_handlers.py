# routes.py
from flask import Flask, render_template, request, redirect, url_for, Blueprint, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os.path
import RunFirstSettings
import uuid
import mimetypes
from PIL import Image
import barterswap

item_handlers = Blueprint('item_handlers', __name__, static_folder='static', template_folder='templates')


@item_handlers.route('/add', methods=['GET', 'POST'])
def add_item():
    if 'user_id' not in session:
        flash("You need to sign in first", "error")
        return redirect(url_for('user_handlers.signin'))  #

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        category = request.form['category']
        condition = request.form['condition']
        random_filename = None
        try:  # TODO bu try except silinecek
            random_filename = barterswap.upload_and_give_name('static/images', request.files['image'],
                                                              barterswap.ALLOWED_ADDITEM_IMAGE_TYPES)
        except Exception as e:
            print(e, 12345)
        # ADD FLASH FEATURE IN THE FUTURE
        if len(name) > 100:
            # flash("Item name cannot exceed 100 characters", "error")
            return redirect(url_for('item_handlers.add_item'))

        if len(description) > 500:
            # flash("Description cannot exceed 500 characters", "error")
            return redirect(url_for('item_handlers.add_item'))

        if len(price) > 10:
            # flash("Price value cannot exceed 10 characters", "error")
            return redirect(url_for('item_handlers.add_item'))
        user_id = session['user_id']
        conn = RunFirstSettings.create_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO items (user_id,title, description, category, starting_price,current_price, condition,image_url) VALUES (%s, %s, %s, %s, %s,%s,%s,%s)',
            (user_id, name, description, category, price, price, condition, random_filename))
        conn.commit()
        conn.close()

        return redirect(url_for('home.home'))  # Ekleme işlemi başarılı olduğunda ana sayfaya yönlendir
    else:
        return render_template('additem.html', max_content_length=barterswap.max_content_length,
                               ALLOWED_IMAGE_TYPES=barterswap.ALLOWED_ADDITEM_IMAGE_TYPES)


@item_handlers.route('/<int:item_id>')
def get_item(item_id):
    # REWRITE WITH BIDS
    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM items WHERE item_id = %s', (item_id,))
    item = list(cursor.fetchone())
    cursor.execute('SELECT username FROM users WHERE user_id = %s', (item[1],))
    seller = cursor.fetchone()[0]
    item[7] = item[7] if item[7] and os.path.exists("static/images/%s" % item[7]) else 'default.png'
    cursor.execute('''
        SELECT bids.*, users.username 
        FROM bids 
        INNER JOIN users ON bids.user_id = users.user_id 
        WHERE bids.item_id = %s 
        ORDER BY bids.bid_amount DESC 
        LIMIT 3
    ''', (item_id,))
    bids = cursor.fetchall()
    cursor.execute('SELECT 1 FROM auctions where item_id = %s and is_active = True', (item_id,))
    has_an_auction = cursor.fetchone()
    conn.close()

    return render_template('item.html', item=tuple(item), bids=bids , seller = seller, has_an_auction = has_an_auction)


@item_handlers.route('/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_item(item_id):
    # NEED  update

    if 'user_id' not in session:
        flash("You need to sign in first", "error")
        return redirect(url_for('user_handlers.signin'))

    if request.method == 'POST':
        print(request.form)
        # if 1:
        #     return render_template('404.html')
        # check item is owned by session user
        user_id = session['user_id']
        conn = RunFirstSettings.create_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM items WHERE item_id = %s and user_id = %s', (item_id, user_id))
        z = cursor.fetchone()
        print(z)
        if not z:
            # flash("You do not have access to edit this item!", "error")
            return redirect(url_for('home.home'))
        # TODO image editing will be added
        name = request.form['name']
        description = request.form['description']
        # category = request.form['category']
        # condition = request.form['condition']
        if 'is_new_image' in request.form and request.form['is_new_image'] == 'on':
            try:  # TODO bu try except silinecek
                random_filename = barterswap.upload_and_give_name('static/images', request.files['image'],
                                                                  barterswap.ALLOWED_ADDITEM_IMAGE_TYPES)
                cursor.execute(
                    'UPDATE items SET title = %s, description = %s, image_url = %s WHERE item_id = %s',
                    (name, description, random_filename, item_id))
                conn.commit()
            except Exception as e:
                print(e, 54321)
        else:
            cursor.execute(
                'UPDATE items SET title = %s, description = %s WHERE item_id = %s',
                (name, description, item_id))
            conn.commit()
        conn.close()
        return redirect(url_for('item_handlers.get_item', item_id=item_id))
    elif request.method == 'GET':
        # REWRITE WITH BIDS
        conn = RunFirstSettings.create_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM items WHERE item_id = %s', (item_id,))
        item = list(cursor.fetchone())
        item[7] = item[7] if item[7] and os.path.exists("static/images/%s" % item[7]) else 'default.png'
        conn.close()
        return render_template('edititem.html', item=item, max_content_length=barterswap.max_content_length,
                               ALLOWED_IMAGE_TYPES=barterswap.ALLOWED_ADDITEM_IMAGE_TYPES)
