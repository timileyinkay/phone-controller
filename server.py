#!/usr/bin/env python3
import asyncio
import websockets
import json
import os
from datetime import datetime
from typing import Dict, List
from aiohttp import web

# Railway Configuration - Use different ports for HTTP and WebSocket
HTTP_PORT = int(os.environ.get("PORT", 8080))  # Railway provides this
WS_PORT = 8081  # Different port for WebSocket
HOST = "0.0.0.0"

class PhoneManager:
    def __init__(self):
        self.connected_phones: Dict = {}
    
    async def register_phone(self, phone_id: str, websocket):
        self.connected_phones[phone_id] = {
            'websocket': websocket,
            'connected_at': datetime.now(),
            'last_seen': datetime.now()
        }
        print(f"✅ {phone_id} - CONNECTED (Total: {len(self.connected_phones)})")
    
    async def handle_phone_message(self, message: str, websocket):
        try:
            data = json.loads(message)
            if data.get('type') == 'register':
                await self.register_phone(data['device_id'], websocket)
        except:
            pass
    
    async def send_command(self, phone_id: str, command: str) -> bool:
        if phone_id in self.connected_phones:
            try:
                await self.connected_phones[phone_id]['websocket'].send(
                    json.dumps({"action": "shell", "command": command})
                )
                self.connected_phones[phone_id]['last_seen'] = datetime.now()
                print(f"📤 Sent to {phone_id}: {command}")
                return True
            except:
                del self.connected_phones[phone_id]
        return False

# Global phone manager instance
phone_manager = PhoneManager()

async def handle_phone_connection(websocket, path):
    try:
        async for message in websocket:
            await phone_manager.handle_phone_message(message, websocket)
    except:
        pass

