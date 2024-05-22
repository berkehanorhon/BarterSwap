import asyncio
from flask import flash, redirect, url_for, render_template, request, session
from tronapi import Tron
import RunFirstSettings
import time
from flask import Blueprint

tron = Tron()
balance_handlers = Blueprint('balance_handlers', __name__, static_folder='static', template_folder='templates')


@balance_handlers.route('/balance', methods=['GET', 'POST'])
def deposit():
    if 'user_id' not in session:
        return redirect(url_for('user_handlers.signin'))

    user_id = session['user_id']

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()


    if request.method == 'POST':
        # Get the user's TRX public key
        cursor.execute('SELECT trx_public_key FROM users WHERE user_id = %s', (user_id,))
        public_key = cursor.fetchone()[0]
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
            return redirect(url_for('balance_handlers.deposit'))

        # Check if money has been transferred from another account to a specific address
        asyncio.run(check_transaction(public_key, amount, user_id))

    # Get the user's balance
    cursor.execute('SELECT balance FROM virtualcurrency WHERE user_id = %s', (user_id,))
    balance = cursor.fetchone()[0]

    cursor.execute('SELECT trx_address FROM users WHERE user_id = %s', (user_id,))
    trx_address = cursor.fetchone()[0]

    conn.close()
    print(222)
    return render_template('deposit.html', balance=balance,trx_address = trx_address)