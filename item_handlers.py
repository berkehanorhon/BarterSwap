# routes.py
from flask import Flask, render_template, request, redirect, url_for, Blueprint, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
import RunFirstSettings

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
        #image = request.form['image']

        #if 'image' not in request.files:
            #flash('No file part', 'error')
        #    return redirect(request.url)

        #file = request.files['image']

        #ADD FLASH FEATURE IN THE FUTURE
        if len(name) > 100:
            #flash("Item name cannot exceed 100 characters", "error")
            return redirect(url_for('user.add_item'))

        if len(description) > 500:
            #flash("Description cannot exceed 500 characters", "error")
            return redirect(url_for('user.add_item'))

        if len(price) > 10:
            #flash("Price value cannot exceed 10 characters", "error")
            return redirect(url_for('user.add_item'))
        user_id = session['user_id']
        conn = RunFirstSettings.create_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO items (user_id,title, description, category, starting_price,current_price, condition) VALUES (%s, %s, %s, %s, %s,%s,%s)',
                       (user_id, name, description, category,price,price,condition))
        conn.commit()
        conn.close()

        return redirect(url_for('home.home'))  # Ekleme işlemi başarılı olduğunda ana sayfaya yönlendir
    else:
        return render_template('additem.html')
