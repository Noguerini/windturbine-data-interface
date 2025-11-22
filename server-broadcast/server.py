import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import eventlet.wsgi
import json

# --- Configuration ---
HOST = '0.0.0.0'
PORT = 15064
DATA_EVENT = 'data'
# ---------------------

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}) 

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# SocketIO Event Handlers
@socketio.on('connect')
def handle_connect():
    """Handles new client connections."""
    print(f"\n✅ Client connected from: {socketio.request.sid}")
    socketio.emit('status', {'message': 'Server connected, ready to receive data'}, room=socketio.request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    """Handles client disconnections."""
    print(f"\n❌ Client disconnected: {socketio.request.sid}")

@socketio.on('client_status')
def handle_client_status(data):
    """Listens for the initial status message from the client."""
    print(f"\nℹ️ Client Status Update ({socketio.request.sid}): {data['message']}")

@socketio.on(DATA_EVENT)
def handle_data(data):
    """
    Listens for the 'data' event, which is the buffer stream payload.
    This is the core function for receiving your data.
    """
    # Print the received data structure for verification
    print(f"--- Data Received ({socketio.request.sid}) ---")
    
    # Use json.dumps to print the dictionary nicely
    # We only print the first few channels to keep the output readable
    
    # Safely print timestamp and a sample of channels
    timestamp = data.get('timestamp')
    channels = data.get('channels', [])
    
    print(f"Timestamp: {timestamp}")
    print(f"Channels (First 5/Total {len(channels)}): {channels[:5]} ...")
    
    # Optional: Emit an acknowledgment back to the client
    # socketio.emit('data_ack', {'status': 'received', 'timestamp': timestamp}, room=socketio.request.sid)

## ▶️ Main Server Execution

if __name__ == '__main__':
    print(f"Starting eventlet WSGI server on http://{HOST}:{PORT}")
    try:
        # Start the server
        eventlet.wsgi.server(eventlet.listen((HOST, PORT)), app)
    except KeyboardInterrupt:
        print("\nServer terminated by user.")
    except Exception as e:
        print(f"\nServer error: {e}")