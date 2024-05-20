from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
import os

db = None


def start_db_pool(app):
    global db
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}/{db_name}'
    app.config['SQLALCHEMY_POOL_SIZE'] = 20
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 280
    db = SQLAlchemy(app)
    print("DB pool has been started...")


def create_sesion_and_execute(sql, item_dict, need_commit=False):
    Session = sqlalchemy.orm.sessionmaker(bind=db.engine)
    with Session() as session:
        execute = session.execute(sql, item_dict)
        if need_commit:
            session.commit()
            return True
        else:
            result = execute.fetchall()
    return result if len(result) != 1 else result[0]


def get_top_bids_by_item_id(item_id):
    sql = sqlalchemy.text('''
        SELECT bids.*, users.username 
        FROM bids 
        INNER JOIN users ON bids.user_id = users.user_id 
        WHERE bids.item_id = :item_id 
        ORDER BY bids.bid_amount DESC 
        LIMIT 3
    ''')
    return create_sesion_and_execute(sql, {"item_id": item_id})


def get_item_by_id(item_id):
    sql = sqlalchemy.text('SELECT * FROM items WHERE item_id = :item_id')
    return list(create_sesion_and_execute(sql, {"item_id": item_id}))

def get_user_data_by_user_id(user_id):
    sql = sqlalchemy.text('SELECT username FROM users WHERE user_id = :user_id')
    return create_sesion_and_execute(sql, {"user_id": user_id})

def is_user_owns_the_item(user_id,item_id):
    sql = sqlalchemy.text('SELECT 1 FROM items WHERE item_id = :item_id and user_id = :user_id')
    return create_sesion_and_execute(sql, {"user_id": user_id, "item_id": item_id})

def is_user_owns_the_item(user_id,item_id):
    sql = sqlalchemy.text('SELECT 1 FROM items WHERE item_id = :item_id and user_id = :user_id')
    return create_sesion_and_execute(sql, {"user_id": user_id, "item_id": item_id})

def update_item_v1(title, description, image_url, item_id):
    sql = sqlalchemy.text('UPDATE items SET title = :title, description = :description, image_url = :image_url WHERE item_id = :item_id')
    return create_sesion_and_execute(sql, {"title": title, "description": description, "image_url": image_url, "item_id": item_id}, True)

def update_item_v2(title, description, item_id):
    sql = sqlalchemy.text('UPDATE items SET title = :title, description = :description WHERE item_id = :item_id')
    return create_sesion_and_execute(sql, {"title": title, "description": description, "item_id": item_id}, True)

def insert_item(user_id, name, description, category, price, condition, random_filename):
    sql = text('INSERT INTO items (user_id, title, description, category, starting_price, current_price, condition, image_url) VALUES (:user_id, :name, :description, :category, :price, :price, :condition, :random_filename)')
    params = {"user_id": user_id, "name": name, "description": description, "category": category, "price": price, "condition": condition, "random_filename": random_filename}
    return create_sesion_and_execute(sql, params, True)
