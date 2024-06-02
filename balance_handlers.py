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
    return render_template('account_balance/deposit.html', balance=balance, trx_address = trx_address)

@balance_handlers.route('/withdraw', methods=['GET', 'POST'])
def withdraw():  # TODO Transactional withdraw implementation
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
                try:
                    # Transaction başlat
                    cursor.execute('BEGIN')

                    # Insert a record into the withdrawRequest table with 'Pending' state
                    cursor.execute(
                        'INSERT INTO withdrawRequest (user_id, withdraw_amount, req_state, trx_address) VALUES (%s, %s, %s, %s)',
                        (user_id, amount, 'Pending', trx_address))

                    # Update the user's balance
                    cursor.execute('UPDATE virtualcurrency SET balance = balance - %s WHERE user_id = %s FOR UPDATE',
                                   (amount, user_id))

                    # Commit işlemi
                    conn.commit()
                    flash('The TRX address is valid and the withdraw request is successful.', 'success')

                except Exception as e:
                    # Rollback işlemi
                    conn.rollback()
                    flash('An error occurred while processing the withdrawal.', 'error')
        else:
            flash('The TRX address is not valid.', 'error')

    # Cleanup işlemleri
    cursor.close()
    conn.close()

    return redirect(url_for('item_handlers.get_item', item_id=item_id))


@balance_handlers.route('/account_balance', methods=['GET', 'POST'])
def account_balance():
    if 'user_id' not in session:
        return redirect(url_for('user_handlers.signin'))

    user_id = session['user_id']

    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()

    # Get the user's balance
    cursor.execute('SELECT balance FROM virtualcurrency WHERE user_id = %s', (user_id,))
    balance = cursor.fetchone()[0]

    # Get the user's deposits
    cursor.execute('SELECT deposit_amount, deposit_date FROM deposit WHERE user_id = %s ORDER BY deposit_date DESC', (user_id,))
    deposits = cursor.fetchall()

    # Get the user's withdraw requests
    cursor.execute('SELECT withdraw_amount, withdraw_date, req_state FROM withdrawRequest WHERE user_id = %s ORDER BY withdraw_date DESC', (user_id,))
    withdraws = cursor.fetchall()

    conn.close()
    return render_template('account_balance/account_balance.html', balance=balance, deposits=deposits, withdraws=withdraws)