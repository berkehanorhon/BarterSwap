# socketio_handlers.py
from flask import session, flash
from flask_socketio import SocketIO, emit
import asyncio
import time
import RunFirstSettings
from tronapi import Tron

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

async def check_transaction(public_key, user_id):
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

            cursor.execute('SELECT balance FROM virtualcurrency WHERE user_id = %s', (user_id,))
            current_balance = cursor.fetchone()[0]

            new_balance = current_balance + int(balance / 1000000)
            cursor.execute('UPDATE virtualcurrency SET balance = %s WHERE user_id = %s', (new_balance, user_id))

            cursor.execute("Select private_key FROM trxkeys WHERE address = %s", (public_key,))
            tron.private_key = cursor.fetchone()[0]
            tron.default_address = public_key

            balance = float(balance / 1000000)
            transaction = tron.trx.send_transaction(source_address, balance)
            conn.commit()
            cursor.close()
            conn.close()

            socketio.emit('transaction_complete', {'message': 'Transaction completed successfully.'}, namespace='/test')
            transaction_started_flags.pop(user_id)
            return

        except Exception as e:
            import traceback
            print(f'Error : {e}')
            traceback.print_exc()
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
