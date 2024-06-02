import mimetypes
import os.path
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
