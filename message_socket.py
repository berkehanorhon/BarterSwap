from flask_socketio import send, emit

import RunFirstSettings
from app import socketio

@socketio.on('send_private_message')
def handle_private_message(data):
    sender_id = data['sender_id']
    recipient_id = data['recipient_id']
    content = data['message_text']
    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO Messages (sender_id, receiver_id, message_text) VALUES (%s, %s, %s)',
        (sender_id, recipient_id, content))
    conn.commit()
    conn.close()
    emit('receive_message', {'content': content, 'sender_id': sender_id}, room=recipient_id)
    emit('new_private_message', {'content': content, 'sender_id': sender_id}, room=recipient_id)

@socketio.on('get_user_messages')
def get_user_messages(user_id):
    conn = RunFirstSettings.create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Messages WHERE sender_id = %s OR receiver_id = %s', (user_id, user_id))
    messages = cursor.fetchall()
    conn.close()
    emit('display_messages', {'messages': messages}, room=user_id)