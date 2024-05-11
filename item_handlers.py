# routes.py
from flask import Flask, render_template, request, redirect, url_for, Blueprint, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os.path
import RunFirstSettings
import uuid
import mimetypes
from PIL import Image

item_handlers = Blueprint('item_handlers', __name__, static_folder='static', template_folder='templates')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
        try:  # TODO bu try except silinecek
            image = request.files['image']
            mimetype = mimetypes.guess_type(image.filename)[0]
            if mimetype not in ['image/jpeg', 'image/png', 'image/jpg']:
                return 'Invalid file type', 415
            filename = secure_filename(image.filename)
            random_filename = str(uuid.uuid4()) + os.path.splitext(filename)[1]
            image_path = os.path.join('static/images', random_filename)

            foo = Image.open(image)
            foo = foo.resize((625, 700))
            foo.save(image_path, optimize=True, quality=95)

            print(image, type(image), image_path, random_filename)
        except Exception as e:
            print(e, 12345)
        # ADD FLASH FEATURE IN THE FUTURE
        if len(name) > 100:
            # flash("Item name cannot exceed 100 characters", "error")
            return redirect(url_for('user.add_item'))

        if len(description) > 500:
            # flash("Description cannot exceed 500 characters", "error")
            return redirect(url_for('user.add_item'))

        if len(price) > 10:
            # flash("Price value cannot exceed 10 characters", "error")
            return redirect(url_for('user.add_item'))
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
        return render_template('additem.html')


@item_handlers.route('/<int:item_id>')
def get_item(item_id):
    # REWRITE WITH BIDS
    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM items WHERE item_id = %s', (item_id,))
    item = cursor.fetchone()

    cursor.execute('''
        SELECT bids.*, users.username 
        FROM bids 
        INNER JOIN users ON bids.user_id = users.user_id 
        WHERE bids.item_id = %s 
        ORDER BY bids.bid_amount DESC 
        LIMIT 3
    ''', (item_id,))
    bids = cursor.fetchall()
    print(bids)
    conn.close()

    return render_template('item.html', item=item,bids=bids)


@item_handlers.route('/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_item(item_id):
    # NEED  update

    if 'user_id' not in session:
        flash("You need to sign in first", "error")

    if request.method == 'POST':
        # check item is owned by session user
        user_id = request.form['user_id']
        if user_id != session['user_id']:
            flash("You can't edit this item", "error")
            return redirect(url_for('home.home'))

        name = request.form['name']
        description = request.form['description']
        category = request.form['category']
        condition = request.form['condition']

        conn = RunFirstSettings.create_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE items SET title = %s, description = %s, category = %s, condition = %s WHERE item_id = %s',
            (name, description, category, condition, item_id))

        conn.commit()
        conn.close()
        item = []
        return redirect(url_for('item.html', item=item))


