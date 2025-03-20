from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import os
import uvicorn

app = FastAPI()

# Get port from environment variable (for Render compatibility)
PORT = int(os.environ.get("PORT", 8000))

html = """ 
<!DOCTYPE html>
<html>
<head>
    <title>Chat Application</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: #f5f5f5; height: 100vh; display: flex; flex-direction: column; }
        .header { background-color: #4e54c8; color: white; padding: 15px 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .chat-container { flex: 1; display: flex; flex-direction: column; max-width: 800px; margin: 0 auto; width: 100%; background: white; box-shadow: 0 0 10px rgba(0,0,0,0.05); }
        .messages-container { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 10px; }
        .message { padding: 10px 15px; border-radius: 18px; max-width: 70%; word-wrap: break-word; list-style-type: none; }
        .message.own { background-color: #4e54c8; color: white; align-self: flex-end; border-bottom-right-radius: 5px; }
        .message.other { background-color: #e9e9eb; color: #333; align-self: flex-start; border-bottom-left-radius: 5px; }
        .message.system { background-color: #f8d7da; color: #721c24; align-self: center; font-size: 0.85rem; padding: 6px 12px; font-style: italic; }
        .message-form { display: flex; padding: 15px; border-top: 1px solid #e0e0e0; background: white; }
        .message-input { flex: 1; padding: 12px 15px; border: 1px solid #ddd; border-radius: 20px; outline: none; font-size: 0.95rem; }
        .send-button { background-color: #4e54c8; color: white; border: none; border-radius: 50%; width: 40px; height: 40px; margin-left: 10px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        .send-button:hover { background-color: #3c40c6; }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="header">
            <h1>WebSocket Chat</h1>
            <h2>Your ID: <span id="ws-id"></span></h2>
        </div>
        <div class="messages-container" id="messages">
            <li class="message system">Welcome to the chat room! You are now connected.</li>
        </div>
        <form class="message-form" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" class="message-input" placeholder="Type a message..." autocomplete="off"/>
            <button class="send-button">Send</button>
        </form>
    </div>
    <script>
        var client_id = Date.now();
        document.querySelector("#ws-id").textContent = client_id;
        
        // Dynamic WebSocket URL based on current protocol and host
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${client_id}`;
        var ws = new WebSocket(wsUrl);

        ws.onopen = function() {
            console.log("Connection established");
        };

        ws.onmessage = function(event) {
            const messagesContainer = document.getElementById('messages');
            const message = document.createElement('li');
            const text = event.data;
            
            if (text.includes("You wrote:")) {
                message.className = "message own";
                message.textContent = text.replace("You wrote: ", "");
            } else if (text.includes("joined the chat") || text.includes("left the chat")) {
                message.className = "message system";
                message.textContent = text;
            } else {
                message.className = "message other";
                message.textContent = text;
            }

            messagesContainer.appendChild(message);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        };

        ws.onclose = function() {
            const messagesContainer = document.getElementById('messages');
            const message = document.createElement('li');
            message.className = "message system";
            message.textContent = "Connection closed. Please refresh the page.";
            messagesContainer.appendChild(message);
        };

        function sendMessage(event) {
            event.preventDefault();
            const input = document.getElementById("messageText");
            const message = input.value.trim();
            if (message) {
                ws.send(message);
                input.value = '';
            }
        }
    </script>
</body>
</html>
"""

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, sender_websocket: WebSocket = None):
        for connection in self.active_connections:
            if connection != sender_websocket:
                try:
                    await connection.send_text(message)
                except:
                    self.disconnect(connection)

manager = ConnectionManager()

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    await manager.broadcast(f"Client #{client_id} joined the chat", websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")

# This is for local development
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)