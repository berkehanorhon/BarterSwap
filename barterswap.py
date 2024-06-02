import mimetypes
import os.path
import subprocess

import yaml
from PIL import Image
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime, timedelta
import RunFirstSettings
from apscheduler.schedulers.background import BackgroundScheduler
import psycopg2

max_content_length = 5 * 1024 * 1024
ALLOWED_ADDITEM_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/jpg'}
MAX_TRANSACTION_RETRY_COUNT = 2


def get_current_time():
    return datetime.utcnow()

def upload_and_give_name(path, image, allowed_types):
    if not image:
        raise Exception("No image uploaded!")
    mimetype = mimetypes.guess_type(image.filename)[0]
    if mimetype not in allowed_types:
        return 'Invalid file type', 415
    filename = secure_filename(image.filename)
    random_filename = str(uuid.uuid4()) + os.path.splitext(filename)[1]
    image_path = os.path.join(path, random_filename)
    foo = Image.open(image)
    foo = foo.resize((625, 700))
    foo.save(image_path, optimize=True, quality=95)

    print(image, type(image), image_path, random_filename)
    return random_filename


def set_end_time(hours):
    now = datetime.utcnow()
    end_time = now + timedelta(hours=hours)
    end_time = end_time.replace(minute=end_time.minute if end_time.second < 30 else end_time.minute + 1, second=55,
                                microsecond=0)
    return end_time


def process_expired_auctions():
    print("Transaction executed!")
    conn = RunFirstSettings.create_connection()
    cur = conn.cursor()
    now = get_current_time()
    for _ in range(MAX_TRANSACTION_RETRY_COUNT):
        try:
            # Start a new transaction
            cur.execute('BEGIN')

            # Select expired auctions
            cur.execute('SELECT item_id FROM auctions WHERE end_time <= %s AND is_active = True', (now,))
            expired_auctions = cur.fetchall()

            # For each expired auction, check if there are any bids
            for auction in expired_auctions:
                cur.execute('SELECT user_id FROM Bids WHERE item_id = %s ORDER BY bid_amount DESC LIMIT 1',
                            (auction[0],))
                highest_bidder_id = cur.fetchone()

                # Check if a transaction already exists for this item_id
                cur.execute('SELECT 1 FROM Transactions WHERE item_id = %s', (auction[0],))
                transaction_exists = cur.fetchone()

                # If there is a highest bid and no transaction exists, create a transaction record
                if highest_bidder_id and not transaction_exists:
                    cur.execute('INSERT INTO Transactions (item_id, buyer_id, transaction_date) VALUES (%s, %s, %s)',
                                (auction[0], highest_bidder_id, now))

                # Update the auction to inactive
                cur.execute('UPDATE auctions SET is_active = False WHERE item_id = %s', (auction[0],))

            # Commit the transaction
            conn.commit()
            print("%s auctions has been closed!" % len(expired_auctions))
            break  # If commit was successful, break the retry loop

        except Exception as e:
            # If an error occurs, rollback the transaction
            conn.rollback()
            print(f"An error occurred at auction transaction: {e}")

    cur.close()
    conn.close()


def load_db_config():
    with open('settings.yaml', 'r') as file:
        config = yaml.safe_load(file)
        return config['database']
def dump_database():
    db_config = load_db_config()

    now = datetime.now()
    date_time = now.strftime("%Y-%m-%d_%H-%M-%S")
    dump_file_path = f"dumps/{date_time}_file.sql"

    # Neon CLI komutunu oluşturma
    dump_cmd = f"neon db dump --project-name {db_config['project_name']} --database-name {db_config['name']} --username {db_config['username']} --password {db_config['password']} --host {db_config['host']} --output-file {dump_file_path}"

    try:
        # Komutu çalıştırma
        subprocess.run(dump_cmd, shell=True, check=True)
        print("Database dump successful.")
    except subprocess.CalledProcessError as e:
        print(f"Database dump failed: {str(e)}")

