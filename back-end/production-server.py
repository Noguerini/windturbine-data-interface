import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import sys
import argparse
import uuid
import numpy as np
import ginsapy.giutility.connect.PyQStationConnectWin as Qstation
import ginsapy.giutility.buffer.GInsDataGetBuffer as QStream
import eventlet.wsgi

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

def start_buffer_stream():
    parser = argparse.ArgumentParser(description="Read values of running buffer and emit them via websocket")
    parser.add_argument("-b", "--buffer_index", type=str, default="0",
                        help="Gi.bench buffer UUID or Controller buffer Index (default: 0)."
                             "Ordering depends on if its a Gi.bench or controller connection")
    parser.add_argument("-a", "--address", type=str, default="192.168.1.100", help="IP address of the Gantner device")

    args = parser.parse_args()

    def is_uuid(value: str) -> bool:
        try:
            uuid.UUID(value)
            return True
        except ValueError:
            return False

    conn_get_stream = QStream.GetProcessBufferServer()

    try:
        count_buffer = conn_get_stream.get_buffer_count()
    except Exception as e:
        print("Error getting buffer count:", e)
        count_buffer = 0

    if count_buffer == 0:
        print("No buffer found.")
    else:
        for buffer_index in range(0, count_buffer):
            try:
                buffer_name, buffer_ID = conn_get_stream.get_buffer_info(int(buffer_index))
                print(f"Found buffer {buffer_index}: {buffer_name} / {buffer_ID}")
            except Exception as e:
                print("Error getting buffer info:", e)

    conn = Qstation.ConnectGIns()

    if is_uuid(args.buffer_index):
        try:
            conn.init_buffer_conn(args.buffer_index)
        except Exception as e:
            print("Error initializing buffer by UUID:", e)
    else:
        try:
            conn.bufferindex = int(args.buffer_index)
        except Exception as e:
            print("Error setting buffer index:", e)

    try:
        conn.init_connection(args.address)
    except Exception as e:
        print("Error initializing connection:", e)

    buffer = conn.yield_buffer()

    print("Starting buffer read loop; emitting to websocket event 'wind_turbine_buffer'")
    try:
        for readbuffer in buffer:
            try:
                parsed = parse_buffer(readbuffer)
                if parsed is not None and parsed["timestamp"] < 40000:
                    socketio.emit('wind_turbine_buffer', parsed, namespace='/')
            except Exception as e:
                print("Emit error:", e)
            socketio.sleep(1)
    except KeyboardInterrupt:
        print("Terminated by user.")
    except Exception as e:
        print("Buffer read loop error:", e)


def parse_buffer(readbuffer):
    if readbuffer is None:
        return None

    # Case 1: list but empty
    if isinstance(readbuffer, list) and len(readbuffer) == 0:
        return None

    # Case 2: list with one ndarray
    if isinstance(readbuffer, list) and len(readbuffer) == 1 and isinstance(readbuffer[0], np.ndarray):
        arr = readbuffer[0]
    elif isinstance(readbuffer, np.ndarray):
        arr = readbuffer
    else:
        return readbuffer  # fallback

    # Case 3: ignore empty arrays
    if arr.size == 0:
        return None

    # Flatten 2D single-row arrays
    if arr.ndim == 2 and arr.shape[0] == 1:
        arr = arr[0]

    # Convert first value to a scalar safely
    timestamp_val = arr[0]
    if isinstance(timestamp_val, np.ndarray):
        timestamp_val = timestamp_val.item() if timestamp_val.size == 1 else float(np.mean(timestamp_val))

    # Convert the rest to a list
    channels = arr[1:]
    if isinstance(channels, np.ndarray):
        channels = channels.flatten().tolist()
    else:
        channels = list(channels)

    channels = channels[:43]
    return {
        "timestamp": float(timestamp_val),
        "channels": channels
    }

# Start streaming once when server runs and also start on client connect if not running
_stream_started = False


@socketio.on('connect')
def handle_connect():
    global _stream_started
    if not _stream_started:
        socketio.start_background_task(start_buffer_stream)
        _stream_started = True
    socketio.emit('status', {'message': 'connected to wind turbine buffer'}, namespace='/')


if __name__ == '__main__':
    if not _stream_started:
        socketio.start_background_task(start_buffer_stream)
        _stream_started = True
    
    print("Starting eventlet WSGI server on http://0.0.0.0:15641")
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 15641)), app)