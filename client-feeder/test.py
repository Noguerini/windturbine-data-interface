import websocket

ws = websocket.WebSocket()
ws.connect("ws://87.152.190.203:15064/ws")

ws.send("Hello from client!")
print("Response:", ws.recv())

ws.close()