def process_expired_auctionsv2(): # TODO !!!!
    print("Transaction executed!")
    conn = RunFirstSettings.create_connection()
    cur = conn.cursor()
    now = get_current_time()
    for _ in range(MAX_TRANSACTION_RETRY_COUNT):
        try:
            # Start a new transaction
            cur.execute('BEGIN')

            # SQL query to handle the entire process in the database
            cur.execute("""
                WITH expired_auctions AS (
                    SELECT item_id
                    FROM auctions
                    WHERE end_time <= %s AND is_active = TRUE
                ),
                highest_bids AS (
                    SELECT item_id, user_id AS buyer_id
                    FROM Bids
                    WHERE item_id IN (SELECT item_id FROM expired_auctions)
                    ORDER BY bid_amount DESC
                ),
                new_transactions AS (
                    SELECT DISTINCT ON (hb.item_id) 
                        hb.item_id, 
                        hb.buyer_id, 
                        %s AS transaction_date
                    FROM highest_bids hb
                    LEFT JOIN Transactions t ON hb.item_id = t.item_id
                    WHERE t.item_id IS NULL
                ),
                update_auctions AS (
                    UPDATE auctions
                    SET is_active = FALSE
                    WHERE item_id IN (SELECT item_id FROM expired_auctions)
                    RETURNING item_id
                )
                INSERT INTO Transactions (item_id, buyer_id, transaction_date)
                SELECT item_id, buyer_id, transaction_date
                FROM new_transactions;
                RETURNING (SELECT count(1) FROM expired_auctions);
            """, (now, now))

            # Commit the transaction
            conn.commit()
            print("Auctions have been processed and closed successfully!")
            break  # If commit was successful, break the retry loop

        except Exception as e:
            # If an error occurs, rollback the transaction
            conn.rollback()
            print(f"An error occurred at auction transaction: {e}")

    cur.close()
    conn.close()


def create_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(process_expired_auctions, 'cron', second='0')
    #scheduler.add_job(dump_database, 'interval', seconds=10)
    return scheduler



def add_bidding_func():
    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()
    cursor.execute(
        """CREATE OR REPLACE FUNCTION add_bid_function(given_item_id INT, new_bid_amount NUMERIC, given_user_id INT, now TIMESTAMP) RETURNS VOID AS $$
    DECLARE
        last_bid RECORD;
    BEGIN
        -- İtemi kilitle
        PERFORM 1
        FROM items
        WHERE items.item_id = given_item_id
        FOR UPDATE;
        
        -- Satırı kilitle
        SELECT * INTO last_bid
        FROM bids
        WHERE bids.item_id = given_item_id
        ORDER BY bid_amount DESC
        LIMIT 1
        FOR UPDATE;

        -- Eğer son teklif null değilse
        IF last_bid IS NOT NULL THEN
            -- Eğer son teklif geri ödenmişse veya son teklif yeni teklifle aynı veya daha yüksekse hata fırlat
            IF last_bid.refunded OR last_bid.bid_amount >= new_bid_amount THEN
                RAISE EXCEPTION 'New bids on the item!' USING ERRCODE = 'B0001';
            END IF;
            -- Önceki teklif verenin bakiyesini güncelle
            UPDATE virtualcurrency
            SET balance = balance + last_bid.bid_amount
            WHERE user_id = last_bid.user_id;
        END IF;

        -- Yeni teklif verenin bakiyesini güncelle
        UPDATE virtualcurrency
        SET balance = balance - new_bid_amount
        WHERE user_id = given_user_id;

        -- İtemin mevcut fiyatını güncelle
        UPDATE items
        SET current_price = new_bid_amount
        WHERE items.item_id = given_item_id;

        -- Yeni teklifi ekle
        INSERT INTO bids (user_id, item_id, bid_amount, bid_date, refunded)
        VALUES (given_user_id, given_item_id, new_bid_amount, now, FALSE);
    END;
    $$ LANGUAGE plpgsql;"""
    )
    conn.commit()
    conn.close()
    return True

