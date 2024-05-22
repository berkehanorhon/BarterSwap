import mimetypes
import os.path
from PIL import Image
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime, timedelta
import RunFirstSettings
from apscheduler.schedulers.background import BackgroundScheduler

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
            cur.execute('SELECT * FROM auctions WHERE end_time <= %s AND is_active = True', (now,))
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


def create_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(process_expired_auctions, 'cron', second='0')
    return scheduler
