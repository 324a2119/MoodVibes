import streamlit as st
import speech_recognition as sr
from pydub import AudioSegment
import io
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# =============================
# Spotify API 認証
# =============================
CLIENT_ID = "ff259b9ec7f3420381662c278fed342f"
CLIENT_SECRET = "a35403dc7fb64531ba6a98c5794fcef8"

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
))

# =============================
# Streamlit UI
# =============================
st.title("🎧 音声で感情を分析 → Spotifyでおすすめプレイリストを表示")

uploaded_file = st.file_uploader("音声ファイルをアップロードしてください", type=["wav", "mp3", "m4a", "flac"])

query = None  # 検索キーワード（感情ワード）を入れる変数

# =============================
# 音声認識処理
# =============================
if uploaded_file:
    st.audio(uploaded_file)

    try:
        # 音声を一時的にWAVに変換
        audio = AudioSegment.from_file(uploaded_file)
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_io.seek(0)

        # 音声認識
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_io) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="ja-JP")

        st.success("🎤 音声認識結果:")
        st.write(text)

        # 簡易的な感情ワード抽出（実際は自然言語処理などで改善可）
        if any(word in text for word in ["楽しい", "嬉しい", "ワクワク", "元気"]):
            query = "happy"
        elif any(word in text for word in ["悲しい", "寂しい", "泣きたい"]):
            query = "sad"
        elif any(word in text for word in ["落ち着く", "癒し", "リラックス"]):
            query = "chill"
        elif any(word in text for word in ["怒り", "ムカつく", "イライラ"]):
            query = "angry"
        else:
            query = "mood"

        st.info(f"🔍 検出された感情に基づく検索ワード: **{query}**")

    except Exception as e:
        st.error(f"音声認識に失敗しました: {e}")

# =============================
# Spotify検索結果を表示
# =============================
if query:
    results = sp.search(q=query, type='playlist', limit=5)

    st.subheader("🎵 Spotifyおすすめプレイリスト:")

    for playlist in results["playlists"]["items"]:
        with st.expander(f"{playlist['name']}  ({playlist['owner']['display_name']})"):
            st.image(playlist["images"][0]["url"], width=300)
            st.write(f"[Spotifyで開く]({playlist['external_urls']['spotify']})")

            # 曲一覧を取得
            tracks = sp.playlist_tracks(playlist["id"])
            for idx, item in enumerate(tracks["items"], start=1):
                track = item["track"]
                st.write(f"{idx}. {track['name']} — {track['artists'][0]['name']}")

