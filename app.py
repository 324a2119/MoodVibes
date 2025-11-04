import gradio as gr
import speech_recognition as sr
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from transformers import pipeline
from dotenv import load_dotenv
import os

# 環境変数読み込み (.env)
load_dotenv()
CLIENT_ID = os.getenv("ff259b9ec7f3420381662c278fed342f")
CLIENT_SECRET = os.getenv("a35403dc7fb64531ba6a98c5794fcef8")

# Spotify API認証
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
))

# 感情分析モデル（日本語可）
emotion_analyzer = pipeline("sentiment-analysis")

def analyze_mood(audio_path):
    # 音声→テキスト
    r = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = r.record(source)
    try:
        text = r.recognize_google(audio_data, language="ja-JP")
    except:
        return "音声を認識できませんでした。", "もう一度お試しください。"

    # 感情分析
    result = emotion_analyzer(text)[0]
    label = result["label"]

    # 感情に応じて検索キーワード設定
    if "POS" in label or "positive" in label.lower():
        query = "happy upbeat"
        mood = "ポジティブ 😊"
    elif "NEG" in label or "negative" in label.lower():
        query = "chill lofi"
        mood = "ネガティブ 😔"
    else:
        query = "relax jazz"
        mood = "ニュートラル 😐"

    # Spotifyでプレイリスト検索
    results = sp.search(q=query, type="playlist", limit=3)
    playlists = []
    for p in results["playlists"]["items"]:
        name = p["name"]
        url = p["external_urls"]["spotify"]
        playlists.append(f"🎵 [{name}]({url})")

    # 出力結果
    playlist_text = "\n".join(playlists)
    return f"🗣️ あなたの話した内容: {text}\n\n感情判定: {mood}", playlist_text

# Gradio UI
app = gr.Interface(
    fn=analyze_mood,
    inputs=gr.Audio(sources=["microphone"], type="filepath", label="今の気分を話してください"),
    outputs=[gr.Textbox(label="解析結果"), gr.Markdown(label="おすすめプレイリスト")],
    title="🎧 MoodTunes AI",
    description="話した内容から感情を分析し、Spotifyのプレイリストをおすすめします。",
)

if __name__ == "__main__":
    app.launch()
