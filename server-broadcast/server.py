import eventlet
eventlet.monkey_patch()

from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO
import eventlet.wsgi

HOST = '0.0.0.0'
PORT = 15064
DATA_EVENT = 'data'

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")


@socketio.on('connect')
def handle_connect(auth):
    print(f"\n✅ Client connected: {request.sid}")
    socketio.emit('status', {'message': 'Server ready'}, room=request.sid)


@socketio.on('disconnect')
def handle_disconnect():
    print(f"\n❌ Client disconnected: {request.sid}")


@socketio.on('client_status')
def handle_client_status(data):
    print(f"\nℹ️ Status from {request.sid}: {data['message']}")


@socketio.on(DATA_EVENT)
def handle_data(data):
    timestamp = data.get('timestamp')
    channels = data.get('channels', [])

    print("--- Data Received ---")
    print(f"Timestamp: {timestamp}")
    print(f"Channels (First 5/{len(channels)}): {channels[:5]} ...")


if __name__ == '__main__':
    print(f"Starting eventlet WSGI server on http://{HOST}:{PORT}")
    eventlet.wsgi.server(eventlet.listen((HOST, PORT)), app)
