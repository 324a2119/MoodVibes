import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import speech_recognition as sr
import tempfile
import os
from dotenv import load_dotenv
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase

# .envファイルを読み込む
load_dotenv()

# ==========================
# Spotify認証
# ==========================
# 環境変数から認証情報を取得
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

# 認証情報が設定されているか確認
if not CLIENT_ID or not CLIENT_SECRET:
    st.error("Spotifyの認証情報が設定されていません。環境変数（.envファイルなど）を確認してください。")
    st.stop()

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
))

# ==========================
# Streamlit UI
# ==========================
st.title("🎵 音声から感情を読み取ってSpotifyプレイリスト検索")
st.write("マイクで話すか、音声ファイルをアップロードして感情を検出します。")

# セッション状態で音声ファイルのパスと録音状態を管理
if "audio_path" not in st.session_state:
    st.session_state.audio_path = None
if "recording_completed" not in st.session_state:
    st.session_state.recording_completed = False

# ==========================
# 音声入力オプション
# ==========================
input_mode = st.radio("音声入力方法を選んでください：", ["🎙️ マイクで話す", "📁 音声ファイルをアップロード"])

# audio_path変数を初期化
audio_path = None

# ==========================
# マイク録音モード
# ==========================
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.audio_frames = b""

    def recv_audio(self, frame):
        # 音声データをバイト列として蓄積
        self.audio_frames += frame.to_ndarray().tobytes()
        return frame


if input_mode == "🎙️ マイクで話す":
    st.info("🎤 『楽しい』『悲しい』『落ち着く』などの感情を話してみてください。録音が終わったら停止ボタンを押してください。")

    webrtc_ctx = webrtc_streamer(
        key="speech-capture",
        mode=WebRtcMode.SENDRECV,
        audio_receiver_size=1024,
        media_stream_constraints={"audio": True, "video": False},
        async_processing=True,
        audio_processor_factory=AudioProcessor,
    )

    # 録音中の処理
    if webrtc_ctx and webrtc_ctx.state.playing:
        st.info("録音中です…停止ボタンを押すと処理が始まります。")
        # 録音開始時に過去の録音状態をリセット
        st.session_state.recording_completed = False
        st.session_state.audio_path = None

    # 録音停止後の処理
    if webrtc_ctx and not webrtc_ctx.state.playing and not st.session_state.recording_completed:
        if hasattr(webrtc_ctx, "audio_processor") and webrtc_ctx.audio_processor:
            audio_data = webrtc_ctx.audio_processor.audio_frames
            if audio_data:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
                    tmp_wav.write(audio_data)
                    st.session_state.audio_path = tmp_wav.name
                st.session_state.recording_completed = True
                # ページを再実行して「録音完了」メッセージを確実に表示
                st.rerun()

    # 録音完了メッセージの表示
    if st.session_state.recording_completed:
        st.success("🎙️ 録音完了！")
        audio_path = st.session_state.audio_path

# ==========================
# アップロードモード
# ==========================
elif input_mode == "📁 音声ファイルをアップロード":
    # 過去の録音状態をリセット
    st.session_state.recording_completed = False
    st.session_state.audio_path = None
    
    uploaded_file = st.file_uploader("音声ファイルをアップロードしてください (wav形式推奨)", type=["wav"])
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(uploaded_file.read())
            audio_path = tmp_file.name
            st.success("📁 ファイルを受け取りました")

# ==========================
# 音声認識処理
# ==========================
if audio_path:
    r = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio = r.record(source)
        text = r.recognize_google(audio, language="ja-JP")
        st.success("🗣️ 音声認識結果:")
        st.write(text)
    except Exception as e:
        st.error(f"音声認識に失敗しました: {e}")
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
                            track_name = track['name']
                            artist_name = track['artists'][0]['name']
                            st.write(f"- {track_name} / {artist_name}")

    os.remove(audio_path)
    # 処理完了後にセッション状態をリセット
    st.session_state.audio_path = None
    st.session_state.recording_completed = False
