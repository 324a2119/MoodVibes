import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import speech_recognition as sr
import tempfile

# ==========================
# Spotify認証
# ==========================
CLIENT_ID = "ff259b9ec7f3420381662c278fed342f"
CLIENT_SECRET = "a35403dc7fb64531ba6a98c5794fcef8"

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
))

# ==========================
# Streamlit UI
# ==========================
st.title("🎵 音声感情でSpotifyプレイリスト検索アプリ")
st.write("音声をアップロードすると、感情に関連するプレイリストを検索します。")

uploaded_file = st.file_uploader(
    "音声ファイルをアップロードしてください (wav, mp3 など)",
    type=["wav", "mp3"]
)

# 検索ボタン
if uploaded_file is not None:
    if st.button("🔍 感情からプレイリストを検索"):
        # 一時ファイルとして保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(uploaded_file.read())
            audio_path = tmp_file.name

        # ==========================
        # 音声 → テキスト変換（ffmpegなし）
        # ==========================
        r = sr.Recognizer()
        try:
            with sr.AudioFile(audio_path) as source:
                audio = r.record(source)
            text = r.recognize_google(audio, language="ja-JP")
            st.write("🗣️ 文字起こし結果:", text)
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
            st.write("🔍 抽出された感情単語:", ", ".join(detected))

        # ==========================
        # Spotifyプレイリスト検索 & 曲一覧表示
        # ==========================
        for keyword in detected:
            st.subheader(f"🎧 「{keyword}」に関連するプレイリスト")

            results = sp.search(q=keyword, type="playlist", limit=5)
            playlists = results['playlists']['items']

            if not playlists:
                st.write("プレイリストが見つかりませんでした。")
                continue

            # プレイリストごとにドロップダウンで詳細表示
            for playlist in playlists:
                playlist_name = playlist['name']
                playlist_url = playlist['external_urls']['spotify']
                playlist_owner = playlist['owner'].get('display_name', '不明')
                playlist_id = playlist['id']
                playlist_image = playlist['images'][0]['url'] if playlist['images'] else None

                with st.expander(f"🎵 {playlist_name}（作成者：{playlist_owner}）"):
                    if playlist_image:
                        st.image(playlist_image, width=250)
                    st.markdown(f"[Spotifyで開く ▶️]({playlist_url})")

                    try:
                        tracks = sp.playlist_tracks(playlist_id)
                        st.write("🎶 曲一覧：")
                        for t in tracks['items']:
                            track = t['track']
                            track_name = track['name']
                            artist_name = track['artists'][0]['name']
                            st.write(f"- {track_name} / {artist_name}")
                    except Exception as e:
                        st.warning(f"曲の取得中にエラーが発生しました: {e}")
