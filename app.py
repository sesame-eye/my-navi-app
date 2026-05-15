import streamlit as st
import pandas as pd
import math
import time
from streamlit_geolocation import streamlit_geolocation

st.set_page_config(page_title="🚗 観光音声ナビ", layout="centered")
st.title("🚗 観光音声ナビ (リアルタイム追跡版)")

# 1. スプレッドシートからデータを取得
# ★ご自身のシートIDに書き換えてください
SHEET_ID = "1AVh_BtwGJJwXbQaiSnNaAlXh7SGhBBBCTMo6W3uPHN4" 
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=10) # キャッシュを10秒に短縮してリアルタイム性をアップ
def load_data():
    return pd.read_csv(SHEET_URL)

try:
    df = load_data()
    st.success("データベース同期中...")
except Exception as e:
    st.error(f"読み込み失敗: {e}")
    st.stop()

# 2. 自動更新（ループ）のためのスイッチ
st.subheader("📡 GPS追跡システム")
run_navigation = st.checkbox("ナビゲーションを開始する", value=True)

# 3. GPS位置情報を取得
location = streamlit_geolocation()

current_lat = location.get("latitude")
current_lng = location.get("longitude")
current_heading = location.get("heading")

# 4. 方位判定ロジック
def is_correct_heading(current, target):
    if current is None or math.isnan(current):
        return False # 停止中は鳴らさない（じゅんさんの黄金ルール）
    
    diff = abs(current - float(target))
    if diff > 180:
        diff = 360 - diff
    return diff <= 60

# 5. 距離計算（ヒュベニの公式）
def calculate_distance(lat1, lng1, lat2, lng2):
    R = 6371000
    rad_lat1, rad_lng1, rad_lat2, rad_lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlat = rad_lat2 - rad_lat1
    dlng = rad_lng2 - rad_lng1
    a = math.sin(dlat/2)**2 + math.cos(rad_lat1) * math.cos(rad_lat2) * math.sin(dlng/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

# 6. 判定と音声再生
if current_lat and current_lng:
    st.write(f"🌐 現在地: {current_lat:.5f}, {current_lng:.5f}")
    st.write(f"🧭 現在の向き: {f'{int(current_heading)}度' if current_heading and not math.isnan(current_heading) else '停止中/方位取得中'}")
    
    if "played_spots" not in st.session_state:
        st.session_state.played_spots = set()

    for index, row in df.iterrows():
        dist = calculate_distance(current_lat, current_lng, row['lat'], row['lng'])
        
        # 250m以内 かつ 未再生
        if dist < 250 and row['name'] not in st.session_state.played_spots:
            if pd.isna(row['direction']) or is_correct_heading(current_heading, row['direction']):
                
                # 音声再生スクリプト
                tts_script = f"""
                <script>
                    var uttr = new SpeechSynthesisUtterance("{row['message']}");
                    uttr.lang = "ja-JP";
                    window.speechSynthesis.speak(uttr);
                </script>
                """
                st.components.v1.html(tts_script, height=0)
                st.session_state.played_spots.add(row['name'])
                st.balloons() # 鳴った瞬間に画面に風船を飛ばす演出！

    # ★ここが肝！「ナビ開始」にチェックが入っている間、3秒ごとに画面を自動再読み込みしてGPSを叩き起こす
    if run_navigation:
        time.sleep(3)
        st.rerun()

else:
    st.info("上のGPSパーツをタップして、位置情報を「常に許可」または「許可」にしてください。")
