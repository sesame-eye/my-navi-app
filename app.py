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
    # JSONという形式の文字列に変換
    spots_json = json.dumps(spots_list, ensure_ascii=False)
except Exception as e:
    st.error(f"スプレッドシート読み込み失敗: {e}")
    st.stop()

st.success("データの読み込みに成功しました。下のボタンを押してスタートしてください。")

# 2. ★超滑らかに動くHTML/JavaScriptの塊を画面に埋め込む
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
        
        const startBtn = document.getElementById('startBtn');
        const display = document.getElementById('display');

        startBtn.onclick = () => {{
            startBtn.style.backgroundColor = "#28a745";
            startBtn.innerText = "🚗 ガイド実行中...";
            display.innerText = "GPS信号をスキャン中...";
            
            // 音声テスト
            speak("ガイドシステムを起動しました。");
            
            // GPS監視をスタート（リロードなしで滑らかに動くモード）
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
            const heading = position.coords.heading;

            // 画面の文字を書き換えるだけ（リロードしないからフラッシュしない！）
            let headingText = (heading !== null && !isNaN(heading)) ? Math.round(heading) + "度" : "停止中";
            display.innerHTML = `経度: ${{lat.toFixed(5)}}<br>緯度: ${{lng.toFixed(5)}}<br>方位: ${{headingText}}`;

            spots.forEach(spot => {{
                const dist = calculateDistance(lat, lng, spot.lat, spot.lng);
                
                // 250m以内 かつ 未再生
                if (dist < 250 && !playedSpots.has(spot.name)) {{
                    // 方位指定がない、または「停止中でない」かつ「方位が一致」
                    if (spot.direction === null || isCorrectHeading(heading, spot.direction)) {{
                        speak(spot.message);
                        playedSpots.add(spot.name);
                    }}
                }}
            }});
        }}

        // 停止中判定付きの方位ロジック（じゅんさん仕様）
        function isCorrectHeading(current, target) {{
            if (current === null || isNaN(current)) return false; 
            let diff = Math.abs(current - target);
            if (diff > 180) diff = 360 - diff;
            return diff <= 60;
        }}

        // 距離計算（ヒュベニの公式）
        function calculateDistance(lat1, lng1, lat2, lng2) {{
            const R = 6371000;
            const f1 = lat1 * Math.PI / 180;
            const f2 = lat2 * Math.PI / 180;
            const df = (lat2 - lat1) * Math.PI / 180;
            const dl = (lng2 - lng1) * Math.PI / 180;
            const a = Math.sin(df/2) * Math.sin(df/2) + Math.cos(f1) * Math.cos(f2) * Math.sin(dl/2) * Math.sin(dl/2);
            return R * (2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)));
        }}

        function speak(text) {{
            const uttr = new SpeechSynthesisUtterance(text);
            uttr.lang = "ja-JP";
            window.speechSynthesis.speak(uttr);
        }}
    </script>
</body>
</html>
"""

# HTMLをStreamlitの画面上に埋め込む（縦幅を広めに確保）
st.components.v1.html(navi_html, height=250)
