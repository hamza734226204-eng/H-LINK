import os
from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO

# 1. تعريف المسارات المطلقة (حل مشكلة عدم ظهور الصفحات)
base_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))

app.config['SECRET_KEY'] = 'cairopy_sec_2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# 2. ربط جميع الصفحات (التي تظهر في صورك السابقة)
@app.route('/')
def index():
    return render_template('index.html') # صفحة الربط الأساسية

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html') # لوحة التحكم

@app.route('/image')
def image_page():
    return render_template('image.html') # صفحة الصورة

@app.route('/qr')
def qr_page():
    return render_template('qr.html') # صفحة الـ QR

# 3. تشغيل السيرفر بما يتوافق مع Render
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
