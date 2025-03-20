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
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: #f5f5f5; height: 100vh; display: flex; flex-direction: column; }
        .header { 
            background: linear-gradient(135deg, #6366f1, #4f46e5); 
            color: white; 
            padding: 15px 20px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.15);
        }
        .header h1 { font-size: 1.5rem; margin-bottom: 5px; }
        .header h2 { font-size: 0.9rem; opacity: 0.8; }
        .chat-container { 
            flex: 1; 
            display: flex; 
            flex-direction: column; 
            max-width: 800px; 
            margin: 0 auto; 
            width: 100%; 
            background: white; 
            box-shadow: 0 5px 20px rgba(0,0,0,0.08);
            border-radius: 12px;
            overflow: hidden;
            margin-top: 20px;
            margin-bottom: 20px;
        }
        .messages-container { 
            flex: 1; 
            overflow-y: auto; 
            padding: 20px; 
            display: flex; 
            flex-direction: column; 
            gap: 12px;
            background-color: #f9fafb;
        }
        .message { 
            padding: 12px 16px; 
            border-radius: 18px; 
            max-width: 75%; 
            word-wrap: break-word; 
            list-style-type: none;
            position: relative;
            animation: fadeIn 0.3s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message.own { 
            background: linear-gradient(135deg, #6366f1, #4f46e5); 
            color: white; 
            align-self: flex-end; 
            border-bottom-right-radius: 5px;
            box-shadow: 0 2px 5px rgba(79, 70, 229, 0.2);
        }
        .message.other { 
            background-color: white; 
            color: #333; 
            align-self: flex-start; 
            border-bottom-left-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            border: 1px solid #eee;
        }
        .message.system { 
            background-color: #fee2e2; 
            color: #991b1b; 
            align-self: center; 
            font-size: 0.85rem; 
            padding: 6px 12px; 
            font-style: italic;
            border-radius: 12px;
            max-width: 90%;
        }
        .message-form { 
            display: flex; 
            padding: 15px; 
            background: white; 
            border-top: 1px solid #f0f0f0;
            align-items: center;
        }
        .message-input { 
            flex: 1; 
            padding: 14px 18px; 
            border: 1px solid #e5e7eb; 
            border-radius: 24px; 
            outline: none; 
            font-size: 0.95rem;
            transition: border 0.2s ease;
            box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        }
        .message-input:focus {
            border-color: #4f46e5;
            box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
        }
        .send-button { 
            background: linear-gradient(135deg, #6366f1, #4f46e5); 
            color: white; 
            border: none; 
            border-radius: 50%; 
            width: 46px; 
            height: 46px; 
            margin-left: 12px; 
            cursor: pointer; 
            display: flex; 
            align-items: center; 
            justify-content: center;
            box-shadow: 0 2px 5px rgba(79, 70, 229, 0.3);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .send-button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(79, 70, 229, 0.4);
        }
        .send-button:active {
            transform: translateY(0);
        }
        .timestamp {
            font-size: 0.7rem;
            opacity: 0.7;
            margin-top: 5px;
            text-align: right;
        }
        .sender-name {
            font-size: 0.8rem;
            font-weight: bold;
            margin-bottom: 4px;
            opacity: 0.8;
        }
        @media (max-width: 640px) {
            .chat-container {
                margin: 0;
                border-radius: 0;
                height: 100vh;
            }
            .message {
                max-width: 85%;
            }
        }
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
            <button class="send-button" type="submit">
                <i class="fas fa-paper-plane"></i>
            </button>
        </form>
    </div>
    <script>
        var client_id = Date.now();
        document.querySelector("#ws-id").textContent = client_id;
        
        // Dynamic WebSocket URL based on current protocol and host
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${client_id}`;
        var ws = new WebSocket(wsUrl);

        function getCurrentTime() {
            const now = new Date();
            return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }

        ws.onopen = function() {
            console.log("Connection established");
        };

        ws.onmessage = function(event) {
            const messagesContainer = document.getElementById('messages');
            const message = document.createElement('li');
            const text = event.data;
            
            if (text.includes("You wrote:")) {
                message.className = "message own";
                
                // Just the message content
                const messageContent = document.createElement('div');
                messageContent.textContent = text.replace("You wrote: ", "");
                message.appendChild(messageContent);
                
                // Add timestamp
                const timestamp = document.createElement('div');
                timestamp.className = "timestamp";
                timestamp.textContent = getCurrentTime();
                message.appendChild(timestamp);
            } else if (text.includes("joined the chat") || text.includes("left the chat")) {
                message.className = "message system";
                message.textContent = text;
            } else if (text.includes("says:")) {
                message.className = "message other";
                
                // Extract client ID and message
                const match = text.match(/Client #(\d+) says: (.*)/);
                if (match) {
                    const clientId = match[1];
                    const messageText = match[2];
                    
                    // Create sender name element
                    const senderName = document.createElement('div');
                    senderName.className = "sender-name";
                    senderName.textContent = `User ${clientId.slice(-4)}`;
                    message.appendChild(senderName);
                    
                    // Create message content
                    const messageContent = document.createElement('div');
                    messageContent.textContent = messageText;
                    message.appendChild(messageContent);
                    
                    // Add timestamp
                    const timestamp = document.createElement('div');
                    timestamp.className = "timestamp";
                    timestamp.textContent = getCurrentTime();
                    message.appendChild(timestamp);
                } else {
                    message.textContent = text;
                }
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
            input.focus();
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