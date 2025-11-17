import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import tempfile
import os
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
from openai import OpenAI

# ==========================
# OpenAI Whisper
# ==========================
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def transcribe_with_whisper(audio_path):
    with open(audio_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-mini-tts",
            file=f
        )
    return transcript.text


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
st.title("🎵 音声から感情を読み取ってSpotifyプレイリスト検索")
st.write("マイクで話すか、音声ファイルをアップロードして感情を検出します。")

input_mode = st.radio("音声入力方法を選んでください：", ["🎙️ マイクで話す", "📁 音声ファイルをアップロード"])

audio_path = None


# ==========================
# マイク録音モード（修正版）
# ==========================
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.audio_frames = b""

    def recv_audio(self, frame):
        self.audio_frames += frame.to_ndarray().tobytes()
        return frame


if input_mode == "🎙️ マイクで話す":
    st.info("🎤 『楽しい』『悲しい』『落ち着く』など話してください。")

    webrtc_ctx = webrtc_streamer(
        key="speech-capture",
        mode=WebRtcMode.SENDRECV,
        audio_receiver_size=1024,
        media_stream_constraints={"audio": True, "video": False},
        async_processing=True,
        audio_processor_factory=AudioProcessor,
    )

    if webrtc_ctx and webrtc_ctx.state.playing:
        st.info("録音中…停止ボタンを押してください。")

    # STOPされたタイミングで音声を保存
    if webrtc_ctx and not webrtc_ctx.state.playing:
        if hasattr(webrtc_ctx, "audio_processor") and webrtc_ctx.audio_processor:
            audio_data = webrtc_ctx.audio_processor.audio_frames
            if audio_data:
                # WAVではなくMP3（WhisperはMP3対応）
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_mp3:
                    tmp_mp3.write(audio_data)
                    audio_path = tmp_mp3.name
                    st.success("🎙️ 録音完了！Whisperで解析します…")


# ==========================
# アップロードモード（mp3対応へ修正）
# ==========================
elif input_mode == "📁 音声ファイルをアップロード":
    uploaded_file = st.file_uploader("音声ファイルをアップロードしてください", type=["wav", "mp3", "m4a"])
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_file.write(uploaded_file.read())
            audio_path = tmp_file.name
            st.success("📁 ファイルを受け取りました")


# ==========================
# Whisperで音声認識
# ==========================
if audio_path:
    try:
        text = transcribe_with_whisper(audio_path)
        st.success("📝 Whisper認識結果:")
        st.write(text)
    except Exception as e:
        st.error(f"Whisperでの音声認識に失敗しました: {e}")
        st.stop()

    # ==========================
    # 感情単語抽出
    # ==========================
    emotion_words = ["楽しい", "悲しい", "ワクワク", "落ち着く", "元気", "切ない"]
    detected = [w for w in emotion_words if w in text]

    if not detected:
        st.info("感情を表す単語が見つかりませんでした。")
    else:
        st.write("抽出された感情単語:", ", ".join(detected))

        # ==========================
        # Spotify検索（邦楽優先）
        # ==========================
        for keyword in detected:
            st.subheader(f"🎧 「{keyword}」に関連するプレイリスト")

            results = sp.search(q=f"{keyword} プレイリスト", type="playlist", limit=5, market="JP")
            playlists = results['playlists']['items']

            if not playlists:
                st.write("見つかりませんでした")
                continue

            for playlist in playlists:
                playlist_name = playlist['name']
                playlist_owner = playlist['owner'].get('display_name', '不明')
                playlist_url = playlist['external_urls']['spotify']
                playlist_image = playlist['images'][0]['url'] if playlist['images'] else None
                playlist_id = playlist['id']

                with st.expander(f"🎵 {playlist_name}  ({playlist_owner})"):
                    if playlist_image:
                        st.image(playlist_image, width=300)
                    st.markdown(f"[Spotifyで開く]({playlist_url})")

                    tracks = sp.playlist_tracks(playlist_id)
                    st.write("🎶 曲一覧：")
                    for t in tracks['items']:
                        track = t['track']
                        if track:
                            st.write(f"- {track['name']} / {track['artists'][0]['name']}")

    os.remove(audio_path)
