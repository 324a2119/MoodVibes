import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import speech_recognition as sr
import tempfile

# ==========================
# Spotify認証
# ==========================
CLIENT_ID = st.secrets["ff259b9ec7f3420381662c278fed342f"]
CLIENT_SECRET = st.secrets["a35403dc7fb64531ba6a98c5794fcef8"]

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
))

# ==========================
# Streamlit UI
# ==========================
st.title("🎵 音声感情でSpotifyプレイリスト検索アプリ")
st.write("音声をアップロードすると、感情に関連するプレイリストを検索します。")

uploaded_file = st.file_uploader("音声ファイルをアップロードしてください (wav, mp3 など)", type=["wav","mp3"])

if uploaded_file is not None:
    # 一時ファイルとして保存
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.read())
        audio_path = tmp_file.name

    # ==========================
    # 音声 → テキスト
    # ==========================
    r = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio = r.record(source)
        text = r.recognize_google(audio, language="ja-JP")
        st.write("文字起こし結果:", text)
    except Exception as e:
        st.error("音声認識に失敗しました: " + str(e))
        st.stop()

    # ==========================
    # 感情単語抽出
    # ==========================
    emotion_words = ["楽しい", "悲しい", "ワクワク", "落ち着く", "元気", "切ない"]
    detected = [w for w in emotion_words if w in text]

    if not detected:
        st.info("感情に合う単語が見つかりませんでした。")
        st.stop()
    else:
        st.write("抽出された感情単語:", ", ".join(detected))

    # ==========================
    # Spotify検索
    # ==========================
    for keyword in detected:
        st.subheader(f"「{keyword}」に関連するプレイリスト")
        results = sp.search(q=keyword, type="playlist", limit=5)
        playlists = results['playlists']['items']
        if not playlists:
            st.write("見つかりませんでした")
        for playlist in playlists:
            st.write(f"- {playlist['name']} ({playlist['owner'].get('display_name','不明')})")
            st.markdown(f"[Spotifyで開く]({playlist['external_urls']['spotify']})")
