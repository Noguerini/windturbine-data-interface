import argparse
import uuid
import numpy as np
import socketio
import time

import ginsapy.giutility.connect.PyQStationConnectWin as Qstation
import ginsapy.giutility.buffer.GInsDataGetBuffer as QStream


# ---------------------------
# Connect to cloud Socket.IO
# ---------------------------

sio = socketio.Client(reconnection=True, reconnection_attempts=999999, reconnection_delay=2)


@sio.event
def connect():
    print("Connected to cloud server")


@sio.event
def disconnect():
    print("Disconnected from cloud server")


def parse_buffer(readbuffer):
    """
    Safely converts a Gantner readbuffer into a JSON-serializable dict.
    """
    if readbuffer is None:
        return None

    if isinstance(readbuffer, list) and len(readbuffer) == 1 and isinstance(readbuffer[0], np.ndarray):
        arr = readbuffer[0]
    elif isinstance(readbuffer, np.ndarray):
        arr = readbuffer
    else:
        return None

    if arr.size == 0:
        return None

    if arr.ndim == 2 and arr.shape[0] == 1:
        arr = arr[0]

    ts = arr[0]
    if isinstance(ts, np.ndarray):
        ts = float(ts.item())

    channels = arr[1:].flatten().tolist()

    return {
        "timestamp": float(ts),
        "channels": channels
    }


def start_buffer_stream(cloud_url):
    # Connect to cloud server
    print(f"Connecting to cloud server: {cloud_url}")
    try:
        sio.connect(cloud_url)
    except Exception as e:
        print("Could not connect to cloud server:", e)
        time.sleep(3)
        start_buffer_stream(cloud_url)

    # Parse CLI args
    parser = argparse.ArgumentParser(description="Gantner feed → cloud websocket client")
    parser.add_argument("-b", "--buffer_index", type=str, default="0",
                        help="Gi.bench buffer UUID or Controller buffer Index")
    parser.add_argument("-a", "--address", type=str, default="192.168.1.100",
                        help="IP address of the Gantner device")

    args = parser.parse_args()

    def is_uuid(value: str) -> bool:
        try:
            uuid.UUID(value)
            return True
        except ValueError:
            return False

    # Discover buffers
    conn_get_stream = QStream.GetProcessBufferServer()
    try:
        count_buffer = conn_get_stream.get_buffer_count()
    except Exception as e:
        print("Error getting buffer count:", e)
        count_buffer = 0

    if count_buffer == 0:
        print("No buffer found.")
    else:
        for i in range(count_buffer):
            try:
                name, bid = conn_get_stream.get_buffer_info(i)
                print(f"Found buffer {i}: {name} / {bid}")
            except Exception as e:
                print("Error getting buffer info:", e)

    # Initialize Gantner connection
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

    print("Starting buffer read loop → cloud websocket")

    counter = 0

    # Stream loop
    for readbuffer in buffer:
        parsed = parse_buffer(readbuffer)
        counter += 1
        if parsed:
            try:
                sio.emit("wind_turbine_buffer", parsed)
                if counter % 500 == 0:
                    print(parsed)
            except Exception as e:
                print("Emit failed (reconnecting):", e)

        time.sleep(0.01)


if __name__ == "__main__":
    CLOUD_WS_URL = "https://MYIP:3000"   # ← fill this in
    
    start_buffer_stream(CLOUD_WS_URL)