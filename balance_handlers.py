import asyncio
from flask import flash, redirect, url_for, render_template, request, session
from tronapi import Tron
import RunFirstSettings
import time
from flask import Blueprint

tron = Tron()
balance_handlers = Blueprint('balance_handlers', __name__, static_folder='static', template_folder='templates')


@balance_handlers.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'user_id' not in session:
        return redirect(url_for('user_handlers.signin'))

    user_id = session['user_id']

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()

    # Get the user's balance
    cursor.execute('SELECT balance FROM virtualcurrency WHERE user_id = %s', (user_id,))
    balance = cursor.fetchone()[0]

    cursor.execute('SELECT trx_address FROM users WHERE user_id = %s', (user_id,))
    trx_address = cursor.fetchone()[0]

    conn.close()
    return render_template('deposit.html', balance=balance,trx_address = trx_address)

@balance_handlers.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'user_id' not in session:
        return redirect(url_for('user_handlers.signin'))

    user_id = session['user_id']

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        trx_address = request.form.get('trx_address')
        amount = float(request.form.get('amount'))  # Get the withdrawal amount

        # Check if the TRX address is valid
        if tron.isAddress(trx_address):
            # Get the user's balance
            cursor.execute('SELECT balance FROM virtualcurrency WHERE user_id = %s', (user_id,))
            balance = cursor.fetchone()[0]

            # Check if the user has enough balance
            if balance < amount:
                flash('Not enough balance for this withdrawal', 'error')
            else:
                # Update the user's balance
                cursor.execute('UPDATE virtualcurrency SET balance = balance - %s WHERE user_id = %s', (amount, user_id))
                conn.commit()
                flash('The TRX address is valid and the withdrawal was successful.', 'success')
        else:
            flash('The TRX address is not valid.', 'error')



    # Get the user's balance
    cursor.execute('SELECT balance FROM virtualcurrency WHERE user_id = %s', (user_id,))
    balance = cursor.fetchone()[0]

    conn.close()
    return render_template('withdraw.html', balance=balance)