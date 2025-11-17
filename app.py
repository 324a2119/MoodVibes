import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import speech_recognition as sr
import tempfile
import os
import json

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
text = ""

# ==========================
# 🎤 Web Speech API（無料）でマイク入力
# ==========================
if input_mode == "🎙️ マイクで話す":
    st.info("🎤 開始ボタンを押して感情を話してください（『楽しい』『悲しい』『落ち着く』など）")

    # 結果受け取り用 session_state
    if "speech_text" not in st.session_state:
        st.session_state["speech_text"] = ""

    # 音声認識UI＋JavaScript
    st.components.v1.html(
        """
        <div>
            <button id="start-btn">🎙️ 認識開始</button>
            <button id="stop-btn">⏹ 停止</button>
            <p id="result">ここに認識結果が表示されます</p>
        </div>

        <script>
        const startBtn = document.getElementById("start-btn");
        const stopBtn = document.getElementById("stop-btn");
        const resultTag = document.getElementById("result");

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recog = new SpeechRecognition();
        recog.lang = "ja-JP";
        recog.interimResults = false;
        recog.continuous = true;

        let finalText = "";

        startBtn.onclick = () => {
            finalText = "";
            recog.start();
            resultTag.innerText = "認識中…話してください";
        };

        stopBtn.onclick = () => {
            recog.stop();
            resultTag.innerText = "停止しました。処理中…";
        };

        recog.onresult = (event) => {
            for (let i = event.resultIndex; i < event.results.length; i++) {
                if (event.results[i].isFinal) {
                    finalText += event.results[i][0].transcript;
                }
            }
            resultTag.innerText = finalText;

            // Streamlitへ認識結果を送信
            window.parent.postMessage(
                {type: "FROM_JS", text: finalText},
                "*"
            );
        };
        </script>
        """,
        height=250
    )

    # JS からのメッセージを受け取る
    msg = st.experimental_get_query_params().get("speech_event", [""])[0]

    # フロント側から POSTMessage の内容を受け取る仕組み
    def js_event_listener():
        from streamlit.runtime.scriptrunner import add_script_run_ctx
        import threading

        def run():
            import time
            import sys

            while True:
                try:
                    event = st.runtime.scriptrunner.script_requests_queue.get(block=False)
                    if event["type"] == "websocket_message":
                        try:
                            data = json.loads(event["data"])
                            if data.get("type") == "FROM_JS":
                                st.session_state["speech_text"] = data["text"]
                        except:
                            pass
                except:
                    time.sleep(0.05)

        th = threading.Thread(target=run, daemon=True)
        add_script_run_ctx(th)
        th.start()

    js_event_listener()

    # 結果を取得
    text = st.session_state.get("speech_text", "")

    if text:
        st.success("🗣️ 音声認識結果:")
        st.write(text)

# ==========================
# 📁 アップロード音声モード
# ==========================
elif input_mode == "📁 音声ファイルをアップロード":
    uploaded_file = st.file_uploader("音声ファイル(mp3, wav) をアップロードしてください", type=["wav", "mp3"])

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(uploaded_file.read())
            audio_path = tmp_file.name

        r = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio = r.record(source)

        try:
            text = r.recognize_google(audio, language="ja-JP")
            st.success("🗣️ 音声認識結果:")
            st.write(text)
        except Exception as e:
            st.error(f"音声認識に失敗しました: {e}")
            st.stop()

# ==========================
# 感情単語抽出 ＆ Spotify検索
# ==========================
if text:
    emotion_words = ["楽しい", "悲しい", "ワクワク", "落ち着く", "元気", "切ない"]
    detected = [w for w in emotion_words if w in text]

    if not detected:
        st.info("感情を表す単語が見つかりませんでした。")
    else:
        st.write("抽出された感情単語:", ", ".join(detected))

        for keyword in detected:
            st.subheader(f"🎧 「{keyword}」に関連するプレイリスト")

            results = sp.search(q=f"{keyword} プレイリスト", type="playlist", limit=5, market="JP")
            playlists = results["playlists"]["items"]

            if not playlists:
                st.write("見つかりませんでした")
                continue

            for playlist in playlists:
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
