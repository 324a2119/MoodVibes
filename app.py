import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import tempfile
import os
from dotenv import load_dotenv
from transformers import pipeline
import librosa
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
import io
from scipy.io.wavfile import write as write_wav

# .envファイルを読み込む
load_dotenv()

# 感情分析モデルをロード（キャッシュを利用して高速化）
@st.cache_resource
def load_emotion_model():
    # 初回実行時、モデル（約350MB）がダウンロードされます
    return pipeline("audio-classification", model="superb/hubert-base-superb-er")

# ==========================
# Spotify認証
# ==========================
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

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

# セッション状態で音声ファイルのパスと処理状態を管理
if "audio_path" not in st.session_state:
    st.session_state.audio_path = None
if "processing_done" not in st.session_state:
    st.session_state.processing_done = True

input_mode = st.radio("音声入力方法を選んでください：", ["🎙️ マイクで話す", "📁 音声ファイルをアップロード"])

audio_path = None

# ==========================
# 🎤 マイク録音モード (streamlit-webrtc)
# ==========================
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.audio_frames = []

    def recv(self, frame):
        # 音声フレームを蓄積
        self.audio_frames.append(frame.to_ndarray())
        return frame

if input_mode == "🎙️ マイクで話す":
    st.info("🎤 開始ボタンを押して感情を話してください。話し終わったら停止ボタンを押してください。")
    
    webrtc_ctx = webrtc_streamer(
        key="speech-to-text",
        mode=WebRtcMode.SENDONLY,
        audio_processor_factory=AudioProcessor,
        media_stream_constraints={"video": False, "audio": True},
    )

    if not webrtc_ctx.state.playing and webrtc_ctx.audio_processor and not st.session_state.processing_done:
        st.info("録音を処理しています...")
        
        # 蓄積した音声フレームを結合
        audio_frames = webrtc_ctx.audio_processor.audio_frames
        if audio_frames:
            sound_chunk = np.concatenate(audio_frames, axis=0)
            sample_rate = 48000 # webrtcのデフォルトサンプルレート

            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                # numpy配列をwav形式のバイトデータに変換
                buffer = io.BytesIO()
                write_wav(buffer, rate=sample_rate, data=sound_chunk)
                tmp_file.write(buffer.read())
                audio_path = tmp_file.name
                st.session_state.audio_path = audio_path
        
        st.session_state.processing_done = True
        st.rerun() # ページを再実行して結果を表示

    if webrtc_ctx.state.playing:
        # 録音開始時に状態をリセット
        st.session_state.processing_done = False
        st.session_state.audio_path = None

# ==========================
# 📁 アップロード音声モード
# ==========================
elif input_mode == "📁 音声ファイルをアップロード":
    st.session_state.processing_done = True # モード切替時にリセット
    st.session_state.audio_path = None

    uploaded_file = st.file_uploader("音声ファイルをアップロードしてください", type=["wav", "mp3", "m4a"])
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            audio_path = tmp_file.name
            st.session_state.audio_path = audio_path
        st.rerun()

# ==========================
# 感情分析 ＆ Spotify検索
# ==========================
if st.session_state.audio_path:
    st.success("✅ 音声ファイルを受け付けました。分析を開始します。")
    current_audio_path = st.session_state.audio_path
    
    try:
        # モデルが期待する16kHzにリサンプリングして読み込み
        speech, sr = librosa.load(current_audio_path, sr=16000)

        # 感情を分析
        emotion_classifier = load_emotion_model()
        results = emotion_classifier(speech)
        top_emotion = results[0]['label']
        
        st.success(f"感情分析の結果: **{top_emotion}**")

        # 英語ラベルを日本語キーワードにマッピング
        emotion_map = {
            "happy": "楽しい",
            "sad": "悲しい",
            "angry": "激しい",
            "neutral": "落ち着く",
        }
        keyword = emotion_map.get(top_emotion)

        if not keyword:
            st.info(f"感情「{top_emotion}」に対応する検索キーワードが見つかりませんでした。")
        else:
            st.write(f"キーワード「{keyword}」でプレイリストを検索します。")
            
            st.subheader(f"🎧 「{keyword}」に関連するプレイリスト")
            search_results = sp.search(q=f"{keyword} プレイリスト", type="playlist", limit=5, market="JP")
            playlists = search_results["playlists"]["items"]

            if not playlists:
                st.write("見つかりませんでした")
            else:
                for playlist in playlists:
                    if not playlist:
                        continue
                    playlist_name = playlist["name"]
                    playlist_owner = playlist["owner"].get("display_name", "不明")
                    playlist_url = playlist["external_urls"]["spotify"]
                    playlist_image = playlist["images"][0]["url"] if playlist["images"] else None
                    playlist_id = playlist["id"]

                    with st.expander(f"🎵 {playlist_name}  ({playlist_owner})"):
                        if playlist_image:
                            st.image(playlist_image, width=300)
                        st.markdown(f"[Spotifyで開く]({playlist_url})")
                        tracks = sp.playlist_tracks(playlist_id)
                        st.write("🎶 曲一覧：")
                        for t in tracks["items"]:
                            track = t["track"]
                            if track:
                                name = track["name"]
                                artist = track["artists"][0]["name"]
                                st.write(f"- {name} / {artist}")
    except Exception as e:
        st.error(f"分析中にエラーが発生しました: {e}")
    finally:
        # 一時ファイルを削除し、セッションステートをリセット
        if os.path.exists(current_audio_path):
            os.remove(current_audio_path)
        st.session_state.audio_path = None
        st.session_state.processing_done = True