# ==================== HTTP SERVER (Web Control Panel) ====================
async def serve_control_panel(request):
    """Serve the HTML control panel"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Phone Controller</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
            .phone-list { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
            .phone-item { padding: 10px; margin: 5px 0; background: white; border-radius: 5px; border-left: 4px solid #28a745; }
            .dialer { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 20px 0; }
            .dial-btn { padding: 20px; font-size: 18px; border: none; border-radius: 5px; background: #007bff; color: white; cursor: pointer; }
            .dial-btn:hover { background: #0056b3; }
            .command-section { margin: 20px 0; }
            .cmd-btn { padding: 10px 15px; margin: 5px; border: none; border-radius: 5px; background: #28a745; color: white; cursor: pointer; }
            .sms-section textarea { width: 100%; height: 100px; margin: 10px 0; }
            .status { padding: 10px; background: #d4edda; border-radius: 5px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📱 Phone Controller</h1>
            <div class="status" id="status">Connected to Server</div>
            
            <div class="phone-list">
                <h3>📱 Connected Phones</h3>
                <div id="phoneList">No phones connected</div>
            </div>

            <div class="command-section">
                <h3>🎯 Select Phone & Command</h3>
                <select id="phoneSelect">
                    <option value="">-- Select Phone --</option>
                </select>
                
                <h4>📞 Dialer</h4>
                <div class="dialer">
                    <button class="dial-btn" onclick="addNumber('1')">1</button>
                    <button class="dial-btn" onclick="addNumber('2')">2</button>
                    <button class="dial-btn" onclick="addNumber('3')">3</button>
                    <button class="dial-btn" onclick="addNumber('4')">4</button>
                    <button class="dial-btn" onclick="addNumber('5')">5</button>
                    <button class="dial-btn" onclick="addNumber('6')">6</button>
                    <button class="dial-btn" onclick="addNumber('7')">7</button>
                    <button class="dial-btn" onclick="addNumber('8')">8</button>
                    <button class="dial-btn" onclick="addNumber('9')">9</button>
                    <button class="dial-btn" onclick="addNumber('*')">*</button>
                    <button class="dial-btn" onclick="addNumber('0')">0</button>
                    <button class="dial-btn" onclick="addNumber('#')">#</button>
                </div>
                <input type="text" id="phoneNumber" placeholder="Phone number" style="width: 100%; padding: 10px; font-size: 16px;">
                <button class="cmd-btn" onclick="dialNumber()">📞 Dial</button>
                <button class="cmd-btn" onclick="clearNumber()">Clear</button>
            </div>

            <div class="command-section">
                <h4>⚡ Quick Commands</h4>
                <button class="cmd-btn" onclick="sendCommand('termux-vibrate -d 1000')">Vibrate</button>
                <button class="cmd-btn" onclick="sendCommand('termux-toast "Hello from Control Panel"')">Show Toast</button>
                <button class="cmd-btn" onclick="sendCommand('termux-battery-status')">Battery Status</button>
                <button class="cmd-btn" onclick="sendCommand('termux-location')">Get Location</button>
                <button class="cmd-btn" onclick="sendCommand('termux-notification --title "Alert" --content "Message from Control Panel"')">Send Notification</button>
            </div>

            <div class="sms-section">
                <h4>💬 Send SMS</h4>
                <input type="text" id="smsNumber" placeholder="Recipient number" style="width: 100%; padding: 10px; margin: 5px 0;">
                <textarea id="smsMessage" placeholder="Message content"></textarea>
                <button class="cmd-btn" onclick="sendSMS()">Send SMS</button>
            </div>

            <div class="command-section">
                <h4>🔧 Custom Command</h4>
                <input type="text" id="customCommand" placeholder="Enter Termux command" style="width: 70%; padding: 10px;">
                <button class="cmd-btn" onclick="sendCustomCommand()">Execute</button>
            </div>
        </div>

        <script>
            let phones = [];
            
            // Update phone list
            async function updatePhones() {
                try {
                    const response = await fetch('/api/phones');
                    phones = await response.json();
                    
                    const phoneList = document.getElementById('phoneList');
                    const phoneSelect = document.getElementById('phoneSelect');
                    
                    phoneList.innerHTML = phones.length ? phones.map(phone => 
                        `<div class="phone-item">${phone}</div>`
                    ).join('') : 'No phones connected';
                    
                    phoneSelect.innerHTML = '<option value="">-- Select Phone --</option>' + 
                        phones.map(phone => `<option value="${phone}">${phone}</option>`).join('');
                } catch (error) {
                    console.error('Error updating phones:', error);
                }
            }
            
            // Phone number functions
            function addNumber(num) {
                document.getElementById('phoneNumber').value += num;
            }
            
            function clearNumber() {
                document.getElementById('phoneNumber').value = '';
            }
            
            // Send commands
            async function sendCommand(command) {
                const phone = document.getElementById('phoneSelect').value;
                if (!phone) return alert('Please select a phone first!');
                
                try {
                    await fetch('/api/command', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({phone, command})
                    });
                    alert('Command sent successfully!');
                } catch (error) {
                    alert('Error sending command: ' + error);
                }
            }
            
            async function dialNumber() {
                const phone = document.getElementById('phoneSelect').value;
                const number = document.getElementById('phoneNumber').value;
                if (!phone || !number) return alert('Please select phone and enter number!');
                
                await sendCommand(`termux-telephony-call "${number}"`);
            }
            
            async function sendSMS() {
                const phone = document.getElementById('phoneSelect').value;
                const number = document.getElementById('smsNumber').value;
                const message = document.getElementById('smsMessage').value;
                if (!phone || !number || !message) return alert('Please fill all SMS fields!');
                
                await sendCommand(`termux-sms-send -n "${number}" "${message}"`);
            }
            
            async function sendCustomCommand() {
                const phone = document.getElementById('phoneSelect').value;
                const command = document.getElementById('customCommand').value;
                if (!phone || !command) return alert('Please select phone and enter command!');
                
                await sendCommand(command);
            }
            
            // Auto-update every 3 seconds
            setInterval(updatePhones, 3000);
            updatePhones();
        </script>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

async def handle_api_phones(request):
    """API endpoint to get connected phones"""
    return web.json_response(list(phone_manager.connected_phones.keys()))

async def handle_api_command(request):
    """API endpoint to send commands to phones"""
    try:
        data = await request.json()
        phone_id = data.get('phone')
        command = data.get('command')
        
        if phone_id and command:
            success = await phone_manager.send_command(phone_id, command)
            return web.json_response({'status': 'success' if success else 'phone not found'})
        return web.json_response({'status': 'invalid data'}, status=400)
    except Exception as e:
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)

async def start_http_server():
    """Start HTTP server for control panel"""
    app = web.Application()
    app.router.add_get('/', serve_control_panel)
    app.router.add_get('/api/phones', handle_api_phones)
    app.router.add_post('/api/command', handle_api_command)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, HTTP_PORT)
    await site.start()
    print(f"🌐 Web control panel: http://{HOST}:{HTTP_PORT}")
    return runner

async def start_websocket_server():
    """Start WebSocket server for phones"""
    # Railway only exposes one port, so we use the same port for both
    ws_server = await websockets.serve(handle_phone_connection, HOST, HTTP_PORT)
    print(f"📡 WebSocket server running on port {HTTP_PORT}")
    return ws_server

async def main():
    print("🚀 Starting Phone Controller Server...")
    print(f"📍 Web Panel: http://thriving-nature.up.railway.app")
    print(f"📡 WebSocket: ws://thriving-nature.up.railway.app")
    
    # Start HTTP server
    http_runner = await start_http_server()
    
    # Start WebSocket server
    await start_websocket_server()
    
    print("✅ Server started successfully!")
    
    # Keep server running
    while True:
        await asyncio.sleep(10)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"💥 Server error: {e}")
