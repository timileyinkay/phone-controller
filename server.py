#!/usr/bin/env python3
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO
import hashlib, hmac, json, time, subprocess, os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'quantum_phoenix_server_2024')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Phoenix registry and command history
PHOENIX_REGISTRY = {}
COMMAND_HISTORY = []
COMMAND_KEY = "quantum_phoenix_master_key_2024"

def sign_command(command):
    """Sign commands with HMAC-SHA256"""
    return hmac.new(
        COMMAND_KEY.encode(), 
        command.encode(), 
        hashlib.sha256
    ).hexdigest()

# SIMPLIFIED HTML - Remove complex features for now
HTML = '''<!DOCTYPE html>
<html>
<head>
    <title>QUANTUM PHOENIX CONTROL</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background: #0a0a0a; color: #00ff00; font-family: monospace; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .header { text-align: center; padding: 20px; border: 1px solid #00ff00; margin-bottom: 20px; }
        .command-interface { padding: 20px; border: 1px solid #00ff00; margin-bottom: 20px; }
        .command-input { width: 100%; padding: 10px; background: #000; color: #00ff00; border: 1px solid #00ff00; margin: 10px 0; }
        .btn { background: #000; color: #00ff00; border: 1px solid #00ff00; padding: 10px; cursor: pointer; }
        .output { background: #000; padding: 15px; border: 1px solid #00ff00; height: 300px; overflow-y: auto; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔥 QUANTUM PHOENIX CONTROL</h1>
            <p>Server Status: <span id="status">Connecting...</span></p>
            <p>Active Clients: <span id="clientCount">0</span></p>
        </div>

        <div class="command-interface">
            <h3>Command Interface</h3>
            <input type="text" id="commandInput" class="command-input" placeholder="Enter command...">
            <button class="btn" onclick="sendCommand()">Send Command</button>
            
            <div class="output" id="output">
                <div>> Quantum Server Ready</div>
                <div>> Waiting for connections...</div>
            </div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        const socket = io();
        
        socket.on('connect', () => {
            document.getElementById('status').textContent = 'Connected';
            addOutput('🔗 Connected to server');
        });

        socket.on('disconnect', () => {
            document.getElementById('status').textContent = 'Disconnected';
            addOutput('❌ Disconnected from server');
        });

        socket.on('phoenix_quantum', (data) => {
            addOutput(`🔥 New client: ${data.id}`);
            updateClientCount();
        });

        socket.on('quantum_response', (data) => {
            addOutput(`📱 ${data.id}: ${data.result}`);
        });

        function sendCommand() {
            const command = document.getElementById('commandInput').value;
            if (!command) return;
            
            addOutput(`📤 Sending: ${command}`);
            socket.emit('quantum_command', {
                id: 'all',  // Send to all clients
                c: command
            });
            
            document.getElementById('commandInput').value = '';
        }

        function addOutput(text) {
            const output = document.getElementById('output');
            const timestamp = new Date().toLocaleTimeString();
            output.innerHTML = `<div>[${timestamp}] ${text}</div>` + output.innerHTML;
        }

        function updateClientCount() {
            // Simple count update - you can make this more sophisticated
            const count = document.querySelectorAll('#output div:contains("New client")').length;
            document.getElementById('clientCount').textContent = count;
        }
    </script>
</body>
</html>'''

@app.route('/')
def quantum_control():
    return render_template_string(HTML)

@app.route('/health')
def health_check():
    return {'status': 'ok', 'clients': len(PHOENIX_REGISTRY)}

@socketio.on('quantum_command')
def handle_quantum_command(data):
    """Handle commands from web interface"""
    phoenix_id = data.get('id')
    command = data.get('c')
    
    # Send command to all connected clients
    for pid, sid in PHOENIX_REGISTRY.items():
        socketio.emit('quantum_command', {'c': command}, room=sid)
    
    print(f"📤 Command broadcast: {command}")

@socketio.on('connect')
def handle_connect():
    print(f"🔗 Client connected: {request.sid}")

@socketio.on('disconnect')  
def handle_disconnect():
    for pid, sid in list(PHOENIX_REGISTRY.items()):
        if sid == request.sid: 
            del PHOENIX_REGISTRY[pid]
            print(f"🔌 Client disconnected: {pid}")

@socketio.on('phoenix_quantum')
def handle_phoenix_quantum(data):
    """Register client connection"""
    phoenix_id = data.get('id', request.sid)
    PHOENIX_REGISTRY[phoenix_id] = request.sid
    
    print(f"🔥 Client registered: {phoenix_id}")
    # Broadcast to all web clients
    socketio.emit('phoenix_quantum', {'id': phoenix_id})

@socketio.on('quantum_response')
def handle_quantum_response(data):
    """Handle responses from clients"""
    print(f"📱 Response from {data.get('id')}: {data.get('result')}")
    # Broadcast response to all web clients
    socketio.emit('quantum_response', data)

# Railway requires this
application = app

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print("🚀 Quantum Phoenix Server Started")
    print(f"📍 Port: {port}")
    socketio.run(application, host='0.0.0.0', port=port, debug=False)