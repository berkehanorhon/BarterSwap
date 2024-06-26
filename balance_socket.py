# socketio_handlers.py
import traceback
from Crypto.Cipher import AES
import base64
import hashlib
from flask import session, flash
from flask_socketio import SocketIO, emit
import asyncio
import time
import RunFirstSettings
from tronapi import Tron
import traceback

# Initialize SocketIO
socketio = SocketIO()

full_node = 'https://api.trongrid.io'
solidity_node = 'https://api.trongrid.io'
event_server = 'https://api.trongrid.io'

tron = Tron(full_node=full_node,
            solidity_node=solidity_node,
            event_server=event_server)

source_address = "TViENFFbjQFmU3gKDUtcXpMYHZJ8xsjXLD"

transaction_started_flags = {}

def derive_key(password: str) -> bytes:
    return hashlib.sha256(password.encode()).digest()

def decrypt_given_data(encrypted_data: str, password: str) -> str:
    key = derive_key(password)
    encrypted_data = base64.b64decode(encrypted_data)
    nonce = encrypted_data[:16]
    ciphertext = encrypted_data[16:]
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    decrypted_data = cipher.decrypt(ciphertext).decode('utf-8')
    return decrypted_data


async def check_transaction(public_key, user_id):  # TODO Transactional deposit implementation
    start_time = time.time()
    transaction_started_flags[user_id] = True
    while time.time() - start_time < 3600:  # 1 hour
        try:
            balance = tron.trx.get_balance(public_key)

            if balance < 5000000:
                await asyncio.sleep(10)
                continue

            conn = RunFirstSettings.create_connection()
            cursor = conn.cursor()

            # Transaction başlat
            cursor.execute('BEGIN')

            cursor.execute('UPDATE virtualcurrency SET balance = balance + %s WHERE user_id = %s',
                           (float(balance / 1000000), user_id))

            cursor.execute("SELECT private_key FROM trxkeys WHERE address = %s", (public_key,))
            private_key_result = cursor.fetchone()

            if not private_key_result:
                raise Exception("Private key not found for the given public key.")

            decrypted_data = decrypt_given_data(private_key_result[0], RunFirstSettings.get_password())

            tron.private_key = decrypted_data
            tron.default_address = public_key

            balance = float(balance / 1000000)
            cursor.execute('INSERT INTO deposit (user_id, deposit_amount) VALUES (%s, %s)', (user_id, balance))

            # Transaction gerçekleştir
            transaction = tron.trx.send_transaction(source_address, balance)
            if not transaction['result']:
                raise Exception("Transaction failed on blockchain side.")

            conn.commit()
            cursor.close()
            conn.close()

            socketio.emit('transaction_complete', {'message': 'Transaction completed successfully.'}, namespace='/test')
            transaction_started_flags.pop(user_id)
            return

        except Exception as e:
            print(f'Error: {e}')
            traceback.print_exc()

            if 'conn' in locals() and conn is not None:
                conn.rollback()
                cursor.close()
                conn.close()

            socketio.emit('transaction_failed', {'message': 'Transaction failed.'}, namespace='/test')
            transaction_started_flags.pop(user_id)
            return
    transaction_started_flags[user_id] = False


def start_check_transaction(public_key, user_id):
    if user_id in transaction_started_flags and transaction_started_flags[user_id] is True:
        return
    asyncio.run(check_transaction(public_key, user_id))

@socketio.on('connect')
def on_custom_connect():
    if 'user_id' in session:
        user_id = session['user_id']
        conn = RunFirstSettings.create_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT trx_address FROM users WHERE user_id = %s', (user_id,))
        public_key = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        # Start background task to check for transactions
        socketio.start_background_task(start_check_transaction, public_key, user_id)
