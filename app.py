import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="🚗 観光音声ナビ", layout="centered")
st.title("🚗 観光音声ナビ (ノーフラッシュ決定版)")

# 1. スプレッドシートからデータを取得
# ★ご自身のシートIDに書き換えてください
SHEET_ID = "1AVh_BtwGJJwXbQaiSnNaAlXh7SGhBBBCTMo6W3uPHN4" 
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    return pd.read_csv(SHEET_URL)

try:
    df = load_data()
    # JavaScriptに渡しやすいようにデータを整える
    spots_list = []
    for _, row in df.iterrows():
        spots_list.append({
            "name": str(row['name']),
            "lat": float(row['lat']),
            "lng": float(row['lng']),
            "direction": None if pd.isna(row['direction']) else float(row['direction']),
            "message": str(row['message'])
        })
    # JSON形式の文字列に変換
    spots_json = json.dumps(spots_list, ensure_ascii=False)
except Exception as e:
    st.error(f"スプレッドシート読み込み失敗: {e}")
    st.stop()

st.success("データの読み込みに成功しました。下のボタンを押してスタートしてください。")

# 2. HTML/JavaScriptの埋め込み（方位5秒キープ機能付き）
navi_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        .container {{
            font-family: sans-serif;
            text-align: center;
            padding: 20px;
            background: #1e1e1e;
            color: #ffffff;
            border-radius: 15px;
        }}
        button {{
            font-size: 20px;
            padding: 20px 40px;
            border-radius: 10px;
            cursor: pointer;
            border: none;
            background-color: #007bff;
            color: white;
            font-weight: bold;
        }}
        #display {{
            margin-top: 20px;
            font-size: 18px;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <button id="startBtn">🧭 ナビゲーションを開始</button>
        <div id="display">ボタンを押すとGPS監視が始まります</div>
    </div>

    <script>
        // Pythonから渡されたスプレッドシートのデータ
        const spots = {spots_json};
        const playedSpots = new Set();
        
        // ★方位キープ用のメモリ変数
        let lastValidHeading = null;     // 最後に認識した有効な方位
        let lastValidHeadingTime = 0;    // それを認識した時刻（タイムスタンプ）
        
        const startBtn = document.getElementById('startBtn');
        const display = document.getElementById('display');

        startBtn.onclick = () => {{
            startBtn.style.backgroundColor = "#28a745";
            startBtn.innerText = "🚗 ガイド実行中...";
            display.innerText = "GPS信号をスキャン中...";
            
            speak("ガイドシステムを起動しました。");
            
            // GPS常時監視スタート（高精度モード）
            if (navigator.geolocation) {{
                navigator.geolocation.watchPosition(checkLocation, (err) => {{
                    display.innerText = "GPSエラー: " + err.message;
                }}, {{
                    enableHighAccuracy: true,
                    maximumAge: 0,
                    timeout: 10000
                }});
            }} else {{
                alert("このブラウザはGPSに対応していません");
            }}
        }};

        function checkLocation(position) {{
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            let heading = position.coords.heading;
            const now = Date.now();

            // 【方位キープ判定】
            // ブラウザが正常に方位を掴んでいたら（走行中）
            if (heading !== null && !isNaN(heading)) {{
                lastValidHeading = heading;
                lastValidHeadingTime = now;
            }}
