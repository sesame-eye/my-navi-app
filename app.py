import streamlit as st
import pandas as pd
import math
from streamlit_geolocation import streamlit_geolocation

st.set_page_config(page_title="🚗 観光音声ナビ", layout="centered")
st.title("🚗 観光音声ナビ (Streamlit版)")

# 1. スプレッドシートからデータを取得（CSVとして一発読み込み）
# 「YOUR_SHEET_ID」の部分をご自身のスプレッドシートIDに書き換えてください
SHEET_ID = "1AVh_BtwGJJwXbQaiSnNaAlXh7SGhBBBCTMo6W3uPHN4"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60) # 60秒間データをキャッシュ（毎回読み込まないようにして高速化）
def load_data():
    return pd.read_csv(SHEET_URL)

try:
    df = load_data()
    st.success("スプレッドシートの読み込み完了！")
except Exception as e:
    st.error(f"読み込み失敗: {e}")
    st.stop()

# 2. スマホのGPS位置情報を取得するパーツ
st.subheader("📡 GPS位置情報")
location = streamlit_geolocation()

current_lat = location.get("latitude")
current_lng = location.get("longitude")
current_heading = location.get("heading") # 進行方向（0〜359度。停止時はNoneまたはnull）

# 3. 方位判定ロジック
def is_correct_heading(current, target):
    if current is None or math.isnan(current):
        return False # 停止中（方位不明）は鳴らさない
    
    diff = abs(current - float(target))
    if diff > 180:
        diff = 360 - diff
    return diff <= 60

# 4. 2点間の距離計算（ヒュベニの公式風・簡易版）
def calculate_distance(lat1, lng1, lat2, lng2):
    R = 6371000 # 地球の半径（メートル）
    rad_lat1, rad_lng1, rad_lat2, rad_lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlat = rad_lat2 - rad_lat1
    dlng = rad_lng2 - rad_lng1
    a = math.sin(dlat/2)**2 + math.cos(rad_lat1) * math.cos(rad_lat2) * math.sin(dlng/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

# 5. 現在地が取得できたら判定スタート
if current_lat and current_lng:
    st.write(f"現在地: {current_lat:.4f}, {current_lng:.4f}")
    st.write(f"現在の向き: {f'{int(current_heading)}度' if current_heading else '停止中/方位取得中'}")
    
    # まだ鳴らしていない場所を記録するセッション状態（Streamlitのメモリ）
    if "played_spots" not in st.session_state:
        st.session_state.played_spots = set()

    for index, row in df.iterrows():
        dist = calculate_distance(current_lat, current_lng, row['lat'], row['lng'])
        
        # 250m以内 かつ まだ鳴っていない場合
        if dist < 250 and row['name'] not in st.session_state.played_spots:
            # 方位指定がない、または方位が一致している場合
            if pd.isna(row['direction']) or is_correct_heading(current_heading, row['direction']):
                
                # ★Streamlit上で音声を鳴らすための裏技（HTML/JavaScriptを埋め込む）
                tts_script = f"""
                <script>
                    var uttr = new SpeechSynthesisUtterance("{row['message']}");
                    uttr.lang = "ja-JP";
                    window.speechSynthesis.speak(uttr);
                </script>
                """
                st.components.v1.html(tts_script, height=0)
                
                # 鳴らしたリストに追加
                st.session_state.played_spots.add(row['name'])
                st.info(f"🔊 案内再生中: {row['name']}")
else:
    st.info("上のGPSパーツをタップして、位置情報の利用を許可してください。")
