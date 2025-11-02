from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

app = Flask(__name__)
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/wind-turbine-data')
def wind_turbine_data():
    # Return the data received from the wind turbine
    return {"data": "Wind turbine data"}

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=15641)