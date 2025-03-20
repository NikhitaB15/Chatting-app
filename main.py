from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat Application</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            
            body {
                background-color: #f5f5f5;
                height: 100vh;
                display: flex;
                flex-direction: column;
            }
            
            .header {
                background-color: #4e54c8;
                color: white;
                padding: 15px 20px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            
            .header h1 {
                font-size: 1.5rem;
                font-weight: 500;
            }
            
            .header h2 {
                font-size: 0.9rem;
                opacity: 0.8;
                font-weight: 400;
                margin-top: 5px;
            }
            
            .chat-container {
                flex: 1;
                display: flex;
                flex-direction: column;
                max-width: 800px;
                margin: 0 auto;
                width: 100%;
                background: white;
                box-shadow: 0 0 10px rgba(0,0,0,0.05);
            }
            
            .messages-container {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            
            .message {
                padding: 10px 15px;
                border-radius: 18px;
                max-width: 70%;
                word-wrap: break-word;
                animation: fadeIn 0.3s;
                list-style-type: none;
            }
            
            .message.own {
                background-color: #4e54c8;
                color: white;
                align-self: flex-end;
                border-bottom-right-radius: 5px;
            }
            
            .message.other {
                background-color: #e9e9eb;
                color: #333;
                align-self: flex-start;
                border-bottom-left-radius: 5px;
            }
            
            .message.system {
                background-color: #f8d7da;
                color: #721c24;
                align-self: center;
                font-size: 0.85rem;
                border-radius: 10px;
                padding: 6px 12px;
                font-style: italic;
            }
            
            .message-form {
                display: flex;
                padding: 15px;
                border-top: 1px solid #e0e0e0;
                background: white;
            }
            
            .message-input {
                flex: 1;
                padding: 12px 15px;
                border: 1px solid #ddd;
                border-radius: 20px;
                outline: none;
                font-size: 0.95rem;
            }
            
            .message-input:focus {
                border-color: #4e54c8;
            }
            
            .send-button {
                background-color: #4e54c8;
                color: white;
                border: none;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                margin-left: 10px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background-color 0.2s;
            }
            
            .send-button:hover {
                background-color: #3c40c6;
            }
            
            .send-icon {
                width: 20px;
                height: 20px;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            /* Responsiveness */
            @media (max-width: 600px) {
                .chat-container {
                    height: 100%;
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
                <button class="send-button">
                    <svg class="send-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="22" y1="2" x2="11" y2="13"></line>
                        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>
                </button>
            </form>
        </div>
        
        <script>
            var client_id = Date.now();
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8000/ws/${client_id}`);
            
            const messagesContainer = document.getElementById('messages');
            
            ws.onopen = function() {
                console.log("Connection established");
            };
            
           ws.onmessage = function(event) {
    const message = document.createElement('li');
    const text = event.data;
    
    // Determine message type
    if (text.startsWith("You wrote:")) {
        message.className = "message own";
        message.textContent = text.replace("You wrote: ", "");
    } else if (text.startsWith("Client #") && (text.includes("joined the chat") || text.includes("left the chat"))) {
        message.className = "message system";
        message.textContent = text;
    } else if (text.startsWith("Client #") && text.includes("says:")) {
        // Handle messages from other users
        message.className = "message other";
        message.textContent = text;
    } else {
        message.className = "message other";
        message.textContent = text;
    }
    
    messagesContainer.appendChild(message);
    scrollToBottom();
};
            
            ws.onclose = function() {
                const message = document.createElement('li');
                message.className = "message system";
                message.textContent = "Connection closed. Please refresh the page.";
                messagesContainer.appendChild(message);
            };
            
            function sendMessage(event) {
                const input = document.getElementById("messageText");
                const message = input.value.trim();
                
                if (message) {
                    ws.send(message);
                    input.value = '';
                }
                
                event.preventDefault();
                input.focus();
            }
            
            function scrollToBottom() {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
            
            // Add event listener for Enter key
            document.getElementById("messageText").addEventListener("keypress", function(e) {
                if (e.key === "Enter" && !e.shiftKey) {
                    sendMessage(e);
                }
            });
            
            // Focus input on load
            window.onload = function() {
                document.getElementById("messageText").focus();
            };
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
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, sender_websocket: WebSocket = None):
        for connection in self.active_connections:
            if connection != sender_websocket: 
                await connection.send_text(message)


manager = ConnectionManager()


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        await manager.broadcast(f"Client #{client_id} joined the chat", websocket)
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"{data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat", websocket)