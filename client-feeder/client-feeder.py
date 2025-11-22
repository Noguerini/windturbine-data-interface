import eventlet
eventlet.monkey_patch()

# Import the client version of socketio
import socketio
import sys
import argparse
import uuid
import numpy as np
import ginsapy.giutility.connect.PyQStationConnectWin as Qstation
import ginsapy.giutility.buffer.GInsDataGetBuffer as QStream
import time # Added for client sleep functionality

# --- Configuration ---
SERVER_URL = 'http://87.152.190.203:15064'
EMIT_EVENT = 'data'
# ---------------------


# Initialize the SocketIO Client
sio = socketio.Client(logger=True, engineio_logger=True, reconnect=True, reconnection_attempts=5)

def parse_buffer(readbuffer):
    """
    Parses the data buffer read from the GINS connection.
    (This function remains largely the same as in the original code)
    """
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
        return readbuffer # fallback

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


def start_buffer_stream():
    """
    Connects to the Gantner device, reads the buffer, and emits data to the server.
    """
    parser = argparse.ArgumentParser(description="Read values of running buffer and emit them via websocket")
    parser.add_argument("-b", "--buffer_index", type=str, default="0",
                        help="Gi.bench buffer UUID or Controller buffer Index (default: 0)."
                             "Ordering depends on if its a Gi.bench or controller connection")
    parser.add_argument("-a", "--address", type=str, default="192.168.1.100", help="IP address of the Gantner device")

    parser.add_argument("-s", "--server_url", type=str, default=SERVER_URL,
                        help=f"WebSocket server URL (default: {SERVER_URL})")

    args = parser.parse_args()
    SERVER_URL = args.server_url

    def is_uuid(value: str) -> bool:
        try:
            uuid.UUID(value)
            return True
        except ValueError:
            return False

    # --- QStream Setup (unchanged) ---
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
    # ---------------------------------

    conn = Qstation.ConnectGIns()

    if is_uuid(args.buffer_index):
        try:
            conn.init_buffer_conn(args.buffer_index)
        except Exception as e:
            print("Error initializing buffer by UUID:", e)
            sys.exit(1)
    else:
        try:
            conn.bufferindex = int(args.buffer_index)
        except Exception as e:
            print("Error setting buffer index:", e)
            sys.exit(1)

    try:
        conn.init_connection(args.address)
    except Exception as e:
        print("Error initializing connection to Gantner device:", e)
        sys.exit(1)

    buffer = conn.yield_buffer()

    # --- Client Connection and Data Loop ---
    try:
        # Connect to the server. This blocks until connected or failed.
        print(f"Connecting to WebSocket server at {SERVER_URL}...")
        sio.connect(SERVER_URL)
        print("Client connected successfully.")

        print(f"Starting buffer read loop; emitting to server event '{EMIT_EVENT}'")
        for readbuffer in buffer:
            try:
                parsed = parse_buffer(readbuffer)
                if parsed is not None and parsed["timestamp"] < 40000:
                    # Use sio.emit to send data to the connected server
                    sio.emit(EMIT_EVENT, parsed)
            except Exception as e:
                print("Emit error:", e)

            # Use time.sleep instead of socketio.sleep since we are in the client context
            time.sleep(1) # Sleep for 1 second between reads
            
    except socketio.exceptions.ConnectionError as e:
        print(f"Connection failed: {e}. Is the server running at {SERVER_URL}?")
    except KeyboardInterrupt:
        print("Terminated by user.")
    except Exception as e:
        print("Buffer read loop or connection error:", e)
    finally:
        # Disconnect gracefully when the loop finishes or an error occurs
        if sio.connected:
            sio.disconnect()
        print("Client disconnected.")

# --- SocketIO Client Event Handlers ---

@sio.event
def connect():
    """Handler for successful connection to the server."""
    print("Connection established with server!")
    # Optional: Send an initial message to the server
    sio.emit('client_status', {'message': 'Gantner buffer client connected'})

@sio.event
def disconnect():
    """Handler for disconnection from the server."""
    print("Disconnected from server.")

@sio.event
def connect_error(data):
    """Handler for connection errors."""
    print(f"The connection failed! Data: {data}")

if __name__ == '__main__':
    start_buffer_stream()