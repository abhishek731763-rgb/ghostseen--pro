from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room
import random, time, base64, os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ghostseen-pro'
socketio = SocketIO(app, cors_allowed_origins="*")

# {room_name: [messages]}
rooms_data = {"global": []}
online_users = {}

def gen_ghost():
    adj = ["Dark","Silent","Cute","Loner","Killer","Shy","Wild","Sad","Lost"]
    return f"{random.choice(adj)}Ghost{random.randint(100,999)}"

@app.route('/')
def home():
    return render_template('chat.html')

@socketio.on('join')
def handle_join(data):
    room = data.get('room','global')
    ghost = data.get('ghost')
    join_room(room)
    if room not in rooms_data:
        rooms_data[room] = []
    online_users[request.sid] = {"ghost": ghost, "room": room}
    emit('history', rooms_data[room], to=request.sid)
    emit('online', len([u for u in online_users.values() if u['room']==room]), room=room)

@socketio.on('message')
def handle_msg(data):
    room = data.get('room','global')
    msg_obj = {
        "id": str(int(time.time()*1000))+str(random.randint(10,99)),
        "ghost": data.get('ghost'),
        "text": data.get('text',''),
        "image": data.get('image',''),
        "time": time.strftime("%I:%M %p"),
        "likes": 0
    }
    if room not in rooms_data:
        rooms_data[room] = []
    rooms_data[room].append(msg_obj)
    if len(rooms_data[room]) > 200:
        rooms_data[room].pop(0)
    emit('new_msg', msg_obj, room=room)

@socketio.on('typing')
def handle_typing(data):
    emit('typing', data, room=data.get('room','global'), include_self=False)

@socketio.on('like')
def handle_like(data):
    room = data.get('room','global')
    msg_id = data.get('id')
    for m in rooms_data.get(room,[]):
        if m['id'] == msg_id:
            m['likes'] += 1
            emit('update_like', m, room=room)
            break

@socketio.on('disconnect')
def handle_dis():
    if request.sid in online_users:
        room = online_users[request.sid]['room']
        del online_users[request.sid]
        emit('online', len([u for u in online_users.values() if u['room']==room]), room=room)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)