def start_database():
    conn = RunFirstSettings.create_connection()
    cur = conn.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS Users '
                '(user_id SERIAL PRIMARY KEY,'
                ' username VARCHAR(50) NOT NULL UNIQUE,'
                ' password VARCHAR(255) NOT NULL,'
                ' email VARCHAR(255) NOT NULL UNIQUE,'
                ' student_id VARCHAR(50) NOT NULL UNIQUE,'
                ' reputation INT NOT NULL DEFAULT 0,'
                ' avatar_url VARCHAR(50) NOT NULL,'
                ' is_admin BOOLEAN NOT NULL DEFAULT FALSE,'
                ' trx_address VARCHAR(50) NOT NULL UNIQUE,'
                ' is_banned BOOLEAN NOT NULL DEFAULT FALSE,'
                ' registration_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)')

    cur.execute('CREATE TABLE IF NOT EXISTS Items '
                '(item_id SERIAL PRIMARY KEY,'
                ' user_id INT NOT NULL,'
                ' title VARCHAR(255) NOT NULL,'
                ' description VARCHAR(1023) NOT NULL,'
                ' category VARCHAR(255) NOT NULL,'
                ' starting_price DECIMAL(10, 2) NOT NULL,'
                ' current_price DECIMAL(10, 2) NOT NULL,'
                ' image_url VARCHAR(50),'
                ' condition VARCHAR(50) NOT NULL,'
                ' is_active BOOLEAN NOT NULL DEFAULT TRUE,'
                ' publish_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,'
                ' FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE)')


    cur.execute('CREATE TABLE IF NOT EXISTS Bids '
                '(user_id INT NOT NULL,'
                ' item_id INT NOT NULL,'
                ' bid_amount DECIMAL(10, 2) NOT NULL,'
                ' bid_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,'
                ' PRIMARY KEY (item_id, user_id, bid_amount),'
                ' FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,'
                ' FOREIGN KEY (item_id) REFERENCES Items(item_id) ON DELETE CASCADE)')



    cur.execute('CREATE TABLE IF NOT EXISTS Transactions '
                '(item_id INT PRIMARY KEY,'
                ' buyer_id INT NOT NULL,'
                ' transaction_date TIMESTAMP NOT NULL,'
                ' FOREIGN KEY (item_id) REFERENCES Items(item_id) ON DELETE CASCADE,'
                ' FOREIGN KEY (buyer_id) REFERENCES Users(user_id) ON DELETE CASCADE)')

    cur.execute('CREATE TABLE IF NOT EXISTS VirtualCurrency '
                '(user_id INT PRIMARY KEY,'
                ' balance DECIMAL(10, 2) NOT NULL DEFAULT 0,'
                ' FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE)')

    cur.execute('CREATE TABLE IF NOT EXISTS Messages '
                '(message_id SERIAL PRIMARY KEY,'
                ' sender_id INT NOT NULL,'
                ' receiver_id INT NOT NULL,'
                ' message_text VARCHAR(1023) NOT NULL,'
                ' send_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,'
                ' FOREIGN KEY (sender_id) REFERENCES Users(user_id) ON DELETE CASCADE,'
                ' FOREIGN KEY (receiver_id) REFERENCES Users(user_id) ON DELETE CASCADE)')

    cur.execute('CREATE TABLE IF NOT EXISTS Auctions '
                '(item_id INT PRIMARY KEY,'
                ' end_time TIMESTAMP NOT NULL,'
                ' is_active BOOLEAN,'
                ' FOREIGN KEY (item_id) REFERENCES Items(item_id) ON DELETE CASCADE)')

    cur.execute('CREATE TABLE IF NOT EXISTS Deposit '
                '(deposit_id SERIAL PRIMARY KEY,'
                ' user_id INT NOT NULL,'
                ' deposit_amount DECIMAL(10, 2) NOT NULL,'
                ' deposit_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,'
                ' FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE)')

    cur.execute('CREATE TABLE IF NOT EXISTS WithdrawRequest '
                '(withdraw_id SERIAL PRIMARY KEY,'
                ' user_id INT NOT NULL,'
                ' withdraw_amount DECIMAL(10, 2) NOT NULL,'
                ' withdraw_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,'
                ' req_state VARCHAR(50),'
                ' trx_address VARCHAR(50) NOT NULL,'
                ' FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE)')

    cur.execute('CREATE TABLE IF NOT EXISTS TrxKeys '
                '(address VARCHAR(100) PRIMARY KEY,'
                ' public_key VARCHAR(255) NOT NULL,'
                ' private_key VARCHAR(300) NOT NULL,'
                ' FOREIGN KEY (address) REFERENCES Users(trx_address) ON DELETE CASCADE)')

    cur.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    cur.execute('CREATE INDEX IF NOT EXISTS items_title_trgm_idx ON items USING gist (title gist_trgm_ops)')
    cur.execute('CREATE INDEX IF NOT EXISTS hash_index_on_itemidx ON items USING HASH (item_id)')

    conn.commit()
    cur.close()
    conn.close()
