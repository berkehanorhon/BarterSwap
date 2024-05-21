import asyncio
from flask import flash, redirect, url_for, render_template, request, session
from tronapi import Tron
import RunFirstSettings
import time
tron = Tron()

from flask import Blueprint

balance_handlers = Blueprint('balance_handlers', __name__, static_folder='static', template_folder='templates')


# Asynchronous function to check if money has been transferred from another account
async def check_transaction(public_key, amount, user_id):
    start_time = time.time()
    while time.time() - start_time < 3600:  # 1 hour
        transactions = tron.trx.get_transactions_related(public_key, 'all')
        for tx in transactions['transaction']:
            # change amount with -+ %10
            if tx['raw_data']['contract'][0]['parameter']['value']['amount'] == amount:
                flash('Money has been transferred from another account', 'success')
                # Get the current balance of the user
                conn = RunFirstSettings.create_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT balance FROM users WHERE user_id = %s', (user_id,))
                current_balance = cursor.fetchone()[0]
                # Add the transferred amount to the current balance
                new_balance = current_balance + amount
                # Update the balance in the database
                cursor.execute('UPDATE users SET balance = %s WHERE user_id = %s', (new_balance, user_id))
                conn.commit()
                return
        await asyncio.sleep(10)  # 10 seconds

@balance_handlers.route('/balance', methods=['GET', 'POST'])
def balance():
    if 'user_id' not in session:
        return redirect(url_for('user_handlers.signin'))

    user_id = session['user_id']

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()

    # Get the user's TRX public key
    cursor.execute('SELECT trx_public_key FROM users WHERE user_id = %s', (user_id,))
    public_key = cursor.fetchone()[0]

    if request.method == 'POST':
        # Check if the user wants to load money into their TRX account
        amount = request.form['amount']

        # Get the user's private key
        cursor.execute('SELECT trx_private_key FROM user_keys WHERE user_id = %s', (user_id,))
        private_key = cursor.fetchone()[0]

        # Perform the money loading operation
        tron.private_key = private_key
        transaction = tron.trx.send_transaction(public_key, amount)

        # Check if the money loading operation was successful
        transaction_info = tron.trx.get_transaction(transaction['transaction']['txID'])
        if transaction_info['ret'][0]['contractRet'] != 'SUCCESS':
            flash('Transaction failed', 'error')
            return redirect(url_for('user_handlers.balance'))

        # Check if money has been transferred from another account to a specific address
        asyncio.run(check_transaction(public_key, amount, user_id))

    # Get the user's balance
    balance = tron.trx.get_balance(public_key)

    conn.close()

    return render_template('balance.html', balance=balance)