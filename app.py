import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="🚗 観光音声ナビ", layout="centered")
st.title("🚗 観光音声ナビ (リアルタイム同期版)")

# 1. スプレッドシートからデータを取得
# ★ご自身のシートIDに書き換えてください
SHEET_ID = "1AVh_BtwGJJwXbQaiSnNaAlXh7SGhBBBCTMo6W3uPHN4" 
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=10)
def load_data():
    return pd.read_csv(SHEET_URL)

try:
    df = load_data()
    st.success("スプレッドシート同期中...")
except Exception as e:
    st.error(f"読み込み失敗: {e}")
    st.stop()

# 2. URLのパラメータ（裏でJavaScriptから送られてくる座標）を受け取る
query_params = st.query_params

# JavaScriptから届いた位置情報をPythonの変数に代入
current_lat = float(query_params.get("lat")) if query_params.get("lat") else None
current_lng = float(query_params.get("lng")) if query_params.get("lng") else None
current_heading = float(query_params.get("heading")) if query_params.get("heading") else None

# 3. 方位判定ロジック
def is_correct_heading(current, target):
    if current is None or math.isnan(current):
        return False # 停止中は鳴らさない（じゅんさんの黄金ルール）
    
    diff = abs(current - float(target))
    if diff > 180:
        diff = 360 - diff
    return diff <= 60

# 4. 距離計算（ヒュベニの公式）
def calculate_distance(lat1, lng1, lat2, lng2):
    R = 6371000
    rad_lat1, rad_lng1, rad_lat2, rad_lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlat = rad_lat2 - rad_lat1
    dlng = rad_lng2 - rad_lng1
    a = math.sin(dlat/2)**2 + math.cos(rad_lat1) * math.cos(rad_lat2) * math.sin(dlng/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

# 5. 現在地の表示と判定
if current_lat and current_lng:
    st.write(f"🌐 リアルタイム現在地: {current_lat:.5f}, {current_lng:.5f}")
    st.write(f"🧭 現在の向き: {f'{int(current_heading)}度' if current_heading and not math.isnan(current_heading) else '停止中/方位取得中'}")
    
    if "played_spots" not in st.session_state:
        st.session_state.played_spots = set()

    for index, row in df.iterrows():
        dist = calculate_distance(current_lat, current_lng, row['lat'], row['lng'])
        
        # 250m以内 かつ 未再生
        if dist < 250 and row['name'] not in st.session_state.played_spots:
            if pd.isna(row['direction']) or is_correct_heading(current_heading, row['direction']):
                
                # 音声再生
                tts_script = f"""
                <script>
                    var uttr = new SpeechSynthesisUtterance("{row['message']}");
                    uttr.lang = "ja-JP";
                    window.speechSynthesis.speak(uttr);
                </script>
                """
                st.components.v1.html(tts_script, height=0)
                st.session_state.played_spots.add(row['name'])
                st.balloons()
else:
    st.warning("📡 GPS信号を待機中、または位置情報の取得がオフです。")

# 6. ★【心臓部】ブラウザのGPSセンサーを直接叩き起こして、Streamlitに位置情報を送りつけるJavaScript
gps_bridge_html = """
<script>
    // 位置情報が更新されるたびに発火する関数
    function updateLocation(position) {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        const heading = position.coords.heading !== null ? position.coords.heading : "";
        
        // StreamlitのURLに座標をセットして、Python側を強制的に最新情報でリロードさせる
        const newUrl = window.parent.location.protocol + "//" + window.parent.location.host + window.parent.location.pathname + `?lat=${lat}&lng=${lng}&heading=${heading}`;
        window.parent.history.replaceState(null, null, newUrl);
        
        // 親ウィンドウ（Streamlit）をリロードしてPython側に通知
        window.parent.location.reload();
    }

    function handleError(error) {
        console.error("GPSエラー:", error);
    }

    // ブラウザのGPS常時監視スタート（高精度モード）
    if (navigator.geolocation) {
        navigator.geolocation.watchPosition(updateLocation, handleError, {
            enableHighAccuracy: true,
            maximumAge: 0,
            timeout: 5000
        });
    } else {
        alert("お使いのブラウザはGPSに対応していません。");
    }
</script>
"""
# 裏でJavaScriptの監視員を常駐させる
st.components.v1.html(gps_bridge_html, height=0)
